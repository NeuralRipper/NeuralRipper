# TODO: Terminal Input → WebSocket Message → Backend Handler → Prime Intellect Pod → Your Model Inference → Response → WebSocket → Terminal Display
# This part will be using websocket?

import json
from fastapi import APIRouter, WebSocket
from ..handlers.llm_eval_handler import LLMEvalHandler


router = APIRouter()


@router.websocket("/ws/eval")
async def llm_evaluate(websocket: WebSocket):
    await websocket.accept()
    handler = LLMEvalHandler()

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await handler.handle_message(websocket, message)
    except Exception as e:
        print(e)

