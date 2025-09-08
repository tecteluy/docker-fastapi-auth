# Test configuration and shared fixtures
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from redis import Redis
import os

from app.main import app
from app.database import get_db, Base
from app.config import settings

# Test database configuration
TEST_DATABASE_URL = "postgresql://test_user:test_password@test-db:5432/test_db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Clean up after all tests
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture
def test_db(test_engine):
    """Provide test database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = SessionLocal()

    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture
def test_client(test_db):
    """Provide FastAPI test client with test database."""
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def test_redis():
    """Provide test Redis client."""
    redis_client = Redis(host='test-redis', port=6379, db=0)
    yield redis_client
    redis_client.flushdb()  # Clean up after test
