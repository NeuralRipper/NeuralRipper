"""
SQLAlchemy Model definition for Inference Sessions Table
"""

from datetime import datetime
from db.base import Base
from sqlalchemy import TIMESTAMP, Enum, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class InferenceSession(Base):
    __tablename__ = "inference_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    gpu_tier: Mapped[str] = mapped_column(String(10), default="t4")
    status: Mapped[str] = mapped_column(
        Enum("pending", "running", "completed", "cancelled"), default="pending"
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("idx_user_time", "user_id", "created_at"),
    )
