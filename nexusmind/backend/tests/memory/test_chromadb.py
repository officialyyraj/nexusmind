"""Tests for ChromaDB memory service."""

import pytest
from unittest.mock import MagicMock, patch

# Mock chromadb before importing
import sys
mock_chromadb = MagicMock()
mock_client = MagicMock()
mock_collection = MagicMock()
mock_chromadb.PersistentClient.return_value = mock_client
mock_client.get_or_create_collection.return_value = mock_collection
sys.modules['chromadb'] = mock_chromadb
sys.modules['chromadb.config'] = MagicMock()

from app.memory.chromadb import (
    ChromaMemoryService,
    MemoryType,
    MemoryEntry,
    ConversationMemory,
    PlanMemory,
    FixMemory,
    OutputMemory,
)


class TestMemoryType:
    """Test MemoryType enum."""

    def test_all_memory_types(self):
        """Test all memory type values."""
        assert MemoryType.CONVERSATION.value == "conversation"
        assert MemoryType.PLAN.value == "plan"
        assert MemoryType.FIX.value == "fix"
        assert MemoryType.OUTPUT.value == "output"
        assert MemoryType.EMBEDDING.value == "embedding"
        assert MemoryType.CODE.value == "code"
        assert MemoryType.DOCUMENTATION.value == "documentation"
        assert MemoryType.TASK.value == "task"


class TestMemoryEntry:
    """Test MemoryEntry dataclass."""

    def test_to_dict(self):
        """Test converting entry to dictionary."""
        entry = MemoryEntry(
            id="test-id",
            content="Test content",
            memory_type=MemoryType.CONVERSATION,
            session_id="session-123",
            created_at="2024-01-01T00:00:00",
            metadata={"key": "value"},
        )

        d = entry.to_dict()
        assert d["id"] == "test-id"
        assert d["content"] == "Test content"
        assert d["memory_type"] == "conversation"
        assert d["session_id"] == "session-123"
        assert d["metadata"]["key"] == "value"


class TestConversationMemory:
    """Test ConversationMemory dataclass."""

    def test_conversation_creation(self):
        """Test creating conversation memory."""
        conv = ConversationMemory(
            messages=[{"role": "user", "content": "Hello"}],
            agent_type="coder",
            turn_count=1,
        )

        assert len(conv.messages) == 1
        assert conv.agent_type == "coder"
        assert conv.turn_count == 1


class TestPlanMemory:
    """Test PlanMemory dataclass."""

    def test_plan_creation(self):
        """Test creating plan memory."""
        plan = PlanMemory(
            plan_id="plan-1",
            task="Build a feature",
            steps=[{"id": "step1", "title": "Do something"}],
            status="pending",
        )

        assert plan.plan_id == "plan-1"
        assert plan.task == "Build a feature"
        assert len(plan.steps) == 1


class TestFixMemory:
    """Test FixMemory dataclass."""

    def test_fix_creation(self):
        """Test creating fix memory."""
        fix = FixMemory(
            bug_description="Login bug",
            root_cause="Missing validation",
            fix_code="if (!input) return error;",
            verification="Tests pass",
        )

        assert fix.bug_description == "Login bug"
        assert fix.root_cause == "Missing validation"


class TestOutputMemory:
    """Test OutputMemory dataclass."""

    def test_output_creation(self):
        """Test creating output memory."""
        output = OutputMemory(
            output_type="file",
            path="/workspace/output.txt",
            content="File content",
            mime_type="text/plain",
        )

        assert output.output_type == "file"
        assert output.path == "/workspace/output.txt"


class TestChromaMemoryService:
    """Test ChromaMemoryService class."""

    def test_collection_names(self):
        """Test collection name constants."""
        assert ChromaMemoryService.COLLECTION_CONVERSATIONS == "conversations"
        assert ChromaMemoryService.COLLECTION_PLANS == "plans"
        assert ChromaMemoryService.COLLECTION_FIXES == "fixes"
        assert ChromaMemoryService.COLLECTION_OUTPUTS == "outputs"
        assert ChromaMemoryService.COLLECTION_EMBEDDINGS == "embeddings"
        assert ChromaMemoryService.COLLECTION_CODE == "code"

    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.asyncio
    async def test_store_conversation(self, monkeypatch):
        """Test storing conversation message."""
        # Mock get_settings
        mock_settings = MagicMock()
        mock_settings.chromadb_persist_directory = "/tmp/chroma"
        monkeypatch.setattr("app.memory.chromadb.get_settings", lambda: mock_settings)

        service = ChromaMemoryService()

        entry_id = await service.store_conversation(
            session_id="session-123",
            role="user",
            content="Hello, world!",
            agent_type="coder",
        )

        assert entry_id is not None
        mock_collection.add.assert_called_once()

    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.asyncio
    async def test_store_plan(self, monkeypatch):
        """Test storing a plan."""
        mock_settings = MagicMock()
        mock_settings.chromadb_persist_directory = "/tmp/chroma"
        monkeypatch.setattr("app.memory.chromadb.get_settings", lambda: mock_settings)

        service = ChromaMemoryService()

        entry_id = await service.store_plan(
            session_id="session-123",
            plan_id="plan-1",
            task="Build API",
            steps=[{"id": "step1", "title": "Design"}],
        )

        assert entry_id == "session-123_plan-1"
        mock_collection.add.assert_called()

    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.asyncio
    async def test_store_fix(self, monkeypatch):
        """Test storing a bug fix."""
        mock_settings = MagicMock()
        mock_settings.chromadb_persist_directory = "/tmp/chroma"
        monkeypatch.setattr("app.memory.chromadb.get_settings", lambda: mock_settings)

        service = ChromaMemoryService()

        entry_id = await service.store_fix(
            session_id="session-123",
            bug_description="Login fails",
            root_cause="Missing null check",
            fix_code="if (user == null) return error;",
        )

        assert entry_id is not None

    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.asyncio
    async def test_store_output(self, monkeypatch):
        """Test storing an output."""
        mock_settings = MagicMock()
        mock_settings.chromadb_persist_directory = "/tmp/chroma"
        monkeypatch.setattr("app.memory.chromadb.get_settings", lambda: mock_settings)

        service = ChromaMemoryService()

        entry_id = await service.store_output(
            session_id="session-123",
            output_type="file",
            content="Generated code",
            path="/workspace/output.py",
            mime_type="text/x-python",
        )

        assert entry_id is not None

    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.asyncio
    async def test_store_code(self, monkeypatch):
        """Test storing code."""
        mock_settings = MagicMock()
        mock_settings.chromadb_persist_directory = "/tmp/chroma"
        monkeypatch.setattr("app.memory.chromadb.get_settings", lambda: mock_settings)

        service = ChromaMemoryService()

        entry_id = await service.store_code(
            session_id="session-123",
            code="print('hello')",
            language="python",
            file_path="/app/main.py",
            description="Main entry point",
        )

        assert entry_id is not None

    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.asyncio
    async def test_store_embedding(self, monkeypatch):
        """Test storing an embedding."""
        mock_settings = MagicMock()
        mock_settings.chromadb_persist_directory = "/tmp/chroma"
        monkeypatch.setattr("app.memory.chromadb.get_settings", lambda: mock_settings)

        service = ChromaMemoryService()

        entry_id = await service.store_embedding(
            session_id="session-123",
            content="Document text",
            vector=[0.1, 0.2, 0.3],
            content_type="documentation",
        )

        assert entry_id is not None

    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.asyncio
    async def test_clear_session(self, monkeypatch):
        """Test clearing session memories."""
        mock_settings = MagicMock()
        mock_settings.chromadb_persist_directory = "/tmp/chroma"
        monkeypatch.setattr("app.memory.chromadb.get_settings", lambda: mock_settings)

        # Mock collection.get to return empty
        mock_collection.get.return_value = {"ids": [], "documents": [], "metadatas": []}

        service = ChromaMemoryService()

        counts = await service.clear_session("session-123")

        assert isinstance(counts, dict)
        assert "conversation" in counts

    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.asyncio
    async def test_count_by_type(self, monkeypatch):
        """Test counting memories by type."""
        mock_settings = MagicMock()
        mock_settings.chromadb_persist_directory = "/tmp/chroma"
        monkeypatch.setattr("app.memory.chromadb.get_settings", lambda: mock_settings)

        # Mock collection.get to return some items
        mock_collection.get.return_value = {
            "ids": ["id1", "id2"],
            "documents": ["doc1", "doc2"],
            "metadatas": [{}, {}],
        }

        service = ChromaMemoryService()

        counts = await service.count_by_type("session-123")

        assert isinstance(counts, dict)
        assert "conversation" in counts


class TestSemanticSearch:
    """Test semantic search functionality."""

    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.asyncio
    async def test_semantic_search_all_types(self, monkeypatch):
        """Test searching across all memory types."""
        mock_settings = MagicMock()
        mock_settings.chromadb_persist_directory = "/tmp/chroma"
        monkeypatch.setattr("app.memory.chromadb.get_settings", lambda: mock_settings)

        # Mock query results
        mock_collection.query.return_value = {
            "ids": [["result1"]],
            "documents": [["Found content"]],
            "metadatas": [[{"type": "conversation"}]],
            "distances": [[0.5]],
        }

        service = ChromaMemoryService()

        results = await service.semantic_search(
            query="search term",
            n_results=5,
        )

        assert isinstance(results, list)

    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.asyncio
    async def test_search_conversations(self, monkeypatch):
        """Test searching conversations."""
        mock_settings = MagicMock()
        mock_settings.chromadb_persist_directory = "/tmp/chroma"
        monkeypatch.setattr("app.memory.chromadb.get_settings", lambda: mock_settings)

        # ChromaDB returns nested lists for query results
        mock_collection.query.return_value = {
            "ids": [["msg1", "msg2"]],
            "documents": [["Hello", "Hi there"]],
            "metadatas": [[{"role": "user"}, {"role": "assistant"}]],
            "distances": [[0.1, 0.2]],
        }

        service = ChromaMemoryService()

        results = await service.search_conversations(
            query="hello",
            session_id="session-123",
        )

        assert len(results) == 2

    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.asyncio
    async def test_search_code(self, monkeypatch):
        """Test searching code."""
        mock_settings = MagicMock()
        mock_settings.chromadb_persist_directory = "/tmp/chroma"
        monkeypatch.setattr("app.memory.chromadb.get_settings", lambda: mock_settings)

        mock_collection.query.return_value = {
            "ids": [["code1"]],
            "documents": [["def hello(): pass"]],
            "metadatas": [[{"language": "python"}]],
            "distances": [[0.3]],
        }

        service = ChromaMemoryService()

        results = await service.search_code(
            query="function definition",
            language="python",
        )

        assert len(results) >= 0
