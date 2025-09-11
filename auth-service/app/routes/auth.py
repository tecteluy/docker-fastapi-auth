from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.auth_service import AuthService
from ..services.oauth_service import OAuthService
from ..middleware.auth_middleware import get_current_user
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.token_service import TokenService
import secrets
import re

class BackupLoginRequest(BaseModel):
    username: str
    password: str
    email: str | None = None
    full_name: str | None = None
    
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
    else:
        oauth_data = await oauth_service.exchange_google_code(code)

    if not oauth_data:
        raise HTTPException(status_code=400, detail="OAuth authentication failed")

    # Create or update user based on OAuth data
    user = auth_service.create_or_update_user(db, oauth_data)

    # Generate JWT tokens for the authenticated user
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

@router.post("/backup-login")
async def backup_login(request: BackupLoginRequest, db: Session = Depends(get_db)):
    """Backup login method using username/password."""
    import os
    import hashlib
    import json
    
    # Get backup credentials from environment variables for security
    backup_users_json = os.getenv("BACKUP_USERS", "")
    
    # Fallback to single user format for backward compatibility
    if not backup_users_json:
        backup_username = os.getenv("BACKUP_ADMIN_USERNAME", "")
        backup_password_hash = os.getenv("BACKUP_ADMIN_PASSWORD_HASH", "")
        
        if backup_username and backup_password_hash:
            backup_users = {
                backup_username: {
                    "password_hash": backup_password_hash,
                    "is_admin": True,
                    "permissions": {"services": ["*"]}
                }
            }
        else:
            backup_users = {}
    else:
        try:
            backup_users = json.loads(backup_users_json)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500,
                detail="Invalid BACKUP_USERS configuration"
            )
    
    # If no backup credentials are configured, disable this endpoint
    if not backup_users:
        raise HTTPException(
            status_code=503,
            detail="Backup login not configured. Please contact an administrator."
        )
    
    # Check if username exists in backup users
    if request.username not in backup_users:
        # Log failed attempt for security monitoring
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed backup login attempt for unknown username: {request.username}")
        raise HTTPException(status_code=401, detail="Invalid backup credentials")
    
    user_config = backup_users[request.username]
    
    # Hash the provided password to compare with stored hash
    provided_password_hash = hashlib.sha256(request.password.encode()).hexdigest()
    
    # Secure comparison to prevent timing attacks
    import hmac
    if not hmac.compare_digest(provided_password_hash, user_config["password_hash"]):
        # Log failed attempt for security monitoring
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed backup login attempt for username: {request.username}")
        
        raise HTTPException(status_code=401, detail="Invalid backup credentials")
    
    # Create or get backup user, using configured profile values
    from ..models.user import User
    backup_username = f"backup_{request.username}"
    backup_user = db.query(User).filter(
        User.username == backup_username,
        User.provider == "backup"
    ).first()

    # Determine email/full_name from config
    cfg_email = user_config.get("email")
    cfg_full = user_config.get("full_name")
    default_email = f"{backup_username}@atrium.local"
    default_full = f"Backup User: {request.username}"
    profile_email = cfg_email or default_email
    profile_full = cfg_full or default_full

    if not backup_user:
        # Create new backup user with configured values
        backup_user = User(
            email=profile_email,
            username=backup_username,
            full_name=profile_full,
            provider="backup",
            provider_id=request.username,
            is_active=True,
            is_admin=user_config.get("is_admin", False),
            permissions=user_config.get("permissions", {"services": []}),
            last_login=None
        )
        db.add(backup_user)
        db.commit()
        db.refresh(backup_user)
    else:
        # Update existing backup user with configured profile values (do not update admin/permissions)
        backup_user.email = profile_email
        backup_user.full_name = profile_full
        db.commit()

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

@router.post("/refresh")
async def refresh_token(
    request: RefreshTokenRequest = Body(...),
    db: Session = Depends(get_db)
):
    """Refresh access token using provided refresh token."""
    result = auth_service.refresh_access_token(db, request.refresh_token)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    return result
