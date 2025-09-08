import httpx
from typing import Optional, Dict, Any
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class OAuthService:
    def __init__(self):
        self.github_client_id = settings.github_client_id
        self.github_client_secret = settings.github_client_secret
        self.google_client_id = settings.google_client_id
        self.google_client_secret = settings.google_client_secret
        self.frontend_url = settings.frontend_url

    def get_github_auth_url(self, state: str) -> str:
        """Generate GitHub OAuth authorization URL."""
        redirect_uri = f"{self.frontend_url}/auth/callback/github"
        return (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={self.github_client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope=user:email"
            f"&state={state}"
        )

    def get_google_auth_url(self, state: str) -> str:
        """Generate Google OAuth authorization URL."""
        redirect_uri = f"{self.frontend_url}/auth/callback/google"
        return (
            f"https://accounts.google.com/o/oauth2/auth"
            f"?client_id={self.google_client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope=openid email profile"
            f"&response_type=code"
            f"&state={state}"
        )

    async def exchange_github_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange GitHub authorization code for access token and user data."""
        try:
            # Exchange code for access token
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        "client_id": self.github_client_id,
                        "client_secret": self.github_client_secret,
                        "code": code,
                    },
                    headers={"Accept": "application/json"}
                )
                token_data = token_response.json()

                if "access_token" not in token_data:
                    return None

                # Get user data
                user_response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"token {token_data['access_token']}",
                        "Accept": "application/json"
                    }
                )
                user_data = user_response.json()

                # Get user email if not public
                if not user_data.get("email"):
                    email_response = await client.get(
                        "https://api.github.com/user/emails",
                        headers={
                            "Authorization": f"token {token_data['access_token']}",
                            "Accept": "application/json"
                        }
                    )
                    emails = email_response.json()
                    primary_email = next((e for e in emails if e["primary"]), None)
                    if primary_email:
                        user_data["email"] = primary_email["email"]

                return {
                    "provider": "github",
                    "provider_id": str(user_data["id"]),
                    "email": user_data.get("email"),
                    "username": user_data["login"],
                    "full_name": user_data.get("name"),
                    "avatar_url": user_data.get("avatar_url"),
                    "provider_data": user_data
                }
        except Exception as e:
            logger.error(f"GitHub OAuth error: {e}")
            return None

    async def exchange_google_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange Google authorization code for access token and user data."""
        try:
            redirect_uri = f"{self.frontend_url}/auth/callback/google"

            async with httpx.AsyncClient() as client:
                # Exchange code for access token
                token_response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": self.google_client_id,
                        "client_secret": self.google_client_secret,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": redirect_uri,
                    }
                )
                token_data = token_response.json()

                if "access_token" not in token_data:
                    return None

                # Get user data
                user_response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={
                        "Authorization": f"Bearer {token_data['access_token']}"
                    }
                )
                user_data = user_response.json()

                return {
                    "provider": "google",
                    "provider_id": user_data["id"],
                    "email": user_data["email"],
                    "username": user_data["email"].split("@")[0],
                    "full_name": user_data.get("name"),
                    "avatar_url": user_data.get("picture"),
                    "provider_data": user_data
                }
        except Exception as e:
            logger.error(f"Google OAuth error: {e}")
            return None
