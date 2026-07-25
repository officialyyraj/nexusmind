# NexusMind - Project Specification

## Overview

**Project Name**: NexusMind  
**Type**: Open-source autonomous multi-agent AI platform  
**Core Functionality**: Orchestrates specialized AI agents to collaborate on complex software engineering tasks  
**Target Users**: Developers, DevOps engineers, technical teams building AI-powered automation

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.109+
- **Language**: Python 3.11+
- **Orchestration**: LangGraph
- **LLM Integration**: LangChain + Ollama + OpenAI-compatible API
- **Database**: PostgreSQL 15+
- **Vector DB**: ChromaDB
- **Cache/PubSub**: Redis 7+
- **Sandbox**: Docker SDK
- **MCP**: mcp-python
- **Auth**: JWT + API Keys

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **State Management**: Zustand
- **Terminal**: xterm.js
- **Code Editor**: Monaco Editor
- **Real-time**: WebSocket + SSE

---

## Functionality Specification

### Core Features

#### 1. Multi-Agent System
- [x] 7 specialized agents: Planner, Researcher, Coder, Reviewer, Tester, Documentation, Manager
- [x] Agent-to-agent communication via message bus
- [x] Parallel agent execution
- [x] Task dependency resolution
- [x] Agent state persistence
- [x] Error handling with retry logic

#### 2. Orchestration
- [x] LangGraph-based workflow orchestration
- [x] Supervisor agent for task routing
- [x] Conditional branching based on task type
- [x] Checkpointing for fault tolerance
- [x] Streaming execution with real-time updates

#### 3. Sandbox Execution
- [x] Docker-based isolated execution
- [x] Container pooling for efficiency
- [x] Terminal emulation (PTY)
- [x] File system access (restricted)
- [x] Browser automation (Playwright)
- [x] Resource limits (CPU, memory, time)

#### 4. Memory System
- [x] ChromaDB semantic memory
- [x] Session context storage
- [x] Cross-session knowledge retention
- [x] Semantic search with embeddings
- [x] Redis caching layer

#### 5. Tools & Integrations
- [x] Terminal tool (bash commands)
- [x] File editor (read/write/edit)
- [x] Web search (Tavily/SerpAPI)
- [x] GitHub integration (PR, issues, reviews)
- [x] Git operations
- [x] Ollama LLM support
- [x] OpenAI-compatible API support

#### 6. Plugin Architecture
- [x] Plugin discovery and loading
- [x] Custom tool registration
- [x] Custom agent capabilities
- [x] Event hooks
- [x] Plugin configuration management

#### 7. MCP Support
- [x] MCP server implementation
- [x] Tool registration as MCP resources
- [x] Bidirectional communication

#### 8. Streaming & Real-time
- [x] WebSocket for bidirectional streaming
- [x] SSE fallback option
- [x] Real-time log streaming
- [x] Agent status updates
- [x] Message streaming

#### 9. Multi-session Conversations
- [x] Session management (CRUD)
- [x] Session archiving
- [x] Message history
- [x] Context preservation
- [x] Session search

---

## API Specification

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
```http
Authorization: Bearer {token}
```

### Endpoints

#### Sessions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sessions` | Create session |
| GET | `/sessions` | List sessions |
| GET | `/sessions/{id}` | Get session |
| PATCH | `/sessions/{id}` | Update session |
| DELETE | `/sessions/{id}` | Delete session |
| POST | `/sessions/{id}/execute` | Execute task |
| POST | `/sessions/{id}/stop` | Stop execution |

#### Messages
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sessions/{id}/messages` | List messages |
| POST | `/sessions/{id}/messages` | Send message |

#### Agents
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sessions/{id}/agents` | Get agent states |
| GET | `/agents/types` | List agent types |
| GET | `/agents/{type}/capabilities` | Get capabilities |

#### Streaming
| Method | Endpoint | Description |
|--------|----------|-------------|
| WS | `/ws/sessions/{id}` | WebSocket stream |
| GET | `/sse/sessions/{id}` | SSE stream |

#### Sandbox
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sandbox/allocate` | Allocate sandbox |
| POST | `/sandbox/{id}/execute` | Execute code |
| POST | `/sandbox/{id}/terminal` | Terminal command |
| GET | `/sandbox/{id}/files` | List files |
| DELETE | `/sandbox/{id}` | Release sandbox |

#### Memory
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/memory/search` | Semantic search |
| POST | `/memory/store` | Store memory |
| GET | `/memory/{session_id}` | Get session memory |

#### Plugins
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/plugins` | List plugins |
| POST | `/plugins` | Install plugin |
| GET | `/plugins/{name}` | Get plugin |
| PATCH | `/plugins/{name}` | Update plugin |
| DELETE | `/plugins/{name}` | Uninstall plugin |

#### MCP
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/mcp/tools` | List MCP tools |
| POST | `/mcp/execute` | Execute MCP tool |

---

## Database Schema

### Tables

#### users
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| name | VARCHAR(255) | |
| password_hash | VARCHAR(255) | |
| created_at | TIMESTAMP | DEFAULT NOW() |
| updated_at | TIMESTAMP | DEFAULT NOW() |

#### sessions
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| user_id | UUID | FOREIGN KEY |
| title | VARCHAR(500) | |
| status | VARCHAR(50) | NOT NULL |
| agent_states | JSONB | DEFAULT '{}' |
| context | JSONB | DEFAULT '{}' |
| created_at | TIMESTAMP | DEFAULT NOW() |
| updated_at | TIMESTAMP | DEFAULT NOW() |
| archived_at | TIMESTAMP | |

#### messages
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| session_id | UUID | FOREIGN KEY |
| role | VARCHAR(50) | NOT NULL |
| content | TEXT | NOT NULL |
| agent_type | VARCHAR(50) | |
| parent_id | UUID | FOREIGN KEY |
| metadata | JSONB | DEFAULT '{}' |
| created_at | TIMESTAMP | DEFAULT NOW() |

#### artifacts
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| session_id | UUID | FOREIGN KEY |
| message_id | UUID | FOREIGN KEY |
| type | VARCHAR(50) | NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| path | TEXT | NOT NULL |
| mime_type | VARCHAR(100) | |
| size_bytes | BIGINT | |
| checksum | VARCHAR(64) | |
| created_at | TIMESTAMP | DEFAULT NOW() |

#### plugins
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| name | VARCHAR(255) | UNIQUE, NOT NULL |
| version | VARCHAR(50) | NOT NULL |
| source | VARCHAR(500) | |
| enabled | BOOLEAN | DEFAULT true |
| config_schema | JSONB | |
| created_at | TIMESTAMP | DEFAULT NOW() |

---

## Folder Structure

```
nexusmind/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── api/v1/
│   │   ├── agents/
│   │   ├── orchestration/
│   │   ├── sandbox/
│   │   ├── memory/
│   │   ├── llm/
│   │   ├── mcp/
│   │   ├── plugins/
│   │   ├── db/
│   │   ├── streaming/
│   │   └── utils/
│   ├── tests/
│   ├── alembic/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── hooks/
│   │   ├── stores/
│   │   └── types/
│   ├── public/
│   ├── next.config.js
│   ├── package.json
│   └── Dockerfile
├── sandbox/
│   ├── Dockerfile
│   └── packages/
├── docs/
├── scripts/
├── docker-compose.yml
└── README.md
```

---

## Development Roadmap

### Phase 1: Foundation (Weeks 1-4)
- [x] Project scaffolding
- [x] FastAPI application structure
- [x] Database models and migrations
- [x] Session management API
- [x] Basic agent base class
- [x] LangGraph orchestration
- [x] Docker sandbox
- [x] WebSocket streaming
- [x] Basic authentication

### Phase 2: Multi-Agent System (Weeks 5-8)
- [x] All 7 agent implementations
- [x] Agent communication
- [x] Parallel execution
- [x] Task dependencies
- [x] Error handling

### Phase 3: Tools & Integrations (Weeks 9-12)
- [x] Terminal tool
- [x] File editor
- [x] Browser automation
- [x] Web search
- [x] GitHub integration
- [x] Memory system
- [x] LLM adapters

### Phase 4: Frontend (Weeks 13-16)
- [x] Next.js setup
- [x] Chat interface
- [x] Agent dashboard
- [x] Terminal component
- [x] File explorer
- [x] Settings pages

### Phase 5: Extensibility (Weeks 17-20)
- [x] Plugin architecture
- [x] MCP support
- [x] Plugin marketplace

### Phase 6: Production (Weeks 21-24)
- [x] Testing
- [x] Documentation
- [x] Deployment configs
- [x] CI/CD

---

## Acceptance Criteria

### Backend
- [x] All API endpoints return correct responses
- [x] Agents execute tasks correctly
- [x] Sandbox isolation prevents cross-contamination
- [x] Memory system stores and retrieves correctly
- [x] WebSocket streaming works in real-time
- [x] Plugin system loads plugins dynamically

### Frontend
- [x] User can create and manage sessions
- [x] Chat interface streams agent responses
- [x] Agent status updates in real-time
- [x] Terminal emulator works correctly
- [x] File explorer shows sandbox files
- [x] Settings pages save configurations

### Integration
- [x] Agents can use all available tools
- [x] LangGraph orchestrates agents correctly
- [x] Docker sandbox executes code securely
- [x] GitHub integration creates PRs
- [x] Memory persists across sessions

### Performance
- [x] API response time < 200ms (p95)
- [x] Sandbox allocation < 2 seconds
- [x] WebSocket latency < 100ms
- [x] Support 10+ concurrent sessions

### Security
- [x] Authentication required for all endpoints
- [x] Sandbox has no network access by default
- [x] File system access restricted to /workspace
- [x] Rate limiting prevents abuse
- [x] Input validation on all endpoints

---

## Design Decisions

1. **LangGraph for Orchestration**: Provides excellent support for complex workflows with cycles and conditional branching

2. **ChromaDB for Memory**: Simple deployment, good performance for our scale, easy migration path

3. **Docker Sandbox**: Complete isolation, industry standard, easy browser automation

4. **PostgreSQL**: Strong consistency, JSONB for flexibility, SQL for analytics

5. **WebSocket Primary**: Bidirectional communication, better for terminals

6. **Next.js App Router**: Server components, built-in streaming, modern patterns

---

## Status

**Current**: Architecture Complete  
**Next**: Implementation Phase 1

---

*Document Version: 1.0*  
*Last Updated: 2025-01-15*
