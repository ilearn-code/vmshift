"""
Migration Tasks
"""
from celery import shared_task
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.migration import Migration, MigrationStatus
from app.models.vm import VirtualMachine, VMStatus
from app.services.artifact_generator import ArtifactGenerator
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="run_migration")
def run_migration_task(self, migration_id: int):
    """
    Execute the full migration workflow:
    1. Generate container artifacts
    2. Build container image
    3. Push to registry
    4. Deploy to target platform
    """
    logger.info(f"Starting migration {migration_id}")
    
    db = SessionLocal()
    
    try:
        migration = db.query(Migration).filter(Migration.id == migration_id).first()
        if not migration:
            raise ValueError(f"Migration with id {migration_id} not found")
        
        vm = db.query(VirtualMachine).filter(VirtualMachine.id == migration.vm_id).first()
        if not vm:
            raise ValueError(f"VM with id {migration.vm_id} not found")
        
        # Step 1: Generate Artifacts (0-25%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 5, "total": 100, "status": "Generating container artifacts..."}
        )
        migration.status = MigrationStatus.GENERATING_ARTIFACTS
        migration.progress_percent = 5
        migration.status_message = "Generating Dockerfile and manifests"
        db.commit()
        
        generator = ArtifactGenerator(migration, vm)
        migration.dockerfile_content = generator.generate_dockerfile()
        migration.kubernetes_manifest = generator.generate_kubernetes_manifest()
        migration.docker_compose = generator.generate_docker_compose()
        migration.progress_percent = 25
        db.commit()
        
        time.sleep(2)  # Simulate processing
        
        # Step 2: Build Image (25-50%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 30, "total": 100, "status": "Building container image..."}
        )
        migration.status = MigrationStatus.BUILDING_IMAGE
        migration.progress_percent = 30
        migration.status_message = "Building Docker image"
        db.commit()
        
        time.sleep(3)  # Simulate build
        migration.progress_percent = 50
        db.commit()
        
        # Step 3: Push Image (50-75%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 55, "total": 100, "status": "Pushing image to registry..."}
        )
        migration.status = MigrationStatus.PUSHING_IMAGE
        migration.progress_percent = 55
        migration.status_message = "Pushing to container registry"
        db.commit()
        
        time.sleep(2)  # Simulate push
        migration.progress_percent = 75
        db.commit()
        
        # Step 4: Deploy (75-100%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 80, "total": 100, "status": "Deploying to cluster..."}
        )
        migration.status = MigrationStatus.DEPLOYING
        migration.progress_percent = 80
        migration.status_message = f"Deploying to {migration.target_platform}"
        db.commit()
        
        time.sleep(3)  # Simulate deployment
        
        # Complete
        migration.status = MigrationStatus.COMPLETED
        migration.progress_percent = 100
        migration.status_message = "Migration completed successfully"
        migration.completed_at = datetime.utcnow()
        
        vm.status = VMStatus.COMPLETED
        db.commit()
        
        logger.info(f"Migration {migration_id} completed successfully")
        
        return {
            "status": "success",
            "migration_id": migration_id,
            "target_platform": migration.target_platform.value,
            "message": "Migration completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Migration {migration_id} failed: {str(e)}")
        
        if migration:
            migration.status = MigrationStatus.FAILED
            migration.error_message = str(e)
            migration.status_message = "Migration failed"
            db.commit()
        
        raise
    finally:
        db.close()


@celery_app.task(bind=True, name="rollback_migration")
def rollback_migration_task(self, migration_id: int):
    """
    Rollback a failed or cancelled migration
    """
    logger.info(f"Rolling back migration {migration_id}")
    
    db = SessionLocal()
    
    try:
        migration = db.query(Migration).filter(Migration.id == migration_id).first()
        if not migration:
            raise ValueError(f"Migration with id {migration_id} not found")
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 50, "total": 100, "status": "Rolling back deployment..."}
        )
        
        # Simulate rollback
        time.sleep(2)
        
        migration.status = MigrationStatus.CANCELLED
        migration.status_message = "Migration rolled back"
        db.commit()
        
        return {
            "status": "success",
            "migration_id": migration_id,
            "message": "Migration rolled back successfully"
        }
        
    except Exception as e:
        logger.error(f"Rollback failed: {str(e)}")
        raise
    finally:
        db.close()
