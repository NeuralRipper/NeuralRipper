"""
Prime Intellect API client for pod management
"""

import os
import json
import asyncio
import aiohttp
import boto3
from typing import AsyncGenerator


class PrimeIntellectClient:
    def __init__(self):
        self.base_url = "https://api.primeintellect.ai/api/v1"
        self.api_key = self._init_api_key()
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _init_api_key(self):
        """Get API key from AWS Secrets Manager or environment"""
        try:
            # Try AWS Secrets Manager first
            aws_client = boto3.client("secretsmanager")
            response = aws_client.get_secret_value(SecretId="neuralripper")
            secrets = json.loads(response['SecretString'])
            if "PRIME_API_KEY" in secrets:
                print("Successfully retrieved api key")
                return secrets["PRIME_API_KEY"]
        except Exception as e:
            print(f"AWS Secrets Manager failed: {e}")

    async def get_gpu_availability(self):
        """Get available GPU types and configurations"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/availability",
                headers=self.headers
            ) as response:
                return await response.json()

    async def create_pod(self, 
                        model_name: str = "meta-llama/Llama-3.1-8B-Instruct",
                        max_price: float = 2.0):
        """Create a new pod for inference with dynamic configuration based on availability"""  
        # Get available GPUs and pick the best option
        availability = await self.get_gpu_availability()
        
        # Find suitable GPU option under max price
        suitable_gpu = None
        for gpu in availability.get('data', []):
            if gpu.get('priceHr', 999) <= max_price:
                suitable_gpu = gpu
                break
        
        if not suitable_gpu:
            raise Exception(f"No suitable GPU found under ${max_price}/hr")
        
        # Select appropriate image for LLM
        available_images = suitable_gpu.get('availableImages', [])
        image = "vllm_llama_8b" if "vllm_llama_8b" in available_images else available_images[0]
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "pod": {
                    "name": f"eval-pod-{int(asyncio.get_event_loop().time())}",
                    "cloudId": suitable_gpu['cloudId'],
                    "gpuType": suitable_gpu['gpuType'],
                    "socket": suitable_gpu.get('socket', 'PCIe'),
                    "gpuCount": 1,
                    "diskSize": 50,
                    "vcpus": 4,
                    "memory": 32,
                    "maxPrice": max_price,
                    "image": image,
                    "envVars": [
                        {
                            "key": "MODEL_NAME",
                            "value": model_name
                        },
                        {
                            "key": "TENSOR_PARALLEL_SIZE",
                            "value": "1"
                        }
                    ],
                    "autoRestart": True
                },
                "provider": {
                    "type": suitable_gpu.get('provider', 'runpod')
                }
            }
            
            async with session.post(
                f"{self.base_url}/pods",
                json=payload,
                headers=self.headers
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    pod_id = data['id']
                    print(f"Pod created: {pod_id}")
                    await self.wait_for_pod_ready(pod_id)
                    return pod_id
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to create pod: {response.status} - {error_text}")

    async def wait_for_pod_ready(self, pod_id: str, timeout: int = 300):
        """Wait for pod to be ready"""
        for _ in range(timeout // 10):
            status = await self.get_pod_status(pod_id)
            if status.get('status') == 'RUNNING':
                print(f"Pod {pod_id} is ready!")
                return True
            elif status.get('status') in ['FAILED', 'TERMINATED']:
                raise Exception(f"Pod failed to start: {status}")
            
            print(f"Pod status: {status.get('status', 'unknown')}, waiting...")
            await asyncio.sleep(10)
        
        raise Exception(f"Pod {pod_id} didn't become ready within {timeout} seconds")

    async def get_pods_history(self):
        """Get pods history"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/pods/history", headers=self.headers) as response:
                return await response.json()
        
    async def get_pods_status(self):
        """Get status of all pods"""       
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/pods", headers=self.headers) as response:
                return await response.json()

    async def get_pod_status(self, pod_id: str) -> dict:
        """Get single pod status"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/pods/{pod_id}",
                headers=self.headers
            ) as response:
                return await response.json()

    async def stream_chat(self, pod_id: str, prompt: str) -> AsyncGenerator[str, None]:
        """Stream chat response from the pod"""
        # Real implementation would connect to pod endpoint
        status = await self.get_pod_status(pod_id)
        endpoint = status.get('endpoint', '')
        
        payload = {
            "model": "meta-llama/Llama-3.1-8B-Instruct",
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{endpoint}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                async for line in response.content:
                    if line:
                        chunk = line.decode('utf-8').strip()
                        if chunk.startswith('data: '):
                            data = chunk[6:]
                            if data == '[DONE]':
                                break
                            try:
                                parsed = json.loads(data)
                                content = parsed['choices'][0]['delta'].get('content', '')
                                if content:
                                    yield content
                            except (json.JSONDecodeError, KeyError):
                                continue

    async def delete_pod(self, pod_id: str):
        """Delete pod to stop billing"""    
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.base_url}/pods/{pod_id}",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    print(f"Pod {pod_id} deleted successfully")
                else:
                    error_text = await response.text()
                    print(f"Failed to delete pod: {response.status} - {error_text}")

    async def chat_complete(self, prompt: str) -> AsyncGenerator[str, None]:
        """Complete workflow: create pod, chat, delete pod"""
        pod_id = None
        try:
            yield "[Creating pod...]"
            pod_id = await self.create_pod()
            
            yield "[Pod ready, generating response...]"
            async for chunk in self.stream_chat(pod_id, prompt):
                yield chunk
                
        except Exception as e:
            yield f"[Error: {str(e)}]"
        finally:
            if pod_id:
                yield "[Cleaning up pod...]"
                await self.delete_pod(pod_id)
