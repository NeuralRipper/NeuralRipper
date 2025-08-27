import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.handlers.llm_eval_handler import LLMEvalHandler

router = APIRouter()
handler = LLMEvalHandler()


@router.websocket("/ws/eval")
async def evaluate(websocket: WebSocket):
    """
    1. Accept new websocket connection
    2. Handle incoming prompt via handler
    """
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await handler.handle_message(websocket, message)
    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()
