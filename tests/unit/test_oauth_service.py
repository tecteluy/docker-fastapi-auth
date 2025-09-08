# Unit tests for OAuth service
import pytest
from unittest.mock import patch, AsyncMock
from app.services.oauth_service import OAuthService

class TestOAuthService:
    def test_get_github_auth_url(self):
        """Test GitHub OAuth URL generation."""
        service = OAuthService()

        url = service.get_github_auth_url("test_state")

        assert "https://github.com/login/oauth/authorize" in url
        assert "client_id=" in url
        assert "redirect_uri=http://localhost:3000/auth/callback/github" in url
        assert "scope=user:email" in url
        assert "state=test_state" in url

    def test_get_google_auth_url(self):
        """Test Google OAuth URL generation."""
        service = OAuthService()

        url = service.get_google_auth_url("test_state")

        assert "https://accounts.google.com/o/oauth2/auth" in url
        assert "client_id=" in url
        assert "redirect_uri=http://localhost:3000/auth/callback/google" in url
        assert "scope=openid email profile" in url
        assert "state=test_state" in url

    @pytest.mark.asyncio
    async def test_exchange_github_code_success(self):
        """Test successful GitHub code exchange."""
        service = OAuthService()

        # Mock the httpx client and responses
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None

            # Mock token response (use regular Mock for synchronous json method)
            from unittest.mock import Mock
            mock_token_response = Mock()
            mock_token_response.json.return_value = {"access_token": "test_token"}
            mock_client.post.return_value = mock_token_response

            # Mock user response
            mock_user_response = Mock()
            mock_user_response.json.return_value = {
                "id": 12345,
                "email": "test@example.com",
                "login": "testuser",
                "name": "Test User",
                "avatar_url": "https://example.com/avatar.jpg"
            }
            mock_client.get.return_value = mock_user_response

            result = await service.exchange_github_code("test_code")

            assert result is not None
            assert result["email"] == "test@example.com"
            assert result["username"] == "testuser"
            assert result["full_name"] == "Test User"
            assert result["provider"] == "github"

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_exchange_github_code_token_error(self, mock_client_class):
        """Test GitHub code exchange with token request error."""
        service = OAuthService()

        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock failed token response
        mock_token_response = AsyncMock()
        mock_token_response.json.side_effect = Exception("Token request failed")
        mock_client.post.return_value = mock_token_response

        result = await service.exchange_github_code("test_code")

        assert result is None

    @pytest.mark.asyncio
    async def test_exchange_google_code_success(self):
        """Test successful Google code exchange."""
        service = OAuthService()

        # Mock the httpx client and responses
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None

            # Mock token response (use regular Mock for synchronous json method)
            from unittest.mock import Mock
            mock_token_response = Mock()
            mock_token_response.json.return_value = {"access_token": "test_token"}
            mock_client.post.return_value = mock_token_response

            # Mock user response
            mock_user_response = Mock()
            mock_user_response.json.return_value = {
                "id": "google123",
                "email": "test@example.com",
                "name": "Test User",
                "picture": "https://example.com/avatar.jpg"
            }
            mock_client.get.return_value = mock_user_response

            result = await service.exchange_google_code("test_code")

            assert result is not None
            assert result["email"] == "test@example.com"
            assert result["username"] == "test"  # Google username is email prefix
            assert result["full_name"] == "Test User"
            assert result["provider"] == "google"
