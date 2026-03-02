
import os
from typing import Dict


class PodHandler:
    """
    Manage RunPod endpoint URLs for different models(original or fine-tuned)
    
    llama: endpoint_id_1
    gpt2: endpoint_id_2
    fine-tuned-mlflow: endpoint_id_3
    ...
    """
    def __init__(self):
        # model: endpoint_url
        self.endpoints: Dict[str, str] = {}

    def init_endpoints(self):
        """
        Load all endpoint urls from .env file

        Add to .env:
          RUNPOD_API_KEY=runpod_api_key
          RUNPOD_ENDPOINT_LLAMA3_70B=endpoint_id_1
          RUNPOD_ENDPOINT_GPT2=endpoint_id_2
          RUNPOD_ENDPOINT_CUSTOM_FINETUNE=endpoint_id_3
        """
        api_key = os.getenv("RUNPOD_API_KEY")
        if not api_key:
            raise ValueError("RUNPOD_API_KEY not set!")
        
        self.api_key = api_key

        # Map model name to the endpoint urls, TODO: dynamic loading if there's more
        # Use actual vLLM model names that match what's loaded on RunPod (case-sensitive)
        model_configs = {
              "qwen/qwen2.5-0.5b-instruct": os.getenv("RUNPOD_ENDPOINT_QWEN"),
          }
        
        # Build OpenAI compatible URLs for models
        for model_name, endpoint_id in model_configs.items():
            if endpoint_id:
                self.endpoints[model_name] = f"https://api.runpod.ai/v2/{endpoint_id}/openai/v1"

        if not self.endpoints:
            raise ValueError("No RunPod endpoints configured")
        
    def get_url(self, model: str):
        """Retrieve OpenAI compatible URL for the model"""
        if model not in self.endpoints:
            available = ", ".join(self.endpoints.keys())
            raise ValueError(f"Model '{model}' not found. Available: {available}")
        return self.endpoints[model]
    
    def get_api_key(self):
        """Get RunPod API KEY for accessing the endpoints"""
        return self.api_key
    
    def list_models(self):
        """List all configured models we set up in RunPod"""
        return list(self.endpoints.keys())
