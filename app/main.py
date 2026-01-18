"""
VMShift Demo - FastAPI Application
Demonstrates VM discovery, migration workflows, and containerization logic
"""

import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app.models import migration, vm
from app.routers import health, migrations, tasks, vms

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting VMShift Demo Application...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    yield
    # Shutdown
    logger.info("Shutting down VMShift Demo Application...")


app = FastAPI(
    title="VMShift Demo API",
    description="""
    A demonstration API for VM-to-Container migration workflows.
    
    ## Features
    * **VM Discovery** - Discover and catalog virtual machines
    * **Migration Workflows** - Orchestrate VM containerization
    * **Task Queue** - Background job processing with Celery
    * **Container Generation** - Generate Dockerfiles and manifests
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(vms.router, prefix="/api/v1/vms", tags=["Virtual Machines"])
app.include_router(migrations.router, prefix="/api/v1/migrations", tags=["Migrations"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "application": "VMShift Demo API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
