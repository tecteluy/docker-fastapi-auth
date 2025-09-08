# Unit tests for token service
import pytest
from unittest.mock import patch
from app.services.token_service import TokenService

class TestTokenService:
    def test_create_access_token(self):
        """Test creating a valid access token."""
        service = TokenService()
        data = {"sub": "user123", "type": "access"}
        token = service.create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_access_token(self):
        """Test verifying a valid access token."""
        service = TokenService()
        data = {"sub": "user123", "type": "access"}
        token = service.create_access_token(data)

        payload = service.verify_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"

    def test_verify_invalid_access_token(self):
        """Test that invalid tokens are rejected."""
        service = TokenService()
        payload = service.verify_access_token("invalid_token")
        assert payload is None

    def test_verify_access_token_jwt_decode_error(self):
        """Test that JWT decoding errors are handled properly."""
        service = TokenService()
        
        # Mock jwt.decode to raise JWTError
        with patch('app.services.token_service.jwt.decode') as mock_decode:
            from app.services.token_service import JWTError
            mock_decode.side_effect = JWTError("Invalid token")
            
            payload = service.verify_access_token("any_token")
            assert payload is None
            mock_decode.assert_called_once()

    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        service = TokenService()
        token = service.create_refresh_token()

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_hash_refresh_token(self):
        """Test hashing a refresh token."""
        service = TokenService()
        token = "test_refresh_token"
        hashed = service.hash_refresh_token(token)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA256 hex length
