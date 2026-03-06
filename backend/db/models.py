"""
SQLAlchemy Model definition for Models Table
"""

from datetime import datetime
from db.base import Base
from sqlalchemy import TIMESTAMP, BigInteger, Boolean, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class Model(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hf_model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    model_type: Mapped[str] = mapped_column(Enum("llm", "cnn"), default="llm")
    parameter_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    quantization: Mapped[str] = mapped_column(String(20), default="FP16")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_downloaded: Mapped[bool] = mapped_column(Boolean, default=False)
    vram_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
