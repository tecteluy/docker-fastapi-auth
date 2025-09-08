from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.auth_service import AuthService
from ..services.oauth_service import OAuthService
from ..middleware.auth_middleware import get_current_user
from ..services.token_service import TokenService
from pydantic import BaseModel
import secrets

class BackupLoginRequest(BaseModel):
    username: str
    password: str

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
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token."""
    tokens = auth_service.refresh_access_token(db, refresh_token)
    if not tokens:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return tokens

@router.post("/logout")
async def logout(refresh_token: str, db: Session = Depends(get_db)):
    """Logout user and revoke refresh token."""
    auth_service.revoke_refresh_token(db, refresh_token)
    return {"message": "Logged out successfully"}

@router.post("/backup-login")
async def backup_login(request: BackupLoginRequest, db: Session = Depends(get_db)):
    """Backup login method using username/password."""
    # Simple backup authentication - in production, use proper password hashing
    # This is for emergency access only
    if request.username == "admin" and request.password == "admin":
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
    else:
        raise HTTPException(status_code=401, detail="Invalid backup credentials")

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
