# NexusMind Architecture

## Overview

NexusMind is an open-source autonomous multi-agent AI platform similar to Manus, Devin, and OpenHands. It provides a FastAPI backend with Next.js frontend integration, a flexible orchestration layer, Docker sandbox execution, and ChromaDB memory.

## Tech Stack

### Backend
- **Framework**: FastAPI 0.140+
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Memory**: ChromaDB (vector store)
- **LLM Providers**: Ollama, OpenAI-compatible, Anthropic
- **Orchestration**: A multi-faceted system using an executor, supervisor, and project generator.
- **Sandbox**: Docker containers
- **Streaming**: WebSocket + Server-Sent Events (SSE)

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **State Management**: React Query + Zustand
- **UI Components**: TailwindCSS + Shadcn/ui
- **Real-time**: WebSocket client

## Folder Structure

```
nexusmind/
├── backend/
│   ├── app/
│   │   ├── __init__.py           # App initialization
│   │   ├── main.py               # FastAPI app factory
│   │   ├── config.py             # Settings with Pydantic
│   │   ├── dependencies.py       # Dependency injection
│   │   │
│   │   ├── api/                  # API endpoints
│   │   │   ├── v1/
│   │   │   │   ├── sessions.py   # Session management
│   │   │   │   ├── agents.py    # Agent types & capabilities
│   │   │   │   ├── sandbox.py    # Sandbox allocation
│   │   │   │   ├── memory.py     # Memory operations
│   │   │   │   ├── plugins.py    # Plugin management
│   │   │   │   └── webhooks.py   # Webhook endpoints
│   │   │   └── ws.py             # WebSocket handlers
│   │   │
│   │   ├── auth/                 # Authentication
│   │   │   ├── service.py        # Auth service
│   │   │   └── routes.py         # Auth endpoints
│   │   │
│   │   ├── agents/               # Multi-agent system
│   │   │   ├── types.py          # AgentType enum
│   │   │   ├── implementations.py # Baseline agent implementations
│   │   │   ├── autonomous.py     # Advanced, tool-using agents
│   │   │   ├── execution_engine.py # Agent tool invocation logic
│   │   │   └── reasoning_loop.py   # Core agent reasoning cycle
│   │   │
│   │   ├── orchestration/        # Orchestration layer
│   │   │   ├── executor.py       # Sequential agent executor
│   │   │   ├── supervisor.py     # Complex multi-agent coordinator
│   │   │   └── project_generator.py # Autonomous project generation
│   │   │
│   │   ├── db/                   # Database models
│   │   │   ├── database.py       # SQLAlchemy setup
│   │   │   ├── session.py        # User, Session, ApiKey models
│   │   │   ├── message.py        # Message model
│   │   │   └── artifact.py       # Artifact, Task, AgentLog models
│   │   │
│   │   ├── llm/                  # LLM providers
│   │   │   ├── routing/          # Intelligent model routing
│   │   │   └── byok/             # Bring-Your-Own-Key service
│   │   │
│   │   ├── mcp/                  # Multi-Contributor Protocol
│   │   │   ├── manager.py        # Manages external tool servers
│   │   │   ├── client.py         # Client for a single tool server
│   │   │   └── registry.py       # Central tool registry
│   │   │
│   │   ├── sandbox/              # Code execution
│   │   │   └── docker.py         # Docker sandbox implementation
│   │   │
│   │   ├── memory/               # Memory system
│   │   │   └── chromadb.py       # ChromaDB integration
│   │   │
│   │   ├── tools/                # Agent tools
│   │   │   ├── registry.py       # Tool registry
│   │   │   └── docker_sandbox_tool.py # Sandbox tool
│   │   │
│   │   ├── streaming/            # Real-time streaming
│   │   │   ├── events.py         # Event types
│   │   │   ├── ws_manager.py     # WebSocket manager
│   │   │   └── sse.py            # SSE handler
│   │   │
│   │   └── utils/                # Utilities
│   │       ├── logger.py         # Structured logging
│   │       └── security.py       # JWT, password hashing
│   │
│   ├── tests/                    # Test suite
│   │   ├── api/
│   │   │   └── test_api.py       # API tests
│   │   └── conftest.py           # Pytest config
│   │
│   ├── alembic/                  # Database migrations
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                     # Next.js frontend (to be created)
│   ├── app/
│   │   ├── page.tsx            # Home page
│   │   ├── sessions/
│   │   │   └── [id]/page.tsx   # Session page
│   │   └── layout.tsx
│   ├── components/
│   │   ├── chat/
│   │   ├── session/
│   │   └── ui/
│   └── package.json
│
├── docker/
│   └── sandbox/                 # Sandbox Docker image
│       └── Dockerfile
│
└── docs/
    └── ARCHITECTURE.md
```

## Database Schema

### Users Table
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| email | VARCHAR(255) | Unique email |
| name | VARCHAR(255) | Display name |
| password_hash | VARCHAR(255) | Bcrypt hash |
| is_active | BOOLEAN | Account status |
| is_superuser | BOOLEAN | Admin flag |
| last_login | TIMESTAMP | Last login time |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update |

### Sessions Table
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Owner FK |
| title | VARCHAR(500) | Session title |
| status | VARCHAR(50) | Status enum |
| agent_states | JSONB | Agent state snapshots |
| context | JSONB | Session context |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update |

### Messages Table
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| session_id | UUID | Session FK |
| role | VARCHAR(50) | user/assistant/system/tool |
| content | TEXT | Message content |
| agent_type | VARCHAR(50) | Which agent |
| parent_id | UUID | Thread parent |
| metadata | JSONB | Extra data |
| tokens_used | INTEGER | Token count |
| created_at | TIMESTAMP | Creation time |

### Tasks Table
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| session_id | UUID | Session FK |
| parent_id | UUID | Parent task |
| agent_type | VARCHAR(50) | Assigned agent |
| description | TEXT | Task description |
| status | VARCHAR(50) | pending/running/done |
| priority | INTEGER | Task priority |
| result | JSONB | Task result |
| error | TEXT | Error message |
| created_at | TIMESTAMP | Creation time |

### Artifacts Table
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| session_id | UUID | Session FK |
| message_id | UUID | Source message |
| type | VARCHAR(50) | file/code/image |
| name | VARCHAR(255) | File name |
| path | TEXT | File path |
| mime_type | VARCHAR(100) | MIME type |
| size_bytes | BIGINT | File size |
| created_at | TIMESTAMP | Creation time |

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Register user |
| POST | /api/v1/auth/login | Login |
| GET | /api/v1/auth/me | Get current user |
| POST | /api/v1/auth/api-keys | Create API key |
| GET | /api/v1/auth/api-keys | List API keys |
| DELETE | /api/v1/auth/api-keys/{id} | Revoke API key |

### Sessions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/sessions/ | List sessions |
| POST | /api/v1/sessions/ | Create session |
| GET | /api/v1/sessions/{id} | Get session |
| PATCH | /api/v1/sessions/{id} | Update session |
| DELETE | /api/v1/sessions/{id} | Delete session |
| POST | /api/v1/sessions/{id}/execute | Execute task |
| POST | /api/v1/sessions/{id}/stop | Stop execution |
| GET | /api/v1/sessions/{id}/messages | List messages |
| POST | /api/v1/sessions/{id}/messages | Add message |

### Agents
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/agents/types | List agent types |
| GET | /api/v1/agents/{type}/capabilities | Get capabilities |

### Sandbox
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/sandbox/allocate | Allocate sandbox |
| DELETE | /api/v1/sandbox/{id} | Release sandbox |
| POST | /api/v1/sandbox/{id}/execute | Execute code |
| GET | /api/v1/sandbox/{id}/terminal | Get terminal |

### Memory
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/memory/search | Search memories |
| POST | /api/v1/memory/store | Store memory |
| DELETE | /api/v1/memory/{id} | Delete memory |

### Plugins
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/plugins/ | List plugins |
| POST | /api/v1/plugins/ | Install plugin |
| DELETE | /api/v1/plugins/{name} | Uninstall plugin |
| POST | /api/v1/plugins/{name}/enable | Enable plugin |
| POST | /api/v1/plugins/{name}/disable | Disable plugin |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/webhooks/ | List webhooks |
| POST | /api/v1/webhooks/ | Register webhook |
| DELETE | /api/v1/webhooks/{id} | Delete webhook |

### WebSocket
| Event | Direction | Description |
|-------|----------|-------------|
| session.join | Client→Server | Join session |
| session.leave | Client→Server | Leave session |
| message | Bidirectional | Send/receive messages |
| agent.* | Server→Client | Agent lifecycle events |
| execution.* | Server→Client | Execution events |
| log | Server→Client | Streaming logs |
| heartbeat | Bidirectional | Keep-alive |

## Agent Communication

### Message Format
```json
{
  "type": "message",
  "session_id": "uuid",
  "role": "user|assistant|system|tool",
  "content": "string",
  "agent_type": "coder|reviewer|...",
  "metadata": {}
}
```

### State Format
```json
{
  "session_id": "uuid",
  "task": "string",
  "context": {},
  "messages": [],
  "artifacts": [],
  "agent_states": {},
  "current_agent": "string",
  "result": {},
  "error": "string|null"
}
```

## Design Decisions

### 1. Async-First Architecture
- All I/O operations are async
- SQLAlchemy with asyncpg driver
- Async LLM provider calls
- Non-blocking streaming

### 2. Consolidated Core Architecture
- **Orchestration**: A multi-faceted layer with a sequential executor, a complex supervisor, and a project generator.
- **Agents**: A centralized framework where agent types are defined in `types.py` and implemented in `implementations.py` and `autonomous.py`.
- **LLM Access**: A dual system combining dynamic, criteria-based routing (`app/llm/routing`) and user-specific credentials (`app/llm/byok`).
- **MCP**: A manager-client architecture (`manager.py`, `client.py`, `registry.py`) for integrating external tools.

### 3. Docker Sandbox Isolation
- Each sandbox is a separate container
- Resource limits (CPU, memory)
- Network isolation option
- Timeout enforcement

### 4. ChromaDB for Semantic Memory
- Persistent vector storage
- Session-scoped memory
- Semantic similarity search
- Metadata filtering

### 5. Multi-Provider LLM Support
- Ollama for local models
- OpenAI-compatible for cloud APIs
- Anthropic for Claude
- Unified chat interface

### 6. Real-time Streaming
- WebSocket for bi-directional
- SSE for server-push
- Event types for different payloads
- Heartbeat for connection health

## Development Roadmap

### Phase 1 ✅ - Foundation
- FastAPI application setup
- Configuration management
- Logging and error handling
- Middleware stack

### Phase 2 ✅ - Database
- SQLAlchemy models
- PostgreSQL integration
- Alembic migrations
- Session management

### Phase 3 ✅ - Authentication
- JWT tokens
- API keys
- User management
- Password hashing

### Phase 4 ✅ - Agents
- 7 agent types
- Consolidated agent framework
- Agent communication
- Tool registry

### Phase 5 ✅ - LLM Providers
- Ollama integration
- OpenAI-compatible API
- Anthropic Claude
- Provider abstraction

### Phase 6 ✅ - Sandbox
- Docker container management
- Code execution
- Terminal emulation
- Resource limits

### Phase 7 ✅ - Memory
- ChromaDB integration
- Semantic search
- Session memory
- Long-term storage

### Phase 8 ✅ - Streaming
- WebSocket manager
- SSE streaming
- Event types
- Connection handling

### Phase 9 ✅ - GitHub Integration
- GitPython for repository operations
- GitHub REST API for PRs and Issues
- Clone, commit, push, pull
- Create/Read Issues and PRs
- Repository tree and file operations
- Code search

### Phase 10 ✅ - MCP Integration
- MCP client with stdio/HTTP/SSE transports
- MCPServerManager for lifecycle management
- MCPRegistry for dynamic tool registration
- Auto-discovery of server tools
- YAML configuration support
- Agent tool invocation

### Phase 11 ✅ - Web Search Integration
- Unified interface for Tavily, Brave, DuckDuckGo
- Async requests with httpx
- Search caching with configurable TTL
- Rate limiting (token bucket algorithm)
- Automatic retries with exponential backoff
- JSON results with structured schemas
- Summarization for results
- Integration with ResearchAgent

### Phase 12 ✅ - Browser Automation
- BrowserTool using Playwright
- Support for Chromium, Firefox, WebKit
- Page navigation and interaction
- Screenshot capture
- JavaScript execution
- Console log collection
- File upload/download
- REST API endpoints
- Integration testing

### Future Phases
- **Phase 13**: CI/CD Pipeline
- **Phase 14**: Frontend (Next.js)
- **Phase 15**: Production Deployment
