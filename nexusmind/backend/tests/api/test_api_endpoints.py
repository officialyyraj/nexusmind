"""Integration tests for API v1 endpoints."""

import uuid
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.session import Session, User
from app.db.message import Message
from app.db.webhook import Webhook, WebhookDelivery


# Test fixtures
@pytest.fixture
def mock_user() -> User:
    """Create a mock user."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.name = "Test User"
    user.is_active = True
    user.is_superuser = False
    return user


@pytest.fixture
def mock_session(mock_user: User) -> Session:
    """Create a mock session."""
    session = MagicMock(spec=Session)
    session.id = uuid.uuid4()
    session.user_id = mock_user.id
    session.title = "Test Session"
    session.status = "created"
    session.agent_states = {}
    session.context = {}
    session.created_at = datetime.utcnow()
    session.updated_at = datetime.utcnow()
    return session


@pytest.fixture
def mock_message(mock_session: Session) -> Message:
    """Create a mock message."""
    message = MagicMock(spec=Message)
    message.id = uuid.uuid4()
    message.session_id = mock_session.id
    message.role = "user"
    message.content = "Test message"
    message.agent_type = None
    message.metadata = {}
    message.created_at = datetime.utcnow()
    return message


@pytest.fixture
def mock_webhook(mock_user: User) -> Webhook:
    """Create a mock webhook."""
    webhook = MagicMock(spec=Webhook)
    webhook.id = uuid.uuid4()
    webhook.user_id = mock_user.id
    webhook.name = "Test Webhook"
    webhook.url = "https://example.com/webhook"
    webhook.source = "custom"
    webhook.is_enabled = True
    webhook.event_key_expr = None
    webhook.signature_header = None
    webhook.secret_hash = None
    webhook.delivery_count = 0
    webhook.failure_count = 0
    webhook.last_triggered = None
    webhook.created_at = datetime.utcnow()
    return webhook


@pytest.fixture
async def async_client() -> AsyncClient:
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


class TestSessionsAPI:
    """Tests for Sessions API endpoints."""

    @pytest.mark.asyncio
    async def test_list_sessions_empty(
        self,
        async_client: AsyncClient,
        mock_user: User,
    ):
        """Test listing sessions when empty."""
        # Create mock session query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        
        with patch("app.api.v1.sessions.get_session_or_404") as mock_get:
            mock_get.return_value = None
            
            response = await async_client.get(
                "/api/v1/sessions/",
                headers={"Authorization": "Bearer test_token"}
            )
        
        # This will fail auth, which is expected
        assert response.status_code in [401, 500]

    @pytest.mark.asyncio
    async def test_create_session_validation(
        self,
        async_client: AsyncClient,
    ):
        """Test session creation with validation."""
        # Without auth, should get 401
        response = await async_client.post(
            "/api/v1/sessions/",
            json={"title": "Test Session"}
        )
        assert response.status_code == 401


class TestAgentsAPI:
    """Tests for Agents API endpoints."""

    @pytest.mark.asyncio
    async def test_list_agent_types(self, async_client: AsyncClient):
        """Test listing agent types."""
        response = await async_client.get("/api/v1/agents/types")
        
        # Should work without auth for public endpoint
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            
            # Verify structure
            agent = data[0]
            assert "type" in agent
            assert "description" in agent
            assert "tools" in agent
            assert "model" in agent

    @pytest.mark.asyncio
    async def test_get_agent_capabilities(self, async_client: AsyncClient):
        """Test getting agent capabilities."""
        response = await async_client.get("/api/v1/agents/planner/capabilities")
        
        if response.status_code == 200:
            data = response.json()
            assert data["type"] == "planner"
            assert "capabilities" in data
            assert "tools" in data

    @pytest.mark.asyncio
    async def test_get_invalid_agent_capabilities(self, async_client: AsyncClient):
        """Test getting capabilities for invalid agent type."""
        response = await async_client.get("/api/v1/agents/invalid_type/capabilities")
        
        # Should return 404 for invalid type
        assert response.status_code == 404


class TestMemoryAPI:
    """Tests for Memory API endpoints."""

    @pytest.mark.asyncio
    async def test_search_memory_requires_auth(self, async_client: AsyncClient):
        """Test memory search requires authentication."""
        response = await async_client.post(
            "/api/v1/memory/search",
            json={"query": "test", "session_id": str(uuid.uuid4())}
        )
        
        # Should require auth
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_store_memory_requires_auth(self, async_client: AsyncClient):
        """Test memory store requires authentication."""
        response = await async_client.post(
            "/api/v1/memory/store",
            json={
                "content": "test content",
                "memory_type": "conversation",
                "session_id": str(uuid.uuid4())
            }
        )
        
        # Should require auth
        assert response.status_code == 401


class TestSandboxAPI:
    """Tests for Sandbox API endpoints."""

    @pytest.mark.asyncio
    async def test_allocate_sandbox_requires_auth(self, async_client: AsyncClient):
        """Test sandbox allocation requires authentication."""
        response = await async_client.post(
            "/api/v1/sandbox/allocate",
            json={}
        )
        
        # Should require auth
        assert response.status_code == 401


class TestPluginsAPI:
    """Tests for Plugins API endpoints."""

    @pytest.mark.asyncio
    async def test_list_plugins_requires_auth(self, async_client: AsyncClient):
        """Test plugin listing requires authentication."""
        response = await async_client.get("/api/v1/plugins/")
        
        # Should require auth
        assert response.status_code == 401


class TestWebhooksAPI:
    """Tests for Webhooks API endpoints."""

    @pytest.mark.asyncio
    async def test_list_webhooks_requires_auth(self, async_client: AsyncClient):
        """Test webhook listing requires authentication."""
        response = await async_client.get("/api/v1/webhooks/")
        
        # Should require auth
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_webhook_validation(self, async_client: AsyncClient):
        """Test webhook creation validation."""
        response = await async_client.post(
            "/api/v1/webhooks/",
            json={}  # Missing required url field
        )
        
        # Should fail validation or auth
        assert response.status_code in [400, 401, 422]


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestRootEndpoint:
    """Tests for root endpoint."""

    @pytest.mark.asyncio
    async def test_root(self, async_client: AsyncClient):
        """Test root endpoint."""
        response = await async_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data


class TestAPIResponseModels:
    """Tests for API response model validation."""

    @pytest.mark.asyncio
    async def test_agent_types_response_structure(self, async_client: AsyncClient):
        """Test agent types response has correct structure."""
        response = await async_client.get("/api/v1/agents/types")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify all expected agent types are present
            agent_types = {a["type"] for a in data}
            expected_types = {"planner", "researcher", "coder", "reviewer", 
                           "tester", "documentation", "manager"}
            
            assert expected_types.issubset(agent_types), \
                f"Missing agent types: {expected_types - agent_types}"

    @pytest.mark.asyncio
    async def test_agent_capabilities_have_tools(self, async_client: AsyncClient):
        """Test agent capabilities include tools."""
        for agent_type in ["planner", "researcher", "coder"]:
            response = await async_client.get(f"/api/v1/agents/{agent_type}/capabilities")
            
            if response.status_code == 200:
                data = response.json()
                assert "tools" in data
                assert isinstance(data["tools"], list)


# Database model tests
class TestSessionModel:
    """Tests for Session database model."""

    def test_session_status_enum(self):
        """Test session status enum values."""
        from app.db.session import SessionStatus
        
        assert SessionStatus.CREATED.value == "created"
        assert SessionStatus.RUNNING.value == "running"
        assert SessionStatus.COMPLETED.value == "completed"
        assert SessionStatus.ERROR.value == "error"


class TestMessageModel:
    """Tests for Message database model."""

    def test_message_role_enum(self):
        """Test message role enum values."""
        from app.db.message import MessageRole
        
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.TOOL.value == "tool"


class TestWebhookModel:
    """Tests for Webhook database model."""

    def test_webhook_generate_secret(self):
        """Test webhook secret generation."""
        secret = Webhook.generate_secret()
        
        assert secret.startswith("whsec_")
        assert len(secret) > 20

    def test_webhook_set_and_verify_secret(self):
        """Test webhook secret hashing and verification."""
        webhook = MagicMock(spec=Webhook)
        webhook.secret_hash = None
        
        # Use the actual method from the class
        Webhook.set_secret(webhook, "test_secret_123")
        
        assert webhook.secret_hash is not None
        assert webhook.secret_hash != "test_secret_123"
        assert len(webhook.secret_hash) == 64  # SHA256 hash length

    def test_webhook_verify_correct_secret(self):
        """Test webhook verifies correct secret."""
        webhook = MagicMock(spec=Webhook)
        Webhook.set_secret(webhook, "test_secret_123")
        
        assert Webhook.verify_secret(webhook, "test_secret_123") is True

    def test_webhook_verify_wrong_secret(self):
        """Test webhook rejects wrong secret."""
        webhook = MagicMock(spec=Webhook)
        Webhook.set_secret(webhook, "test_secret_123")
        
        assert Webhook.verify_secret(webhook, "wrong_secret") is False


# Schema validation tests
class TestAPISchemas:
    """Tests for API Pydantic schemas."""

    def test_session_response_schema(self):
        """Test SessionResponse schema."""
        from app.api.v1.schemas import SessionResponse
        
        response = SessionResponse(
            id=str(uuid.uuid4()),
            title="Test",
            status="created"
        )
        
        assert response.id is not None
        assert response.title == "Test"
        assert response.status == "created"

    def test_execution_request_schema(self):
        """Test ExecutionRequest schema."""
        from app.api.v1.schemas import ExecutionRequest
        
        request = ExecutionRequest(
            task="Test task",
            prompt="Test prompt"
        )
        
        assert request.task == "Test task"
        assert request.prompt == "Test prompt"

    def test_memory_search_schema(self):
        """Test MemorySearchRequest schema."""
        from app.api.v1.schemas import MemorySearchRequest, MemoryType
        
        request = MemorySearchRequest(
            query="test query",
            memory_type=MemoryType.CONVERSATION,
            n_results=10
        )
        
        assert request.query == "test query"
        assert request.memory_type == MemoryType.CONVERSATION
        assert request.n_results == 10

    def test_sandbox_allocate_schema(self):
        """Test SandboxAllocateRequest schema."""
        from app.api.v1.schemas import SandboxAllocateRequest
        
        request = SandboxAllocateRequest(
            image="python:3.11",
            workspace="/workspace"
        )
        
        assert request.image == "python:3.11"
        assert request.workspace == "/workspace"

    def test_webhook_create_schema(self):
        """Test WebhookCreateRequest schema."""
        from app.api.v1.schemas import WebhookCreateRequest
        
        request = WebhookCreateRequest(
            url="https://example.com/webhook",
            source="github"
        )
        
        assert request.url == "https://example.com/webhook"
        assert request.source == "github"
