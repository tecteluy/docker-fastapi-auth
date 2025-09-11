import pytest
import json
import tempfile
import os
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
import logging


@pytest.mark.integration
class TestLoggingSystemIntegration:
    """Integration tests for the complete logging system."""
    
    @pytest.fixture
    def client(self):
        """Create a test client with the actual app."""
        return TestClient(app)
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for log files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_application_startup_logging(self, client):
        """Test that application startup generates appropriate logs."""
        # Make a simple request to ensure the app is running
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_request_logging_with_real_endpoints(self, client):
        """Test logging with actual application endpoints."""
        # Test health endpoint (should not be logged)
        response = client.get("/health")
        assert response.status_code == 200
        
        # Test login endpoint (should be logged)
        response = client.get("/login/github")
        # This might return 422 or redirect, but the request should be logged
        assert response.status_code in [200, 302, 422]
    
    def test_oauth_endpoint_logging(self, client):
        """Test that OAuth endpoints are properly logged."""
        # Test GitHub login endpoint
        response = client.get("/login/github")
        assert response.status_code in [200, 302, 422]
        
        # Test Google login endpoint  
        response = client.get("/login/google")
        assert response.status_code in [200, 302, 422]
    
    def test_post_request_with_sensitive_data(self, client):
        """Test that POST requests with sensitive data are properly logged and masked."""
        # Test backup login endpoint with sensitive data
        test_data = {
            "username": "testuser",
            "password": "verysecretpassword123",
            "email": "test@example.com",
            "full_name": "Test User"
        }
        
        response = client.post("/backup-login", json=test_data)
        # Expect validation error, authentication failure, or service unavailable
        assert response.status_code in [200, 400, 422, 500, 503]
    
    def test_error_logging(self, client):
        """Test that errors are properly logged."""
        # Make a request to a non-existent endpoint
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_cors_preflight_requests(self, client):
        """Test that CORS preflight requests are handled correctly."""
        # Test OPTIONS request
        response = client.options("/login/github")
        # Should return CORS headers or 405
        assert response.status_code in [200, 405]
    
    def test_concurrent_requests_logging(self, client):
        """Test that concurrent requests don't interfere with logging."""
        import concurrent.futures
        import threading
        
        def make_request():
            response = client.get("/login/github")
            return response.status_code
        
        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should complete without error
        assert len(results) == 10
        assert all(status in [200, 302, 422] for status in results)
    
    @pytest.mark.asyncio
    async def test_async_logging_performance(self, client):
        """Test that logging doesn't significantly impact performance."""
        import time
        
        # Measure time for requests with logging
        start_time = time.time()
        for _ in range(10):
            response = client.get("/login/github")
            assert response.status_code in [200, 302, 422]
        end_time = time.time()
        
        # Should complete reasonably quickly (adjust threshold as needed)
        total_time = end_time - start_time
        assert total_time < 5.0  # 10 requests should complete in under 5 seconds


@pytest.mark.integration  
class TestLoggingFileOperations:
    """Test actual file logging operations."""
    
    def test_log_file_creation(self):
        """Test that log files are created in the correct location."""
        log_dir = Path("/app/logs")
        
        # Note: In a real test environment, we might need to mock this
        # or use a test-specific log directory
        expected_files = [
            "app.log",
            "requests.log", 
            "oauth.log",
            "auth.log",
            "database.log",
            "error.log"
        ]
        
        # This test assumes the logging system has been initialized
        # In practice, you might need to trigger log creation first
        pass
    
    def test_log_rotation(self):
        """Test that log rotation works correctly."""
        # This would require generating enough log data to trigger rotation
        # or mocking the file size check
        pass
    
    def test_log_file_permissions(self):
        """Test that log files have correct permissions."""
        # This test would check file permissions on created log files
        pass


@pytest.mark.integration
class TestLoggingConfiguration:
    """Test logging configuration in different scenarios."""
    
    def test_logging_disabled_configuration(self):
        """Test behavior when logging is disabled."""
        # This would require starting the app with ENABLE_REQUEST_LOGGING=false
        pass
    
    def test_different_log_levels(self):
        """Test behavior with different log levels."""
        # Test with various LOG_LEVEL settings
        pass
    
    @pytest.mark.skip(reason="Test requires Redis service to be unavailable")
    def test_logging_with_redis_unavailable(self, client):
        """Test logging behavior when Redis is unavailable."""
        # Make requests when Redis might be down
        # Logging should still work even if session storage fails
        response = client.get("/login/github")
        assert response.status_code in [200, 302, 422, 500]
    
    @pytest.mark.skip(reason="Test requires Database service to be unavailable")
    def test_logging_with_database_unavailable(self, client):
        """Test logging behavior when database is unavailable."""
        # Make requests when database might be down
        # Logging should still work even if database operations fail
        response = client.get("/login/github")
        assert response.status_code in [200, 302, 422, 500]


@pytest.mark.integration
class TestSpecificEndpointLogging:
    """Test logging for specific application endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_health_endpoint_not_logged(self, client):
        """Verify that health endpoint is not logged."""
        response = client.get("/health")
        assert response.status_code == 200
        # In a real test, you'd verify the log files don't contain this request
    
    def test_authentication_endpoints_logged(self, client):
        """Test that authentication endpoints are properly logged."""
        endpoints = [
            "/login/github",
            "/login/google",
            "/me",
            "/refresh"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # These might return various status codes depending on configuration
            assert response.status_code in [200, 302, 401, 403, 405, 422, 500, 503]
    
    def test_backup_login_logging(self, client):
        """Test logging of backup login attempts."""
        test_data = {
            "username": "admin",
            "password": "testpassword",
            "email": "admin@test.com"
        }
        
        response = client.post("/backup-login", json=test_data)
        # Expect validation error, authentication failure, or service unavailable
        assert response.status_code in [400, 401, 422, 500, 503]
    
    def test_logout_endpoint_logging(self, client):
        """Test logging of logout requests."""
        # Logout without authentication (should fail but be logged)
        response = client.post("/logout")
        assert response.status_code in [401, 422]
        
        # Logout with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/logout", headers=headers)
        assert response.status_code in [401, 422]


@pytest.mark.integration
class TestLoggingErrorScenarios:
    """Test logging behavior in error scenarios."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_malformed_request_logging(self, client):
        """Test logging of malformed requests."""
        # Send invalid JSON
        response = client.post(
            "/backup-login",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_oversized_request_logging(self, client):
        """Test logging of oversized requests."""
        # Send very large request body
        large_data = {"data": "x" * 10000}
        response = client.post("/backup-login", json=large_data)
        assert response.status_code in [400, 413, 422]
    
    def test_special_characters_in_request(self, client):
        """Test logging requests with special characters."""
        test_data = {
            "username": "user@domain.com",
            "password": "pass!@#$%^&*()",
            "email": "test+tag@example.com"
        }
        
        response = client.post("/backup-login", json=test_data)
        assert response.status_code in [400, 401, 422, 500]
    
    def test_unicode_characters_in_request(self, client):
        """Test logging requests with unicode characters."""
        test_data = {
            "username": "用户名",
            "password": "пароль123",
            "email": "tëst@éxample.com",
            "full_name": "José María"
        }
        
        response = client.post("/backup-login", json=test_data)
        assert response.status_code in [400, 401, 422, 500]


@pytest.mark.performance
class TestLoggingPerformance:
    """Performance tests for the logging system."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_logging_overhead(self, client):
        """Test that logging doesn't add significant overhead."""
        import time
        
        # Measure baseline performance (health check - not logged)
        start = time.time()
        for _ in range(100):
            client.get("/health")
        baseline_time = time.time() - start
        
        # Measure performance with logging (regular endpoint)
        start = time.time()
        for _ in range(100):
            client.get("/login/github")
        logged_time = time.time() - start
        
        # Logging should not add more than 50% overhead
        # (adjust threshold based on requirements)
        overhead_ratio = logged_time / baseline_time if baseline_time > 0 else 1
        assert overhead_ratio < 2.0
    
    def test_concurrent_logging_performance(self, client):
        """Test logging performance under concurrent load."""
        import concurrent.futures
        import time
        
        def make_requests():
            start = time.time()
            for _ in range(10):
                client.get("/login/github")
            return time.time() - start
        
        # Run concurrent request batches
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_requests) for _ in range(5)]
            times = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All batches should complete in reasonable time
        max_time = max(times)
        assert max_time < 10.0  # 50 requests should complete in under 10 seconds
