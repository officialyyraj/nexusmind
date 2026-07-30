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


# ==================== Execution Schemas ====================


class ExecutionStateEnum(str, Enum):
    """Execution lifecycle states."""
    
    QUEUED = "queued"
    STARTING = "starting"
    PLANNING = "planning"
    RESEARCHING = "researching"
    CODING = "coding"
    REVIEWING = "reviewing"
    TESTING = "testing"
    DOCUMENTING = "documenting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    RESUMING = "resuming"


class ExecutionStepResponse(BaseModel):
    """Execution step response."""
    
    id: str
    execution_id: str
    step_order: int
    agent_type: str
    description: str
    state: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    retry_count: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None


class ExecutionLogResponse(BaseModel):
    """Execution log entry response."""
    
    id: str
    execution_id: str
    step_id: str | None = None
    level: str
    message: str
    details: dict[str, Any] | None = None
    agent_type: str | None = None
    action: str | None = None
    timestamp: datetime | None = None


class ExecutionResponse(BaseModel):
    """Execution response model."""
    
    id: str
    session_id: str
    workflow_id: str | None = None
    task: str
    state: str
    current_agent: str | None = None
    current_step_index: int = 0
    total_steps: int = 0
    progress_percent: int = 0
    retry_count: int = 0
    max_retries: int = 3
    duration_seconds: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    error_type: str | None = None
    is_cancelled: bool = False
    can_retry: bool = False
    created_at: datetime | None = None
    
    class Config:
        from_attributes = True


class ExecutionDetailResponse(ExecutionResponse):
    """Detailed execution response with all metadata."""
    
    prompt: str | None = None
    agent_types: list[str] = Field(default_factory=list)
    previous_state: str | None = None
    state_changed_at: datetime | None = None
    last_checkpoint_at: datetime | None = None
    checkpoint_data: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    error_details: dict[str, Any] | None = None
    retry_history: list[dict[str, Any]] = Field(default_factory=list)
    agent_timings: dict[str, dict[str, Any]] = Field(default_factory=dict)
    cancelled_at: datetime | None = None
    cancelled_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionListResponse(BaseModel):
    """List of executions response."""
    
    executions: list[ExecutionResponse]
    total: int
    limit: int
    offset: int


class ExecutionCreateRequest(BaseModel):
    """Request to create a new execution."""
    
    session_id: str = Field(..., description="Session ID to execute in")
    task: str = Field(..., description="Task description")
    prompt: str | None = Field(None, description="Optional prompt override")
    agent_types: list[str] | None = Field(None, description="Specific agent types to use")
    max_retries: int = Field(3, description="Maximum retry attempts per step")
    workflow_id: str | None = Field(None, description="Optional workflow identifier")


class ExecutionCancelRequest(BaseModel):
    """Request to cancel an execution."""
    
    cancelled_by: str = Field("user", description="Who initiated cancellation")


class ExecutionRetryResponse(BaseModel):
    """Response when retrying an execution."""
    
    execution_id: str
    retry_count: int
    success: bool
    message: str
