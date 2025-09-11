from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from .database import engine, Base
from .routes.auth import router as auth_router
from .config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.environment == "production" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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
    version="1.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
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
