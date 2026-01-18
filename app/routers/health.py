"""
Health Check Router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
from app.database import get_db
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "vmshift-api"}


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with dependency status"""
    health_status = {
        "status": "healthy",
        "service": "vmshift-api",
        "dependencies": {}
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["dependencies"]["database"] = {
            "status": "healthy",
            "type": "postgresql"
        }
    except Exception as e:
        health_status["dependencies"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        health_status["dependencies"]["redis"] = {
            "status": "healthy",
            "type": "redis"
        }
    except Exception as e:
        health_status["dependencies"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe"""
    try:
        db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception:
        return {"ready": False}


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"alive": True}
