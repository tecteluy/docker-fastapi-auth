# Logging System

The FastAPI Authentication Service includes a comprehensive logging system that provides detailed insights into application behavior, OAuth flows, database operations, and HTTP requests.

## Log Configuration

### Environment Variables

The logging system can be configured using the following environment variables:

```bash
# Enable/disable request logging
ENABLE_REQUEST_LOGGING=true

# Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO
```

### Default Settings

- **Request Logging**: Enabled by default
- **Log Level**: INFO
- **Log Rotation**: 10MB max file size, 5 backup files
- **Log Directory**: `/app/logs` (mounted to `./logs` on host)

## Log Files

The system generates several specialized log files:

### 1. Application Logs (`app.log`)
- General application events and errors
- Service startup/shutdown events
- Configuration changes
- General debugging information

### 2. Request Logs (`requests.log`)
- Detailed HTTP request/response logging
- Request method, URL, headers
- Response status codes and processing time
- Client IP addresses and user agents
- **Note**: Request body logging is currently disabled to prevent middleware conflicts

### 3. OAuth Logs (`oauth.log`)
- OAuth provider interactions
- Authorization flows
- Token exchanges
- Provider-specific errors and responses

### 4. Authentication Logs (`auth.log`)
- User login/logout events
- JWT token generation and validation
- Authentication failures and security events
- Session management

### 5. Database Logs (`database.log`)
- Database connection events
- Query performance information
- Migration events
- Database errors and warnings

### 6. Error Logs (`error.log`)
- Application errors and exceptions
- Stack traces for debugging
- Critical system failures

## Log Format

All logs use a consistent format:
```
YYYY-MM-DD HH:MM:SS - logger_name - LEVEL - message
```

Request logs include additional structured JSON data:
```json
{
  "type": "http_request",
  "request": {
    "method": "POST",
    "url": "http://localhost:8008/login/github",
    "path": "/login/github",
    "query_params": {},
    "headers": {...},
    "client_ip": "172.21.0.1",
    "user_agent": "Mozilla/5.0...",
    "body": {...}
  },
  "response": {
    "status_code": 200,
    "headers": {...},
    "process_time": 0.1234
  },
  "timestamp": 1694123456.789
}
```

## Security Features

### Sensitive Data Masking

The logging system automatically masks sensitive information:
- Passwords
- API keys and secrets
- JWT tokens
- OAuth client secrets
- Authorization headers

Masked fields show only the last 4 characters: `***word`

### Health Check Filtering

Health check requests (`/health`, `/`, `/docs`, `/openapi.json`) are excluded from request logs to reduce noise.

## Accessing Logs

### Using Docker Compose

```bash
# View real-time logs for the auth service
docker-compose logs -f auth-service

# View specific log file
docker-compose exec auth-service tail -f /app/logs/requests.log

# View last 100 lines of application logs
docker-compose exec auth-service tail -100 /app/logs/app.log
```

### Host File System

Logs are mounted to the host filesystem in the `./logs` directory:

```bash
# View request logs
tail -f ./logs/requests.log

# View error logs
tail -f ./logs/error.log

# View all authentication events
grep "login\|logout\|auth" ./logs/auth.log
```

## Log Management

### Rotation

Log files automatically rotate when they reach 10MB:
- Original file: `app.log`
- Rotated files: `app.log.1`, `app.log.2`, etc.
- Maximum 5 backup files are kept

### Cleanup

To clean up old logs:

```bash
# Remove all log files (service must be stopped)
rm -f ./logs/*.log*

# Or remove logs older than 30 days
find ./logs -name "*.log*" -mtime +30 -delete
```

## Enabling/Disabling Logging

### Disable Request Logging

```bash
# In .env file
ENABLE_REQUEST_LOGGING=false

# Or set environment variable
export ENABLE_REQUEST_LOGGING=false
```

### Change Log Level

```bash
# In .env file
LOG_LEVEL=DEBUG  # More verbose logging
LOG_LEVEL=WARNING  # Less verbose logging

# Or set environment variable
export LOG_LEVEL=DEBUG
```

### Restart Service

After changing logging configuration:

```bash
docker-compose restart auth-service
```

## Troubleshooting

### No Logs Generated

1. Check if the logs directory is mounted correctly
2. Verify file permissions on the logs directory
3. Check container logs for permission errors:
   ```bash
   docker-compose logs auth-service
   ```

### Log Files Too Large

1. Adjust rotation settings in `logging_config.py`
2. Lower the log level to reduce verbosity
3. Disable request logging for high-traffic scenarios

### Missing Sensitive Data in Logs

The system automatically masks sensitive data. If you need to see full request data for debugging:

1. Temporarily modify the `_mask_sensitive_data` method in `logging_middleware.py`
2. **Always** restore masking before production deployment

## Production Recommendations

1. **Log Level**: Use `INFO` or `WARNING` in production
2. **Request Logging**: Consider disabling for high-traffic applications
3. **Log Retention**: Implement external log rotation/archival
4. **Monitoring**: Set up log aggregation (ELK stack, Splunk, etc.)
5. **Alerts**: Monitor error logs for application issues

## Development Tips

1. **Debugging**: Use `LOG_LEVEL=DEBUG` for detailed information
2. **Testing**: Check logs to verify OAuth flows and authentication
3. **Performance**: Monitor `process_time` in request logs
4. **Security**: Review authentication logs for suspicious activity
