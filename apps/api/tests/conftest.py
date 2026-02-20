from __future__ import annotations

import os

# Use SQLite in-memory for tests — must be set before app imports
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["API_KEY"] = "test-key"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", echo=False, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    from app.db import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(monkeypatch):
    """TestClient with in-memory SQLite and mocked worker."""
    engine = create_engine(
        "sqlite://",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSession = sessionmaker(bind=engine)

    # Import models so Base knows about all tables
    from app.db import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Patch SessionLocal everywhere it's been imported
    monkeypatch.setattr("app.db.session.SessionLocal", TestSession)
    monkeypatch.setattr("app.routes.jobs.SessionLocal", TestSession)
    monkeypatch.setattr("app.routes.webhooks.SessionLocal", TestSession)
    monkeypatch.setattr("app.routes.stats.SessionLocal", TestSession)
    monkeypatch.setattr("app.services.audit.SessionLocal", TestSession)

    # Prevent init_db from trying to create tables on the production engine
    monkeypatch.setattr("app.db.session.init_db", lambda: None)

    # Mock celery task to no-op for CRUD tests
    monkeypatch.setattr(
        "app.routes.jobs.run_scan_job",
        type("FakeTask", (), {"delay": staticmethod(lambda payload: None)})(),
    )

    from app.main import api

    with TestClient(api) as c:
        yield c

    Base.metadata.drop_all(bind=engine)
