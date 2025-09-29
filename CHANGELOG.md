# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.2] - 2025-09-29

### Fixed
- **OAuth Integration**: Fixed OAuth redirect logic to properly redirect to frontend with tokens
- **Token Handling**: Corrected OAuth callback redirect to use `redirect_uri` instead of hardcoded frontend URL
- **Frontend Integration**: Improved OAuth flow completion for Angular frontend integration

### Technical Details
- Updated OAuth callback redirect mechanism in `auth.py`
- Fixed token passing to frontend applications
- Maintained backward compatibility for existing OAuth configurations

## [1.1.1] - 2025-09-28

### Fixed
- Minor bug fixes and improvements

## [1.1.0] - 2025-09-11

## [1.1.0] - 2025-09-11

### Changed
- **BREAKING**: Project rebranded from "Atrium Authentication Service" to "FastAPI Authentication Service"
- **BREAKING**: Repository name changed from `docker-atrium-auth` to `docker-fastapi-auth`
- **BREAKING**: Container names updated from `atrium-auth-*` to `fastapi-auth-*`
- **BREAKING**: Network name changed from `atrium-auth-network` to `fastapi-auth-network`
- **BREAKING**: Default backup user email domain changed from `@atrium.local` to `@fastapi.local`
- **BREAKING**: API endpoints simplified - removed `/auth` prefix from all endpoints:
  - `/auth/login/{provider}` → `/login/{provider}`
  - `/auth/callback/{provider}` → `/callback/{provider}`
  - `/auth/refresh` → `/refresh`
  - `/auth/logout` → `/logout`
  - `/auth/me` → `/me`
  - `/auth/backup-login` → `/backup-login`

### Added
- Added missing `/logout` endpoint implementation

### Updated
- All documentation and README files with new branding
- OAuth callback URLs updated to reflect new endpoint structure
- API examples updated with simplified endpoint paths
- OpenAPI documentation updated with new endpoint structure
- All test files and integration tests updated
- Configuration scripts and examples updated

### Technical Details
- Updated project metadata across all configuration files
- Maintained backward compatibility for existing OAuth configurations
- All 39 tests continue to pass with updated assertions
- No breaking changes to API endpoints or functionality
- Database schema remains unchanged

### Migration Notes
- If upgrading from 1.0.x, update your docker-compose references to new service names
- Update any external references to container names or network names
- OAuth configurations and user data remain unchanged

## [1.0.0] - 2025-09-08

### Added
- Initial production-ready release
- OAuth 2.0 / OpenID Connect authentication service
- GitHub and Google OAuth integration
- JWT token management with refresh tokens
- User management with role-based access control
- Security features (CSRF protection, rate limiting)
- Health monitoring endpoints
- Comprehensive testing framework (39 tests)
- Docker containerization
- Backup user authentication system
- Complete documentation and deployment guides

### Security
- Secure JWT token handling
- Password hashing with bcrypt
- CSRF protection with state validation
- Redis-based session management
- Input validation and sanitization
