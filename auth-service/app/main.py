from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .database import engine, Base
from .routes.auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Startup: Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Warning: Could not create database tables: {e}")
        # Don't fail the startup if database isn't ready yet

    yield

    # Shutdown: Clean up resources if needed
    pass

app = FastAPI(
    title="Atrium Lens Authentication Service",
    description="OAuth 2.0 / OpenID Connect authentication service for Atrium Lens",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "Atrium Lens Authentication Service"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
