from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.complaints import router as complaints_router
from app.api.preprocessing import router as preprocessing_router
from app.config import settings
from app.db.database import Base, engine
from app.models import Complaint, ComplaintPreprocessing


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure upload directory exists and create tables if they do not exist
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic (if needed in future phases)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Nagrik Setu: AI-Powered Grievance Ingestion, Language Detection & Preprocessing API",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded static media files
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# Register routers
app.include_router(complaints_router)
app.include_router(preprocessing_router)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to Nagrik Setu API",
        "docs_url": "/docs",
        "health_check": "/api/health",
    }
