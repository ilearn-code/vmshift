"""
Basic tests for VMShift API
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check(self):
        """Test basic health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_liveness_probe(self):
        """Test Kubernetes liveness probe"""
        response = client.get("/live")
        assert response.status_code == 200
        assert response.json()["alive"] is True

    def test_root_endpoint(self):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "application" in data
        assert "version" in data


class TestVMEndpoints:
    """Test VM-related endpoints"""

    def test_list_vms_empty(self):
        """Test listing VMs when empty"""
        response = client.get("/api/v1/vms/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_vm(self):
        """Test creating a new VM"""
        vm_data = {
            "name": "test-vm-01",
            "uuid": "test-uuid-001",
            "os_type": "Windows Server 2019",
            "os_family": "windows",
            "cpu_count": 4,
            "memory_mb": 8192,
            "disk_gb": 100.0,
        }
        response = client.post("/api/v1/vms/", json=vm_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-vm-01"
        assert data["uuid"] == "test-uuid-001"

    def test_get_vm_not_found(self):
        """Test getting a non-existent VM"""
        response = client.get("/api/v1/vms/99999")
        assert response.status_code == 404


class TestMigrationEndpoints:
    """Test Migration-related endpoints"""

    def test_list_migrations_empty(self):
        """Test listing migrations when empty"""
        response = client.get("/api/v1/migrations/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_migration_not_found(self):
        """Test getting a non-existent migration"""
        response = client.get("/api/v1/migrations/99999")
        assert response.status_code == 404


class TestTaskEndpoints:
    """Test Task-related endpoints"""

    def test_get_task_status(self):
        """Test getting task status"""
        response = client.get("/api/v1/tasks/non-existent-task-id")
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data
