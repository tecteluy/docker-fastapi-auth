# Integration tests for authentication endpoints
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

class TestAuthEndpoints:
    def test_login_github_redirect(self, test_client: TestClient):
        """Test GitHub OAuth login initiation."""
        response = test_client.get("/auth/login/github")
        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert "state" in data
        assert "github.com/login/oauth/authorize" in data["auth_url"]

    def test_login_google_redirect(self, test_client: TestClient):
        """Test Google OAuth login initiation."""
        response = test_client.get("/auth/login/google")
        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert "state" in data
        assert "accounts.google.com/o/oauth2/auth" in data["auth_url"]

    def test_login_unsupported_provider(self, test_client: TestClient):
        """Test login with unsupported OAuth provider."""
        response = test_client.get("/auth/login/twitter")
        assert response.status_code == 400
        assert "Unsupported provider" in response.json()["detail"]

    @patch('app.services.oauth_service.OAuthService.exchange_github_code')
    def test_github_callback_success(self, mock_exchange, test_client: TestClient, test_db):
        """Test successful GitHub OAuth callback."""
        # Mock successful OAuth exchange
        mock_exchange.return_value = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "avatar_url": "https://example.com/avatar.jpg",
            "provider": "github",
            "provider_id": "12345",
            "provider_data": {"login": "testuser"}
        }

        response = test_client.get("/auth/callback/github?code=test_code&state=test_state")
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data

    @patch('app.services.oauth_service.OAuthService.exchange_github_code')
    def test_github_callback_oauth_error(self, mock_exchange, test_client: TestClient):
        """Test GitHub OAuth callback with OAuth service error."""
        mock_exchange.return_value = None

        response = test_client.get("/auth/callback/github?code=test_code&state=test_state")
        assert response.status_code == 400
        assert "OAuth authentication failed" in response.json()["detail"]

    def test_callback_missing_parameters(self, test_client: TestClient):
        """Test OAuth callback with missing parameters."""
        response = test_client.get("/auth/callback/github")
        assert response.status_code == 422  # Validation error

    def test_refresh_token_endpoint(self, test_client: TestClient):
        """Test token refresh endpoint exists and handles invalid tokens."""
        # Test with missing refresh_token field
        response = test_client.post("/auth/refresh", json={})
        assert response.status_code == 422  # Validation error for missing field
