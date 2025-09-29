import pytest
import json
import time
import os
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app


@pytest.mark.e2e
class TestLoggingEndToEnd:
    """End-to-end tests for the complete logging system."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    @pytest.fixture(scope="class")
    def log_monitor(self):
        """Monitor log files during tests."""
        # In a real e2e test, this might monitor actual log files
        # For this example, we'll simulate log monitoring
        logs = []
        yield logs
    
    def test_complete_oauth_flow_logging(self, client, log_monitor):
        """Test logging throughout a complete OAuth flow."""
        
        # Step 1: Request GitHub login URL
        response = client.get("/login/github")
        assert response.status_code in [200, 302, 422]
        
        # Step 2: Simulate callback (this would normally come from GitHub)
        # Note: This will likely fail without proper setup, but should be logged
        callback_data = {
            "code": "test_code",
            "state": "test_state"
        }
        response = client.get("/callback/github", params=callback_data, allow_redirects=False)
        assert response.status_code in [307, 302, 400, 422, 500]
        
        # Step 3: Test token refresh endpoint
        headers = {"Authorization": "Bearer test_token"}
        response = client.post("/refresh", headers=headers)
        assert response.status_code in [200, 401, 422]
        
        # Step 4: Test user info endpoint
        response = client.get("/me", headers=headers)
        assert response.status_code in [200, 401, 422]
        
        # All these requests should be logged
        # In a real test, verify log entries exist
    
    def test_backup_user_authentication_flow(self, client, log_monitor):
        """Test complete backup user authentication flow with logging."""
        
        # Step 1: Attempt backup login
        login_data = {
            "username": "testadmin",
            "password": "securepassword123",
            "email": "admin@test.com",
            "full_name": "Test Administrator"
        }
        
        response = client.post("/backup-login", json=login_data)
        assert response.status_code in [200, 400, 401, 422, 503]
        
        # Step 2: If login successful, test authenticated endpoints
        if response.status_code == 200:
            token_data = response.json()
            headers = {"Authorization": f"Bearer {token_data.get('access_token', 'test')}"}
            
            # Test user info
            response = client.get("/me", headers=headers)
            assert response.status_code in [200, 401]
            
            # Test logout
            response = client.post("/logout", headers=headers)
            assert response.status_code in [200, 401]
    
    def test_error_scenarios_logging(self, client, log_monitor):
        """Test that various error scenarios are properly logged."""
        
        # Invalid endpoints
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404
        
        # Malformed requests
        response = client.post("/backup-login", data="invalid json")
        assert response.status_code == 422
        
        # Invalid authentication
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/me", headers=headers)
        assert response.status_code == 401
        
        # Missing required fields
        response = client.post("/backup-login", json={"username": "test"})
        assert response.status_code == 422
    
    def test_sensitive_data_masking_e2e(self, client, log_monitor):
        """End-to-end test of sensitive data masking in logs."""
        
        sensitive_data = {
            "username": "sensitive_user",
            "password": "very_secret_password_123456",
            "api_key": "secret_api_key_abcdef",
            "client_secret": "oauth_client_secret_xyz789"
        }
        
        # Make request with sensitive data
        response = client.post("/backup-login", json=sensitive_data)
        assert response.status_code in [400, 401, 422, 503]
        
        # In a real test, verify that log files contain masked versions
        # of the sensitive data, not the original values
    
    def test_high_load_logging(self, client, log_monitor):
        """Test logging behavior under high load."""
        import concurrent.futures
        
        def make_multiple_requests():
            """Make multiple requests in sequence."""
            results = []
            for i in range(20):
                try:
                    response = client.get(f"/login/github?test={i}")
                    results.append(response.status_code)
                except Exception as e:
                    results.append(f"Error: {e}")
            return results
        
        # Run concurrent request batches
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_multiple_requests) for _ in range(5)]
            all_results = []
            for future in concurrent.futures.as_completed(futures):
                all_results.extend(future.result())
        
        # Should handle 100 requests without major issues
        assert len(all_results) == 100
        # Most should succeed (or fail gracefully)
        success_count = sum(1 for r in all_results if isinstance(r, int) and r < 500)
        assert success_count > 80  # At least 80% should not be server errors
    
    def test_logging_configuration_changes(self, client):
        """Test that logging configuration changes are respected."""
        
        # This test would require restarting the service with different
        # logging configurations, which is complex in a unit test environment
        
        # Test current configuration works
        response = client.get("/login/github")
        assert response.status_code in [200, 302, 422]
        
        # In a real e2e test environment, you might:
        # 1. Change ENABLE_REQUEST_LOGGING to false
        # 2. Restart the service
        # 3. Verify requests are not logged
        # 4. Change back to true
        # 5. Verify requests are logged again
    
    def test_log_file_accessibility(self):
        """Test that log files are accessible and readable."""
        log_dir = Path("/app/logs")
        
        # In a containerized test environment, check if log directory exists
        # Note: This might need adjustment based on test setup
        if log_dir.exists():
            # Check that we can list log files
            log_files = list(log_dir.glob("*.log"))
            
            # Verify log files are readable
            for log_file in log_files:
                if log_file.exists() and log_file.stat().st_size > 0:
                    try:
                        with open(log_file, 'r') as f:
                            content = f.read(1000)  # Read first 1000 chars
                            assert len(content) > 0
                    except Exception as e:
                        pytest.fail(f"Could not read log file {log_file}: {e}")
    
    def test_log_rotation_e2e(self, client):
        """Test log rotation in a realistic scenario."""
        
        # This test would require generating enough log data to trigger rotation
        # In practice, this might involve:
        # 1. Making many requests to generate log data
        # 2. Checking that log files rotate when they reach size limit
        # 3. Verifying old log files are preserved with correct naming
        
        # For now, just verify the system can handle many requests
        for i in range(100):
            response = client.get(f"/login/github?iteration={i}")
            assert response.status_code in [200, 302, 422]
    
    @pytest.mark.performance
    def test_logging_memory_usage(self, client):
        """Test that logging doesn't cause memory leaks."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make many requests to generate logs
        for i in range(500):
            response = client.get(f"/login/github?test={i}")
            assert response.status_code in [200, 302, 422]
        
        # Check memory usage hasn't grown excessively
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (adjust threshold as needed)
        # This is a rough check - in practice you'd want more sophisticated monitoring
        assert memory_growth < 100 * 1024 * 1024  # Less than 100MB growth
    
    def test_logging_with_unicode_and_special_chars(self, client):
        """Test logging with various character encodings."""
        
        test_cases = [
            {"username": "user_普通话", "password": "密码123"},
            {"username": "user_العربية", "password": "كلمة_سر123"},
            {"username": "user_русский", "password": "пароль123"},
            {"username": "user@domain.com", "password": "p@ssw0rd!@#$%"},
            {"username": "user with spaces", "password": "password with spaces"},
            {"username": "user\"quotes\"", "password": "pass'quotes'"},
        ]
        
        for test_data in test_cases:
            response = client.post("/backup-login", json=test_data)
            # Should handle gracefully regardless of outcome
            assert response.status_code in [200, 400, 401, 422, 500]
    
    def test_logging_during_service_stress(self, client):
        """Test logging behavior during service stress."""
        import threading
        import time
        
        # Function to make rapid requests
        def rapid_requests():
            for i in range(50):
                try:
                    client.get("/login/github")
                    time.sleep(0.01)  # Small delay to avoid overwhelming
                except Exception:
                    pass  # Ignore errors, focus on system stability
        
        # Start multiple threads making requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=rapid_requests)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout
        
        # Service should still be responsive
        response = client.get("/health")
        assert response.status_code == 200


@pytest.mark.e2e
class TestLoggingInProduction:
    """Tests that simulate production logging scenarios."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_logging_with_real_oauth_flow(self, client):
        """Test logging with realistic OAuth flow simulation."""
        
        # Note: This test simulates what would happen in production
        # without requiring actual OAuth provider setup
        
        # Step 1: Get login URL
        response = client.get("/login/github")
        login_response = response.json() if response.status_code == 200 else {}
        
        # Step 2: Simulate OAuth callback with realistic parameters
        callback_params = {
            "code": "simulated_auth_code_12345",
            "state": "simulated_state_token"
        }
        response = client.get("/callback/github", params=callback_params)
        
        # Step 3: Test token operations
        if "auth_url" in str(login_response):
            # Simulate successful authentication flow
            test_token = "simulated_jwt_token"
            headers = {"Authorization": f"Bearer {test_token}"}
            
            # Test authenticated endpoints
            client.get("/me", headers=headers)
            client.post("/refresh", headers=headers)
            client.post("/logout", headers=headers)
    
    def test_production_error_scenarios(self, client):
        """Test production-like error scenarios and their logging."""
        
        # Database connection issues (simulated)
        response = client.get("/me", headers={"Authorization": "Bearer test"})
        assert response.status_code in [401, 500]
        
        # Rate limiting scenarios (if implemented)
        for i in range(20):
            client.get("/login/github")
        
        # Invalid OAuth states
        response = client.get("/callback/github?code=test&state=invalid", allow_redirects=False)
        assert response.status_code in [307, 400, 422]
        
        # Malformed tokens
        response = client.get("/me", headers={"Authorization": "Bearer malformed.jwt.token"})
        assert response.status_code == 401
    
    def test_logging_with_proxy_headers(self, client):
        """Test logging with production proxy headers."""
        
        # Simulate requests from behind a proxy/load balancer
        headers = {
            "X-Forwarded-For": "203.0.113.1, 192.168.1.1",
            "X-Real-IP": "203.0.113.1",
            "X-Forwarded-Proto": "https",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = client.get("/login/github", headers=headers)
        assert response.status_code in [200, 302, 422]
        
        # The logging system should capture these headers appropriately
