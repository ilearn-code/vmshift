"""
Migrations Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models.vm import VirtualMachine
from app.models.migration import Migration, MigrationStatus
from app.schemas.migration import (
    MigrationCreate, MigrationUpdate, MigrationResponse,
    MigrationArtifactsResponse, MigrationStartRequest, MigrationStartResponse
)
from app.tasks.migration_tasks import run_migration_task
from app.services.artifact_generator import ArtifactGenerator

router = APIRouter()


@router.get("/", response_model=List[MigrationResponse])
async def list_migrations(
    skip: int = 0,
    limit: int = 100,
    status_filter: MigrationStatus = None,
    db: Session = Depends(get_db)
):
    """List all migrations"""
    query = db.query(Migration)
    if status_filter:
        query = query.filter(Migration.status == status_filter)
    migrations = query.offset(skip).limit(limit).all()
    return migrations


@router.get("/{migration_id}", response_model=MigrationResponse)
async def get_migration(migration_id: int, db: Session = Depends(get_db)):
    """Get a specific migration by ID"""
    migration = db.query(Migration).filter(Migration.id == migration_id).first()
    if not migration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Migration with id {migration_id} not found"
        )
    return migration


@router.post("/", response_model=MigrationResponse, status_code=status.HTTP_201_CREATED)
async def create_migration(
    migration_data: MigrationCreate,
    db: Session = Depends(get_db)
):
    """Create a new migration configuration"""
    # Verify VM exists
    vm = db.query(VirtualMachine).filter(
        VirtualMachine.id == migration_data.vm_id
    ).first()
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Virtual machine with id {migration_data.vm_id} not found"
        )
    
    # Set default base image based on OS family
    if not migration_data.base_image:
        if vm.os_family == "windows":
            migration_data.base_image = "mcr.microsoft.com/windows/servercore:ltsc2022"
        else:
            migration_data.base_image = "ubuntu:22.04"
    
    migration = Migration(**migration_data.model_dump())
    db.add(migration)
    db.commit()
    db.refresh(migration)
    return migration


@router.put("/{migration_id}", response_model=MigrationResponse)
async def update_migration(
    migration_id: int,
    migration_update: MigrationUpdate,
    db: Session = Depends(get_db)
):
    """Update a migration"""
    migration = db.query(Migration).filter(Migration.id == migration_id).first()
    if not migration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Migration with id {migration_id} not found"
        )
    
    update_data = migration_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(migration, key, value)
    
    db.commit()
    db.refresh(migration)
    return migration


@router.delete("/{migration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_migration(migration_id: int, db: Session = Depends(get_db)):
    """Delete a migration"""
    migration = db.query(Migration).filter(Migration.id == migration_id).first()
    if not migration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Migration with id {migration_id} not found"
        )
    
    # Only allow deletion if not in progress
    if migration.status == MigrationStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a migration that is in progress"
        )
    
    db.delete(migration)
    db.commit()


@router.post("/{migration_id}/start", response_model=MigrationStartResponse)
async def start_migration(migration_id: int, db: Session = Depends(get_db)):
    """Start the migration process"""
    migration = db.query(Migration).filter(Migration.id == migration_id).first()
    if not migration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Migration with id {migration_id} not found"
        )
    
    if migration.status not in [MigrationStatus.PENDING, MigrationStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Migration is already {migration.status}"
        )
    
    # Update status and start time
    migration.status = MigrationStatus.IN_PROGRESS
    migration.started_at = datetime.utcnow()
    migration.progress_percent = 0
    migration.status_message = "Migration started"
    
    # Queue the migration task
    task = run_migration_task.delay(migration_id)
    migration.celery_task_id = task.id
    
    db.commit()
    
    return MigrationStartResponse(
        migration_id=migration_id,
        task_id=task.id,
        status="started",
        message="Migration task has been queued"
    )


@router.post("/{migration_id}/cancel")
async def cancel_migration(migration_id: int, db: Session = Depends(get_db)):
    """Cancel a running migration"""
    migration = db.query(Migration).filter(Migration.id == migration_id).first()
    if not migration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Migration with id {migration_id} not found"
        )
    
    if migration.status != MigrationStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Can only cancel migrations that are in progress"
        )
    
    migration.status = MigrationStatus.CANCELLED
    migration.status_message = "Migration cancelled by user"
    db.commit()
    
    return {"message": "Migration cancelled", "migration_id": migration_id}


@router.get("/{migration_id}/artifacts", response_model=MigrationArtifactsResponse)
async def get_migration_artifacts(migration_id: int, db: Session = Depends(get_db)):
    """Get generated artifacts for a migration"""
    migration = db.query(Migration).filter(Migration.id == migration_id).first()
    if not migration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Migration with id {migration_id} not found"
        )
    
    return MigrationArtifactsResponse(
        migration_id=migration_id,
        dockerfile=migration.dockerfile_content,
        kubernetes_manifest=migration.kubernetes_manifest,
        docker_compose=migration.docker_compose
    )


@router.post("/{migration_id}/generate-artifacts", response_model=MigrationArtifactsResponse)
async def generate_migration_artifacts(migration_id: int, db: Session = Depends(get_db)):
    """Generate container artifacts for a migration"""
    migration = db.query(Migration).filter(Migration.id == migration_id).first()
    if not migration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Migration with id {migration_id} not found"
        )
    
    # Get associated VM
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == migration.vm_id).first()
    
    # Generate artifacts
    generator = ArtifactGenerator(migration, vm)
    
    migration.dockerfile_content = generator.generate_dockerfile()
    migration.kubernetes_manifest = generator.generate_kubernetes_manifest()
    migration.docker_compose = generator.generate_docker_compose()
    
    db.commit()
    
    return MigrationArtifactsResponse(
        migration_id=migration_id,
        dockerfile=migration.dockerfile_content,
        kubernetes_manifest=migration.kubernetes_manifest,
        docker_compose=migration.docker_compose
    )
