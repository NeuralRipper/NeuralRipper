from concurrent.futures import ThreadPoolExecutor
import mlflow
import mlflow.pytorch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
import torch


class TextModelHandler:
    """
    Service to load and manage trained models
    """
    
    def __init__(self, max_workers: int = 8):
        self.model = None
        self.tokenizer = None
        self.device = None
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def load_model(self, model_uri: str = None, fallback_model: str = "gpt2"):
        # Get tokenizer name from model name
        tokenizer_name = fallback_model

        if model_uri:
            try:
                print(f"Loading trained model from MLflow: {model_uri}")
                self.model = mlflow.pytorch.load_model(model_uri)
                print("Loaded trained model from MLflow")
            except Exception as e:
                print(f"MLflow loading failed: {e}")
                print(f"Falling back to pretrained {fallback_model}...")
                self.model = AutoModelForCausalLM.from_pretrained(fallback_model)
                print(f"Loaded pretrained {fallback_model} model")
        else:
            print(f"No MLflow model URI provided, loading pretrained {fallback_model}...")
            self.model = AutoModelForCausalLM.from_pretrained(fallback_model)
            print(f"Loaded pretrained {fallback_model} model")

        # Load tokenizer (use AutoTokenizer for flexibility)
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

        # GPT-2 tokenizer doesn't have a pad token, so we set it to eos_token
        # This is needed for batch processing and proper attention masking
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Determine the best device to run inference on
        # Priority: CUDA > MPS (Apple Silicon) > CPU
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
            print("Using CUDA GPU")
        elif torch.backends.mps.is_available():
            self.device = torch.device("mps") 
            print("Using Apple MPS")
        else:
            self.device = torch.device("cpu")
            print("Using CPU")


        # Move model to the selected device
        self.model.to(self.device)
        
        # Set model to evaluation mode (disables dropout, batch norm, etc.)
        # This is important for consistent inference results
        self.model.eval()
        
        print(f"Model loaded successfully on {self.device}")

    def generate_stream(self, prompt: str, max_new_tokens: int = 100, temperature: float = 0.7):
        """
        Generate streaming response for a given prompt
        
        TextIteratorStreamer is a special iterator that works with model.generate()
        to yield tokens one by one as they're generated, instead of waiting for 
        the complete response.
        
        1. Create a TextIteratorStreamer linked to the tokenizer
        2. Pass this streamer to model.generate() along with other parameters
        3. Run generation in a separate thread (non-blocking)
        4. The streamer yields decoded text pieces as tokens are generated
        5. We can iterate over the streamer to get text chunks in real-time
        """

        # Ensure model is loaded (this shouldn't happen if startup event worked)
        if self.model is None:
            print("Model not loaded at startup, loading now...")
            self.load_model()

        # Tokenize the input prompt, return_tensors="pt" returns PyTorch tensors
        inputs = self.tokenizer(prompt, return_tensors="pt")
        input_ids = inputs['input_ids'].to(self.device)

        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,       # Don't repeat the input prompt
            skip_special_tokens=True  # Clean output without special tokens
        )

        # Setup generation parameters
        generation_kwargs = {
            "input_ids": input_ids,
            "streamer": streamer,               # Our streaming object
            "max_new_tokens": max_new_tokens,   # How many new tokens to generate
            "temperature": temperature,         # Randomness (0.0 = deterministic, 1.0 = very random)
            "do_sample": True,                  # Enable sampling (needed for temperature)
            "pad_token_id": self.tokenizer.eos_token_id,  # Padding token
            "eos_token_id": self.tokenizer.eos_token_id,  # End of sequence token
        }

        # Submit generation task to the thread pool
        future = self.executor.submit(self.model.generate, **generation_kwargs)
        
        for new_text in streamer:
            yield new_text
        
        # Ensure task ends well
        future.result()

    def shutdown(self):
        """Cleanup resources on shutdown"""
        try:
            if hasattr(self, 'model'):
                del self.model
            if hasattr(self, 'tokenizer'):
                del self.tokenizer
            print("TextModelHandler shutdown complete")
        except Exception as e:
            print(f"Error during TextModelHandler shutdown: {e}")
