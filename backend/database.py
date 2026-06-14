"""
database.py  –  SQLAlchemy models and DB initialisation.
Supports both SQLite (local dev) and PostgreSQL (production via DATABASE_URL env var).
"""
import os
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Use DATABASE_URL env var (Render PostgreSQL) or fall back to local SQLite
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./sports_tv.db")

# Render gives postgres:// URLs, but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs check_same_thread=False; Postgres doesn't
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Category(Base):
    __tablename__ = "categories"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), unique=True, nullable=False)  # e.g. "Football"
    icon        = Column(String(10), default="⚽")                  # Emoji icon
    sort_order  = Column(Integer, default=0)
    created_at  = Column(DateTime, default=datetime.utcnow)

    streams     = relationship("Stream", back_populates="category", cascade="all, delete")


class Stream(Base):
    __tablename__ = "streams"

    id              = Column(Integer, primary_key=True, index=True)
    category_id     = Column(Integer, ForeignKey("categories.id"), nullable=False)
    title           = Column(String(255), nullable=False)      # e.g. "Canada vs Bosnia"
    participants    = Column(String(255), default="")           # "Team A vs Team B"
    sport           = Column(String(100), default="")
    source_url      = Column(Text, nullable=False)             # source page URL
    iframe_url      = Column(Text, default="")                 # embed iframe URL
    hls_url         = Column(Text, default="")                 # direct .m3u8 link
    thumbnail_url   = Column(Text, default="")                 # OG image if available
    is_live         = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    progress        = Column(Integer, default=0)  # extraction progress 0-100

    category        = relationship("Category", back_populates="streams")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
