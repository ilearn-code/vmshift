"""
Tasks Router - Celery task management
"""
from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from app.celery_app import celery_app

router = APIRouter()


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a Celery task"""
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "ready": task_result.ready(),
        "successful": task_result.successful() if task_result.ready() else None,
    }
    
    if task_result.ready():
        if task_result.successful():
            response["result"] = task_result.result
        else:
            response["error"] = str(task_result.result)
    elif task_result.status == "PROGRESS":
        response["progress"] = task_result.info
    
    return response


@router.delete("/{task_id}")
async def revoke_task(task_id: str, terminate: bool = False):
    """Revoke/cancel a Celery task"""
    celery_app.control.revoke(task_id, terminate=terminate)
    return {
        "task_id": task_id,
        "message": f"Task {'terminated' if terminate else 'revoked'}"
    }


@router.get("/")
async def list_active_tasks():
    """List all active Celery tasks"""
    inspector = celery_app.control.inspect()
    
    active = inspector.active() or {}
    scheduled = inspector.scheduled() or {}
    reserved = inspector.reserved() or {}
    
    return {
        "active": active,
        "scheduled": scheduled,
        "reserved": reserved
    }


@router.get("/workers/status")
async def get_worker_status():
    """Get status of all Celery workers"""
    inspector = celery_app.control.inspect()
    
    stats = inspector.stats() or {}
    ping = inspector.ping() or {}
    
    return {
        "workers": list(stats.keys()),
        "stats": stats,
        "ping": ping
    }
