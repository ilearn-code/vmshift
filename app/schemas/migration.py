"""
Pydantic Schemas for Migrations
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.migration import MigrationStatus, TargetPlatform


class MigrationBase(BaseModel):
    """Base Migration schema"""

    name: str = Field(..., description="Migration name")
    target_platform: TargetPlatform = Field(default=TargetPlatform.KUBERNETES)
    target_namespace: str = Field(default="default")


class MigrationCreate(MigrationBase):
    """Schema for creating a migration"""

    vm_id: int = Field(..., description="ID of the VM to migrate")
    base_image: Optional[str] = Field(None, description="Base container image")
    container_port: Optional[int] = Field(None, description="Container port to expose")
    replicas: int = Field(default=1, ge=1, le=10)
    registry_url: Optional[str] = Field(None, description="Container registry URL")
    image_name: Optional[str] = Field(None, description="Target image name")
    image_tag: str = Field(default="latest")


class MigrationUpdate(BaseModel):
    """Schema for updating a migration"""

    status: Optional[MigrationStatus] = None
    progress_percent: Optional[int] = Field(None, ge=0, le=100)
    status_message: Optional[str] = None
    error_message: Optional[str] = None


class MigrationResponse(MigrationBase):
    """Schema for migration responses"""

    id: int
    vm_id: int
    status: MigrationStatus
    progress_percent: int
    status_message: Optional[str]
    error_message: Optional[str]
    base_image: Optional[str]
    container_port: Optional[int]
    replicas: int
    registry_url: Optional[str]
    image_name: Optional[str]
    image_tag: str
    celery_task_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class MigrationArtifactsResponse(BaseModel):
    """Response containing generated migration artifacts"""

    migration_id: int
    dockerfile: Optional[str]
    kubernetes_manifest: Optional[str]
    docker_compose: Optional[str]


class MigrationStartRequest(BaseModel):
    """Request to start a migration"""

    migration_id: int


class MigrationStartResponse(BaseModel):
    """Response from starting a migration"""

    migration_id: int
    task_id: str
    status: str
    message: str
