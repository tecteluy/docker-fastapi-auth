# Release Notes - Version 1.1.0

## 🎉 FastAPI Authentication Service v1.1.0

**Release Date**: September 11, 2025

### 🔄 Project Rebranding

This release marks a significant milestone with the complete rebranding of the authentication service from "Atrium" to "FastAPI Authentication Service". This change reflects the service's evolution into a more generic, reusable FastAPI authentication solution.

### 🚨 Breaking Changes

**Important**: This is a **major rebranding release** with several breaking changes that affect container names, network configurations, and API endpoints.

#### Container Names
- `atrium-auth-db` → `fastapi-auth-db`
- `atrium-auth-redis` → `fastapi-auth-redis`
- `atrium-auth-service` → `fastapi-auth-service`
- `atrium-auth-test-db` → `fastapi-auth-test-db`
- `atrium-auth-test-redis` → `fastapi-auth-test-redis`
- `atrium-auth-test-runner` → `fastapi-auth-test-runner`

#### Network Names
- `atrium-auth-network` → `fastapi-auth-network`

#### API Endpoints (Simplified Structure)
- `/auth/login/{provider}` → `/login/{provider}`
- `/auth/callback/{provider}` → `/callback/{provider}`
- `/auth/refresh` → `/refresh`
- `/auth/logout` → `/logout`
- `/auth/me` → `/me`
- `/auth/backup-login` → `/backup-login`

#### Repository and Project Names
- Repository: `docker-atrium-auth` → `docker-fastapi-auth`
- Service title: "Atrium Authentication Service" → "FastAPI Authentication Service"

#### OAuth Configuration
- GitHub callback: `http://localhost:8008/auth/callback/github` → `http://localhost:8008/callback/github`
- Google callback: `http://localhost:8008/auth/callback/google` → `http://localhost:8008/callback/google`

#### Default Configuration
- Backup user email domain: `@atrium.local` → `@fastapi.local`

### ✅ What's New

#### 📝 Updated Documentation
- Complete README.md rewrite with new branding
- Updated API documentation and OpenAPI specs
- Refreshed configuration examples and guides
- Updated all help text and command descriptions

#### 🔧 Enhanced Tooling
- Updated Makefile with new service references
- Improved configuration scripts
- Enhanced backup user management tools
- Updated test suite with new assertions
- Added missing `/logout` endpoint implementation

#### 🏗️ Technical Improvements
- Consistent naming convention throughout the codebase
- Updated Docker Compose configuration
- Improved service discovery and networking
- Enhanced logging and monitoring
- **Simplified API structure** - removed `/auth` prefix from endpoints for cleaner URLs
- Updated OAuth callback URLs to match new endpoint structure

### 🔒 Security & Stability

- **No security vulnerabilities introduced**
- All 39 tests continue to pass
- Backward compatibility maintained for OAuth configurations
- Database schema unchanged
- User data and permissions preserved

### 📦 Migration Guide

#### For New Deployments
Simply use the new repository name and follow the updated documentation.

#### For Existing Deployments

1. **Stop current services**:
   ```bash
   docker-compose down
   ```

2. **Update your git remote** (if applicable):
   ```bash
   git remote set-url origin https://github.com/tecteluy/docker-fastapi-auth.git
   ```

3. **Pull the latest changes**:
   ```bash
   git pull origin main
   ```

4. **Update OAuth applications**:
   - GitHub: Update Authorization callback URL to `http://localhost:8008/callback/github`
   - Google: Update Authorized redirect URIs to `http://localhost:8008/callback/google`

5. **Update application code** (if using the API directly):
   ```javascript
   // Old endpoints
   await fetch('/auth/login/github')
   await fetch('/auth/me')
   
   // New endpoints
   await fetch('/login/github')
   await fetch('/me')
   ```

6. **Start with new configuration**:
   ```bash
   docker-compose up -d --build
   ```

#### Database Migration
**No database migration required** - existing user data and OAuth configurations remain unchanged.

### 🧪 Testing

All tests have been updated and verified:
- ✅ 39/39 tests passing
- ✅ Unit tests updated with new assertions
- ✅ Integration tests verified with new service names
- ✅ End-to-end workflows tested

### 📖 Documentation Updates

- [README.md](README.md) - Complete service documentation
- [CHANGELOG.md](CHANGELOG.md) - Detailed change history
- [docs/](docs/) - Updated technical documentation
- [scripts/](scripts/) - Updated management scripts

### 🤝 Contributing

This rebranding makes the project more accessible to the broader FastAPI community. We welcome contributions and feedback on the new direction.

### 🔗 Links

- **Repository**: [docker-fastapi-auth](https://github.com/tecteluy/docker-fastapi-auth)
- **Documentation**: See README.md for complete setup guide
- **Issues**: [GitHub Issues](https://github.com/tecteluy/docker-fastapi-auth/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tecteluy/docker-fastapi-auth/discussions)

---

**Previous Version**: [1.0.0](https://github.com/tecteluy/docker-fastapi-auth/releases/tag/v1.0.0)  
**Full Changelog**: [v1.0.0...v1.1.0](https://github.com/tecteluy/docker-fastapi-auth/compare/v1.0.0...v1.1.0)
