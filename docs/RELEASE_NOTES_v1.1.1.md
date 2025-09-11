# Release Notes v1.1.1

**Release Date:** September 11, 2025
**Tag:** `v1.1.1`
**Branch:** `develop`

## 🚀 Major Features

### Comprehensive Logging Middleware System
- **RequestLoggingMiddleware**: Complete HTTP request/response logging with sensitive data masking
- **Configurable Logging**: Enable/disable functionality via `ENABLE_REQUEST_LOGGING` environment variable
- **Persistent Storage**: Docker volume mounting to `./logs/` directory for log persistence
- **Multi-File Logging**: Separate log files for different concerns:
  - `requests.log` - HTTP request/response logging
  - `auth.log` - Authentication-specific logs
  - `oauth.log` - OAuth flow logs
  - `error.log` - Error logs
  - `app.log` - General application logs
  - `database.log` - Database operation logs

### Advanced Security Features
- **Sensitive Data Masking**: Automatic masking of passwords, tokens, and sensitive fields
- **Configurable Exclusions**: Health endpoints excluded from logging
- **Security Headers**: Proper handling of authorization headers

### Performance & Monitoring
- **Async Logging**: Non-blocking logging with FastAPI async support
- **Memory Usage Tracking**: Performance monitoring with `psutil` integration
- **Concurrent Request Handling**: Thread-safe logging for high-load scenarios
- **Response Time Tracking**: Process time measurement for each request

## 🔧 Technical Improvements

### Port Configuration
- **Breaking Change**: Service now runs on port **8008** (was 8006)
- Updated `BACKEND_URL` environment variable to match actual service port
- Consistent port mapping: `8008:8000` (external:internal)

### Testing Infrastructure
- **114 Tests Passing**: Comprehensive test coverage
- **Test Categories**: Unit, Integration, and End-to-End tests
- **Test Types**: 
  - Unit tests for middleware functionality
  - Integration tests for endpoint logging
  - E2E tests for complete logging flows
- **Mock Testing**: Proper async mock handling for external services
- **Performance Testing**: Load testing and memory usage validation

### Code Quality
- **Async/Await Patterns**: Proper async handling throughout codebase
- **Error Handling**: Comprehensive error handling and logging
- **Type Hints**: Full type annotation coverage
- **Code Organization**: Clean separation of concerns

## 📚 Documentation & Scripts

### Documentation
- **`docs/LOGGING.md`**: Comprehensive logging system documentation
- **`docs/README.md`**: Updated project documentation
- **Configuration Examples**: Environment variable examples and setup guides

### Testing Scripts
- **`scripts/test-logging.sh`**: Automated logging functionality testing
- **Test Utilities**: Helper functions and fixtures for testing
- **Configuration Files**: Updated pytest configuration

## 🐛 Bug Fixes

### Test Fixes
- Fixed hanging test issues caused by middleware consuming request body
- Resolved async mock configuration problems
- Fixed status code assertions for various endpoint scenarios
- Added missing `psutil` dependency for memory monitoring

### Middleware Fixes
- **Critical Fix**: Middleware no longer consumes request body, preventing endpoint access issues
- Proper handling of different content types
- Fixed Unicode and special character handling in logs
- Resolved concurrent request logging conflicts

## 🔄 Dependencies

### New Dependencies
- `psutil==5.9.6` - System and process monitoring
- Enhanced logging dependencies

### Updated Dependencies
- All existing dependencies maintained with latest compatible versions
- Test framework dependencies updated for better async support

## ⚠️ Breaking Changes

1. **Port Change**: Service now runs on port 8008 instead of 8006
2. **Environment Variables**: Added new logging-related environment variables
3. **Log Files**: New log files will be created in the `logs/` directory

## 🚀 Migration Guide

### For Existing Users
1. Update any hardcoded references from port 8006 to 8008
2. Update environment variables if overriding defaults:
   ```bash
   ENABLE_REQUEST_LOGGING=true  # Enable/disable logging
   LOG_LEVEL=INFO              # Set log level
   ```
3. Ensure the `logs/` directory is properly mounted for log persistence

### Docker Compose
```yaml
services:
  auth-service:
    ports:
      - "8008:8000"  # Updated port mapping
    volumes:
      - ./logs:/app/logs  # Log persistence
    environment:
      - ENABLE_REQUEST_LOGGING=true
      - LOG_LEVEL=INFO
```

## 📊 Test Results

```
114 passed, 15 skipped, 13 warnings in 5.10s
```

- **Total Tests**: 129
- **Passed**: 114 ✅
- **Skipped**: 15 (intentional)
- **Failed**: 0 ✅
- **Test Coverage**: Comprehensive coverage across all logging functionality

## 🎯 Next Steps

- Monitor logging performance in production
- Consider additional log retention policies
- Evaluate integration with external logging systems
- Performance optimizations for high-traffic scenarios

## 🙏 Acknowledgments

This release represents a significant enhancement to the authentication service with a focus on observability, security, and maintainability. The comprehensive logging system provides valuable insights into system behavior while maintaining security best practices.
