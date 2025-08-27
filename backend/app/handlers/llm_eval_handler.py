import json
from fastapi import WebSocket
from app.utils.prime_intellect_client import PrimeIntellectClient


class LLMEvalHandler:
    """
    Handle websocket connections for LLM inference streaming
    """
    def __init__(self):
        self.pi_client = PrimeIntellectClient()
        self.current_pod_id = None

    async def handle_message(self, websocket: WebSocket, message: dict):
        if message['type'] == "chat":
            content = message["content"]
            await self.stream_chat_response(websocket, content)

    async def stream_chat_response(self, websocket: WebSocket, prompt: str):
        """Stream response from Prime Intellect pod"""
        try:
            # For now, use the complete workflow that manages pod lifecycle
            async for chunk in self.pi_client.chat_complete(prompt):
                if chunk.startswith('[') and chunk.endswith(']'):
                    # Status message
                    await self.send_status(websocket, chunk[1:-1])
                else:
                    # Response chunk
                    await self.send_chunk(websocket, chunk)
            
            # Send completion
            await websocket.send_text(json.dumps({
                "type": "response_complete"
            }))
            
        except Exception as e:
            await self.send_error(websocket, str(e))

    async def send_chunk(self, websocket: WebSocket, chunk: str):
        """Send response chunk to client"""
        await websocket.send_text(json.dumps({
            "type": "response_chunk",
            "chunk": chunk
        }))

    async def send_status(self, websocket: WebSocket, message: str):
        """Send status update to client"""
        await websocket.send_text(json.dumps({
            "type": "status",
            "message": message
        }))

    async def send_error(self, websocket: WebSocket, error_message: str):
        """Send error message to client"""
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": error_message
        }))
    