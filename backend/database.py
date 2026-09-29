import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set. Check backend/.env or Render environment variables."
    )


# ============================================================
# DATABASE ENGINE
# ============================================================
# Render/PostgreSQL connections can occasionally be closed while idle.
# These settings make SQLAlchemy validate pooled connections and recycle
# them periodically instead of reusing a stale connection.

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=2,
    max_overflow=1,
    pool_timeout=30,
    pool_reset_on_return="rollback",
    connect_args={
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)


# ============================================================
# SESSION
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# BASE MODEL
# ============================================================

Base = declarative_base()
