from fastapi import WebSocket


class LLMEvalHandler:
    """
    Handle websocket connections for LLM inference streaming
    """
    def __init__(self):
        pass

    # TODO, define all functions, following https://fastapi.tiangolo.com/advanced/websockets/
    async def handle_message(self, websocket: WebSocket, message: dict):
        if message['type'] == "chat":
            content = message["content"]
            print(content)

            response = f"Received message: {content}"
    
            await websocket.send_text(response)