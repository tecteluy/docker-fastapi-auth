# Unit tests for auth service
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from app.services.auth_service import AuthService
from app.models.user import User

class TestAuthService:
    def test_create_or_update_user_new_user(self):
        """Test creating a new user."""
        service = AuthService()
        mock_db = Mock(spec=Session)

        # Mock that user doesn't exist
        mock_db.query.return_value.filter.return_value.first.return_value = None

        oauth_data = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "avatar_url": "https://example.com/avatar.jpg",
            "provider": "github",
            "provider_id": "12345",
            "provider_data": {"login": "testuser"}
        }

        user = service.create_or_update_user(mock_db, oauth_data)

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.provider == "github"
        assert user.provider_id == "12345"
        assert user.is_active == True
        assert user.is_admin == False
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_or_update_user_existing_user(self):
        """Test updating an existing user."""
        service = AuthService()
        mock_db = Mock(spec=Session)

        existing_user = User(
            email="old@example.com",
            username="olduser",  # Username should NOT change for existing users
            provider="github",
            provider_id="12345"
        )

        # Mock that user exists
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user

        oauth_data = {
            "email": "new@example.com",
            "username": "newuser",  # This won't be used for existing users
            "full_name": "New User",
            "avatar_url": "https://example.com/new.jpg",
            "provider": "github",
            "provider_id": "12345",
            "provider_data": {"login": "newuser"}
        }

        user = service.create_or_update_user(mock_db, oauth_data)

        # Verify the user object was updated (but username stays the same)
        assert user.email == "new@example.com"
        assert user.username == "olduser"  # Username should NOT change for existing users
        assert user.full_name == "New User"
        assert user.avatar_url == "https://example.com/new.jpg"
        mock_db.commit.assert_called_once()

    @patch('app.services.token_service.TokenService.create_access_token')
    @patch('app.services.token_service.TokenService.create_refresh_token')
    @patch('app.services.token_service.TokenService.hash_refresh_token')
    def test_create_tokens(self, mock_hash, mock_refresh, mock_access, test_db):
        """Test creating access and refresh tokens."""
        service = AuthService()

        # Mock token creation
        mock_access.return_value = "access_token_123"
        mock_refresh.return_value = "refresh_token_456"
        mock_hash.return_value = "hashed_refresh_token"

        # Create a user with an ID
        user = User(
            id=1,
            email="test@example.com", 
            username="testuser"
        )

        tokens = service.create_tokens(test_db, user)

        assert tokens["access_token"] == "access_token_123"
        assert tokens["refresh_token"] == "refresh_token_456"
        assert tokens["token_type"] == "bearer"
        mock_access.assert_called_once()
        mock_refresh.assert_called_once()
        mock_hash.assert_called_once_with("refresh_token_456")
