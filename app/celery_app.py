"""
Celery Application Configuration
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "vmshift",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.vm_tasks",
        "app.tasks.migration_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "app.tasks.vm_tasks.*": {"queue": "discovery"},
        "app.tasks.migration_tasks.*": {"queue": "migration"},
    },
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-old-tasks": {
            "task": "app.tasks.maintenance.cleanup_old_tasks",
            "schedule": 3600.0,  # Every hour
        },
    },
)

# For Windows compatibility
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
)
