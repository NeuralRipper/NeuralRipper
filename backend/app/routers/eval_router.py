import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect



router = APIRouter(tags=["evaluation"], 
                   description="Handling streaming of the tokens via websocket, accepting client prompt&model, streaming back at token level.")

@router.websocket("/ws/eval")
async def evaluation(websocket: WebSocket):
    # wait and accept websocket connection from frontend
    await websocket.accept()

    try:
        async for message in websocket.iter_text(): 
            # load data into json
            data = json.loads(message)
            # retrieve data from the ws message
            model = data.get("model", "llama-3-70b")
            prompt = data.get("prompt", "")

            if not prompt:
                await websocket.send_json({"error": "No prompt provided"})
                continue

            # stream tokens back to client
            async for token in websocket.app.state.queue_handler.stream_inference(model, prompt):
                await websocket.send_json({"token": token})

            # send completion signal
            await websocket.send_json({"done": True})
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({"error": str(e)})
