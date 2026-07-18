from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)
# Import routers
from backend.app.api import auth
from backend.app.api import complaints
from backend.app.api import assignments

# Lifespan context for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 CleanLoop API Starting...")
    yield
    # Shutdown
    logger.info("🛑 CleanLoop API Shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title="CleanLoop API",
    description="Community Waste & Sanitation Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "ok", "service": "cleanloop-api"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "CleanLoop API",
        "version": "0.1.0",
        "status": "running"
    }
# Register routers
app.include_router(auth.router, prefix="/api")
app.include_router(complaints.router, prefix="/api")
app.include_router(assignments.router, prefix="/api")

# TODO: Add routes
# - /api/complaints
# - /api/assignments
# - /api/hotspots
# - /api/metrics

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
