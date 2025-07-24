from fastapi import APIRouter
from contextlib import asynccontextmanager
from fastapi.responses import StreamingResponse
import mlflow

from app.handlers.text_model_handler import TextModelHandler


router = APIRouter(prefix="/infer", tags=['infer'])
handler = TextModelHandler()

def get_default_text_model():
    """Get the first available text model from MLflow"""
    try:
        mlflow.set_tracking_uri("https://mlflow-server-631028107267.us-central1.run.app/")
        
        # Search for registered models
        models = mlflow.search_registered_models()
        
        # Filter for text models (look for common text model patterns)
        text_model_patterns = ["gpt", "bert", "t5", "llama", "text", "conversational"]
        
        for model in models:
            model_name = model.name.lower()
            if any(pattern in model_name for pattern in text_model_patterns):
                latest_version = model.latest_versions[0] if model.latest_versions else None
                if latest_version:
                    model_uri = f"models:/{model.name}/{latest_version.version}"
                    print(f"Found text model: {model_uri}")
                    return model_uri
        
        print("No text models found in MLflow registry")
        return None
        
    except Exception as e:
        print(f"Failed to search MLflow models: {e}")
        return None


@asynccontextmanager
async def lifespan(app):
    """Lifespan context manager for startup/shutdown events"""
    # Startup: Load model when the server starts
    print("Loading text model at startup...")
    
    # Dynamically get first available text model
    model_uri = get_default_text_model()
    fallback_model = "gpt2"
    
    handler.load_model(model_uri=model_uri, fallback_model=fallback_model)
    print("Text model ready for inference")
    
    # Server runs here
    yield  
    
    # Shutdown: Cleanup resources
    print("Shutting down text model handler...")
    handler.shutdown()
    print("Cleanup complete")


@router.post("/chat")
async def chatCompletion(data: dict):
    """
    Streaming chat completion endpoint:
        1. Takes a generator function that yields data chunks
        2. Sends each chunk to the client immediately as it's produced
        3. Client receives data progressively (streaming)
        4. Connection stays open until generator is exhausted
    
    Key benefits:
        - Reduced perceived latency (user sees response immediately)
        - Lower memory usage (don't need to store full response)
        - Better user experience for long-running operations
    """
    
    # Extract prompt from request body
    prompt = data.get("prompt", "")

    # Validate input, return default value if empty
    if not prompt:
        prompt = "Yo what's up my choom!"
    
    # Create streaming response
    return StreamingResponse(
        generate_text_stream(prompt=prompt),       # call func with prompt
        media_type="text/plain"     # tells client this is plain text
    )


def generate_text_stream(prompt: str):
    """
    Async generator that yields text chunks for streaming
    
    This function bridges the sync model generation with async FastAPI
    """

    max_tokens = 100         # Maximum tokens to generate
    temperature = 0.75       # Creativity level (0.0 = deterministic, 1.0 = very creative)

    try:
        for chunk in handler.generate_stream(
            prompt=prompt,
            max_new_tokens=max_tokens,
            temperature=temperature
        ):
            yield chunk
    except Exception as e:
        yield f"Error generatig response: {e}"


