"""
Configuration management for NeuralRipper backend
Uses environment variables with sensible defaults
"""

import os
from typing import List


class Settings:
    """Application settings loaded from environment variables"""

    # Modal Configuration
    MODAL_APP_NAME: str = os.getenv("MODAL_APP_NAME", "neuralripper-inference")

    # Default Model
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "qwen")

    # Available Models (comma-separated in env)
    AVAILABLE_MODELS: List[str] = os.getenv(
        "AVAILABLE_MODELS",
        "qwen,llama-3-70b"
    ).split(",")

    # Queue Settings
    BATCH_TIMEOUT: float = float(os.getenv("BATCH_TIMEOUT", "0.1"))
    MAX_BATCH_SIZE: int = int(os.getenv("MAX_BATCH_SIZE", "5"))

    # Inference Settings
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    DEFAULT_MAX_TOKENS: int = int(os.getenv("DEFAULT_MAX_TOKENS", "500"))


# Global settings instance
settings = Settings()
