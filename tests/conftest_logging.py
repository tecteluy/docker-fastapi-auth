import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock
import logging


@pytest.fixture
def temp_log_directory():
    """Create a temporary directory for log files during testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_logging_settings():
    """Mock logging settings for testing."""
    settings = Mock()
    settings.enable_request_logging = True
    settings.log_level = "INFO"
    settings.log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    settings.log_file_max_bytes = 10485760
    settings.log_file_backup_count = 5
    return settings


@pytest.fixture
def isolated_logger():
    """Create an isolated logger for testing."""
    logger_name = f"test_logger_{os.getpid()}"
    logger = logging.getLogger(logger_name)
    
    # Clear any existing handlers
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    
    yield logger
    
    # Cleanup
    logger.handlers.clear()


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request for testing."""
    request = Mock()
    request.method = "GET"
    request.url = Mock()
    request.url.path = "/test"
    request.url.__str__ = Mock(return_value="http://test.com/test")
    request.query_params = {}
    request.headers = {
        "user-agent": "test-agent",
        "host": "test.com"
    }
    request.client = Mock()
    request.client.host = "127.0.0.1"
    return request


@pytest.fixture
def mock_response():
    """Create a mock FastAPI response for testing."""
    response = Mock()
    response.status_code = 200
    response.headers = {"content-type": "application/json"}
    return response


@pytest.fixture(scope="session")
def logging_test_config():
    """Configuration for logging tests."""
    return {
        "test_endpoints": [
            "/login/github",
            "/login/google",
            "/callback/github",
            "/callback/google",
            "/refresh",
            "/me",
            "/backup-login",
            "/logout"
        ],
        "skip_endpoints": [
            "/health",
            "/",
            "/docs",
            "/openapi.json"
        ],
        "sensitive_fields": [
            "password",
            "token", 
            "secret",
            "key",
            "authorization",
            "refresh_token",
            "access_token",
            "client_secret",
            "api_key"
        ],
        "test_data_sets": {
            "basic_login": {
                "username": "testuser",
                "password": "testpassword123",
                "email": "test@example.com"
            },
            "sensitive_data": {
                "username": "admin",
                "password": "super_secret_password_123456",
                "api_key": "very_secret_api_key_abcdef", 
                "client_secret": "oauth_secret_xyz789",
                "authorization": "Bearer jwt_token_12345"
            },
            "unicode_data": {
                "username": "用户_العربية_русский",
                "password": "密码_كلمة_سر_пароль123",
                "email": "tëst@éxample.com"
            }
        }
    }


# Pytest markers for logging tests
def pytest_configure(config):
    """Configure pytest markers for logging tests."""
    config.addinivalue_line(
        "markers", "logging: mark test as a logging test"
    )
    config.addinivalue_line(
        "markers", "logging_unit: mark test as a logging unit test"
    )
    config.addinivalue_line(
        "markers", "logging_integration: mark test as a logging integration test"
    )
    config.addinivalue_line(
        "markers", "logging_e2e: mark test as a logging end-to-end test"
    )
    config.addinivalue_line(
        "markers", "logging_performance: mark test as a logging performance test"
    )


# Custom assertions for logging tests
class LoggingAssertions:
    """Custom assertions for logging tests."""
    
    @staticmethod
    def assert_log_entry_structure(log_entry_json):
        """Assert that a log entry has the expected structure."""
        import json
        
        log_data = json.loads(log_entry_json)
        
        # Check required top-level fields
        assert "type" in log_data
        assert "request" in log_data
        assert "response" in log_data
        assert "timestamp" in log_data
        
        # Check request structure
        request = log_data["request"]
        assert "method" in request
        assert "url" in request
        assert "path" in request
        
        # Check response structure
        response = log_data["response"]
        assert "status_code" in response
        assert "process_time" in response
    
    @staticmethod
    def assert_sensitive_data_masked(log_entry_json, original_data):
        """Assert that sensitive data is properly masked in log entry."""
        import json
        
        log_data = json.loads(log_entry_json)
        request_body = log_data.get("request", {}).get("body", {})
        
        if not isinstance(request_body, dict):
            return  # Skip if body is not a dict
        
        sensitive_fields = ["password", "token", "secret", "key", "authorization"]
        
        for field in sensitive_fields:
            for key in request_body:
                if isinstance(key, str) and field.lower() in key.lower():
                    original_value = original_data.get(key, "")
                    logged_value = request_body.get(key, "")
                    
                    if original_value and len(original_value) > 4:
                        # Should be masked with *** prefix
                        assert logged_value.startswith("***")
                        # Should end with last 4 chars of original
                        assert logged_value.endswith(original_value[-4:])
                    elif original_value:
                        # Short values should be completely masked
                        assert logged_value == "***"
    
    @staticmethod
    def assert_no_sensitive_data_leaked(log_entry_json, sensitive_values):
        """Assert that no sensitive values appear in plain text in logs."""
        import json
        
        log_data = json.loads(log_entry_json)
        log_str = json.dumps(log_data)
        
        for sensitive_value in sensitive_values:
            if sensitive_value and len(sensitive_value) > 4:
                # The full sensitive value should not appear in logs
                assert sensitive_value not in log_str


@pytest.fixture
def logging_assertions():
    """Provide logging assertions for tests."""
    return LoggingAssertions()


# Test data generators
class TestDataGenerator:
    """Generate test data for logging tests."""
    
    @staticmethod
    def generate_request_data(method="GET", path="/test", include_body=False):
        """Generate mock request data."""
        data = {
            "method": method,
            "url": f"http://test.com{path}",
            "path": path,
            "query_params": {},
            "headers": {
                "user-agent": "test-agent",
                "host": "test.com"
            },
            "client_ip": "127.0.0.1",
            "user_agent": "test-agent"
        }
        
        if include_body and method in ["POST", "PUT", "PATCH"]:
            data["body"] = {
                "username": "testuser",
                "password": "testpassword123"
            }
        else:
            data["body"] = None
        
        return data
    
    @staticmethod
    def generate_response_data(status_code=200, process_time=0.1):
        """Generate mock response data."""
        return {
            "status_code": status_code,
            "headers": {"content-type": "application/json"},
            "process_time": process_time
        }
    
    @staticmethod
    def generate_sensitive_data():
        """Generate test data with sensitive fields."""
        return {
            "username": "admin",
            "password": "super_secret_password_123456",
            "api_key": "secret_api_key_abcdefghijklmnop",
            "client_secret": "oauth_client_secret_xyz789abc",
            "authorization": "Bearer jwt_token_very_long_12345",
            "refresh_token": "refresh_jwt_token_67890",
            "access_token": "access_jwt_token_abcdef",
            "normal_field": "this_should_not_be_masked"
        }


@pytest.fixture
def test_data_generator():
    """Provide test data generator for tests."""
    return TestDataGenerator()
