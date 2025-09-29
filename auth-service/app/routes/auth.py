from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.auth_service import AuthService
from ..services.oauth_service import OAuthService
from ..services.token_service import TokenService
from ..middleware.auth_middleware import get_current_user
from ..config import settings
from pydantic import BaseModel, field_validator
from urllib.parse import quote, unquote
import logging
import re
import secrets

# Use auth-specific logger
logger = logging.getLogger("fastapi.auth")

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

router = APIRouter(tags=["Authentication"])
auth_service = AuthService()
oauth_service = OAuthService()
token_service = TokenService()

@router.get("/login/{provider}")
async def login(provider: str, request: Request):
    """Initiate OAuth login flow."""
    if provider not in ["github", "google"]:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    # Get redirect_uri from query parameters (sent by Angular app)
    redirect_uri = request.query_params.get("redirect_uri")
    if not redirect_uri:
        # Fallback to configured frontend URL if no redirect_uri provided
        redirect_uri = f"{settings.frontend_url}/auth/callback"

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store redirect_uri and provider in state for later retrieval (you might want to use Redis for production)
    # For now, we'll embed it in the state parameter
    state_data = f"{state}:{redirect_uri}:{provider}"

    # Store state in session (you might want to use Redis for production)
    if provider == "github":
        auth_url = oauth_service.get_github_auth_url(state_data, redirect_uri)
    else:  # google
        auth_url = oauth_service.get_google_auth_url(state_data, redirect_uri)

    return {"auth_url": auth_url, "state": state_data}

@router.get("/callback")
async def generic_auth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback from any provider (extracts provider from state)."""
    print(f"DEBUG: Raw state: {state}")
    # URL-decode the state parameter first
    decoded_state = unquote(state)
    print(f"DEBUG: Decoded state: {decoded_state}")

    # Extract state, redirect_uri, and provider from state (format: "state:redirect_uri:provider")
    try:
        # Split on the last colon to get provider, then split the rest on first colon
        if ":" not in decoded_state:
            raise ValueError("Invalid state format")
        
        # Find the last colon (separates provider)
        last_colon_idx = decoded_state.rfind(":")
        if last_colon_idx == -1:
            raise ValueError("Invalid state format")
            
        provider = decoded_state[last_colon_idx + 1:]
        state_and_url = decoded_state[:last_colon_idx]
        
        # Now split state_and_url on the first colon
        first_colon_idx = state_and_url.find(":")
        if first_colon_idx == -1:
            raise ValueError("Invalid state format")
            
        state_part = state_and_url[:first_colon_idx]
        redirect_uri = state_and_url[first_colon_idx + 1:]
        
        print(f"DEBUG: Parsed - state_part: {state_part}, redirect_uri: {redirect_uri}, provider: {provider}")
        
    except ValueError:
        # Fallback for old state format
        raise HTTPException(status_code=400, detail="Invalid state format")

    print(f"DEBUG: Provider: {provider}")
    if provider not in ["github", "google"]:
        print(f"DEBUG: Unsupported provider: {provider}")
        raise HTTPException(status_code=400, detail="Unsupported provider")

    # Exchange code for user data
    if provider == "github":
        oauth_data = await oauth_service.exchange_github_code(code)
    else:
        oauth_data = await oauth_service.exchange_google_code(code, redirect_uri)

    if not oauth_data:
        # Redirect to frontend with error
        from ..config import settings
        error_redirect = f"{settings.frontend_url}/?error=oauth_failed"
        return RedirectResponse(url=error_redirect)

    # Create or update user based on OAuth data
    user = auth_service.create_or_update_user(db, oauth_data)

    # Generate JWT tokens for the authenticated user
    tokens = auth_service.create_tokens(db, user)

    # Redirect to frontend with tokens as URL fragments
    from ..config import settings
    success_redirect = (
        f"{settings.frontend_url}/"
        f"?access_token={quote(tokens['access_token'])}"
        f"&refresh_token={quote(tokens['refresh_token'])}"
        f"&token_type={quote(tokens['token_type'])}"
        f"&expires_in={tokens['expires_in']}"
    )
    return RedirectResponse(url=success_redirect)

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

    # Extract redirect_uri from state (format: "state:redirect_uri")
    try:
        state_part, redirect_uri = state.split(":", 1)
    except ValueError:
        # Fallback for old state format without redirect_uri
        redirect_uri = f"{settings.frontend_url}/auth/callback"
        state_part = state

    # Exchange code for user data
    if provider == "github":
        oauth_data = await oauth_service.exchange_github_code(code)
    else:
        oauth_data = await oauth_service.exchange_google_code(code, redirect_uri)

    if not oauth_data:
        # Redirect to frontend with error
        from ..config import settings
        error_redirect = f"{settings.frontend_url}/?error=oauth_failed"
        return RedirectResponse(url=error_redirect)

    # Create or update user based on OAuth data
    user = auth_service.create_or_update_user(db, oauth_data)

    # Generate JWT tokens for the authenticated user
    tokens = auth_service.create_tokens(db, user)

    # Redirect to frontend with tokens as URL fragments
    from ..config import settings
    success_redirect = (
        f"{settings.frontend_url}/"
        f"?access_token={quote(tokens['access_token'])}"
        f"&refresh_token={quote(tokens['refresh_token'])}"
        f"&token_type={quote(tokens['token_type'])}"
        f"&expires_in={tokens['expires_in']}"
    )
    return RedirectResponse(url=success_redirect)

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
    default_email = f"{backup_username}@fastapi.local"
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

@router.post("/logout")
async def logout(
    request: RefreshTokenRequest = Body(...),
    db: Session = Depends(get_db)
):
    """Logout user and revoke refresh token."""
    success = auth_service.revoke_refresh_token(db, request.refresh_token)
    if not success:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return {"message": "Successfully logged out"}
