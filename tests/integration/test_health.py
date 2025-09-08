# Basic health check test
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import lifespan

class TestHealthCheck:
    def test_health_endpoint(self, test_client: TestClient):
        """Test that the health endpoint returns healthy status."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_root_endpoint(self, test_client: TestClient):
        """Test that the root endpoint returns the expected message."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Atrium Authentication Service" in data["message"]

    @pytest.mark.asyncio
    @patch('app.main.Base')
    @patch('app.main.engine')
    @patch('app.main.logger')
    async def test_lifespan_startup_success(self, mock_logger, mock_engine, mock_base):
        """Test successful application startup in lifespan handler."""
        from fastapi import FastAPI
        
        # Mock the database operations
        mock_metadata = Mock()
        mock_base.metadata = mock_metadata
        
        app = FastAPI()
        
        # Test the lifespan context manager
        async with lifespan(app):
            # Verify database table creation was attempted
            mock_metadata.create_all.assert_called_once_with(bind=mock_engine)
            mock_logger.info.assert_called_once_with("Database tables created successfully")

    @pytest.mark.asyncio
    @patch('app.main.Base')
    @patch('app.main.engine')
    @patch('app.main.logger')
    async def test_lifespan_startup_database_error(self, mock_logger, mock_engine, mock_base):
        """Test database error handling in lifespan handler."""
        from fastapi import FastAPI
        
        # Mock the database operations to raise an exception
        mock_metadata = Mock()
        mock_metadata.create_all.side_effect = Exception("Database connection failed")
        mock_base.metadata = mock_metadata
        
        app = FastAPI()
        
        # Test the lifespan context manager
        async with lifespan(app):
            # Verify error was logged but startup continued
            mock_logger.warning.assert_called_once()
            assert "Could not create database tables" in mock_logger.warning.call_args[0][0]
