# Testing Guide for Docker FastAPI Auth Service

## Overview

This document describes the testing setup for the Docker FastAPI Auth Service, including how to run tests using Docker Compose.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests
│   ├── __init__.py
│   ├── test_token_service.py
│   └── ...
├── integration/             # Integration tests
│   ├── __init__.py
│   ├── test_health.py
│   └── ...
├── e2e/                     # End-to-end tests
│   ├── __init__.py
│   └── ...
└── ...
```

## Running Tests

### Method 1: Using Docker Compose (Recommended)

All test dependencies are installed within containers, not on the host machine.

```bash
# Run all tests
docker-compose --profile test run --rm test-runner

# Run specific test categories
docker-compose --profile test run --rm test-runner pytest tests/unit/
docker-compose --profile test run --rm test-runner pytest tests/integration/
docker-compose --profile test run --rm test-runner pytest tests/e2e/

# Run with coverage report
docker-compose --profile test run --rm test-runner pytest tests/ --cov=app --cov-report=html
```

### Method 2: Using Test Script

```bash
# Run all tests
./scripts/run-tests.sh

# Run specific test categories
./scripts/run-tests.sh unit
./scripts/run-tests.sh integration
./scripts/run-tests.sh e2e
```

### Method 3: Manual Docker Commands

```bash
# Start test services
docker-compose --profile test up -d test-db test-redis

# Run tests
docker-compose --profile test run --rm test-runner pytest tests/ -v

# Stop test services
docker-compose --profile test down
```

## Test Configuration

### Test Database
- **Host**: test-db
- **Port**: 5432
- **Database**: test_db
- **User**: test_user
- **Password**: test_password

### Test Redis
- **Host**: test-redis
- **Port**: 6379
- **Database**: 0 (no password for tests)

### Test JWT Configuration
- **Secret Key**: test-secret-key-for-testing-only-change-in-production
- **Algorithm**: HS256
- **Access Token Expiry**: 30 minutes
- **Refresh Token Expiry**: 7 days

## Writing Tests

### Unit Tests
```python
# tests/unit/test_your_service.py
import pytest
from app.services.your_service import YourService

class TestYourService:
    def test_some_functionality(self):
        service = YourService()
        result = service.some_method()
        assert result == expected_value
```

### Integration Tests
```python
# tests/integration/test_your_endpoint.py
import pytest
from fastapi.testclient import TestClient

class TestYourEndpoint:
    def test_endpoint_functionality(self, test_client: TestClient):
        response = test_client.get("/your-endpoint")
        assert response.status_code == 200
```

### Available Fixtures

- `test_client`: FastAPI TestClient with test database
- `test_db`: SQLAlchemy test database session
- `test_redis`: Redis test client
- `test_engine`: SQLAlchemy test engine

## Test Coverage

The test configuration includes:
- Coverage reporting with `pytest-cov`
- HTML coverage reports
- Terminal coverage summary
- Missing lines reporting

## CI/CD Integration

For CI/CD pipelines, use:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          docker-compose --profile test up -d test-db test-redis
          docker-compose --profile test run --rm test-runner pytest --cov=app
          docker-compose --profile test down
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure test ports (5433 for DB, 6380 for Redis) are available
2. **Container not starting**: Check Docker logs with `docker-compose --profile test logs`
3. **Database connection errors**: Wait for test-db to be healthy before running tests
4. **Redis connection errors**: Ensure test-redis is running and accessible

### Debug Commands

```bash
# Check test service status
docker-compose --profile test ps

# View test logs
docker-compose --profile test logs test-runner

# Access test database
docker-compose --profile test exec test-db psql -U test_user -d test_db

# Access test Redis
docker-compose --profile test exec test-redis redis-cli
```
