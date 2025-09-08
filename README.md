# Docker Atrium Auth Service

Centralized OAuth 2.0 / OpenID Connect authentication service for the Atrium infrastructure ecosystem.

## Overview

This service provides enterprise-grade authentication and authorization for all Atrium services, replacing the simple token-based authentication with a comprehensive user management system supporting multiple OAuth providers.

## Features

- **OAuth 2.0 / OpenID Connect Integration**
  - GitHub OAuth
  - Google OAuth
  - Extensible for additional providers
- **JWT Token Management**
  - Access tokens (configurable expiry, default 30 minutes)
  - Refresh tokens (configurable expiry, default 7 days)
  - Secure token revocation
- **User Management**
  - User profiles with permissions
  - Admin role management
  - Service-specific permissions
- **Session Management**
  - Redis-based session storage
  - CSRF protection
- **Emergency Access**
  - Backup login mechanism
  - Admin override capabilities
- **Security Features**
  - CORS configuration
  - Token hashing and validation
  - Secure password handling

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Atrium Apps   │    │  Auth Service    │    │  OAuth Provider │
│ (Lens, Nexus,   │◄──►│  (FastAPI)       │◄──►│  (GitHub/Google)│
│  Nginx, etc.)   │    └──────────────────┘    └─────────────────┘
└─────────────────┘             │
                                │
                                ▼
                     ┌──────────────────┐
                     │   User Database  │
                     │   (PostgreSQL)   │
                     │   + Redis Cache  │
                     └──────────────────┘
```

## Quick Start

1. **Clone and setup**:
```bash
git clone git@github.com:tecteluy/docker-atrium-auth.git
cd docker-atrium-auth
cp .env.example .env
```

2. **Configure OAuth providers** (see [OAuth Setup](#oauth-setup))

3. **Start services**:
```bash
# Development
docker compose --profile dev up -d --build

# Production
docker compose --profile prod up -d --build
```

4. **Verify health**:
```bash
curl http://localhost:8006/health
```

## Migration from docker-atrium-lens

This service is being migrated from the `docker-atrium-lens` project to become a standalone, reusable authentication service for the entire Atrium ecosystem.

### Migration Status

- [x] Repository created
- [ ] Auth service code migrated
- [ ] Docker configuration migrated
- [ ] Environment configuration setup
- [ ] OAuth provider configuration
- [ ] Database migrations setup
- [ ] Testing framework setup
- [ ] Integration with other Atrium services
- [ ] Documentation completion

### Migration Steps

1. **Copy auth service code from lens project**:
```bash
# Copy auth service directory
cp -r ../docker-atrium-lens/auth-service/ ./

# Copy relevant environment files
cp ../docker-atrium-lens/.env.example ./
cp ../docker-atrium-lens/.env.template ./
```

2. **Create standalone docker-compose.yml**:
```bash
# Extract auth-related services from lens docker-compose.yml
# - auth-service
# - auth-db (PostgreSQL)
# - auth-redis
```

3. **Update configuration**:
   - Update service URLs and ports
   - Configure standalone networking
   - Update environment variables

4. **Setup database migrations**:
```bash
# Initialize Alembic for database migrations
docker compose exec auth-service alembic init migrations
docker compose exec auth-service alembic revision --autogenerate -m "Initial migration"
docker compose exec auth-service alembic upgrade head
```

5. **Update dependent services**:
   - Modify `docker-atrium-lens` to use external auth service
   - Update `docker-atrium-nexus` to integrate with auth service
   - Configure other Atrium services for JWT authentication

## OAuth Setup

### GitHub OAuth Application

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Create new OAuth App:
   - **Application name**: `Atrium Infrastructure Authentication`
   - **Homepage URL**: `http://localhost:3000` (dev) / `https://your-domain.com` (prod)
   - **Authorization callback URL**: `http://localhost:8006/auth/callback/github`
3. Add credentials to `.env`:
```bash
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
```

### Google OAuth Application

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials:
   - **Authorized redirect URIs**: `http://localhost:8006/auth/callback/google`
5. Add credentials to `.env`:
```bash
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# OAuth Providers
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
POSTGRES_USER=atrium_auth
POSTGRES_PASSWORD=secure_password_change_this
POSTGRES_DB=atrium_auth
POSTGRES_HOST=auth-db
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://auth-redis:6379/0

# Application URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8006

# API Configuration
API_TOKEN=secure-api-token-change-this
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| GET | `/auth/login/{provider}` | Initiate OAuth login |
| GET | `/auth/callback/{provider}` | Handle OAuth callback |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Logout and revoke tokens |
| POST | `/auth/backup-login` | Emergency backup login |
| GET | `/auth/me` | Get current user info |

## Integration with Atrium Services

### For Client Applications (Frontend)

```javascript
// Example integration in Next.js
const authConfig = {
  authApiUrl: process.env.NEXT_PUBLIC_AUTH_API_URL || 'http://localhost:8006',
  providers: ['github', 'google']
};

// Login flow
const loginUrl = `${authConfig.authApiUrl}/auth/login/github`;
```

### For Backend Services (APIs)

```python
# Example integration in FastAPI
import httpx
from fastapi import Depends, HTTPException, Header

async def verify_token(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://auth-service:8001/auth/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
        
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    return response.json()
```

## Development

### Local Development Setup

```bash
# Install development dependencies
cd auth-service
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Start database services
docker compose up auth-db auth-redis -d

# Run auth service locally
cd auth-service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Database Migrations

```bash
# Generate new migration
docker compose exec auth-service alembic revision --autogenerate -m "Description of changes"

# Apply migrations
docker compose exec auth-service alembic upgrade head

# Rollback migration
docker compose exec auth-service alembic downgrade -1
```

### Testing

```bash
# Run all tests
docker compose --profile test up test-runner

# Run specific test file
docker compose exec auth-service pytest tests/test_auth_routes.py -v

# Run with coverage
docker compose exec auth-service pytest --cov=app tests/
```

## Deployment

### Development Deployment
```bash
docker compose --profile dev up -d --build
```

### Production Deployment
```bash
# Update environment variables for production
# Use strong passwords and secure tokens
# Configure proper OAuth callback URLs

docker compose --profile prod up -d --build
```

### Health Monitoring
```bash
# Check service health
curl http://localhost:8006/health

# Check logs
docker compose logs auth-service -f
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` files with real credentials
2. **JWT Secrets**: Use strong, unique secrets in production
3. **Database Security**: Use strong passwords and restrict network access
4. **OAuth Callbacks**: Ensure callback URLs are properly configured
5. **HTTPS**: Use HTTPS in production for all authentication flows
6. **Token Storage**: Use secure storage mechanisms on client side

## Integration Timeline

### Phase 1: Standalone Service (Current)
- [x] Create repository structure
- [ ] Migrate auth service code
- [ ] Setup Docker configuration
- [ ] Configure OAuth providers
- [ ] Setup database and migrations

### Phase 2: Lens Integration
- [ ] Update docker-atrium-lens to use external auth service
- [ ] Modify frontend authentication flow
- [ ] Update API client configurations

### Phase 3: Nexus Integration
- [ ] Replace API token auth with JWT in docker-atrium-nexus
- [ ] Add user permission checking
- [ ] Update management API endpoints

### Phase 4: Full Ecosystem Integration
- [ ] Integrate with docker-atrium-nginx
- [ ] Add authentication to docker-atrium-certbot
- [ ] Extend to other Atrium services
- [ ] Implement service-specific permissions

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/description`
3. Make changes and test thoroughly
4. Commit with clear messages
5. Push to your fork and create Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions, please use the GitHub Issues system or contact the Atrium development team.
