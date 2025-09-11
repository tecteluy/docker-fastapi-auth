#!/usr/bin/env bash
set -e

# Configuration wizard for FastAPI Authentication Service
# This script will prompt for required environment variables and generate a .env file.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/.."
ENV_FILE="$PROJECT_ROOT/.env"

echo "\n=== FastAPI Auth Service Configuration Wizard ===\n"

# helper to prompt with default value
prompt() {
    local var_name="$1"
    local prompt_text="$2"
    local default_value="$3"
    read -p "$prompt_text [$default_value]: " input
    if [ -z "$input" ]; then
        echo "$default_value"
    else
        echo "$input"
    fi
}

# GitHub OAuth
GITHUB_CLIENT_ID=$(prompt GITHUB_CLIENT_ID "GitHub Client ID" "")
GITHUB_CLIENT_SECRET=$(prompt GITHUB_CLIENT_SECRET "GitHub Client Secret" "")

# Google OAuth
GOOGLE_CLIENT_ID=$(prompt GOOGLE_CLIENT_ID "Google Client ID" "")
GOOGLE_CLIENT_SECRET=$(prompt GOOGLE_CLIENT_SECRET "Google Client Secret" "")

# JWT
JWT_SECRET_KEY=$(prompt JWT_SECRET_KEY "JWT Secret Key (hex)" "$(openssl rand -hex 32)")
JWT_ALGORITHM=$(prompt JWT_ALGORITHM "JWT Algorithm" "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=$(prompt JWT_ACCESS_TOKEN_EXPIRE_MINUTES "Access Token Expire Minutes" "30")
JWT_REFRESH_TOKEN_EXPIRE_DAYS=$(prompt JWT_REFRESH_TOKEN_EXPIRE_DAYS "Refresh Token Expire Days" "7")

# Database
POSTGRES_USER=$(prompt POSTGRES_USER "Postgres User" "atrium_auth")
POSTGRES_PASSWORD=$(prompt POSTGRES_PASSWORD "Postgres Password" "")
POSTGRES_DB=$(prompt POSTGRES_DB "Postgres DB Name" "atrium_auth")
POSTGRES_PORT=$(prompt POSTGRES_PORT "Postgres Port" "5432")
POSTGRES_HOST_AUTH_METHOD=$(prompt POSTGRES_HOST_AUTH_METHOD "Postgres Host Auth Method" "scram-sha-256")

    # Redis
    # Generate a strong random password if none provided
    REDIS_PASSWORD=$(prompt REDIS_PASSWORD "Redis Password" "$(openssl rand -hex 16)")
REDIS_PORT=$(prompt REDIS_PORT "Redis Port" "6379")

# URLs and Ports
FRONTEND_URL=$(prompt FRONTEND_URL "Frontend URL" "http://localhost:3000")
BACKEND_URL=$(prompt BACKEND_URL "Backend URL" "http://localhost:8008")
AUTH_SERVICE_PORT=$(prompt AUTH_SERVICE_PORT "Auth Service Port" "8008")

# API TOKEN and ENV
API_TOKEN=$(prompt API_TOKEN "Internal API Token" "$(openssl rand -hex 16)")
ENVIRONMENT=$(prompt ENVIRONMENT "Environment (production/development)" "production")

# Create .env
cat > "$ENV_FILE" <<EOF
# Docker FastAPI Auth Service Configuration

# OAuth Providers Configuration
GITHUB_CLIENT_ID=$GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET=$GITHUB_CLIENT_SECRET
GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET

# JWT Configuration
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ALGORITHM=$JWT_ALGORITHM
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=$JWT_ACCESS_TOKEN_EXPIRE_MINUTES
JWT_REFRESH_TOKEN_EXPIRE_DAYS=$JWT_REFRESH_TOKEN_EXPIRE_DAYS

# Database Configuration
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_DB=$POSTGRES_DB
POSTGRES_PORT=$POSTGRES_PORT
POSTGRES_HOST_AUTH_METHOD=$POSTGRES_HOST_AUTH_METHOD

# Redis Configuration
REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_PORT=$REDIS_PORT

# Application URLs
FRONTEND_URL=$FRONTEND_URL
BACKEND_URL=$BACKEND_URL

# Service Ports
AUTH_SERVICE_PORT=$AUTH_SERVICE_PORT

# API Configuration
API_TOKEN=$API_TOKEN

# Development/Testing
ENVIRONMENT=$ENVIRONMENT

# Backup Users (leave blank or configure manually)
# BACKUP_USERS={"username": {"password_hash": "<hash>", "is_admin": true, "permissions": {"services": ["*"]}}}
EOF

echo "\n.env file created at $ENV_FILE\n"
