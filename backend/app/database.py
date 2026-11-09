import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load the backend's local settings regardless of the process working directory.
# Environment variables supplied by a deployment take precedence over .env.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://localhost/studyflow_db",
).strip() or "postgresql+psycopg://localhost/studyflow_db"

# Render provides PostgreSQL URLs without SQLAlchemy's psycopg driver suffix.
# Keep local and Docker URLs unchanged while making the managed URL explicit.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL.removeprefix("postgres://")
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL.removeprefix("postgresql://")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
