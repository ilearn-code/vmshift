"""
Pydantic Schemas for Virtual Machines
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.vm import VMStatus


class VMBase(BaseModel):
    """Base VM schema"""
    name: str = Field(..., description="VM name")
    os_type: Optional[str] = Field(None, description="Operating system type")
    os_family: Optional[str] = Field(None, description="OS family: windows or linux")
    cpu_count: Optional[int] = Field(None, ge=1, description="Number of CPUs")
    memory_mb: Optional[int] = Field(None, ge=512, description="Memory in MB")
    disk_gb: Optional[float] = Field(None, ge=1, description="Disk size in GB")
    ip_address: Optional[str] = Field(None, description="IP address")


class VMCreate(VMBase):
    """Schema for creating a VM"""
    uuid: str = Field(..., description="Unique VM identifier")
    datacenter: Optional[str] = None
    cluster: Optional[str] = None
    host: Optional[str] = None
    network_config: Optional[Dict[str, Any]] = None
    discovered_services: Optional[List[str]] = None
    installed_software: Optional[List[str]] = None


class VMUpdate(BaseModel):
    """Schema for updating a VM"""
    name: Optional[str] = None
    status: Optional[VMStatus] = None
    discovered_services: Optional[List[str]] = None
    installed_software: Optional[List[str]] = None


class VMResponse(VMBase):
    """Schema for VM responses"""
    id: int
    uuid: str
    status: VMStatus
    hypervisor: str
    datacenter: Optional[str]
    cluster: Optional[str]
    host: Optional[str]
    network_config: Optional[Dict[str, Any]]
    discovered_services: Optional[List[str]]
    installed_software: Optional[List[str]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class VMDiscoveryRequest(BaseModel):
    """Request to discover VMs from hypervisor"""
    hypervisor_type: str = Field(default="vsphere", description="Hypervisor type")
    host: str = Field(..., description="Hypervisor host address")
    username: str = Field(..., description="Username for authentication")
    password: str = Field(..., description="Password for authentication")
    datacenter: Optional[str] = Field(None, description="Specific datacenter to scan")


class VMDiscoveryResponse(BaseModel):
    """Response from VM discovery task"""
    task_id: str
    status: str
    message: str
