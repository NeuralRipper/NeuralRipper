import asyncio
from collections import defaultdict
from typing import AsyncGenerator, List, Tuple
import time
import json

import httpx

from backend.app.handlers.pod_handler import PodHandler


class QueueHandler:
    """
    Handles batching and streaming responses

    1. Client sends prompt via WebSocket
    2. stream_inference() puts (prompt, response_channel) into request_queue
    3. _collect_batch() waits 100ms, grabs up to 8 requests
    4. _process_batch() sends batch to RunPod (async task, non-blocking)
    5. As tokens arrive, _process_batch() routes them:
        choice["index"] → response_channels[index].put(token)
    6. stream_inference() wakes up (was blocked on response_channel.get())
    7. Yields token → WebSocket → Frontend
    8. Loop continues until None signal (end of stream)
    """
    def __init__(self, pod_handler: PodHandler):
        # pod handler to communicate with RunPod
        self.pod_handler = pod_handler

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
        for model in self.pod_handler.list_models():
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
        Send batch as CONCURRENT requests to vLLM, which auto batches them internally for GPU efficiency
        """
        # Python idiom, unpack operator with zip, prompts and response channels
        # [("hi", res_c1), ("hello", res_c2)] -> ("hi", "hello"), (res_c1, res_c2)
        prompts, response_channels = zip(*batch)

        # Get correlated RunPod endpoint URL for this model, and API KEY for auth
        url = self.pod_handler.get_url(model=model)
        api_key = self.pod_handler.get_api_key()

        # Headers for auth bearer
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Create separate async tasks for each prompt
        tasks = []
        for i, prompt in enumerate(prompts):
            task = asyncio.create_task(
                self._stream_single_request(url, headers, model, prompt, response_channels[i])
            )
            tasks.append(task)
        # Return a future aggregating results from the given coroutines/futures.
        # Send all requests concurrently, vLLM will batch them internally    
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _stream_single_request(
        self,
        url: str,
        headers: dict,
        model: str,
        prompt: str,
        response_channel: asyncio.Queue
    ):
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            # httpx and aiohttp both works as async http client, but httpx is preferrable with morden design and better maintained
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Stream response from RunPod
                async with client.stream(
                    "POST",
                    f"{url}/chat/completions",
                    json=payload,
                    headers=headers
                ) as res:
                    # Parse Server-Sent Events(SSE) format
                    async for line in res.aiter_lines():
                        if not line.strip() or line.strip() == "data: [DONE]":
                            continue

                        if line.startswith("data: "):
                            # Parse json datas, remove "data: " prefix
                            data = json.loads(line[6:])

                            # Single Request, Route the tokens back to corresponding channel
                            for choice in data.get("choices", []):
                                delta = choice.get("delta", {})
                                content = delta.get("content", "")

                                if content:
                                    # Send token to the client waiting on this channel
                                    await response_channel.put(content)

        except Exception as e:
            # If any error, send error msg to all clients no matter who causes it
            await response_channel.put(f"Error: {str(e)}")
        finally:
            # Signal complete to all clients(None -> End of stream)
            await response_channel.put(None)
