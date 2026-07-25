"""Test configuration for NexusMind."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings() -> Settings:
    """Get test settings."""
    return get_settings()


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Create a mock database session."""
    from sqlalchemy.ext.asyncio import AsyncSession
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()

    # Mock query results
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    return session


@pytest.fixture
def client(mock_db_session: AsyncMock) -> TestClient:
    """Create test client with mocked dependencies."""
    # Override database dependency
    async def override_get_db():
        yield mock_db_session

    from app.auth.routes import get_db
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client

    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def mock_user_id() -> str:
    """Mock user ID for tests."""
    return "test_user_123"


@pytest.fixture
def mock_session_id() -> str:
    """Mock session ID for tests."""
    return "sess_test_123"
