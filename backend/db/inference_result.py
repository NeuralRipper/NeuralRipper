"""
SQLAlchemy Model definition for Inference Results Table
"""

from datetime import datetime
from db.base import Base
from sqlalchemy import TIMESTAMP, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class InferenceResult(Base):
    __tablename__ = "inference_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("inference_sessions.id", ondelete="CASCADE"), nullable=False)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    status: Mapped[str] = mapped_column(Enum("pending", "streaming", "completed", "failed"), default="pending")
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    finish_reason: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # token counts
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # latency
    ttft_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    tpot_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens_per_second: Mapped[float | None] = mapped_column(Float, nullable=True)
    e2e_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    # GPU
    gpu_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gpu_utilization_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gpu_memory_used_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gpu_memory_total_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
