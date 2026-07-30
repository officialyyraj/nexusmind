"""API endpoint tests."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test root endpoint returns service info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data

    def test_health_check(self, client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestSessionEndpoints:
    """Test session endpoints."""

    def test_list_sessions(self, client: TestClient) -> None:
        """Test listing sessions."""
        response = client.get("/api/v1/sessions/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_session(self, client: TestClient) -> None:
        """Test creating a session."""
        response = client.post(
            "/api/v1/sessions/",
            json={"title": "Test Session"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    def test_get_session(self, client: TestClient) -> None:
        """Test getting a session."""
        response = client.get("/api/v1/sessions/test_sess_123")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_sess_123"


class TestAgentEndpoints:
    """Test agent endpoints."""

    def test_list_agent_types(self, client: TestClient) -> None:
        """Test listing agent types."""
        response = client.get("/api/v1/agents/types")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 7
        agent_types = [a["type"] for a in data]
        assert "planner" in agent_types
        assert "coder" in agent_types
        assert "reviewer" in agent_types

    def test_get_agent_capabilities(self, client: TestClient) -> None:
        """Test getting agent capabilities."""
        response = client.get("/api/v1/agents/coder/capabilities")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "coder"
        assert "capabilities" in data
        assert "tools" in data


class TestSandboxEndpoints:
    """Test sandbox endpoints."""

    def test_allocate_sandbox(self, client: TestClient) -> None:
        """Test allocating a sandbox."""
        response = client.post("/api/v1/sandbox/allocate")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "allocated"

    def test_release_sandbox(self, client: TestClient) -> None:
        """Test releasing a sandbox."""
        response = client.delete("/api/v1/sandbox/test_sand_123")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "released"


class TestMemoryEndpoints:
    """Test memory endpoints."""

    def test_search_memory(self, client: TestClient) -> None:
        """Test searching memory."""
        response = client.post(
            "/api/v1/memory/search",
            json={"query": "test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    def test_store_memory(self, client: TestClient) -> None:
        """Test storing memory."""
        response = client.post(
            "/api/v1/memory/store",
            json={"content": "test memory", "session_id": "test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stored"] is True


class TestPluginEndpoints:
    """Test plugin endpoints."""

    def test_list_plugins(self, client: TestClient) -> None:
        """Test listing plugins."""
        response = client.get("/api/v1/plugins/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_install_plugin(self, client: TestClient) -> None:
        """Test installing a plugin."""
        response = client.post(
            "/api/v1/plugins/",
            json={"name": "test-plugin"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["installed"] is True
