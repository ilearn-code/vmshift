"""
Virtual Machines Router
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.vm import VirtualMachine, VMStatus
from app.schemas.vm import (VMCreate, VMDiscoveryRequest, VMDiscoveryResponse,
                            VMResponse, VMUpdate)
from app.tasks.vm_tasks import discover_vms_task

router = APIRouter()


@router.get("/", response_model=List[VMResponse])
async def list_virtual_machines(
    skip: int = 0,
    limit: int = 100,
    status_filter: VMStatus = None,
    db: Session = Depends(get_db),
):
    """List all discovered virtual machines"""
    query = db.query(VirtualMachine)
    if status_filter:
        query = query.filter(VirtualMachine.status == status_filter)
    vms = query.offset(skip).limit(limit).all()
    return vms


@router.get("/{vm_id}", response_model=VMResponse)
async def get_virtual_machine(vm_id: int, db: Session = Depends(get_db)):
    """Get a specific virtual machine by ID"""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Virtual machine with id {vm_id} not found",
        )
    return vm


@router.post("/", response_model=VMResponse, status_code=status.HTTP_201_CREATED)
async def create_virtual_machine(vm_data: VMCreate, db: Session = Depends(get_db)):
    """Create/register a new virtual machine"""
    # Check if VM with this UUID already exists
    existing_vm = (
        db.query(VirtualMachine).filter(VirtualMachine.uuid == vm_data.uuid).first()
    )
    if existing_vm:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Virtual machine with UUID {vm_data.uuid} already exists",
        )

    vm = VirtualMachine(**vm_data.model_dump())
    db.add(vm)
    db.commit()
    db.refresh(vm)
    return vm


@router.put("/{vm_id}", response_model=VMResponse)
async def update_virtual_machine(
    vm_id: int, vm_update: VMUpdate, db: Session = Depends(get_db)
):
    """Update a virtual machine"""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Virtual machine with id {vm_id} not found",
        )

    update_data = vm_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(vm, key, value)

    db.commit()
    db.refresh(vm)
    return vm


@router.delete("/{vm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_virtual_machine(vm_id: int, db: Session = Depends(get_db)):
    """Delete a virtual machine"""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Virtual machine with id {vm_id} not found",
        )

    db.delete(vm)
    db.commit()


@router.post("/discover", response_model=VMDiscoveryResponse)
async def discover_virtual_machines(request: VMDiscoveryRequest):
    """Start VM discovery task from hypervisor"""
    # Queue the discovery task with Celery
    task = discover_vms_task.delay(
        hypervisor_type=request.hypervisor_type,
        host=request.host,
        username=request.username,
        password=request.password,
        datacenter=request.datacenter,
    )

    return VMDiscoveryResponse(
        task_id=task.id, status="queued", message="VM discovery task has been queued"
    )


@router.post("/{vm_id}/analyze", response_model=VMDiscoveryResponse)
async def analyze_virtual_machine(vm_id: int, db: Session = Depends(get_db)):
    """Analyze a VM for installed services and software"""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Virtual machine with id {vm_id} not found",
        )

    # Update status to analyzing
    vm.status = VMStatus.ANALYZING
    db.commit()

    # This would queue an analysis task
    # For demo, we'll return a mock response
    return VMDiscoveryResponse(
        task_id="demo-analysis-task",
        status="queued",
        message=f"Analysis task queued for VM {vm.name}",
    )
