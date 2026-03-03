"""
SQLAlchemy Model definition for User Table

Industrial Standard:
Mapped -> type hint only
mapped_column() -> actual columndefinition
"""



from datetime import datetime
from base import Base
from sqlalchemy import TIMESTAMP, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func     # used to generate SQL functions, like CURRENT_TIMESTAMP


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    google_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())  # CURRENT_TIMESTAMP
