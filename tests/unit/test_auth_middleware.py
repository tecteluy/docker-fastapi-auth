# Unit tests for authentication middleware
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from app.models.user import User
from app.middleware.auth_middleware import get_current_user, require_admin

class TestAuthMiddleware:
    @pytest.mark.asyncio
    @patch('app.middleware.auth_middleware.token_service')
    @patch('app.middleware.auth_middleware.get_db')
    async def test_get_current_user_valid_token(self, mock_get_db, mock_token_service):
        """Test get_current_user with valid token."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock token service
        mock_token_service.verify_access_token.return_value = {
            "sub": "123",
            "email": "test@example.com",
            "is_admin": False
        }
        
        # Mock user
        mock_user = Mock()
        mock_user.id = 123
        mock_user.is_active = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Mock credentials
        mock_credentials = Mock()
        mock_credentials.credentials = "valid_token"
        
        result = await get_current_user(mock_credentials, mock_db)
        
        assert result == mock_user
        mock_token_service.verify_access_token.assert_called_once_with("valid_token")

    @pytest.mark.asyncio
    @patch('app.middleware.auth_middleware.token_service')
    @patch('app.middleware.auth_middleware.get_db')
    async def test_get_current_user_invalid_token(self, mock_get_db, mock_token_service):
        """Test get_current_user with invalid token."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock token service to return None (invalid token)
        mock_token_service.verify_access_token.return_value = None
        
        mock_credentials = Mock()
        mock_credentials.credentials = "invalid_token"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials, mock_db)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.middleware.auth_middleware.token_service')
    @patch('app.middleware.auth_middleware.get_db')
    async def test_get_current_user_missing_user_id(self, mock_get_db, mock_token_service):
        """Test get_current_user with token missing user ID."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock token service with payload missing 'sub'
        mock_token_service.verify_access_token.return_value = {
            "email": "test@example.com"
        }
        
        mock_credentials = Mock()
        mock_credentials.credentials = "token_without_sub"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials, mock_db)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token payload" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.middleware.auth_middleware.token_service')
    @patch('app.middleware.auth_middleware.get_db')
    async def test_get_current_user_user_not_found(self, mock_get_db, mock_token_service):
        """Test get_current_user when user is not found."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_token_service.verify_access_token.return_value = {
            "sub": "123"
        }
        
        # Mock user not found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        mock_credentials = Mock()
        mock_credentials.credentials = "valid_token"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials, mock_db)
        
        assert exc_info.value.status_code == 401
        assert "User not found or inactive" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.middleware.auth_middleware.token_service')
    @patch('app.middleware.auth_middleware.get_db')
    async def test_get_current_user_inactive_user(self, mock_get_db, mock_token_service):
        """Test get_current_user with inactive user."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_token_service.verify_access_token.return_value = {
            "sub": "123"
        }
        
        # Mock inactive user
        mock_user = Mock()
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        mock_credentials = Mock()
        mock_credentials.credentials = "valid_token"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials, mock_db)
        
        assert exc_info.value.status_code == 401
        assert "User not found or inactive" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_admin_success(self):
        """Test require_admin with admin user."""
        mock_user = Mock()
        mock_user.is_admin = True
        
        result = await require_admin(mock_user)
        
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_require_admin_failure(self):
        """Test require_admin with non-admin user."""
        mock_user = Mock()
        mock_user.is_admin = False
        
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(mock_user)
        
        assert exc_info.value.status_code == 403
        assert "Admin privileges required" in exc_info.value.detail

    def test_user_model_creation(self):
        """Test User model can be created properly."""
        user = User(
            email="test@example.com",
            username="testuser",
            provider="github",
            provider_id="12345",
            is_active=True,
            is_admin=False
        )
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.provider == "github"
        assert user.provider_id == "12345"
        assert user.is_active == True
        assert user.is_admin == False
