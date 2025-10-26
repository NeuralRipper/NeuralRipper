import asyncio
from collections import defaultdict
from typing import AsyncGenerator, List, Tuple
import time

from app.handlers.modal_handler import ModalHandler


class QueueHandler:
    """
    Handles batching and streaming responses

    1. Client sends prompt via WebSocket
    2. stream_inference() puts (prompt, response_channel) into request_queue
    3. _collect_batch() waits 100ms, grabs up to 8 requests
    4. _process_batch() sends batch to Modal (async task, non-blocking)
    5. As tokens arrive, _process_batch() routes them to response channels
    6. stream_inference() wakes up (was blocked on response_channel.get())
    7. Yields token → WebSocket → Frontend
    8. Loop continues until None signal (end of stream)
    """
    def __init__(self, modal_handler: ModalHandler):
        # modal handler to communicate with Modal GPUs
        self.modal_handler = modal_handler

        # share queues for batching requests by model
        # {model_name: Queue of (prompt, response_channel)}
        self.requests_queues = defaultdict(asyncio.Queue)

        # Background async workers(tasks), one per model
        self.workers = {}

        # Batching config
        self.batch_timeout = 0.1    # Max wait time (100ms)
        self.max_batch_size = 5     # Max requests per batch(5)

    def start_workers(self):
        """
        Start background workers for all configured models

        llama: worker1, while loop keeps collecting and processing in separate task
        gpt2: worker2, while loop do the same
        ...
        """
        for model in self.modal_handler.list_models():
            self.workers[model] = asyncio.create_task(self._worker(model))

    async def _worker(self, model: str):
        """Background worker continuously processes batches for a model, collect and process batches"""
        while True:
            # Collect a batch for current model
            batch = await self._collect_batch(model)

            if batch:
                # process batch in a separate task(non blocking async)
                asyncio.create_task(self._process_batch(model, batch))
            else:
                # No requests, sleep a little bit to avoid frequent check
                await asyncio.sleep(0.1)

    async def stream_inference(self, model: str, prompt: str) -> AsyncGenerator[str, None]:
        """
        Submit a prompt then stream tokens back in real-time
        1. Create response channel(async.Queue) for this request
        2. Adds (prompt, response_channel) to the shared request queue
        3. Wait for the tokens to arrive in the response channel
        4. Yields tokens back to the caller (WebSocket handler)
        
        Args:
            model: Model name (e.g., "llama-3-70b, our fine-tuned model")
            prompt: User's input prompt
        Yields:
            str: Tokens as they arrive from RunPod
        """
        # create a one-time response channel for this request
        response_channel = asyncio.Queue()
        
        # Add (prompt, response_channel) to the shared request queue
        await self.requests_queues[model].put((prompt, response_channel))

        # Wait for the tokens to arrive
        while True:
            token = await response_channel.get()
            if token is None:   # End of stream signal
                break
            yield token         # Keep yielding tokens
            
    async def _collect_batch(self, model: str) -> List[Tuple[str, asyncio.Queue]]:    
        """
        Collect a batch of requests within certain time range(interval)
        This is the dequeue process, getting requests from the same model in shared requests queue
        1. Wait for time limit
        2. Collect up to max_batch_size
        3. Return the requests when timeout or batch is full

        Balance the latency(timeout) and efficiency(larger batch -> better GPU utilization)

        Args:
            model: Model name
        Return:
            List of requests, [(llama, res_channel1), (gpt2, res_channel2), ....]
        """
        batch = []
        end_time = time.time() + self.batch_timeout

        # Keep collecting requests until times up or the batch is full
        while time.time() < end_time and len(batch) < self.max_batch_size:
            try:
                # wait for the remaining time
                item = await asyncio.wait_for(
                    self.requests_queues[model].get(),
                    timeout=end_time - time.time()
                )
                batch.append(item)
            except asyncio.TimeoutError:
                # Timeout, process what we got in the batch
                break
        return batch
    
    async def _process_batch(self, model: str, batch: List[Tuple[str, asyncio.Queue]]):
        """
        Send batch as CONCURRENT requests to Modal, which auto batches them internally for GPU efficiency
        """
        # Python idiom, unpack operator with zip, prompts and response channels
        # [("hi", res_c1), ("hello", res_c2)] -> ("hi", "hello"), (res_c1, res_c2)
        prompts, response_channels = zip(*batch)

        # Create separate async tasks for each prompt
        tasks = []
        for i, prompt in enumerate(prompts):
            task = asyncio.create_task(
                self._stream_single_request(model, prompt, response_channels[i])
            )
            tasks.append(task)
        # Return a future aggregating results from the given coroutines/futures.
        # Send all requests concurrently, Modal vLLM will batch them internally
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _stream_single_request(
        self,
        model: str,
        prompt: str,
        response_channel: asyncio.Queue
    ):
        """
        Stream tokens from Modal GPU to response channel

        Args:
            model: Model name (e.g., "qwen")
            prompt: User's input prompt
            response_channel: Queue to send tokens back to client
        """
        try:
            # Stream tokens from Modal GPU using modal_handler
            async for token in self.modal_handler.stream_inference(
                model_name=model,
                prompt=prompt,
                temperature=0.7,
                max_tokens=500
            ):
                # Send token to the client waiting on this channel
                await response_channel.put(token)

        except Exception as e:
            # If any error, send error msg to client
            print(f"Error in _stream_single_request: {e}")
            import traceback
            traceback.print_exc()
            await response_channel.put(f"Error: {str(e)}")
        finally:
            # Signal complete (None -> End of stream)
            print(f"Stream complete for prompt: {prompt[:50]}...")
            await response_channel.put(None)
