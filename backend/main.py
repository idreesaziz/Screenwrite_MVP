"""
Main FastAPI application for Screenwrite backend.

Aggregates all routers and configures CORS, middleware, and error handlers.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.analysis_router import router as analysis_router
from api.composition_router import router as composition_router
from api.stock_router import router as stock_router
from api.media_router import router as media_router
from api.upload_router import router as upload_router
from api.agent_router import router as agent_router

# Load environment variables
load_dotenv()

# Set required Vertex AI environment variables
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'True'
os.environ['GOOGLE_CLOUD_LOCATION'] = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')

# Create FastAPI app
app = FastAPI(
    title="Screenwrite API",
    description="AI-powered video composition and content generation API",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analysis_router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(composition_router, prefix="/api/v1/compositions", tags=["Composition Generation"])
app.include_router(stock_router, prefix="/api/v1/stock", tags=["Stock Media"])
app.include_router(media_router, prefix="/api/v1/media", tags=["Media Generation"])
app.include_router(upload_router, prefix="/api/v1/upload", tags=["Media Upload"])
app.include_router(agent_router, prefix="/api/v1/agent", tags=["Agent"])

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Public health check endpoint."""
    return {
        "status": "healthy",
        "service": "screenwrite-backend-v2",
        "version": "2.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Screenwrite API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run with extended timeout for long operations
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        timeout_keep_alive=600,  # 10 minutes for long operations
        timeout_graceful_shutdown=30
    )
