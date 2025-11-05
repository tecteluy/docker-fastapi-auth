from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.auth_service import AuthService
from ..services.oauth_service import OAuthService
from ..services.token_service import TokenService
from ..middleware.auth_middleware import get_current_user, verify_api_token
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

    # Debug: Log all query parameters
    logger = logging.getLogger(__name__)
    logger.info(f"All query params: {dict(request.query_params)}")

    # Get redirect_uri from query parameters (sent by client app)
    redirect_uri = request.query_params.get("redirect_uri")
    if not redirect_uri:
        # Use the provider-specific callback endpoint through the configured base URL
        redirect_uri = f"{settings.base_url}/callback/{provider}"
    
    # Get client_redirect_uri - where to redirect after successful auth
    client_redirect_uri = request.query_params.get("client_redirect_uri")
    logger.info(f"client_redirect_uri from query: '{client_redirect_uri}'")
    if not client_redirect_uri:
        # Default to signin page if not specified
        client_redirect_uri = f"{settings.frontend_url}/signin?success=true"
        logger.info(f"Using default client_redirect_uri: {client_redirect_uri}")
    else:
        logger.info(f"Using provided client_redirect_uri: {client_redirect_uri}")

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store redirect_uri, client_redirect_uri and provider in state for later retrieval
    # Format: "state|oauth_redirect_uri|client_redirect_uri|provider" (using | separator to avoid URL colon conflicts)
    state_data = f"{state}|{redirect_uri}|{client_redirect_uri}|{provider}"
    logger.info(f"Generated state_data: {state_data}")

    # Store state in session (you might want to use Redis for production)
    if provider == "github":
        auth_url = oauth_service.get_github_auth_url(state_data, redirect_uri)
    else:  # google
        auth_url = oauth_service.get_google_auth_url(state_data, redirect_uri)

    return {"auth_url": auth_url, "state": state_data}



@router.get("/callback/{provider}")
async def auth_callback(
    provider: str,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback for specific provider."""
    logger = logging.getLogger(__name__)
    logger.info(f"OAuth callback received - Provider: {provider}, Code: {code[:10]}..., State: {state}")
    
    if provider not in ["github", "google"]:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    # Extract redirect_uri and client_redirect_uri from state 
    # Handle both pipe format "state|redirect_uri|client_redirect_uri|provider" and old colon format
    try:
        # URL-decode the state parameter first
        decoded_state = unquote(state)
        
        # Parse state based on format - check for pipe separator first (new format)
        if "|" in decoded_state:
            # New pipe format: state|redirect_uri|client_redirect_uri|provider
            state_parts = decoded_state.split("|")
            if len(state_parts) >= 4:
                state_part = state_parts[0]
                redirect_uri = state_parts[1] 
                client_redirect_uri = state_parts[2]
                state_provider = state_parts[3]
            else:
                # Fallback for malformed pipe format
                redirect_uri = f"{settings.base_url}/callback/{provider}"
                client_redirect_uri = f"{settings.frontend_url}/signin?success=true"
                state_provider = provider
        elif decoded_state.count(":") >= 2:
            # Old colon format: state:redirect_uri:provider or state:redirect_uri:client_redirect_uri:provider
            state_parts = decoded_state.split(":")
            state_part = state_parts[0]
            
            # Check if this has client_redirect_uri (4+ parts) vs old format (3 parts)
            if len(state_parts) >= 4:
                # New format: state:redirect_uri:client_redirect_uri:provider (but URLs have colons too)
                # Need to handle URLs with colons properly
                redirect_uri = ":".join(state_parts[1:-2])  # Middle parts form the redirect_uri
                client_redirect_uri = state_parts[-2]  # Second to last is client_redirect_uri
                state_provider = state_parts[-1]  # Last part is provider
            else:
                # Old format: state:redirect_uri:provider
                redirect_uri = ":".join(state_parts[1:-1])  # Everything except first and last
                state_provider = state_parts[-1]  # Last part is provider
                client_redirect_uri = f"{settings.frontend_url}/signin?success=true"  # Default
        else:
            # Fallback
            redirect_uri = f"{settings.base_url}/callback/{provider}"
            client_redirect_uri = f"{settings.frontend_url}/signin?success=true"
            state_provider = provider
            
    except (ValueError, IndexError):
        # Fallback for malformed state
        redirect_uri = f"{settings.base_url}/callback/{provider}"
        client_redirect_uri = f"{settings.frontend_url}/signin?success=true"

    logger.info(f"Parsed state - redirect_uri: {redirect_uri}, client_redirect_uri: {client_redirect_uri}")

    # Exchange code for user data
    if provider == "github":
        oauth_data = await oauth_service.exchange_github_code(code)
    else:
        oauth_data = await oauth_service.exchange_google_code(code, redirect_uri)

    if not oauth_data:
        logger.error(f"OAuth exchange failed for provider {provider} with redirect_uri: {redirect_uri}")
        # Redirect to client app with error - remove any existing success param and add error
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed_url = urlparse(client_redirect_uri)
        query_params = parse_qs(parsed_url.query)
        
        # Remove success parameter if it exists and add error parameter
        query_params.pop('success', None)
        query_params['error'] = ['oauth_failed']
        
        # Rebuild the URL
        new_query = urlencode(query_params, doseq=True)
        error_redirect = urlunparse((
            parsed_url.scheme, parsed_url.netloc, parsed_url.path,
            parsed_url.params, new_query, parsed_url.fragment
        ))
        logger.info(f"Redirecting to error page: {error_redirect}")
        return RedirectResponse(url=error_redirect)

    # Check if user exists (don't auto-create new users)
    user = auth_service.get_existing_user(db, oauth_data)
    
    if not user:
        # User is not registered - redirect with NotRegistered error
        logger.info(f"User not registered: {oauth_data.get('email', 'Unknown')} from {provider}")
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed_url = urlparse(client_redirect_uri)
        query_params = parse_qs(parsed_url.query)
        
        # Remove success parameter if it exists and add error parameter
        query_params.pop('success', None)
        query_params['error'] = ['NotRegistered']
        query_params['name'] = [oauth_data.get('full_name', oauth_data.get('username', 'User'))]
        
        # Rebuild the URL
        new_query = urlencode(query_params, doseq=True)
        error_redirect = urlunparse((
            parsed_url.scheme, parsed_url.netloc, parsed_url.path,
            parsed_url.params, new_query, parsed_url.fragment
        ))
        logger.info(f"Redirecting to not registered error: {error_redirect}")
        return RedirectResponse(url=error_redirect)

    # Generate JWT tokens for the authenticated user
    tokens = auth_service.create_tokens(db, user)

    # Use the client_redirect_uri from state
    return RedirectResponse(url=client_redirect_uri)

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
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user (client should remove tokens)."""
    # In a more advanced implementation, you might want to blacklist the refresh token
    return {"message": "Logged out successfully"}

class PreRegisterUserRequest(BaseModel):
    email: str
    provider: str  # 'github' or 'google'
    provider_id: str
    username: str
    full_name: str | None = None

@router.post("/admin/pre-register")
async def pre_register_user(
    request: PreRegisterUserRequest, 
    db: Session = Depends(get_db),
    api_token_valid: bool = Depends(verify_api_token)  # Require valid API token
):
    """Pre-register a user so they can sign in via OAuth. 
    
    Requires:
    - Valid API token in Authorization header (Bearer <API_TOKEN>)
    
    This endpoint is restricted to authorized administrators only.
    """
    from ..models.user import User
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        User.provider == request.provider,
        User.provider_id == request.provider_id
    ).first()
    
    if existing_user:
        return {"message": f"User {request.email} is already registered"}
    
    # Create pre-registered user
    user = User(
        email=request.email,
        username=request.username,
        full_name=request.full_name,
        provider=request.provider,
        provider_id=request.provider_id,
        provider_data={},
        is_active=True,
        is_admin=False,
        permissions={"services": []}
    )
    db.add(user)
    db.commit()
    
    return {"message": f"User {request.email} pre-registered successfully"}

@router.get("/admin/users")
async def list_users(
    db: Session = Depends(get_db),
    api_token_valid: bool = Depends(verify_api_token)
):
    """List all registered users. Requires API token authentication."""
    from ..models.user import User
    
    users = db.query(User).all()
    
    return {
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "provider": user.provider,
                "provider_id": user.provider_id,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "created_at": user.created_at,
                "last_login": user.last_login
            }
            for user in users
        ]
    }

@router.delete("/admin/users/{user_id}")
async def remove_user(
    user_id: int,
    db: Session = Depends(get_db),
    api_token_valid: bool = Depends(verify_api_token)
):
    """Remove a user by ID. Requires API token authentication."""
    from ..models.user import User
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store user info for response
    user_info = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "provider": user.provider
    }
    
    # Delete the user
    db.delete(user)
    db.commit()
    
    return {"message": f"User {user_info['email']} removed successfully", "user": user_info}

@router.get("/admin/users/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    api_token_valid: bool = Depends(verify_api_token)
):
    """Get a specific user by ID. Requires API token authentication."""
    from ..models.user import User
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "provider": user.provider,
        "provider_id": user.provider_id,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "created_at": user.created_at,
        "last_login": user.last_login,
        "permissions": user.permissions
    }
