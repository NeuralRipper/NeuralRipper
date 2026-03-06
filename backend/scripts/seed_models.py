"""
Seed ~25 curated LLM models into the database with VRAM estimates.
Upserts: skips if hf_model_id already exists.

Called automatically on server startup via main.py lifespan.
Can also run standalone: cd backend && uv run python scripts/seed_models.py

min_gpu: minimum GPU tier required (architecture constraints, not just VRAM).
  - None = runs on any GPU (T4+)
  - "a10g" = needs A10G+ (compute 8.0+, e.g. Gemma 2 sliding window attn)
  - "a100" = needs A100+
  - "h100" = needs H100
"""

import asyncio
import logging
import sys
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

# allow standalone execution from scripts/ dir
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import Model

logger = logging.getLogger(__name__)

MODELS = [
    # Qwen 2.5 family
    {"name": "Qwen2.5-0.5B-Instruct", "hf_model_id": "Qwen/Qwen2.5-0.5B-Instruct", "parameter_count": 500_000_000, "vram_gb": 2, "min_gpu": None, "description": "Qwen2.5 0.5B — ultra-lightweight, fast inference"},
    {"name": "Qwen2.5-1.5B-Instruct", "hf_model_id": "Qwen/Qwen2.5-1.5B-Instruct", "parameter_count": 1_500_000_000, "vram_gb": 4, "min_gpu": None, "description": "Qwen2.5 1.5B — small but capable"},
    {"name": "Qwen2.5-3B-Instruct", "hf_model_id": "Qwen/Qwen2.5-3B-Instruct", "parameter_count": 3_000_000_000, "vram_gb": 7, "min_gpu": None, "description": "Qwen2.5 3B — balanced size/performance"},
    {"name": "Qwen2.5-7B-Instruct", "hf_model_id": "Qwen/Qwen2.5-7B-Instruct", "parameter_count": 7_000_000_000, "vram_gb": 16, "min_gpu": None, "description": "Qwen2.5 7B — strong 7B-class model"},
    {"name": "Qwen2.5-14B-Instruct", "hf_model_id": "Qwen/Qwen2.5-14B-Instruct", "parameter_count": 14_000_000_000, "vram_gb": 30, "min_gpu": None, "description": "Qwen2.5 14B — mid-tier, needs A100+"},
    {"name": "Qwen2.5-32B-Instruct", "hf_model_id": "Qwen/Qwen2.5-32B-Instruct", "parameter_count": 32_000_000_000, "vram_gb": 68, "min_gpu": None, "description": "Qwen2.5 32B — large, needs H100"},
    # Llama 3.x family
    {"name": "Llama-3.2-1B-Instruct", "hf_model_id": "meta-llama/Llama-3.2-1B-Instruct", "parameter_count": 1_000_000_000, "vram_gb": 3, "min_gpu": None, "description": "Llama 3.2 1B — lightweight edge model"},
    {"name": "Llama-3.2-3B-Instruct", "hf_model_id": "meta-llama/Llama-3.2-3B-Instruct", "parameter_count": 3_000_000_000, "vram_gb": 7, "min_gpu": None, "description": "Llama 3.2 3B — compact general-purpose"},
    {"name": "Llama-3.1-8B-Instruct", "hf_model_id": "meta-llama/Llama-3.1-8B-Instruct", "parameter_count": 8_000_000_000, "vram_gb": 17, "min_gpu": None, "description": "Llama 3.1 8B — flagship 8B, strong reasoning"},
    # Phi family (Microsoft)
    {"name": "Phi-3-mini-4k", "hf_model_id": "microsoft/Phi-3-mini-4k-instruct", "parameter_count": 3_800_000_000, "vram_gb": 8, "min_gpu": None, "description": "Phi-3 Mini 3.8B — strong for its size"},
    {"name": "Phi-4", "hf_model_id": "microsoft/phi-4", "parameter_count": 14_000_000_000, "vram_gb": 30, "min_gpu": None, "description": "Phi-4 14B — latest from Microsoft"},
    # Gemma 2 family (Google) — needs compute 8.0+ (sliding window attn shared memory)
    {"name": "Gemma-2-2B-it", "hf_model_id": "google/gemma-2-2b-it", "parameter_count": 2_000_000_000, "vram_gb": 5, "min_gpu": "a10g", "description": "Gemma 2 2B — lightweight Google model"},
    {"name": "Gemma-2-9B-it", "hf_model_id": "google/gemma-2-9b-it", "parameter_count": 9_000_000_000, "vram_gb": 19, "min_gpu": "a10g", "description": "Gemma 2 9B — mid-tier Google model"},
    {"name": "Gemma-2-27B-it", "hf_model_id": "google/gemma-2-27b-it", "parameter_count": 27_000_000_000, "vram_gb": 56, "min_gpu": "a10g", "description": "Gemma 2 27B — large, needs H100"},
    # Mistral family
    {"name": "Mistral-7B-Instruct-v0.3", "hf_model_id": "mistralai/Mistral-7B-Instruct-v0.3", "parameter_count": 7_000_000_000, "vram_gb": 15, "min_gpu": None, "description": "Mistral 7B v0.3 — proven 7B architecture"},
    # DeepSeek R1 distills
    {"name": "DeepSeek-R1-Distill-1.5B", "hf_model_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B", "parameter_count": 1_500_000_000, "vram_gb": 4, "min_gpu": None, "description": "DeepSeek R1 distilled to 1.5B — reasoning-tuned"},
    {"name": "DeepSeek-R1-Distill-7B", "hf_model_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", "parameter_count": 7_000_000_000, "vram_gb": 16, "min_gpu": None, "description": "DeepSeek R1 distilled to 7B — reasoning-tuned"},
    {"name": "DeepSeek-R1-Distill-14B", "hf_model_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B", "parameter_count": 14_000_000_000, "vram_gb": 30, "min_gpu": None, "description": "DeepSeek R1 distilled to 14B — strong reasoning"},
    {"name": "DeepSeek-R1-Distill-32B", "hf_model_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B", "parameter_count": 32_000_000_000, "vram_gb": 68, "min_gpu": None, "description": "DeepSeek R1 distilled to 32B — needs H100"},
    # SmolLM2 (HuggingFace)
    {"name": "SmolLM2-135M", "hf_model_id": "HuggingFaceTB/SmolLM2-135M-Instruct", "parameter_count": 135_000_000, "vram_gb": 1, "min_gpu": None, "description": "SmolLM2 135M — tiny, instant inference"},
    {"name": "SmolLM2-360M", "hf_model_id": "HuggingFaceTB/SmolLM2-360M-Instruct", "parameter_count": 360_000_000, "vram_gb": 2, "min_gpu": None, "description": "SmolLM2 360M — tiny, fast inference"},
    {"name": "SmolLM2-1.7B", "hf_model_id": "HuggingFaceTB/SmolLM2-1.7B-Instruct", "parameter_count": 1_700_000_000, "vram_gb": 4, "min_gpu": None, "description": "SmolLM2 1.7B — small but surprisingly capable"},
]

# GPU tier ordering for comparisons
GPU_TIER_ORDER = {"t4": 0, "a10g": 1, "a100": 2, "h100": 3}


async def seed_models(engine: AsyncEngine):
    """Upsert curated models into DB. Safe to call on every startup."""
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        inserted = 0
        updated = 0
        for m in MODELS:
            result = await session.execute(
                select(Model).where(Model.hf_model_id == m["hf_model_id"])
            )
            existing = result.scalar_one_or_none()
            if existing:
                # Update min_gpu if it changed
                if existing.min_gpu != m["min_gpu"]:
                    existing.min_gpu = m["min_gpu"]
                    updated += 1
                continue
            session.add(Model(
                name=m["name"],
                hf_model_id=m["hf_model_id"],
                model_type="llm",
                parameter_count=m["parameter_count"],
                quantization="FP16",
                description=m["description"],
                is_downloaded=False,
                vram_gb=m["vram_gb"],
                min_gpu=m["min_gpu"],
            ))
            inserted += 1

        await session.commit()
        logger.info(f"Seeded models: {inserted} new, {updated} updated, {len(MODELS) - inserted - updated} unchanged")


if __name__ == "__main__":
    from db.connection import start_engine
    from db.base import Base

    async def main():
        engine = start_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await seed_models(engine)
        await engine.dispose()

    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
