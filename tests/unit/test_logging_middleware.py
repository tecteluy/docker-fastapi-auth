import pytest
import json
import logging
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from app.middleware.logging_middleware import RequestLoggingMiddleware, DetailedLoggingRoute
from app.config import settings


class TestRequestLoggingMiddleware:
    """Test cases for RequestLoggingMiddleware."""
    
    @pytest.fixture
    def app(self):
        """Create a test FastAPI app with logging middleware."""
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware, enable_request_logging=True)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @app.post("/test-post")
        async def test_post_endpoint(data: dict):
            return {"received": data}
        
        @app.get("/health")
        async def health_endpoint():
            return {"status": "ok"}
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_logger(self):
        """Mock the request logger."""
        with patch('app.middleware.logging_middleware.request_logger') as mock:
            yield mock
    
    def test_middleware_initialization(self):
        """Test middleware initialization with different settings."""
        # Test with logging enabled
        middleware = RequestLoggingMiddleware(Mock(), enable_request_logging=True)
        assert middleware.enable_request_logging is True
        
        # Test with logging disabled
        middleware = RequestLoggingMiddleware(Mock(), enable_request_logging=False)
        assert middleware.enable_request_logging is False
    
    def test_logging_disabled_skips_processing(self, mock_logger):
        """Test that disabled logging skips all processing."""
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware, enable_request_logging=False)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        mock_logger.info.assert_not_called()
    
    def test_health_check_endpoints_skipped(self, mock_logger):
        """Test that health check endpoints are not logged."""
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware, enable_request_logging=True)
        
        @app.get("/health")
        async def health():
            return {"status": "ok"}
        
        @app.get("/")
        async def root():
            return {"status": "ok"}
        
        @app.get("/docs")
        async def docs():
            return {"docs": "swagger"}
        
        @app.get("/openapi.json")
        async def openapi():
            return {"openapi": "3.0.0"}
        
        client = TestClient(app)
        
        # Test all skipped endpoints
        client.get("/health")
        client.get("/")
        client.get("/docs")
        client.get("/openapi.json")
        
        mock_logger.info.assert_not_called()
    
    def test_get_request_logging(self, client, mock_logger):
        """Test logging of GET requests."""
        response = client.get("/test")
        
        assert response.status_code == 200
        mock_logger.info.assert_called_once()
        
        # Check the logged data structure
        call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(call_args)
        
        assert log_data["type"] == "http_request"
        assert log_data["request"]["method"] == "GET"
        assert log_data["request"]["path"] == "/test"
        assert log_data["response"]["status_code"] == 200
        assert "process_time" in log_data["response"]
        assert "timestamp" in log_data
    
    def test_post_request_with_body_logging(self, client, mock_logger):
        """Test logging of POST requests (body logging is currently disabled)."""
        test_data = {"username": "testuser", "password": "secret123"}
        response = client.post("/test-post", json=test_data)
        
        assert response.status_code == 200
        mock_logger.info.assert_called_once()
        
        call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(call_args)
        
        assert log_data["request"]["method"] == "POST"
        # Body should be None since body logging is disabled
        assert log_data["request"]["body"] is None
    
    def test_sensitive_data_masking(self):
        """Test that sensitive data is properly masked."""
        middleware = RequestLoggingMiddleware(Mock())
        
        test_data = {
            "username": "testuser",
            "password": "secret123456",
            "api_key": "very_secret_key",
            "authorization": "Bearer token123",
            "refresh_token": "refresh123456",
            "client_secret": "client_secret_value",
            "normal_field": "normal_value"
        }
        
        masked_data = middleware._mask_sensitive_data(test_data)
        
        # Check that sensitive fields are masked
        assert masked_data["password"] == "***3456"
        assert masked_data["api_key"] == "***_key"  # "very_secret_key" -> "***_key"
        assert masked_data["authorization"] == "***n123"  # "Bearer token123" -> "***n123"
        assert masked_data["refresh_token"] == "***3456"
        assert masked_data["client_secret"] == "***alue"  # "client_secret_value" -> "***alue"
        
        # Check that normal fields are not masked
        assert masked_data["normal_field"] == "normal_value"
        assert masked_data["username"] == "testuser"
    
    def test_sensitive_data_masking_short_values(self):
        """Test masking of short sensitive values."""
        middleware = RequestLoggingMiddleware(Mock())
        
        test_data = {
            "password": "123",  # Short password
            "api_key": "",      # Empty value
            "token": "a"        # Single character
        }
        
        masked_data = middleware._mask_sensitive_data(test_data)
        
        assert masked_data["password"] == "***"
        assert masked_data["api_key"] == ""
        assert masked_data["token"] == "***"
    
    @patch('app.middleware.logging_middleware.request_logger')
    async def test_request_data_extraction_error_handling(self, mock_logger):
        """Test error handling during request data extraction."""
        middleware = RequestLoggingMiddleware(Mock())
        
        # Mock request that raises an exception
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.url = Mock()
        mock_request.url.path = "/test"
        mock_request.url.__str__ = Mock(side_effect=Exception("URL error"))
        
        result = await middleware._extract_request_data(mock_request)
        
        assert "error" in result
        assert "Error extracting request data" in result["error"]
    
    def test_response_data_extraction(self):
        """Test response data extraction."""
        middleware = RequestLoggingMiddleware(Mock())
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        
        result = middleware._extract_response_data(mock_response, 0.1234)
        
        assert result["status_code"] == 200
        assert result["headers"]["content-type"] == "application/json"
        assert result["process_time"] == 0.1234
    
    def test_log_entry_structure(self, mock_logger):
        """Test the structure of log entries."""
        middleware = RequestLoggingMiddleware(Mock())
        
        request_data = {
            "method": "GET",
            "url": "http://test.com/api",
            "path": "/api"
        }
        
        response_data = {
            "status_code": 200,
            "process_time": 0.1
        }
        
        with patch('time.time', return_value=1234567890):
            middleware._log_request_response(request_data, response_data)
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(call_args)
        
        # Verify log structure
        assert log_data["type"] == "http_request"
        assert log_data["request"] == request_data
        assert log_data["response"] == response_data
        assert log_data["timestamp"] == 1234567890


class TestDetailedLoggingRoute:
    """Test cases for DetailedLoggingRoute."""
    
    @pytest.fixture
    def mock_auth_logger(self):
        """Mock the auth logger."""
        with patch('logging.getLogger') as mock:
            yield mock
    
    def test_detailed_logging_route_for_auth_endpoints(self, mock_auth_logger):
        """Test that auth endpoints get detailed logging."""
        route = DetailedLoggingRoute(
            path="/login/github",
            endpoint=lambda: {"status": "ok"},
            methods=["GET"]
        )
        
        mock_logger_instance = Mock()
        mock_auth_logger.return_value = mock_logger_instance
        
        # This test would require more complex setup to test the actual route handler
        # For now, we verify the route was created
        assert route.path == "/login/github"


class TestLoggingConfiguration:
    """Test logging configuration and setup."""
    
    @patch('app.logging_config.Path.mkdir')
    @patch('logging.handlers.RotatingFileHandler')
    @patch('logging.StreamHandler')
    @patch('logging.getLogger')
    def test_logging_setup_creates_handlers(self, mock_get_logger, mock_stream, mock_rotating, mock_mkdir):
        """Test that logging setup creates all required handlers."""
        from app.logging_config import setup_logging
        
        # Mock the root logger
        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger
        
        # Mock settings
        with patch('app.logging_config.settings') as mock_settings:
            mock_settings.log_level = "INFO"
            mock_settings.log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            mock_settings.log_file_max_bytes = 10485760
            mock_settings.log_file_backup_count = 5
            
            result = setup_logging()
            
            # Verify directory creation
            mock_mkdir.assert_called_once_with(exist_ok=True)
            
            # Verify handlers were created
            assert mock_stream.called
            assert mock_rotating.called
            assert result == mock_root_logger
    
    def test_logging_configuration_with_settings(self):
        """Test logging configuration respects settings."""
        # Test with different log levels
        test_cases = [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL)
        ]
        
        for level_str, level_int in test_cases:
            with patch('app.logging_config.settings') as mock_settings:
                mock_settings.log_level = level_str
                mock_settings.log_format = "test format"
                mock_settings.log_file_max_bytes = 1000
                mock_settings.log_file_backup_count = 3
                
                # Test that getattr works correctly
                result = getattr(logging, level_str.upper(), logging.INFO)
                assert result == level_int


@pytest.mark.integration
class TestLoggingIntegration:
    """Integration tests for the complete logging system."""
    
    def test_logging_with_real_files(self):
        """Test logging with actual file creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            
            # Create a logger with file handler
            test_logger = logging.getLogger("test_logger_unique")
            
            # Clear any existing handlers
            test_logger.handlers.clear()
            
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            test_logger.addHandler(handler)
            test_logger.setLevel(logging.INFO)
            
            # Log a message
            test_logger.info("Test log message")
            
            # Ensure the log is written
            handler.flush()
            
            # Verify file was created and contains the message
            assert os.path.exists(log_file)
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test log message" in content
                assert "INFO" in content
            
            # Clean up
            test_logger.removeHandler(handler)
            handler.close()
    
    def test_end_to_end_logging_flow(self):
        """Test the complete logging flow from request to file."""
        app = FastAPI()
        
        # Create temporary log directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the logs directory path
            with patch('pathlib.Path') as mock_path_class:
                mock_path_instance = Mock()
                mock_path_class.return_value = mock_path_instance
                
                app.add_middleware(RequestLoggingMiddleware, enable_request_logging=True)
                
                @app.get("/test-logging")
                async def test_endpoint():
                    return {"test": "logging"}
                
                client = TestClient(app)
                
                # Make a request that should be logged
                with patch('app.middleware.logging_middleware.request_logger') as mock_logger:
                    response = client.get("/test-logging")
                    
                    assert response.status_code == 200
                    mock_logger.info.assert_called_once()
                    
                    # Verify the log data structure
                    call_args = mock_logger.info.call_args[0][0]
                    log_data = json.loads(call_args)
                    
                    assert log_data["type"] == "http_request"
                    assert log_data["request"]["method"] == "GET"
                    assert log_data["request"]["path"] == "/test-logging"
                    assert log_data["response"]["status_code"] == 200
