"""
Application Configuration
Loads settings from environment variables
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "VMShift Demo"
    DEBUG: bool = False
    
    # Database - PostgreSQL (Akamai Managed Database)
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/vmshift"
    
    # Redis (for Celery broker)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # API Keys (for external integrations)
    VSPHERE_HOST: str = ""
    VSPHERE_USER: str = ""
    VSPHERE_PASSWORD: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
