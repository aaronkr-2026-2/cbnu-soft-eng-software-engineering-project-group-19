import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["SECRET_KEY"] = "test-only-secret-key-with-at-least-32-bytes"
os.environ["DATABASE_URL"] = "sqlite://"

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.routers import certificates, courses, lessons, quizzes  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(courses, "save_course_banner", lambda _course, _db: None)

    def no_ai_banner(*_args):
        raise lessons.AIConfigurationError("AI is intentionally disabled in tests")

    monkeypatch.setattr(lessons, "generate_lesson_banner", no_ai_banner)
    monkeypatch.setattr(lessons, "store_lesson_banner", lambda *_args: None)
    monkeypatch.setattr(quizzes, "consume_passkey_proof", lambda *_args: None)
    monkeypatch.setattr(certificates, "consume_passkey_proof", lambda *_args: None)

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()
