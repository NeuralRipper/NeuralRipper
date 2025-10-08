import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter(tags=["evaluation"])


@router.websocket("/ws/eval")
async def evaluation(websocket: WebSocket):
    """
        WebSocket endpoint for streaming LLM inference.
        
        Accepts: {"model": "qwen-0.5b", "prompt": "your prompt"}
        Streams: {"token": "..."}, {"done": true}
    """
    # wait and accept websocket connection from frontend
    await websocket.accept()

    try:
        async for message in websocket.iter_text():
            print(f"Received message: {message}")
            # load data into json
            data = json.loads(message)
            # retrieve data from the ws message
            model = data.get("model", "llama-3-70b")
            prompt = data.get("prompt", "")

            if not prompt:
                await websocket.send_json({"error": "No prompt provided"})
                continue

            print(f"Starting inference for model={model}, prompt={prompt}")
            # stream tokens back to client
            async for token in websocket.app.state.queue_handler.stream_inference(model, prompt):
                print(f"Sending token: {token}")
                await websocket.send_json({"token": token})

            # send completion signal
            print("Sending done signal")
            await websocket.send_json({"done": True})
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()
        await websocket.send_json({"error": str(e)})
