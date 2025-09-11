from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional

class Settings(BaseSettings):
    # OAuth Providers
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    # JWT Configuration
    jwt_secret_key: str = "your-super-secret-jwt-key-change-this"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Database
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_db: str = "atrium_auth"
    postgres_host: str = "auth-db"
    postgres_port: int = 5432
    postgres_host_auth_method: str = "scram-sha-256"

    # Redis
    redis_url: str = "redis://auth-redis:6379/0"
    redis_password: Optional[str] = None
    redis_port: int = 6379

    # Application URLs
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8006"

    # Service Configuration
    auth_service_port: int = 8008

    # API Configuration
    api_token: str = "changeme"

    # Environment
    environment: str = "production"

    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()
