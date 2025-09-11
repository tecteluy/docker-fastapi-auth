# Git Release Commands for v1.1.0

## Pre-Release Checklist ✅

- [x] Version updated in main.py (1.0.0 → 1.1.0)
- [x] Version badge added to README.md
- [x] Changelog created (CHANGELOG.md)
- [x] Release notes created (RELEASE_NOTES_v1.1.0.md)
- [x] All tests passing (58 passed, 12 skipped)
- [x] Documentation updated with new branding

## Git Commands to Create Release

### 1. Stage all changes
```bash
git add .
```

### 2. Commit with release message
```bash
git commit -m "Release v1.1.0: Rebrand to FastAPI Authentication Service

- Project rebranded from Atrium to FastAPI Authentication Service
- Updated container names and network configurations 
- Enhanced documentation and configuration scripts
- All 58 tests passing
- Backward compatibility maintained for OAuth configurations

BREAKING CHANGES:
- Container names: atrium-auth-* → fastapi-auth-*
- Network name: atrium-auth-network → fastapi-auth-network
- Repository: docker-atrium-auth → docker-fastapi-auth
- Email domain: @atrium.local → @fastapi.local"
```

### 3. Create and push tag
```bash
git tag -a v1.1.0 -m "Version 1.1.0 - FastAPI Authentication Service Rebranding

Major rebranding release transitioning from Atrium to FastAPI Authentication Service.

Key Changes:
- Complete project rebranding and documentation updates
- Updated container and network naming conventions
- Enhanced configuration and management tools
- All tests updated and verified (58 passing)

Breaking Changes:
- Service and container names updated
- Network configuration changed
- Repository name changed

Migration required for existing deployments.
See RELEASE_NOTES_v1.1.0.md for detailed migration guide."

git push origin v1.1.0
```

### 4. Push changes to main branch
```bash
git push origin main
```

## GitHub Release Creation

After pushing the tag, create a GitHub release:

1. Go to GitHub repository releases page
2. Click "Create a new release"
3. Select tag: `v1.1.0`
4. Release title: `v1.1.0 - FastAPI Authentication Service`
5. Description: Copy content from RELEASE_NOTES_v1.1.0.md
6. Mark as "Set as the latest release"
7. Publish release

## Post-Release Actions

1. Update any CI/CD pipelines with new repository name
2. Update documentation links if repository was moved
3. Notify users about breaking changes via appropriate channels
4. Update any external service integrations

## Version Verification

Verify the version is correctly set:
```bash
# Check API version
curl http://localhost:8008/docs
# Should show version 1.1.0 in OpenAPI spec

# Check container names
docker-compose ps
# Should show fastapi-auth-* container names
```
