"""Main FastAPI application for LinkML Schema Manager."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import API_TITLE, API_VERSION, API_DESCRIPTION, LOG_LEVEL, LOG_FILE
from app.database import init_db
from app.routers import schemas, codegen, validation
from app.utils.logging_middleware import LoggingMiddleware, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: Initialize database
    setup_logging(LOG_LEVEL, LOG_FILE)
    await init_db()
    yield
    # Shutdown: cleanup if needed


# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(schemas.router)
app.include_router(codegen.router)
app.include_router(validation.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "description": "FastAPI-based LinkML schema manager, validator, and toolkit",
        "endpoints": {
            "schemas": "/schemas",
            "code_generation": "/codegen",
            "validation": "/validate",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
