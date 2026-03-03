"""
SQLAlchemy Model definition for Inference Results Table
"""

from datetime import datetime
from db.base import Base
from sqlalchemy import TIMESTAMP, Enum, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class InferenceResult(Base):
    __tablename__ = "inference_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # we might need to search result based on session id(innoDB already indexed)
    session_id: Mapped[int] = mapped_column(ForeignKey("inference_sessions.id", ondelete="CASCADE"), nullable=False)
    # we might need to search result based on model id(innoDB already indexed)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    status: Mapped[str] = mapped_column(Enum("pending", "streaming", "completed", "failed"), default="pending")
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ttft_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    tpot_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens_per_second: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    e2e_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
