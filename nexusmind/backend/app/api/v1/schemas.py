"""Pydantic schemas for API v1 endpoints."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ==================== Session Schemas ====================


class SessionStatus(str, Enum):
    """Session status."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class SessionResponse(BaseModel):
    """Session response model."""

    id: str
    title: str | None = None
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class SessionDetailResponse(SessionResponse):
    """Detailed session response with agent states and context."""

    agent_states: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)


class SessionCreate(BaseModel):
    """Request to create a session."""

    title: str | None = None


class SessionUpdate(BaseModel):
    """Request to update a session."""

    title: str | None = None
    status: str | None = None
    context: dict[str, Any] | None = None


class ExecutionRequest(BaseModel):
    """Request to execute a task."""

    task: str = Field(..., description="Task description")
    prompt: str | None = Field(None, description="Optional prompt override")
    agent_types: list[str] | None = Field(None, description="Specific agent types to use")


class ExecutionResponse(BaseModel):
    """Execution response model."""

    execution_id: str
    session_id: str
    status: str


class MessageResponse(BaseModel):
    """Message response model."""

    id: str
    session_id: str
    role: str
    content: str
    agent_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Request to create a message."""

    role: str = Field(..., description="Message role (user/assistant/system/tool)")
    content: str = Field(..., description="Message content")
    agent_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentStatesResponse(BaseModel):
    """Agent states response."""

    session_id: str
    agents: dict[str, Any] = Field(default_factory=dict)


# ==================== Agent Schemas ====================


class AgentTypeInfo(BaseModel):
    """Agent type information."""

    type: str
    description: str
    tools: list[str]
    model: str


class AgentCapabilitiesResponse(BaseModel):
    """Agent capabilities response."""

    type: str
    capabilities: list[str]
    tools: list[str]


# ==================== Memory Schemas ====================


class MemoryType(str, Enum):
    """Memory type."""

    CONVERSATION = "conversation"
    PLAN = "plan"
    FIX = "fix"
    OUTPUT = "output"
    CODE = "code"
    DOCUMENTATION = "documentation"
    TASK = "task"


class MemorySearchRequest(BaseModel):
    """Memory search request."""

    query: str = Field(..., description="Search query")
    session_id: str | None = None
    memory_type: MemoryType | None = None
    n_results: int = Field(5, description="Number of results")


class MemorySearchResult(BaseModel):
    """Single memory search result."""

    id: str
    content: str
    distance: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemorySearchResponse(BaseModel):
    """Memory search response."""

    results: list[MemorySearchResult]
    query: str


class MemoryStoreRequest(BaseModel):
    """Request to store memory."""

    content: str = Field(..., description="Memory content")
    memory_type: MemoryType = Field(..., description="Type of memory")
    session_id: str = Field(..., description="Session ID")
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryStoreResponse(BaseModel):
    """Memory store response."""

    id: str
    stored: bool = True


class SessionMemoryResponse(BaseModel):
    """Session memory response."""

    session_id: str
    memories: list[MemorySearchResult]


class MemoryClearResponse(BaseModel):
    """Memory clear response."""

    session_id: str
    cleared: bool = True
    deleted_counts: dict[str, int] | None = None


# ==================== Sandbox Schemas ====================


class SandboxStatus(str, Enum):
    """Sandbox status."""

    ALLOCATING = "allocating"
    ALLOCATED = "allocated"
    RUNNING = "running"
    BUSY = "busy"
    STOPPED = "stopped"
    ERROR = "error"
    TIMEOUT = "timeout"


class SandboxAllocateRequest(BaseModel):
    """Request to allocate a sandbox."""

    image: str | None = Field(None, description="Docker image to use")
    workspace: str = Field("/app/workspace", description="Workspace directory")


class SandboxResponse(BaseModel):
    """Sandbox response model."""

    id: str
    status: str
    container_id: str | None = None
    created_at: datetime | None = None


class ExecutionResultResponse(BaseModel):
    """Execution result response."""

    execution_id: str
    sandbox_id: str
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    timed_out: bool = False


class TerminalRequest(BaseModel):
    """Terminal command request."""

    command: str = Field(..., description="Command to execute")
    timeout: int = Field(300, description="Timeout in seconds")
    workdir: str = Field("/app/workspace", description="Working directory")


class FileListResponse(BaseModel):
    """File list response."""

    files: list[dict[str, Any]]


class FileReadResponse(BaseModel):
    """File read response."""

    sandbox_id: str
    path: str
    content: str


class FileWriteRequest(BaseModel):
    """File write request."""

    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content")


class FileWriteResponse(BaseModel):
    """File write response."""

    sandbox_id: str
    path: str
    written: bool = True


# ==================== Plugin Schemas ====================


class PluginType(str, Enum):
    """Plugin type."""

    TOOL = "tool"
    AGENT = "agent"
    WORKFLOW = "workflow"
    API = "api"
    INTEGRATION = "integration"


class PluginStatus(str, Enum):
    """Plugin status."""

    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class PluginResponse(BaseModel):
    """Plugin response model."""

    name: str
    version: str | None = None
    status: str
    description: str | None = None
    plugin_type: str | None = None


class PluginDetailResponse(PluginResponse):
    """Detailed plugin response."""

    manifest: dict[str, Any] | None = None
    installed_at: datetime | None = None
    error: str | None = None


class PluginInstallRequest(BaseModel):
    """Plugin install request."""

    name: str = Field(..., description="Plugin name")
    source: str = Field("marketplace", description="Source: marketplace, local, url")
    version: str | None = None


class PluginUpdateRequest(BaseModel):
    """Plugin update request."""

    enabled: bool | None = None
    settings: dict[str, Any] | None = None


# ==================== Webhook Schemas ====================


class WebhookResponse(BaseModel):
    """Webhook response model."""

    id: str
    url: str
    enabled: bool = True
    created_at: datetime | None = None


class WebhookDetailResponse(WebhookResponse):
    """Detailed webhook response."""

    source: str | None = None
    event_key_expr: str | None = None
    signature_header: str | None = None
    last_triggered: datetime | None = None
    delivery_count: int = 0


class WebhookCreateRequest(BaseModel):
    """Webhook create request."""

    url: str = Field(..., description="Webhook URL")
    source: str = Field("custom", description="Event source")
    event_key_expr: str | None = Field(None, description="JMESPath expression for event type")
    signature_header: str | None = Field(None, description="Signature header name")
    webhook_secret: str | None = Field(None, description="Webhook secret for verification")


class WebhookUpdateRequest(BaseModel):
    """Webhook update request."""

    url: str | None = None
    enabled: bool | None = None
    event_key_expr: str | None = None


class WebhookDeliveryResponse(BaseModel):
    """Webhook delivery response."""

    id: str
    webhook_id: str
    status: str
    payload: dict[str, Any] | None = None
    response_status: int | None = None
    response_body: str | None = None
    error: str | None = None
    delivered_at: datetime | None = None


class WebhookRotateSecretResponse(BaseModel):
    """Webhook secret rotation response."""

    id: str
    new_secret: str | None = None
    rotated_at: datetime
