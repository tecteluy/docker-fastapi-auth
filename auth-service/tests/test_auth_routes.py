import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models.user import User

# Custom test database configuration
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    """Override database dependency for testing."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def test_client():
    """Create test client with fresh database."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create test client
    client = TestClient(app)

    yield client

    # Clean up after test
    Base.metadata.drop_all(bind=test_engine)

def test_github_login_initiation(test_client):
    """Test GitHub OAuth initiation."""
    response = test_client.get("/auth/login/github")
    assert response.status_code == 200
    data = response.json()
    assert "auth_url" in data
    assert "state" in data
    assert "github.com" in data["auth_url"]

def test_invalid_provider(test_client):
    """Test invalid OAuth provider."""
    response = test_client.get("/auth/login/invalid")
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_oauth_callback_success(test_client, monkeypatch):
    """Test successful OAuth callback."""
    # Mock OAuth service
    async def mock_exchange_github_code(code):
        return {
            "provider": "github",
            "provider_id": "123456",
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "avatar_url": "https://example.com/avatar.png",
            "provider_data": {}
        }

    monkeypatch.setattr("app.routes.auth.oauth_service.exchange_github_code", mock_exchange_github_code)

    response = test_client.get("/auth/callback/github?code=test_code&state=test_state")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"

def test_backup_login_success(test_client):
    """Test successful backup login."""
    response = test_client.post("/auth/backup-login", json={
        "username": "admin",
        "password": "admin"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["username"] == "backup_admin"

def test_backup_login_invalid_credentials(test_client):
    """Test backup login with invalid credentials."""
    response = test_client.post("/auth/backup-login", json={
        "username": "admin",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "Invalid backup credentials" in data["detail"]
