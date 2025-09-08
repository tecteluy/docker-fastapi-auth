from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional
from ..models.user import User, RefreshToken
from .token_service import TokenService
from .oauth_service import OAuthService

class AuthService:
    def __init__(self):
        self.token_service = TokenService()
        self.oauth_service = OAuthService()

    def create_or_update_user(self, db: Session, oauth_data: dict) -> User:
        """Create new user or update existing user from OAuth data."""
        user = db.query(User).filter(
            User.provider == oauth_data["provider"],
            User.provider_id == oauth_data["provider_id"]
        ).first()

        if user:
            # Update existing user
            user.email = oauth_data["email"]
            user.full_name = oauth_data["full_name"]
            user.avatar_url = oauth_data["avatar_url"]
            user.provider_data = oauth_data["provider_data"]
            user.last_login = datetime.utcnow()
            user.updated_at = datetime.utcnow()
        else:
            # Create new user
            user = User(
                email=oauth_data["email"],
                username=oauth_data["username"],
                full_name=oauth_data["full_name"],
                avatar_url=oauth_data["avatar_url"],
                provider=oauth_data["provider"],
                provider_id=oauth_data["provider_id"],
                provider_data=oauth_data["provider_data"],
                is_active=True,
                is_admin=False,
                permissions={"services": []},
                last_login=datetime.utcnow()
            )
            db.add(user)

        db.commit()
        db.refresh(user)
        return user

    def create_tokens(self, db: Session, user: User) -> dict:
        """Create access and refresh tokens for user."""
        # Create access token
        access_token = self.token_service.create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "is_admin": user.is_admin,
            "permissions": user.permissions
        })

        # Create refresh token
        refresh_token = self.token_service.create_refresh_token()
        refresh_token_hash = self.token_service.hash_refresh_token(refresh_token)

        # Store refresh token in database
        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=datetime.utcnow() + timedelta(days=self.token_service.refresh_token_expire_days)
        )
        db.add(db_refresh_token)
        db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.token_service.access_token_expire_minutes * 60
        }

    def refresh_access_token(self, db: Session, refresh_token: str) -> Optional[dict]:
        """Refresh access token using refresh token."""
        token_hash = self.token_service.hash_refresh_token(refresh_token)

        db_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        ).first()

        if not db_token:
            return None

        user = db.query(User).filter(User.id == db_token.user_id).first()
        if not user or not user.is_active:
            return None

        # Create new access token
        access_token = self.token_service.create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "is_admin": user.is_admin,
            "permissions": user.permissions
        })

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.token_service.access_token_expire_minutes * 60
        }

    def revoke_refresh_token(self, db: Session, refresh_token: str) -> bool:
        """Revoke refresh token."""
        token_hash = self.token_service.hash_refresh_token(refresh_token)
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()

        if db_token:
            db_token.is_revoked = True
            db.commit()
            return True
        return False
