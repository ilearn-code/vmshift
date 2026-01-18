"""
VM Model - Virtual Machine representation
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, Float
from sqlalchemy.sql import func
import enum
from app.database import Base


class VMStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    ANALYZING = "analyzing"
    READY = "ready"
    MIGRATING = "migrating"
    COMPLETED = "completed"
    FAILED = "failed"


class VirtualMachine(Base):
    """Virtual Machine model for tracking discovered VMs"""
    __tablename__ = "virtual_machines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    uuid = Column(String(100), unique=True, index=True)
    
    # VM Configuration
    os_type = Column(String(100))  # e.g., "Windows Server 2019", "Ubuntu 20.04"
    os_family = Column(String(50))  # "windows" or "linux"
    cpu_count = Column(Integer)
    memory_mb = Column(Integer)
    disk_gb = Column(Float)
    
    # Network Configuration
    ip_address = Column(String(50))
    network_config = Column(JSON)  # Store network details as JSON
    
    # VMware/Hypervisor Info
    hypervisor = Column(String(50), default="vsphere")
    datacenter = Column(String(100))
    cluster = Column(String(100))
    host = Column(String(255))
    
    # Discovery metadata
    discovered_services = Column(JSON)  # List of discovered services (IIS, SQL, etc.)
    installed_software = Column(JSON)   # List of installed applications
    
    # Status tracking
    status = Column(Enum(VMStatus), default=VMStatus.DISCOVERED)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<VirtualMachine(name='{self.name}', status='{self.status}')>"
