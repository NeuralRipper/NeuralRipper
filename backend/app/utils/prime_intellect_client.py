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
        
        # Fallback to environment variable
        api_key = os.environ.get('PRIME_API_KEY')
        if api_key:
            return api_key
            
        # Demo mode
        print("WARNING: No PRIME_API_KEY found - using demo mode")
        return "demo"
        

    async def create_pod(self, 
                        model_name: str = "meta-llama/Llama-3.1-8B-Instruct",
                        gpu_type: str = "RTX4090",
                        gpu_count: int = 1,
                        max_price: float = 2.0):
        """Create a new pod for inference with configurable parameters"""
        if self.api_key == "demo":
            # Demo mode - simulate pod creation
            await asyncio.sleep(1)
            return "demo-pod-123"
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "pod": {
                    "name": f"eval-pod-{int(asyncio.get_event_loop().time())}",
                    "image": "primeintellect/vllm:latest",
                    "gpuType": gpu_type,
                    "gpuCount": gpu_count,
                    "diskSize": 50,
                    "vcpus": 4,
                    "memory": 32,
                    "maxPrice": max_price,
                    "envVars": [
                        {
                            "key": "MODEL_NAME",
                            "value": model_name
                        },
                        {
                            "key": "TENSOR_PARALLEL_SIZE",
                            "value": str(gpu_count)
                        }
                    ],
                    "autoRestart": True
                },
                "provider": {
                    "type": "runpod"
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
        if self.api_key == "demo":
            await asyncio.sleep(2)
            return True
            
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

    async def get_pods(self):
        """Get all pods"""
        if self.api_key == "demo":
            return [{"id": "demo-pod-123", "status": "RUNNING"}]
            
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/pods", headers=self.headers) as response:
                return await response.json()

    async def get_pods_history(self):
        """Get pods history"""
        if self.api_key == "demo":
            return {"data": []}
            
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/pods/history", headers=self.headers) as response:
                return await response.json()
        
    async def get_pods_status(self):
        """Get status of all pods"""
        return await self.get_pods()

    async def get_pod_status(self, pod_id: str) -> dict:
        """Get single pod status"""
        if self.api_key == "demo":
            return {"status": "RUNNING", "endpoint": "http://demo.local:8000"}
            
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/pods/{pod_id}",
                headers=self.headers
            ) as response:
                return await response.json()

    async def stream_chat(self, pod_id: str, prompt: str) -> AsyncGenerator[str, None]:
        """Stream chat response from the pod"""
        if self.api_key == "demo":
            # Demo response
            demo_response = f"🤖 Demo response to: '{prompt}'\n\nThis is a simulated streaming response from Prime Intellect. In production, this would connect to your actual pod and stream real LLM responses.\n\nThe pod lifecycle management is working correctly!"
            
            for chunk in demo_response.split():
                yield chunk + " "
                await asyncio.sleep(0.1)
            return
        
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
        if self.api_key == "demo":
            print(f"Demo: Pod {pod_id} deleted")
            return
            
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
    
    



    