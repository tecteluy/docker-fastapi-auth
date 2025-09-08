from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.auth_service import AuthService
from ..services.oauth_service import OAuthService
from ..middleware.auth_middleware import get_current_user
from ..services.token_service import TokenService
from pydantic import BaseModel, field_validator
import secrets
import re

class BackupLoginRequest(BaseModel):
    username: str
    password: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Username cannot be empty')
        if len(v) > 50:
            raise ValueError('Username too long')
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError('Username contains invalid characters')
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v or len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 100:
            raise ValueError('Password too long')
        return v

class RefreshTokenRequest(BaseModel):
    refresh_token: str
    
    @field_validator('refresh_token')
    @classmethod
    def validate_refresh_token(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Refresh token cannot be empty')
        return v.strip()

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()
oauth_service = OAuthService()
token_service = TokenService()

@router.get("/login/{provider}")
async def login(provider: str, request: Request):
    """Initiate OAuth login flow."""
    if provider not in ["github", "google"]:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state in session (you might want to use Redis for production)
    if provider == "github":
        auth_url = oauth_service.get_github_auth_url(state)
    else:  # google
        auth_url = oauth_service.get_google_auth_url(state)

    return {"auth_url": auth_url, "state": state}

@router.get("/callback/{provider}")
async def auth_callback(
    provider: str,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback."""
    if provider not in ["github", "google"]:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    # Exchange code for user data
    if provider == "github":
        oauth_data = await oauth_service.exchange_github_code(code)
    else:  # google
        oauth_data = await oauth_service.exchange_google_code(code)

    if not oauth_data:
        raise HTTPException(status_code=400, detail="OAuth authentication failed")

    # Create or update user
    user = auth_service.create_or_update_user(db, oauth_data)

    # Create tokens
    tokens = auth_service.create_tokens(db, user)

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "is_admin": user.is_admin,
            "permissions": user.permissions
        },
        **tokens
    }

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token."""
    tokens = auth_service.refresh_access_token(db, request.refresh_token)
    if not tokens:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return tokens

@router.post("/logout")
async def logout(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Logout user and revoke refresh token."""
    auth_service.revoke_refresh_token(db, request.refresh_token)
    return {"message": "Logged out successfully"}

@router.post("/backup-login")
async def backup_login(request: BackupLoginRequest, db: Session = Depends(get_db)):
    """Backup login method using username/password."""
    import os
    import hashlib
    
    # Get backup credentials from environment variables for security
    backup_username = os.getenv("BACKUP_ADMIN_USERNAME", "")
    backup_password_hash = os.getenv("BACKUP_ADMIN_PASSWORD_HASH", "")
    
    # If no backup credentials are configured, disable this endpoint
    if not backup_username or not backup_password_hash:
        raise HTTPException(
            status_code=503, 
            detail="Backup login not configured. Please contact administrator."
        )
    
    # Hash the provided password to compare with stored hash
    provided_password_hash = hashlib.sha256(request.password.encode()).hexdigest()
    
    # Secure comparison to prevent timing attacks
    import hmac
    if not (request.username == backup_username and 
            hmac.compare_digest(provided_password_hash, backup_password_hash)):
        # Log failed attempt for security monitoring
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed backup login attempt for username: {request.username}")
        
        raise HTTPException(status_code=401, detail="Invalid backup credentials")
    
    # Create or get backup user
    from ..models.user import User
    backup_user = db.query(User).filter(User.username == "backup_admin").first()

    if not backup_user:
        backup_user = User(
            email="backup@atrium.local",
            username="backup_admin",
            full_name="Backup Administrator",
            provider="backup",
            provider_id="backup_admin",
            is_active=True,
            is_admin=True,
            permissions={"services": ["*"]},
            last_login=None
        )
        db.add(backup_user)
        db.commit()
        db.refresh(backup_user)

    # Log successful backup login for security monitoring
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Successful backup login for username: {request.username}")

    # Create tokens
    tokens = auth_service.create_tokens(db, backup_user)

    return {
        "user": {
            "id": backup_user.id,
            "email": backup_user.email,
            "username": backup_user.username,
            "full_name": backup_user.full_name,
            "is_admin": backup_user.is_admin,
            "permissions": backup_user.permissions
        },
        **tokens
    }

@router.get("/me")
async def get_current_user(current_user=Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "avatar_url": current_user.avatar_url,
        "is_admin": current_user.is_admin,
        "permissions": current_user.permissions
    }
