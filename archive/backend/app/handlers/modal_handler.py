"""
Modal Handler - Interface between FastAPI backend and Modal GPU inference

Provides async streaming interface for queue_handler.
"""

import modal
import asyncio
from typing import AsyncGenerator

from app.config import settings


class ModalHandler:
    """
    Manages connections to Modal serverless inference.
    Replaces PodHandler for Modal-based streaming.
    """

    def __init__(self, app_name: str | None = None):
        self.app_name = app_name or settings.MODAL_APP_NAME
        self._model_class = None
        self._model_instances = {}

    def _get_model_class(self):
        """Lazy load the Modal Model class."""
        if self._model_class is None:
            self._model_class = modal.Cls.from_name(self.app_name, "Model")
        return self._model_class

    def get_model_instance(self, model_name: str):
        """Get or create Modal Model instance for given model name."""
        if model_name not in self._model_instances:
            ModelClass = self._get_model_class()
            self._model_instances[model_name] = ModelClass(model_name=model_name)
        return self._model_instances[model_name]

    def list_models(self) -> list[str]:
        """List available models from configuration."""
        # TODO: Query Modal Volume for actual models dynamically
        return settings.AVAILABLE_MODELS

    async def stream_inference(
        self,
        model_name: str,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream inference tokens from Modal GPU.

        Args:
            model_name: Which model to use
            prompt: Input prompt
            temperature: Sampling temperature (defaults from config)
            max_tokens: Max tokens to generate (defaults from config)

        Yields:
            Individual token strings as they're generated
        """
        # Use config defaults if not provided
        temperature = temperature if temperature is not None else settings.DEFAULT_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else settings.DEFAULT_MAX_TOKENS

        model = self.get_model_instance(model_name)
        messages = [{"role": "user", "content": prompt}]

        # Modal's remote_gen() returns a SYNC generator, not async
        # We need to run it in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        gen = model.generate_stream.remote_gen(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Use lambda to avoid StopIteration crossing async boundary
        while True:
            chunk = await loop.run_in_executor(None, lambda: next(gen, None))
            if chunk is None:  # Generator exhausted
                break
            yield chunk
