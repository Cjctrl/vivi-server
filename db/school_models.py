"""
SQLAlchemy models for school-related data.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

from config.settings import SCHOOL_DB_PATH

Base = declarative_base()


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    class_name = Column(String, nullable=False)
    due_date = Column(String, nullable=True)
    status = Column(String, default="upcoming")
    grade = Column(String, nullable=True)
    category = Column(String, nullable=True)
    source = Column(String, default="google_classroom")
    google_id = Column(String, unique=True, nullable=True)
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_name = Column(String, nullable=False)
    assignment_title = Column(String, nullable=True)
    score = Column(Float, nullable=True)
    percentage = Column(Float, nullable=True)
    letter_grade = Column(String, nullable=True)
    source = Column(String, default="powerschool")
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    google_event_id = Column(String, unique=True, nullable=False)
    calendar_name = Column(String, nullable=True)
    title = Column(String, nullable=False)
    start_datetime = Column(String, nullable=False)
    end_datetime = Column(String, nullable=False)
    all_day = Column(Boolean, default=False)
    location = Column(String, nullable=True)
    description = Column(String, nullable=True)
    is_recurring = Column(Boolean, default=False)
    category = Column(String, nullable=True)
    synced_at = Column(DateTime(timezone=True), server_default=func.now())


class ProjectRecord(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    source = Column(String, nullable=False)
    file_or_path = Column(String, nullable=False)
    status = Column(String, nullable=False)
    last_modified = Column(String, nullable=True)
    has_tasks = Column(Boolean, default=False)
    readme_preview = Column(String, nullable=True)
    current_branch = Column(String, nullable=True)
    scanned_at = Column(DateTime(timezone=True), server_default=func.now())


class PhotoMemoryRecord(Base):
    __tablename__ = "photo_memories"

    id             = Column(String,  primary_key=True)                         # UUID from Qdrant
    image_path     = Column(String,  nullable=True)
    description    = Column(Text,    nullable=False, default="")
    ocr_text       = Column(Text,    nullable=True)
    tags           = Column(JSON,    default=list)
    file_hash      = Column(String,  index=True, nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    times_recalled = Column(Integer, default=0)
    last_recalled  = Column(DateTime(timezone=True), nullable=True)


engine = create_engine(f"sqlite:///{SCHOOL_DB_PATH}", echo=False)


def init_db() -> None:
    """Create tables. Call explicitly at startup; do NOT run on import."""
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
