# NexusMind - Autonomous Multi-Agent AI Platform

## Executive Summary

NexusMind is an open-source autonomous AI platform inspired by Manus, Devin, and OpenHands. It orchestrates a team of specialized AI agents that collaborate to complete complex software engineering tasks—from research and planning to coding, testing, and documentation.

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [System Architecture](#system-architecture)
3. [Folder Structure](#folder-structure)
4. [Database Schema](#database-schema)
5. [Agent System](#agent-system)
6. [Agent Communication](#agent-communication)
7. [Message Format](#message-format)
8. [API Specification](#api-specification)
9. [LangGraph Orchestration](#langgraph-orchestration)
10. [Sandbox Execution](#sandbox-execution)
11. [Memory System](#memory-system)
12. [Plugin Architecture](#plugin-architecture)
13. [MCP Support](#mcp-support)
14. [Frontend Architecture](#frontend-architecture)
15. [Streaming Infrastructure](#streaming-infrastructure)
16. [Tech Stack Summary](#tech-stack-summary)
17. [Development Roadmap](#development-roadmap)

---

## Design Principles

### 1. **Modularity & Extensibility**
- Every component is independently deployable and replaceable
- Agents can be added, removed, or upgraded without system-wide changes
- Plugin architecture allows third-party extensions

### 2. **Resilience & Fault Tolerance**
- Each agent operates in isolation with its own context
- Sandbox isolation prevents cascading failures
- Automatic retry mechanisms with exponential backoff

### 3. **Transparency & Observability**
- All agent actions are logged and streamable
- Full audit trail of decisions and reasoning
- Real-time visibility into agent collaboration

### 4. **Security First**
- Sandboxed execution environment for all code
- No arbitrary system access from agents
- Strict permission scoping for tools and resources

### 5. **Developer Ergonomics**
- Local-first development with Docker Compose
- Hot-reload for rapid iteration
- Comprehensive API documentation

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐ │
│  │   Next.js Web   │    │   CLI Client    │    │   VS Code Extension     │ │
│  │   (Port 3000)   │    │   (Terminal)    │    │   (IDE Integration)     │ │
│  └────────┬────────┘    └────────┬────────┘    └───────────┬─────────────┘ │
└───────────┼──────────────────────┼──────────────────────────┼───────────────┘
            │                      │                          │
            ▼                      ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             API GATEWAY                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    FastAPI (Port 8000)                                 ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  ││
│  │  │ REST API     │  │ WebSocket    │  │ SSE          │  │ MCP Server │  ││
│  │  │ /api/v1      │  │ /ws          │  │ /sse         │  │ /mcp/v1    │  ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATION LAYER                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    LangGraph State Machine                              ││
│  │  ┌─────────────────────────────────────────────────────────────────┐    ││
│  │  │                    Supervisor Agent                              │    ││
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────┐ │    ││
│  │  │  │ Planner │  │Research │  │ Coder   │  │Reviewer │  │Tester │ │    ││
│  │  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └───┬───┘ │    ││
│  │  │       │            │            │            │            │     │    ││
│  │  │  ┌────┴────────────┴────────────┴────────────┴────────────┴─┐   │    ││
│  │  │  │              Message Bus (In-Memory/Redis)                 │   │    ││
│  │  │  └────────────────────────────────────────────────────────────┘   │    ││
│  │  └─────────────────────────────────────────────────────────────────┘    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENT EXECUTION                                   │
│  ┌───────────────────────┐    ┌───────────────────────┐                   │
│  │   Docker Sandbox      │    │   Docker Sandbox      │                   │
│  │   ┌─────────────────┐ │    │   ┌─────────────────┐ │                   │
│  │   │ Agent Worker 1  │ │    │   │ Agent Worker N  │ │                   │
│  │   │ - Terminal      │ │    │   │ - Terminal      │ │                   │
│  │   │ - File System   │ │    │   │ - File System   │ │                   │
│  │   │ - Browser       │ │    │   │ - Browser       │ │                   │
│  │   │ - Git           │ │    │   │ - Git           │ │                   │
│  │   └─────────────────┘ │    │   └─────────────────┘ │                   │
│  └───────────────────────┘    └───────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  PostgreSQL  │  │   ChromaDB    │  │    Redis     │  │  File Storage  │  │
│  │  (Sessions)  │  │   (Memory)   │  │  (Cache/Q)   │  │  (Artifacts)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Folder Structure

```
nexusmind/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application entry
│   │   ├── config.py                  # Configuration management
│   │   ├── dependencies.py           # Dependency injection
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py          # API router aggregator
│   │   │   │   ├── sessions.py        # Session endpoints
│   │   │   │   ├── agents.py          # Agent control endpoints
│   │   │   │   ├── sandbox.py         # Sandbox management
│   │   │   │   ├── plugins.py         # Plugin management
│   │   │   │   ├── memory.py          # Memory/retrieval endpoints
│   │   │   │   └── webhooks.py        # Webhook endpoints
│   │   │   └── ws.py                  # WebSocket handlers
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # Base agent class
│   │   │   ├── registry.py           # Agent registry
│   │   │   ├── supervisor.py         # Supervisor/coordinator
│   │   │   ├── types/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── planner.py
│   │   │   │   ├── researcher.py
│   │   │   │   ├── coder.py
│   │   │   │   ├── reviewer.py
│   │   │   │   ├── tester.py
│   │   │   │   ├── documentation.py
│   │   │   │   └── manager.py
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       ├── terminal.py
│   │   │       ├── browser.py
│   │   │       ├── file_editor.py
│   │   │       ├── search.py
│   │   │       └── github.py
│   │   │
│   │   ├── orchestration/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py              # LangGraph definition
│   │   │   ├── state.py              # State schema
│   │   │   ├── nodes.py              # Graph nodes
│   │   │   ├── edges.py              # Conditional edges
│   │   │   └── executor.py           # Graph executor
│   │   │
│   │   ├── sandbox/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py            # Sandbox lifecycle
│   │   │   ├── docker.py             # Docker operations
│   │   │   ├── executor.py           # Code execution
│   │   │   ├── terminal.py          # PTY/shell interface
│   │   │   └── browser.py           # Browser automation
│   │   │
│   │   ├── memory/
│   │   │   ├── __init__.py
│   │   │   ├── chromadb.py           # ChromaDB integration
│   │   │   ├── vector_store.py       # Vector operations
│   │   │   ├── semantic_cache.py     # Semantic caching
│   │   │   └── session_memory.py     # Session context
│   │   │
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── factory.py            # LLM provider factory
│   │   │   ├── ollama.py             # Ollama adapter
│   │   │   ├── openai.py             # OpenAI-compatible adapter
│   │   │   └── base.py               # Base LLM interface
│   │   │
│   │   ├── mcp/
│   │   │   ├── __init__.py
│   │   │   ├── server.py             # MCP server implementation
│   │   │   ├── protocol.py           # MCP protocol handlers
│   │   │   └── tools.py              # MCP tool adapters
│   │   │
│   │   ├── plugins/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py            # Plugin lifecycle
│   │   │   ├── loader.py             # Plugin discovery/loading
│   │   │   ├── registry.py           # Plugin registry
│   │   │   └── templates/
│   │   │       ├── __init__.py
│   │   │       └── example.py
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py           # Database connection
│   │   │   ├── session.py            # Session models
│   │   │   ├── message.py            # Message models
│   │   │   ├── artifact.py          # Artifact models
│   │   │   └── migrations/           # Alembic migrations
│   │   │
│   │   ├── streaming/
│   │   │   ├── __init__.py
│   │   │   ├── ws_manager.py         # WebSocket connection manager
│   │   │   ├── sse.py                # SSE handler
│   │   │   └── events.py            # Event definitions
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── rate_limiter.py
│   │       ├── logger.py
│   │       └── security.py
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── api/
│   │   ├── agents/
│   │   ├── orchestration/
│   │   └── integration/
│   │
│   ├── alembic/
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── pyproject.toml
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx              # Home/dashboard
│   │   │   ├── sessions/
│   │   │   │   ├── page.tsx          # Session list
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx      # Session detail
│   │   │   │       └── layout.tsx
│   │   │   ├── settings/
│   │   │   │   └── page.tsx
│   │   │   └── api/
│   │   │       └── [...trpc]/
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                    # Shadcn/ui components
│   │   │   ├── chat/
│   │   │   │   ├── ChatWindow.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── MessageInput.tsx
│   │   │   │   └── AgentAvatars.tsx
│   │   │   ├── session/
│   │   │   │   ├── SessionList.tsx
│   │   │   │   ├── SessionCard.tsx
│   │   │   │   └── SessionHeader.tsx
│   │   │   ├── terminal/
│   │   │   │   ├── Terminal.tsx
│   │   │   │   └── TerminalOutput.tsx
│   │   │   ├── streaming/
│   │   │   │   ├── StreamViewer.tsx
│   │   │   │   └── LogPanel.tsx
│   │   │   ├── agents/
│   │   │   │   ├── AgentStatus.tsx
│   │   │   │   ├── AgentTimeline.tsx
│   │   │   │   └── AgentCard.tsx
│   │   │   └── plugins/
│   │   │       ├── PluginCard.tsx
│   │   │       └── PluginMarketplace.tsx
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts                 # API client
│   │   │   ├── websocket.ts           # WebSocket client
│   │   │   ├── streaming.ts          # SSE client
│   │   │   └── utils.ts
│   │   │
│   │   ├── hooks/
│   │   │   ├── useSession.ts
│   │   │   ├── useStreaming.ts
│   │   │   ├── useAgents.ts
│   │   │   └── useWebSocket.ts
│   │   │
│   │   ├── stores/
│   │   │   ├── sessionStore.ts        # Zustand store
│   │   │   ├── agentStore.ts
│   │   │   └── uiStore.ts
│   │   │
│   │   ├── types/
│   │   │   ├── api.ts
│   │   │   ├── agent.ts
│   │   │   └── message.ts
│   │   │
│   │   └── styles/
│   │       └── globals.css
│   │
│   ├── public/
│   ├── next.config.js
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── Dockerfile
│
├── sandbox/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── packages/
│   │   ├── browser/
│   │   │   ├── playwright/
│   │   │   └── puppeteer/
│   │   ├── terminal/
│   │   │   ├── bash/
│   │   │   └── zsh/
│   │   └── tools/
│   │       ├── git/
│   │       ├── npm/
│   │       └── docker-cli/
│   └── config/
│       └── playwright.config.js
│
├── docs/
│   ├── architecture/
│   ├── api/
│   └── plugins/
│
├── scripts/
│   ├── dev.sh
│   ├── build.sh
│   └── deploy.sh
│
├── .github/
│   └── workflows/
│
├── docker-compose.yml
├── README.md
└── SPEC.md
```

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     User        │     │    Session      │     │    Message     │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │────<│ id (PK)         │────<│ id (PK)         │
│ email           │     │ user_id (FK)    │     │ session_id (FK)│
│ name            │     │ title           │     │ role           │
│ api_key         │     │ status          │     │ content        │
│ created_at      │     │ created_at      │     │ agent_type     │
│ updated_at      │     │ updated_at      │     │ metadata       │
└─────────────────┘     │ archived_at     │     │ created_at     │
        │               └─────────────────┘     └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   ApiKey        │     │    Artifact     │     │  MessageEmbed  │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │     │ id (PK)         │     │ id (PK)         │
│ user_id (FK)    │     │ session_id (FK) │     │ message_id (FK)│
│ key_hash        │     │ type           │     │ embedding_id   │
│ name            │     │ name           │     │ vector         │
│ created_at      │     │ path           │     │ created_at     │
│ last_used_at    │     │ size           │     └─────────────────┘
│ expires_at      │     │ created_at     │
└─────────────────┘     └─────────────────┘
        │
        │
        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Plugin       │     │   PluginConfig  │     │  AgentLog      │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │     │ id (PK)         │     │ id (PK)         │
│ name            │     │ plugin_id (FK)  │     │ session_id (FK)│
│ version         │     │ key            │     │ agent_type     │
│ source          │     │ value          │     │ action         │
│ enabled         │     └─────────────────┘     │ details        │
│ config_schema   │                             │ created_at     │
│ created_at      │                             └─────────────────┘
└─────────────────┘
```

### SQL Schema (PostgreSQL)

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    password_hash VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API Keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(500),
    status VARCHAR(50) NOT NULL DEFAULT 'created',
    agent_states JSONB DEFAULT '{}',
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    archived_at TIMESTAMP WITH TIME ZONE
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    agent_type VARCHAR(50),
    parent_id UUID REFERENCES messages(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for message retrieval
CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_messages_created ON messages(created_at);

-- Artifacts table (files created by agents)
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id),
    type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    path TEXT NOT NULL,
    mime_type VARCHAR(100),
    size_bytes BIGINT,
    checksum VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent logs table
CREATE TABLE agent_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    agent_type VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_agent_logs_session ON agent_logs(session_id);
CREATE INDEX idx_agent_logs_created ON agent_logs(created_at);

-- Plugins table
CREATE TABLE plugins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    version VARCHAR(50) NOT NULL,
    source VARCHAR(500),
    description TEXT,
    enabled BOOLEAN DEFAULT true,
    config_schema JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Plugin configurations
CREATE TABLE plugin_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id UUID NOT NULL REFERENCES plugins(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    UNIQUE(plugin_id, key)
);

-- LLM Provider configurations
CREATE TABLE llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    provider_type VARCHAR(50) NOT NULL,
    base_url TEXT,
    api_key_encrypted TEXT,
    model VARCHAR(100) NOT NULL,
    is_default BOOLEAN DEFAULT false,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Agent System

### Agent Overview

| Agent | Role | Primary Tools | Triggers |
|-------|------|---------------|----------|
| **Planner** | Decomposes tasks, creates roadmaps | File reader, search | Always runs first |
| **Researcher** | Gathers context, documentation | Web search, GitHub, file reader | On research requests |
| **Coder** | Writes/modifies code | File editor, terminal, git | On implementation tasks |
| **Reviewer** | Analyzes code quality | File reader, terminal | After coder完成任务 |
| **Tester** | Validates functionality | Terminal, browser | After code changes |
| **Documentation** | Generates docs | File editor, search | On documentation requests |
| **Manager** | Coordinates agents, routes tasks | All agent tools | Central orchestrator |

### Agent State Machine

```
┌─────────────┐
│   IDLE      │◄─────────────────────────────┐
└──────┬──────┘                              │
       │ assign_task()                       │
       ▼                                      │
┌─────────────┐     ┌─────────────┐          │
│  RECEIVING  │────>│  PLANNING    │─────────┤
└─────────────┘     └──────┬──────┘          │
                           │                  │
       ┌───────────────────┼──────────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│  EXECUTING  │────>│   WAITING   │
└──────┬──────┘     └──────┬──────┘
       │                    │
       │      ┌─────────────┼─────────────┐
       │      │             │             │
       ▼      ▼             ▼             ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  COMPLETED  │  │   ERROR     │  │   TIMEOUT   │  │  CANCELLED  │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

### Agent Base Class

```python
class Agent(ABC):
    """Base class for all agents"""
    
    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        llm: LLMClient,
        tools: list[Tool],
        memory: AgentMemory,
        sandbox: SandboxManager
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.sandbox = sandbox
        self.state = AgentState.IDLE
        self.conversation_history: list[Message] = []
    
    @abstractmethod
    async def process_message(self, message: Message) -> Message:
        """Process incoming message and return response"""
        pass
    
    @abstractmethod
    async def plan(self, task: Task) -> list[SubTask]:
        """Create execution plan for task"""
        pass
    
    async def execute(self, subtask: SubTask) -> ExecutionResult:
        """Execute a single subtask"""
        pass
    
    async def reflect(self, result: ExecutionResult) -> Reflection:
        """Self-reflect on execution result"""
        pass
```

---

## Agent Communication

### Message Bus Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Message Bus                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Redis Pub/Sub                          │  │
│  │  Channel: session:{session_id}:messages                   │  │
│  │  Channel: agent:{agent_id}:tasks                          │  │
│  │  Channel: system:events                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Planner Agent  │  │  Coder Agent    │  │ Reviewer Agent │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Supervisor Agent  │
                    │   (Orchestrator)    │
                    └─────────────────────┘
```

### Communication Patterns

#### 1. **Direct Messaging** (Agent to Agent)
```python
# Agent sends task to specific agent
message = Message(
    to_agent="coder",
    content=TaskSpecification(...),
    priority=Priority.HIGH
)
await message_bus.send(message)
```

#### 2. **Broadcast** (Supervisor to All)
```python
# Supervisor broadcasts session state update
broadcast = Broadcast(
    event=SessionEvent.STATE_CHANGED,
    payload=SessionState(...),
    recipients=AgentType.all()
)
await message_bus.broadcast(broadcast)
```

#### 3. **Request/Response** (Sync Communication)
```python
# Researcher responds to Planner's research request
response = await message_bus.request(
    to_agent="researcher",
    message=ResearchRequest(query="..."),
    timeout=30
)
```

---

## Message Format

### Core Message Schema

```python
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from enum import Enum

class AgentType(str, Enum):
    MANAGER = "manager"
    PLANNER = "planner"
    RESEARCHER = "researcher"
    CODER = "coder"
    REVIEWER = "reviewer"
    TESTER = "tester"
    DOCUMENTATION = "documentation"

class MessageType(str, Enum):
    TASK = "task"
    RESPONSE = "response"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    EVENT = "event"
    BROADCAST = "broadcast"

class Priority(int, Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 10
    URGENT = 20

class Message(BaseModel):
    """Core message format for agent communication"""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: MessageType
    session_id: str
    from_agent: Optional[str] = None
    to_agent: Optional[str] = None  # None for broadcasts
    content: Any
    metadata: dict[str, Any] = Field(default_factory=dict)
    priority: Priority = Priority.NORMAL
    reply_to: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # Embeddings for semantic retrieval
    embedding: Optional[list[float]] = None

class TaskMessage(Message):
    """Task-specific message with execution context"""
    
    def __init__(self, **data):
        data["type"] = MessageType.TASK
        super().__init__(**data)
    
    content: TaskSpecification

class TaskSpecification(BaseModel):
    """Task description and requirements"""
    
    task_id: str
    description: str
    goals: list[str]
    constraints: list[str]
    tools_allowed: list[str]
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    dependencies: list[str] = []  # Task IDs this depends on
    context: dict[str, Any] = Field(default_factory=dict)

class ResponseMessage(Message):
    """Response message with execution results"""
    
    def __init__(self, **data):
        data["type"] = MessageType.RESPONSE
        super().__init__(**data)
    
    content: ExecutionResult
    success: bool
    error: Optional[str] = None

class ExecutionResult(BaseModel):
    """Result of task execution"""
    
    task_id: str
    status: str  # "success", "partial", "failed"
    output: Any
    artifacts: list[Artifact] = []
    logs: list[LogEntry] = []
    metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)
    next_steps: list[str] = []

class ExecutionMetrics(BaseModel):
    """Execution performance metrics"""
    
    duration_seconds: float
    tokens_used: int = 0
    api_calls: int = 0
    tools_used: list[str] = []
    errors: list[str] = []
```

### Event Message Schema

```python
class EventType(str, Enum):
    # Session events
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    SESSION_ERROR = "session_error"
    
    # Agent events
    AGENT_ACTIVATED = "agent_activated"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    
    # Streaming events
    LOG_ENTRY = "log_entry"
    STREAM_CHUNK = "stream_chunk"
    PROGRESS_UPDATE = "progress_update"
    
    # Artifact events
    ARTIFACT_CREATED = "artifact_created"
    FILE_MODIFIED = "file_modified"

class EventMessage(Message):
    """Event notification message"""
    
    def __init__(self, **data):
        data["type"] = MessageType.EVENT
        super().__init__(**data)
    
    content: Event

class Event(BaseModel):
    """Event payload"""
    
    event_type: EventType
    source: str  # agent_id or system
    data: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class LogEntry(BaseModel):
    """Agent log entry"""
    
    level: str  # DEBUG, INFO, WARN, ERROR
    message: str
    source: str
    timestamp: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
```

---

## API Specification

### REST API Endpoints

#### Sessions

```
POST   /api/v1/sessions                    # Create session
GET    /api/v1/sessions                    # List sessions
GET    /api/v1/sessions/{id}               # Get session
PATCH  /api/v1/sessions/{id}               # Update session
DELETE /api/v1/sessions/{id}               # Delete session
POST   /api/v1/sessions/{id}/archive       # Archive session
POST   /api/v1/sessions/{id}/execute       # Execute task
POST   /api/v1/sessions/{id}/stop          # Stop execution
```

#### Messages

```
GET    /api/v1/sessions/{id}/messages      # List messages
POST   /api/v1/sessions/{id}/messages       # Send message
GET    /api/v1/messages/{id}                # Get message
```

#### Agents

```
GET    /api/v1/sessions/{id}/agents        # Get agent states
GET    /api/v1/agents/types                # List agent types
GET    /api/v1/agents/{type}/capabilities  # Get agent capabilities
```

#### Streaming

```
WS     /api/v1/ws/sessions/{id}            # WebSocket for session
SSE    /api/v1/sse/sessions/{id}            # Server-Sent Events
```

#### Sandbox

```
POST   /api/v1/sandbox/allocate            # Allocate sandbox
POST   /api/v1/sandbox/{id}/execute        # Execute code
POST   /api/v1/sandbox/{id}/terminal       # Terminal command
GET    /api/v1/sandbox/{id}/files          # List files
POST   /api/v1/sandbox/{id}/files          # Write file
GET    /api/v1/sandbox/{id}/files/{path}   # Read file
DELETE /api/v1/sandbox/{id}                # Release sandbox
```

#### Memory

```
POST   /api/v1/memory/search               # Semantic search
POST   /api/v1/memory/store                # Store memory
GET    /api/v1/memory/{session_id}         # Get session memory
DELETE /api/v1/memory/{session_id}         # Clear session memory
```

#### Plugins

```
GET    /api/v1/plugins                     # List plugins
POST   /api/v1/plugins                     # Install plugin
GET    /api/v1/plugins/{name}             # Get plugin details
PATCH  /api/v1/plugins/{name}             # Update plugin
DELETE /api/v1/plugins/{name}              # Uninstall plugin
POST   /api/v1/plugins/{name}/enable       # Enable plugin
POST   /api/v1/plugins/{name}/disable      # Disable plugin
```

#### MCP

```
GET    /api/v1/mcp/tools                   # List MCP tools
POST   /api/v1/mcp/execute                # Execute MCP tool
```

### Request/Response Examples

#### Create Session

```http
POST /api/v1/sessions
Content-Type: application/json
Authorization: Bearer {api_key}

{
    "title": "Build REST API",
    "context": {
        "language": "python",
        "framework": "fastapi"
    }
}
```

```json
{
    "id": "sess_abc123",
    "title": "Build REST API",
    "status": "created",
    "created_at": "2025-01-15T10:30:00Z",
    "agents": {
        "planner": {"status": "idle"},
        "researcher": {"status": "idle"},
        "coder": {"status": "idle"}
    }
}
```

#### Execute Task

```http
POST /api/v1/sessions/sess_abc123/execute
Content-Type: application/json
Authorization: Bearer {api_key}

{
    "task": "Create a user authentication system with JWT tokens",
    "goals": [
        "Implement login/logout endpoints",
        "Add JWT token generation and validation",
        "Create password hashing with bcrypt"
    ],
    "constraints": [
        "Use Python FastAPI",
        "Store tokens in Redis",
        "Include unit tests"
    ]
}
```

```json
{
    "execution_id": "exec_xyz789",
    "status": "started",
    "session_id": "sess_abc123",
    "stream_url": "/api/v1/ws/sessions/sess_abc123"
}
```

#### WebSocket Streaming

```javascript
// Client connects to WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/sessions/sess_abc123');

// Receive messages
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch (message.type) {
        case 'log_entry':
            console.log(`[${message.data.level}] ${message.data.message}`);
            break;
        case 'agent_status':
            updateAgentUI(message.data);
            break;
        case 'artifact_created':
            showArtifact(message.data);
            break;
        case 'stream_chunk':
            appendToOutput(message.data.content);
            break;
    }
};
```

---

## LangGraph Orchestration

### Graph Definition

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    """State shared across all agents"""
    session_id: str
    task: TaskSpecification
    messages: Annotated[list[Message], operator.add]
    agent_states: dict[str, AgentState]
    artifacts: list[Artifact]
    context: dict[str, Any]
    current_agent: str | None
    execution_plan: list[SubTask] | None
    errors: list[str]

# Graph nodes
def supervisor_node(state: AgentState) -> AgentState:
    """Root node that routes to appropriate agent"""
    pass

def planner_node(state: AgentState) -> AgentState:
    """Planner creates execution roadmap"""
    pass

def researcher_node(state: AgentState) -> AgentState:
    """Researcher gathers information"""
    pass

def coder_node(state: AgentState) -> AgentState:
    """Coder implements features"""
    pass

def reviewer_node(state: AgentState) -> AgentState:
    """Reviewer validates code"""
    pass

def tester_node(state: AgentState) -> AgentState:
    """Tester runs tests"""
    pass

def documentation_node(state: AgentState) -> AgentState:
    """Documentation generates docs"""
    pass

# Build graph
graph = StateGraph(AgentState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("planner", planner_node)
graph.add_node("researcher", researcher_node)
graph.add_node("coder", coder_node)
graph.add_node("reviewer", reviewer_node)
graph.add_node("tester", tester_node)
graph.add_node("documentation", documentation_node)

# Define edges
graph.add_edge("__root__", "supervisor")
graph.add_edge("supervisor", "planner")
graph.add_edge("planner", END)  # or route to specific agent

# Conditional routing
def should_research(state: AgentState) -> str:
    if state["task"].requires_research:
        return "researcher"
    return "coder"

graph.add_conditional_edges(
    "planner",
    should_research,
    {
        "researcher": "researcher",
        "coder": "coder"
    }
)

# Parallel execution
def execute_parallel(agents: list[str]):
    """Execute multiple agents in parallel"""
    pass

compiled_graph = graph.compile()
```

### Execution Flow

```
User Input
    │
    ▼
┌─────────────────┐
│   Supervisor    │ ◄── Routes based on task type
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌─────────┐     ┌─────────┐
│ Planner │ │Research │     │  Coder  │──► File Editor
└────┬────┘ └────┬────┘     └────┬────┘──► Terminal
     │           │                │──► Git
     ▼           ▼                │
┌─────────┐ ┌─────────┐          ▼
│  Goals  │ │Context  │     ┌─────────┐
└─────────┘ └─────────┘     │Reviewer │
                            └────┬────┘
                                 │
                            ┌────┴────┐
                            ▼         ▼
                       ┌─────────┐ ┌─────────┐
                       │ Tester  │ │   Doc   │
                       └─────────┘ └─────────┘
                            │         │
                            └────┬────┘
                                 ▼
                            ┌─────────┐
                            │ Supervisor│
                            │  (Output) │
                            └─────────┘
```

---

## Sandbox Execution

### Docker Sandbox Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     Sandbox Manager                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Container Pool                        │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐        │  │
│  │  │Sandbox │  │Sandbox │  │Sandbox │  │Sandbox │   ...   │  │
│  │  │   1    │  │   2    │  │   3    │  │   4    │        │  │
│  │  └────────┘  └────────┘  └────────┘  └────────┘        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│   Terminal     │  │   Browser      │  │   File System  │
│   (PTY/SSH)    │  │   (Playwright) │  │   (9P/FUSE)    │
└────────────────┘  └────────────────┘  └────────────────┘
```

### Sandbox Dockerfile

```dockerfile
FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git curl wget vim nano \
    python3.11 python3-pip \
    nodejs npm \
    docker-cli \
    openssh-client \
    rsync \
    && rm -rf /var/lib/apt/lists/*

# Install browser automation
RUN pip install playwright \
    && playwright install chromium

# Configure workspace
WORKDIR /workspace
RUN mkdir -p /workspace/project /workspace/artifacts

# Security: Non-root user
RUN useradd -m -s /bin/bash agent \
    && echo "agent:agent" | chpasswd \
    && mkdir -p /home/agent/.ssh \
    && chown -R agent:agent /workspace

USER agent
ENV PATH="/home/agent/.local/bin:${PATH}"

# Entry point
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

### Sandbox API

```python
class SandboxManager:
    """Manages sandbox lifecycle"""
    
    async def allocate(self, session_id: str) -> str:
        """Allocate a sandbox for a session"""
        container = await self.pool.acquire()
        return container.id
    
    async def execute(
        self,
        sandbox_id: str,
        code: str,
        language: str,
        timeout: int = 60
    ) -> ExecutionResult:
        """Execute code in sandbox"""
        pass
    
    async def terminal(
        self,
        sandbox_id: str,
        command: str,
        cwd: str = "/workspace"
    ) -> TerminalOutput:
        """Execute terminal command"""
        pass
    
    async def browse(
        self,
        sandbox_id: str,
        url: str,
        action: BrowserAction
    ) -> BrowserResult:
        """Perform browser automation"""
        pass
    
    async def release(self, sandbox_id: str):
        """Release sandbox back to pool"""
        pass
```

---

## Memory System

### ChromaDB Integration

```python
from chromadb.config import Settings
import chromadb

class MemoryManager:
    """Manages semantic memory using ChromaDB"""
    
    def __init__(self, persist_directory: str = "./data/chroma"):
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        self.collection = self.client.get_or_create_collection(
            name="agent_memory",
            metadata={"hnsw:space": "cosine"}
        )
    
    async def store(
        self,
        content: str,
        metadata: dict,
        session_id: str,
        agent_type: str
    ) -> str:
        """Store memory with semantic embedding"""
        embedding = await self.embedding_model.embed(content)
        
        return self.collection.add(
            documents=[content],
            metadatas=[{
                **metadata,
                "session_id": session_id,
                "agent_type": agent_type
            }],
            ids=[str(uuid4())]
        )
    
    async def search(
        self,
        query: str,
        session_id: str | None = None,
        agent_type: str | None = None,
        limit: int = 10
    ) -> list[MemoryEntry]:
        """Semantic search over memories"""
        query_embedding = await self.embedding_model.embed(query)
        
        where_filter = {}
        if session_id:
            where_filter["session_id"] = session_id
        if agent_type:
            where_filter["agent_type"] = agent_type
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter if where_filter else None
        )
        
        return [
            MemoryEntry(
                id=results["ids"][0][i],
                content=results["documents"][0][i],
                metadata=results["metadatas"][0][i],
                distance=results["distances"][0][i]
            )
            for i in range(len(results["ids"][0]))
        ]
    
    async def get_session_context(
        self,
        session_id: str,
        max_entries: int = 50
    ) -> list[MemoryEntry]:
        """Get recent context for a session"""
        results = self.collection.get(
            where={"session_id": session_id},
            limit=max_entries,
            include=["documents", "metadatas"]
        )
        
        return [
            MemoryEntry(
                id=results["ids"][i],
                content=results["documents"][i],
                metadata=results["metadatas"][i]
            )
            for i in range(len(results["ids"]))
        ]
```

### Memory Types

| Type | Storage | Retention | Use Case |
|------|---------|-----------|----------|
| **Session Memory** | ChromaDB | Session duration | Current task context |
| **Long-term Memory** | ChromaDB | Persistent | Learned patterns |
| **Semantic Cache** | Redis | TTL-based | Frequent queries |
| **Artifact Storage** | S3/Local | Persistent | Generated files |

---

## Plugin Architecture

### Plugin Structure

```
plugins/
└── my-plugin/
    ├── __init__.py           # Plugin entry point
    ├── plugin.json           # Plugin manifest
    ├── src/
    │   ├── __init__.py
    │   ├── tools.py          # Custom tools
    │   ├── agents.py         # Custom agents
    │   └── handlers.py       # Event handlers
    ├── prompts/
    │   └── system.md
    └── tests/
        └── test_plugin.py
```

### Plugin Manifest

```json
{
    "name": "github-integration",
    "version": "1.0.0",
    "description": "GitHub integration for code review and PR management",
    "author": "NexusMind Team",
    "entry_point": "plugins:MyPlugin",
    "permissions": ["github", "webhook"],
    "tools": [
        {
            "name": "create_pr",
            "description": "Create a pull request",
            "parameters": {
                "repo": "string",
                "title": "string",
                "body": "string"
            }
        }
    ],
    "agents": [
        {
            "type": "reviewer",
            "capabilities": ["github_review"]
        }
    ],
    "config_schema": {
        "github_token": {"type": "string", "required": true}
    }
}
```

### Plugin Manager

```python
class PluginManager:
    """Manages plugin lifecycle and discovery"""
    
    def __init__(self, plugin_dir: str = "./plugins"):
        self.plugin_dir = plugin_dir
        self.plugins: dict[str, Plugin] = {}
        self.tools: dict[str, Tool] = {}
    
    async def discover(self):
        """Discover and load all plugins"""
        for path in Path(self.plugin_dir).iterdir():
            if path.is_dir() and (path / "plugin.json").exists():
                await self.load_plugin(path)
    
    async def load_plugin(self, path: Path) -> Plugin:
        """Load a single plugin"""
        manifest = json.loads((path / "plugin.json").read_text())
        module = importlib.import_module(str(path).replace("/", "."))
        
        plugin_class = getattr(module, "Plugin")
        plugin = plugin_class(manifest, path)
        
        await plugin.initialize()
        self.plugins[plugin.name] = plugin
        
        for tool in plugin.tools:
            self.tools[tool.name] = tool
        
        return plugin
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: dict
    ) -> Any:
        """Execute a plugin tool"""
        tool = self.tools.get(tool_name)
        if not tool:
            raise PluginNotFoundError(tool_name)
        
        return await tool.execute(parameters)
```

---

## MCP Support

The Model Context Protocol (MCP) integration enables NexusMind to connect to standards-compliant MCP servers and expose their tools to agents.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MCP Integration                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                        MCPServerManager                               │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │  │
│  │  │  Server Config  │  │  Health Checks   │  │  Auto Reconnect  │ │  │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘ │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    ↓                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                          MCPClient                                   │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │  │
│  │  │  StdioTransport │  │  HTTPTransport   │  │  Tool Discovery │ │  │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘ │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    ↓                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                         MCPRegistry                                  │  │
│  │  - Dynamic tool registration                                         │  │
│  │  - Tool invocation with timeout/cancellation                         │  │
│  │  - Permission validation                                             │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Features

- **Server Management**: Add, remove, enable, disable MCP servers dynamically
- **Tool Discovery**: Automatically discover tools from connected servers  
- **Tool Execution**: Execute MCP tools with sync/async support, streaming, timeout, and cancellation
- **Transport Abstraction**: Support for stdio and HTTP transports with a common interface
- **Health Checks**: Periodic health checks with automatic reconnection
- **Security**: Trusted servers, tool allowlist/blocklist, permission validation
- **API Integration**: Full REST API for server and tool management

### Folder Structure

```
nexusmind/backend/app/mcp/
├── __init__.py
├── client.py           # MCP client implementation
├── exceptions.py       # MCP-specific exceptions
├── manager.py         # Server manager with lifecycle
├── registry.py         # Tool registry
├── schemas.py         # Pydantic models
├── server_manager.py    # Backwards compatibility
├── protocol.py         # Protocol definitions
├── tools.py            # Tool integration
├── utils/
│   └── __init__.py    # Logging utilities
└── transports/
    ├── __init__.py
    ├── base.py         # Base transport interface
    ├── http.py         # HTTP transport
    └── stdio.py        # Stdio transport
```

### Configuration

MCP servers are configured via YAML in `config/mcp.yaml`:

```yaml
enabled: true
default_timeout: 30
auto_discover: true

servers:
  filesystem:
    name: filesystem
    transport: stdio
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-filesystem"
      - "/workspace"
    enabled: true
    trusted: true
    auto_reconnect: true
    
  github:
    name: github
    transport: stdio
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-github"
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/mcp/servers` | List all servers |
| POST | `/api/v1/mcp/servers` | Add new server |
| DELETE | `/api/v1/mcp/servers/{name}` | Remove server |
| POST | `/api/v1/mcp/servers/{name}/start` | Start server |
| POST | `/api/v1/mcp/servers/{name}/stop` | Stop server |
| POST | `/api/v1/mcp/servers/{name}/enable` | Enable server |
| POST | `/api/v1/mcp/servers/{name}/disable` | Disable server |
| GET | `/api/v1/mcp/tools` | List all tools |
| GET | `/api/v1/mcp/tools/{name}` | Get tool details |
| POST | `/api/v1/mcp/tools/{name}/execute` | Execute tool |
| GET | `/api/v1/mcp/status` | Get system status |
| GET | `/api/v1/mcp/health` | Get health status |

---

## Frontend Architecture

### Next.js App Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx           # Dashboard home
│   │   │   ├── sessions/
│   │   │   │   ├── page.tsx       # Session list
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx   # Session detail
│   │   │   │       └── files/     # File browser
│   │   │   ├── settings/
│   │   │   │   ├── page.tsx       # User settings
│   │   │   │   ├── agents/       # Agent config
│   │   │   │   ├── plugins/      # Plugin management
│   │   │   │   └── llm/          # LLM provider settings
│   │   │   └── marketplace/
│   │   │       └── page.tsx       # Plugin marketplace
│   │   ├── api/
│   │   │   └── trpc/[trpc]/
│   │   │       └── route.ts
│   │   ├── layout.tsx
│   │   └── page.tsx
│   │
│   ├── components/
│   │   ├── ui/                    # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── dropdown-menu.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── scroll-area.tsx
│   │   │   └── ...
│   │   │
│   │   ├── chat/
│   │   │   ├── ChatWindow.tsx     # Main chat interface
│   │   │   ├── MessageList.tsx    # Message display
│   │   │   ├── MessageItem.tsx    # Individual message
│   │   │   ├── MessageInput.tsx   # Input with suggestions
│   │   │   ├── AgentBadge.tsx     # Agent identifier
│   │   │   └── StreamingIndicator.tsx
│   │   │
│   │   ├── session/
│   │   │   ├── SessionList.tsx
│   │   │   ├── SessionCard.tsx
│   │   │   ├── SessionHeader.tsx
│   │   │   └── SessionStats.tsx
│   │   │
│   │   ├── agent/
│   │   │   ├── AgentPanel.tsx     # Agent status panel
│   │   │   ├── AgentTimeline.tsx  # Execution timeline
│   │   │   ├── AgentAvatar.tsx
│   │   │   └── AgentStateIndicator.tsx
│   │   │
│   │   ├── terminal/
│   │   │   ├── Terminal.tsx       # xterm.js wrapper
│   │   │   ├── TerminalToolbar.tsx
│   │   │   └── TerminalOutput.tsx
│   │   │
│   │   ├── file-explorer/
│   │   │   ├── FileTree.tsx
│   │   │   ├── FileItem.tsx
│   │   │   └── FileEditor.tsx     # Monaco editor
│   │   │
│   │   └── logs/
│   │       ├── LogViewer.tsx
│   │       ├── LogFilter.tsx
│   │       └── LogEntry.tsx
│   │
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts          # API client setup
│   │   │   ├── sessions.ts
│   │   │   ├── agents.ts
│   │   │   └── plugins.ts
│   │   ├── websocket.ts           # WebSocket client
│   │   ├── streaming.ts          # SSE client
│   │   └── utils.ts
│   │
│   ├── hooks/
│   │   ├── useSession.ts
│   │   ├── useStreaming.ts
│   │   ├── useAgents.ts
│   │   ├── useWebSocket.ts
│   │   └── useTerminal.ts
│   │
│   ├── stores/
│   │   ├── sessionStore.ts        # Zustand store
│   │   │   ├── sessions[]
│   │   │   ├── currentSession
│   │   │   ├── messages[]
│   │   │   └── actions
│   │   │
│   │   ├── agentStore.ts
│   │   │   ├── agentStates{}
│   │   │   ├── activeAgents[]
│   │   │   └── logs[]
│   │   │
│   │   └── uiStore.ts
│   │       ├── sidebarOpen
│   │       ├── activePanel
│   │       └── theme
│   │
│   └── types/
│       ├── api.ts
│       ├── agent.ts
│       ├── message.ts
│       └── session.ts
```

### Component Hierarchy

```
App
├── (Auth) Layout
│   ├── Login Page
│   └── Register Page
│
└── (Dashboard) Layout
    ├── Sidebar
    │   ├── Logo
    │   ├── Navigation
    │   │   ├── Dashboard
    │   │   ├── Sessions
    │   │   ├── Marketplace
    │   │   └── Settings
    │   └── User Menu
    │
    └── Main Content
        ├── Dashboard Page
        ├── Sessions Layout
        │   ├── Session List Page
        │   └── Session Detail Page
        │       ├── Chat Window
        │       ├── Agent Panel
        │       ├── File Explorer
        │       ├── Terminal
        │       └── Log Viewer
        │
        ├── Settings Layout
        │   ├── General Settings
        │   ├── Agent Configuration
        │   ├── Plugin Management
        │   └── LLM Providers
        │
        └── Marketplace Page
```

### State Management (Zustand)

```typescript
// stores/sessionStore.ts
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';

interface Message {
  id: string;
  role: 'user' | 'agent';
  content: string;
  agentType?: AgentType;
  timestamp: Date;
}

interface Session {
  id: string;
  title: string;
  status: 'created' | 'running' | 'completed' | 'error';
  messages: Message[];
  createdAt: Date;
}

interface SessionStore {
  sessions: Session[];
  currentSession: Session | null;
  
  // Actions
  setSessions: (sessions: Session[]) => void;
  addSession: (session: Session) => void;
  setCurrentSession: (session: Session | null) => void;
  addMessage: (sessionId: string, message: Message) => void;
  updateSessionStatus: (sessionId: string, status: string) => void;
}

export const useSessionStore = create<SessionStore>()(
  immer((set) => ({
    sessions: [],
    currentSession: null,
    
    setSessions: (sessions) => set({ sessions }),
    addSession: (session) => set((state) => {
      state.sessions.push(session);
    }),
    setCurrentSession: (session) => set({ currentSession: session }),
    addMessage: (sessionId, message) => set((state) => {
      const session = state.sessions.find(s => s.id === sessionId);
      if (session) {
        session.messages.push(message);
      }
      if (state.currentSession?.id === sessionId) {
        state.currentSession.messages.push(message);
      }
    }),
    updateSessionStatus: (sessionId, status) => set((state) => {
      const session = state.sessions.find(s => s.id === sessionId);
      if (session) session.status = status;
      if (state.currentSession?.id === sessionId) {
        state.currentSession.status = status;
      }
    }),
  }))
);
```

---

## Streaming Infrastructure

### WebSocket Manager

```python
class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        # session_id -> list of connections
        self.active_connections: dict[str, list[WebSocket]] = {}
        # connection_id -> session_id
        self.connection_sessions: dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept and register new connection"""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        
        conn_id = str(uuid4())
        self.active_connections[session_id].append(websocket)
        self.connection_sessions[conn_id] = session_id
        
        # Subscribe to Redis channel
        await self.pubsub.subscribe(f"session:{session_id}:events")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove connection"""
        conn_id = None
        for cid, ws in self._connections.items():
            if ws == websocket:
                conn_id = cid
                break
        
        if conn_id:
            session_id = self.connection_sessions.pop(conn_id, None)
            if session_id and session_id in self.active_connections:
                self.active_connections[session_id] = [
                    ws for ws in self.active_connections[session_id]
                    if ws != websocket
                ]
    
    async def send_to_session(self, session_id: str, message: dict):
        """Broadcast message to all connections in session"""
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass  # Connection might be closed
    
    async def broadcast_log(self, session_id: str, log: LogEntry):
        """Stream log entry to client"""
        await self.send_to_session(session_id, {
            "type": "log_entry",
            "data": log.model_dump()
        })
```

### Event Types for Streaming

```python
class StreamEvent(str, Enum):
    # Agent events
    AGENT_STARTED = "agent_started"
    AGENT_PROGRESS = "agent_progress"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    
    # Message events
    MESSAGE_CREATED = "message_created"
    MESSAGE_UPDATED = "message_updated"
    
    # Artifact events
    ARTIFACT_CREATED = "artifact_created"
    FILE_MODIFIED = "file_modified"
    
    # Terminal events
    TERMINAL_OUTPUT = "terminal_output"
    TERMINAL_CLOSED = "terminal_closed"
    
    # System events
    SESSION_STATUS_CHANGED = "session_status_changed"
    HEARTBEAT = "heartbeat"
```

---

## Tech Stack Summary

### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | FastAPI 0.109+ | REST API, WebSocket, SSE |
| **Orchestration** | LangGraph | Agent workflow management |
| **LLM** | LangChain + Ollama/OpenAI | AI model integration |
| **Database** | PostgreSQL 15+ | Sessions, users, messages |
| **Vector DB** | ChromaDB | Semantic memory |
| **Cache** | Redis 7+ | Pub/Sub, rate limiting |
| **Sandbox** | Docker SDK | Isolated code execution |
| **MCP** | mcp-python | Model Context Protocol |
| **Auth** | JWT + API Keys | Authentication |

### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | Next.js 14 (App Router) | React frontend |
| **UI Components** | shadcn/ui | Component library |
| **Styling** | Tailwind CSS | Styling |
| **State** | Zustand | Client state |
| **Forms** | React Hook Form + Zod | Form handling |
| **Terminal** | xterm.js | Terminal emulation |
| **Editor** | Monaco Editor | Code editing |
| **Real-time** | Native WebSocket | Streaming |
| **Icons** | Lucide React | Icons |

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Container** | Docker + Docker Compose | Development, deployment |
| **Orchestration** | Docker Swarm / Kubernetes | Container orchestration |
| **Reverse Proxy** | Nginx | Load balancing, SSL |
| **Monitoring** | Prometheus + Grafana | Metrics, dashboards |
| **Logging** | ELK Stack | Centralized logging |

---

## Development Roadmap

### Phase 1: Foundation (Weeks 1-4)

**Goal**: Core backend with basic agent execution

- [ ] Project scaffolding and repository setup
- [ ] FastAPI application with basic structure
- [ ] Database models and migrations (PostgreSQL)
- [ ] Session management API
- [ ] Message handling API
- [ ] Basic agent base class
- [ ] Simple LangGraph orchestration
- [ ] Docker sandbox with terminal access
- [ ] WebSocket streaming infrastructure
- [ ] Basic authentication (JWT)

**Deliverables**:
- Working REST API for sessions
- Single-agent execution capability
- Real-time streaming of agent logs
- Docker-based sandbox execution

### Phase 2: Multi-Agent System (Weeks 5-8)

**Goal**: Full agent team with collaboration

- [ ] Implement all 7 agent types
- [ ] Agent-to-agent communication (message bus)
- [ ] Parallel agent execution
- [ ] Task dependency resolution
- [ ] Supervisor/Manager agent
- [ ] Agent state persistence
- [ ] Error handling and retry logic
- [ ] Rate limiting and quotas

**Deliverables**:
- All 7 agents functional
- Agent collaboration working
- Parallel task execution
- Error recovery mechanisms

### Phase 3: Tools & Integrations (Weeks 9-12)

**Goal**: Rich tool ecosystem and integrations

- [ ] Terminal tool with PTY support
- [ ] File editor tool (create, read, update, delete)
- [ ] Browser automation (Playwright)
- [ ] Web search tool
- [ ] GitHub integration (PR creation, reviews)
- [ ] ChromaDB memory integration
- [ ] Redis caching layer
- [ ] Ollama LLM adapter
- [ ] OpenAI-compatible API adapter

**Deliverables**:
- All core tools working
- GitHub integration complete
- Memory system operational
- Multiple LLM providers supported

### Phase 4: Frontend (Weeks 13-16)

**Goal**: Complete user interface

- [ ] Next.js project setup
- [ ] Authentication UI
- [ ] Session list and management
- [ ] Chat interface with streaming
- [ ] Agent status dashboard
- [ ] Terminal component (xterm.js)
- [ ] File explorer with Monaco editor
- [ ] Log viewer
- [ ] Settings pages
- [ ] Responsive design

**Deliverables**:
- Complete web UI
- Real-time streaming UX
- File editing capability
- Agent monitoring dashboard

### Phase 5: Extensibility (Weeks 17-20)

**Goal**: Plugin system and MCP support

- [ ] Plugin architecture design
- [ ] Plugin discovery and loading
- [ ] Plugin API (tools, agents, events)
- [ ] MCP server implementation
- [ ] MCP tool registration
- [ ] Built-in plugins (GitHub, Jira, Slack)
- [ ] Plugin marketplace API
- [ ] Plugin sandboxing/security

**Deliverables**:
- Plugin system working
- MCP protocol support
- Sample plugins
- Plugin documentation

### Phase 6: Polish & Production (Weeks 21-24)

**Goal**: Production-ready release

- [ ] Comprehensive testing (unit, integration, e2e)
- [ ] Performance optimization
- [ ] Security audit
- [ ] Documentation (API, user guide, architecture)
- [ ] Docker Compose for easy deployment
- [ ] Kubernetes manifests
- [ ] CI/CD pipeline
- [ ] Monitoring and alerting
- [ ] Error tracking (Sentry)
- [ ] Load testing

**Deliverables**:
- Production-ready application
- Complete documentation
- Deployment guides
- Open-source release

---

## Design Decisions

### 1. LangGraph over Custom State Machine

**Decision**: Use LangGraph for agent orchestration

**Rationale**:
- LangGraph provides excellent support for complex workflows with cycles
- Built-in checkpointing for fault tolerance
- Native support for conditional branching
- Integrates well with LangChain for LLM integration
- Active maintenance by LangChain team

**Alternative considered**: Custom state machine (rejected due to complexity)

### 2. ChromaDB for Vector Storage

**Decision**: Use ChromaDB over Pinecone/Weaviate

**Rationale**:
- Single-file deployment, no external services
- Excellent for development and small-to-medium scale
- Easy to upgrade to cloud services later
- Simple API matching our requirements
- Good integration with LangChain

**Trade-off**: Limited horizontal scalability

### 3. Docker Sandbox over WebAssembly

**Decision**: Docker containers for sandboxing

**Rationale**:
- Complete OS-level isolation
- Native performance for all operations
- Industry standard for containerization
- Easy to add browser automation (Playwright)
- Well-understood security model

**Trade-off**: Higher resource overhead than WASM

### 4. WebSocket over Server-Sent Events

**Decision**: Primary streaming via WebSocket, SSE as fallback

**Rationale**:
- Bidirectional communication
- Better for interactive terminals
- Native browser support
- SSE as alternative for simpler clients

### 5. PostgreSQL over NoSQL

**Decision**: PostgreSQL for all structured data

**Rationale**:
- Strong consistency for session state
- JSONB for flexible metadata
- Excellent performance with proper indexing
- SQL for complex queries (analytics)
- Mature ecosystem

**Trade-off**: Schema migrations required

### 6. Next.js App Router over Pages Router

**Decision**: Next.js 14 App Router

**Rationale**:
- Server components for better performance
- Built-in streaming with Suspense
- Modern React patterns
- File-based routing with layouts
- Better for real-time features

### 7. Zustand over Redux/Jotai

**Decision**: Zustand for state management

**Rationale**:
- Minimal boilerplate
- Built-in TypeScript support
- Good performance
- Works well with SSR
- Immer integration for immutable updates

---

## Security Considerations

### Sandbox Isolation

1. **Network**: No outbound network by default; explicit allowlisting
2. **Filesystem**: Restricted to `/workspace` directory
3. **Processes**: Resource limits (CPU, memory, time)
4. **User**: Non-root execution within container
5. **Capabilities**: Dropped Linux capabilities

### API Security

1. **Authentication**: JWT for users, API keys for integrations
2. **Rate Limiting**: Per-user and per-endpoint limits
3. **Input Validation**: Pydantic models + Zod schemas
4. **CORS**: Configured allowed origins
5. **CSRF**: SameSite cookies, CSRF tokens

### Data Security

1. **Encryption at Rest**: Database encryption
2. **Encryption in Transit**: TLS 1.3
3. **Secrets**: Environment variables, secret manager
4. **Audit Logging**: All actions logged with user context

---

## Scalability Considerations

### Horizontal Scaling

1. **Stateless API**: All state in database/Redis
2. **Connection Pooling**: PgBouncer for PostgreSQL
3. **Redis Clustering**: For pub/sub and caching
4. **Load Balancing**: Multiple API instances

### Agent Scaling

1. **Container Pool**: Pre-warmed sandbox containers
2. **Queue-based Execution**: Tasks queued in Redis
3. **Auto-scaling**: Kubernetes HPA based on queue depth
4. **Resource Quotas**: Per-user resource limits

---

## Monitoring & Observability

### Metrics

- Request latency (p50, p95, p99)
- Agent execution duration
- LLM token usage
- Sandbox utilization
- Error rates by type

### Logging

- Structured JSON logs
- Correlation IDs for tracing
- Log levels: DEBUG, INFO, WARN, ERROR
- ELK stack integration

### Alerts

- High error rate threshold
- Slow response times
- Resource exhaustion
- Agent timeout patterns

---

## Future Enhancements

1. **Multi-user Collaboration**: Real-time co-editing, presence
2. **Distributed Agents**: Agents across multiple machines
3. **Visual Workflow Builder**: UI for creating agent flows
4. **Custom Agent SDK**: For building domain-specific agents
5. **Enterprise Features**: SSO, audit logs, compliance
6. **Cloud Offering**: Managed NexusMind service

---

*Document Version: 1.0*  
*Last Updated: 2025-01-15*  
*Status: Architecture Complete*
