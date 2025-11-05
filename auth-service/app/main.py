from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from .database import engine, Base
from .routes.auth import router as auth_router
from .config import settings
from .logging_config import setup_logging
from .middleware import RequestLoggingMiddleware

# Setup logging system
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Startup: Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.warning(f"Could not create database tables: {e}")
        # Don't fail the startup if database isn't ready yet

    yield

    # Shutdown: Clean up resources if needed
    pass

app = FastAPI(
    title="FastAPI Authentication Service",
    description="OAuth 2.0 / OpenID Connect authentication service for FastAPI",
    version="1.1.2",
    lifespan=lifespan,
    root_path=settings.root_path
)

# Add request logging middleware
app.add_middleware(
    RequestLoggingMiddleware,
    enable_request_logging=settings.enable_request_logging
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        settings.website_url,
        "http://localhost:3000",  # Development
        "http://localhost:8443",  # Production port 1
        "http://localhost:9443"   # Production port 2
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "FastAPI Authentication Service"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
