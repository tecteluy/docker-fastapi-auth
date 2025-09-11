import time
import logging
import json
from typing import Callable
from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import asyncio
from ..config import settings

# Configure request/response logger
request_logger = logging.getLogger("fastapi.requests")
request_handler = logging.FileHandler("/app/logs/requests.log")
request_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
request_handler.setFormatter(request_formatter)
request_logger.addHandler(request_handler)
request_logger.setLevel(logging.INFO)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log HTTP requests and responses with configurable logging.
    """
    
    def __init__(self, app, enable_request_logging: bool = True):
        super().__init__(app)
        self.enable_request_logging = enable_request_logging
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging if disabled
        if not self.enable_request_logging:
            return await call_next(request)
            
        # Skip logging for health checks to reduce noise
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Extract request data
        request_data = await self._extract_request_data(request)
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Extract response data
        response_data = self._extract_response_data(response, process_time)
        
        # Log the request/response
        self._log_request_response(request_data, response_data)
        
        return response
    
    async def _extract_request_data(self, request: Request) -> dict:
        """Extract relevant request data for logging."""
        try:
            # Get basic request info without consuming the body
            return {
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "body": None  # Skip body reading to avoid consuming it
            }
        except Exception as e:
            return {
                "method": request.method,
                "url": str(request.url),
                "error": f"Error extracting request data: {str(e)}"
            }
    
    def _extract_response_data(self, response: Response, process_time: float) -> dict:
        """Extract relevant response data for logging."""
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "process_time": round(process_time, 4)
        }
    
    def _mask_sensitive_data(self, data: dict) -> dict:
        """Mask sensitive data in request/response bodies."""
        sensitive_fields = [
            "password", "token", "secret", "key", "authorization",
            "refresh_token", "access_token", "client_secret", "api_key"
        ]
        
        masked_data = data.copy()
        for field in sensitive_fields:
            for key in masked_data:
                if isinstance(key, str) and field.lower() in key.lower():
                    if isinstance(masked_data[key], str) and masked_data[key]:
                        masked_data[key] = f"***{masked_data[key][-4:]}" if len(masked_data[key]) > 4 else "***"
        
        return masked_data
    
    def _log_request_response(self, request_data: dict, response_data: dict):
        """Log the request and response data."""
        log_entry = {
            "type": "http_request",
            "request": request_data,
            "response": response_data,
            "timestamp": time.time()
        }
        
        # Log as JSON for structured logging
        request_logger.info(json.dumps(log_entry, default=str, indent=2))


class DetailedLoggingRoute(APIRoute):
    """
    Custom APIRoute that provides detailed logging for specific endpoints.
    """
    
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request: Request) -> Response:
            # Log detailed info for authentication endpoints
            if request.url.path.startswith(("/login", "/callback", "/refresh", "/logout", "/me", "/backup-login")):
                logger = logging.getLogger(f"fastapi.auth.{request.url.path.strip('/')}")
                logger.info(f"Processing {request.method} {request.url.path}")
            
            return await original_route_handler(request)
        
        return custom_route_handler
