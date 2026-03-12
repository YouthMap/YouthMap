"""Shared test fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.base import Base
from database.models import Config, User, PermanentStationType, Band, Mode
from database.operations import DatabaseOperations


def make_test_db():
    """Create a fresh in-memory SQLite database with default content, and return a DatabaseOperations instance."""
    # StaticPool + check_same_thread=False: all sessions share one connection so
    # the in-memory database is visible to threads spawned by run_in_executor.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    session = SessionLocal()
    try:
        Config.initialize(session)
        User.initialize(session)
        PermanentStationType.initialize(session)
        Band.initialize(session)
        Mode.initialize(session)
    finally:
        session.close()

    return DatabaseOperations(SessionLocal)


@pytest.fixture
def db():
    """Provide a fresh in-memory database for each test."""
    return make_test_db()
