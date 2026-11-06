from sqlalchemy import String, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from .db import Base
class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(240))
    source_path: Mapped[str] = mapped_column(Text)
    output_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="uploaded")
    duration: Mapped[float] = mapped_column(default=0)
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    project_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
