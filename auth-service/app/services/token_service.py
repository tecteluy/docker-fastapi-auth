from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from ..config import settings
import hashlib
import secrets

class TokenService:
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self) -> str:
        """Create secure refresh token."""
        return secrets.token_urlsafe(32)

    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT access token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != "access":
                return None
            return payload
        except JWTError:
            return None

    def hash_refresh_token(self, token: str) -> str:
        """Create hash of refresh token for database storage."""
        return hashlib.sha256(token.encode()).hexdigest()
