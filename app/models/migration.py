"""
Migration Model - Migration workflow tracking
"""

import enum

from sqlalchemy import (JSON, Column, DateTime, Enum, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class MigrationStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    GENERATING_ARTIFACTS = "generating_artifacts"
    BUILDING_IMAGE = "building_image"
    PUSHING_IMAGE = "pushing_image"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TargetPlatform(str, enum.Enum):
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    OPENSHIFT = "openshift"
    EKS = "eks"
    AKS = "aks"


class Migration(Base):
    """Migration workflow model"""

    __tablename__ = "migrations"

    id = Column(Integer, primary_key=True, index=True)
    vm_id = Column(Integer, ForeignKey("virtual_machines.id"), nullable=False)

    # Migration configuration
    name = Column(String(255), nullable=False)
    target_platform = Column(Enum(TargetPlatform), default=TargetPlatform.KUBERNETES)
    target_namespace = Column(String(100), default="default")

    # Container configuration
    base_image = Column(
        String(255)
    )  # e.g., "mcr.microsoft.com/windows/servercore:ltsc2022"
    container_port = Column(Integer)
    replicas = Column(Integer, default=1)

    # Generated artifacts (stored as JSON)
    dockerfile_content = Column(Text)
    kubernetes_manifest = Column(Text)
    docker_compose = Column(Text)

    # Registry info
    registry_url = Column(String(255))
    image_name = Column(String(255))
    image_tag = Column(String(100), default="latest")

    # Status and progress
    status = Column(Enum(MigrationStatus), default=MigrationStatus.PENDING)
    progress_percent = Column(Integer, default=0)
    status_message = Column(String(500))
    error_message = Column(Text)

    # Celery task tracking
    celery_task_id = Column(String(100))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<Migration(name='{self.name}', status='{self.status}')>"
