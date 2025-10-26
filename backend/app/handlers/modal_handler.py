"""
Modal Handler - Interface between FastAPI backend and Modal GPU inference

Provides async streaming interface for queue_handler.
"""

import modal
from typing import AsyncGenerator


class ModalHandler:
    """
    Manages connections to Modal serverless inference.
    Replaces PodHandler for Modal-based streaming.
    """

    def __init__(self, app_name: str = "neuralripper-inference"):
        self.app_name = app_name
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
        """List available models (hardcoded for now)."""
        # TODO: Query Modal Volume for actual models
        return ["qwen"]

    async def stream_inference(
        self,
        model_name: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> AsyncGenerator[str, None]:
        """
        Stream inference tokens from Modal GPU.

        Args:
            model_name: Which model to use
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Max tokens to generate

        Yields:
            Individual token strings as they're generated
        """
        model = self.get_model_instance(model_name)
        messages = [{"role": "user", "content": prompt}]

        async for chunk in model.generate_stream.remote_gen(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            yield chunk
