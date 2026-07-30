# NexusMind - Project Structure

```
nexusmind/
├── backend/                          # FastAPI backend application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI application entry
│   │   ├── config.py                 # Configuration management
│   │   ├── dependencies.py           # Dependency injection
│   │   │
│   │   ├── api/                      # API endpoints
│   │   │   ├── v1/
│   │   │   │   ├── router.py         # API router aggregator
│   │   │   │   ├── sessions.py       # Session management
│   │   │   │   ├── agents.py         # Agent control
│   │   │   │   ├── sandbox.py        # Sandbox management
│   │   │   │   ├── plugins.py        # Plugin management
│   │   │   │   ├── memory.py         # Memory/retrieval
│   │   │   │   └── webhooks.py       # Webhook endpoints
│   │   │   └── ws.py                 # WebSocket handlers
│   │   │
│   │   ├── agents/                   # Agent system
│   │   │   ├── base.py               # Base agent class
│   │   │   ├── registry.py           # Agent registry
│   │   │   ├── supervisor.py        # Supervisor agent
│   │   │   ├── types/               # Agent implementations
│   │   │   │   ├── planner.py
│   │   │   │   ├── researcher.py
│   │   │   │   ├── coder.py
│   │   │   │   ├── reviewer.py
│   │   │   │   ├── tester.py
│   │   │   │   ├── documentation.py
│   │   │   │   └── manager.py
│   │   │   └── tools/                # Agent tools
│   │   │       ├── terminal.py
│   │   │       ├── browser.py
│   │   │       ├── file_editor.py
│   │   │       ├── search.py
│   │   │       └── github.py
│   │   │
│   │   ├── orchestration/             # LangGraph orchestration
│   │   │   ├── graph.py              # Graph definition
│   │   │   ├── state.py              # State schema
│   │   │   ├── nodes.py              # Graph nodes
│   │   │   ├── edges.py              # Conditional edges
│   │   │   └── executor.py           # Graph executor
│   │   │
│   │   ├── sandbox/                  # Docker sandbox
│   │   │   ├── manager.py            # Sandbox lifecycle
│   │   │   ├── docker.py             # Docker operations
│   │   │   ├── executor.py           # Code execution
│   │   │   ├── terminal.py          # PTY/shell interface
│   │   │   └── browser.py          # Browser automation
│   │   │
│   │   ├── memory/                   # Memory system
│   │   │   ├── chromadb.py           # ChromaDB integration
│   │   │   ├── vector_store.py       # Vector operations
│   │   │   ├── semantic_cache.py     # Semantic caching
│   │   │   └── session_memory.py     # Session context
│   │   │
│   │   ├── llm/                      # LLM integration
│   │   │   ├── factory.py            # LLM provider factory
│   │   │   ├── ollama.py             # Ollama adapter
│   │   │   ├── openai.py            # OpenAI adapter
│   │   │   └── base.py              # Base LLM interface
│   │   │
│   │   ├── mcp/                      # MCP support
│   │   │   ├── server.py             # MCP server
│   │   │   ├── protocol.py           # Protocol handlers
│   │   │   └── tools.py              # MCP tool adapters
│   │   │
│   │   ├── plugins/                  # Plugin system
│   │   │   ├── manager.py            # Plugin lifecycle
│   │   │   ├── loader.py             # Plugin discovery
│   │   │   ├── registry.py           # Plugin registry
│   │   │   └── templates/           # Plugin templates
│   │   │
│   │   ├── db/                       # Database layer
│   │   │   ├── database.py           # Database connection
│   │   │   ├── session.py           # Session models
│   │   │   ├── message.py           # Message models
│   │   │   ├── artifact.py          # Artifact models
│   │   │   └── migrations/          # Alembic migrations
│   │   │
│   │   ├── streaming/                # Real-time streaming
│   │   │   ├── ws_manager.py         # WebSocket manager
│   │   │   ├── sse.py               # SSE handler
│   │   │   └── events.py           # Event definitions
│   │   │
│   │   └── utils/                    # Utilities
│   │       ├── rate_limiter.py
│   │       ├── logger.py
│   │       └── security.py
│   │
│   ├── tests/                        # Test suite
│   │   ├── conftest.py
│   │   ├── api/
│   │   ├── agents/
│   │   ├── orchestration/
│   │   └── integration/
│   │
│   ├── alembic/                      # Database migrations
│   │
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                         # Next.js frontend
│   ├── src/
│   │   ├── app/                     # App Router pages
│   │   │   ├── (auth)/             # Auth routes
│   │   │   │   ├── login/
│   │   │   │   └── register/
│   │   │   ├── (dashboard)/        # Dashboard routes
│   │   │   │   ├── sessions/
│   │   │   │   │   └── [id]/
│   │   │   │   ├── settings/
│   │   │   │   │   ├── agents/
│   │   │   │   │   ├── plugins/
│   │   │   │   │   └── llm/
│   │   │   │   └── marketplace/
│   │   │   └── api/trpc/           # tRPC API routes
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn/ui components
│   │   │   ├── chat/              # Chat interface
│   │   │   ├── session/           # Session management
│   │   │   ├── agent/             # Agent UI
│   │   │   ├── terminal/           # Terminal emulator
│   │   │   ├── file-explorer/     # File browser
│   │   │   └── logs/              # Log viewer
│   │   │
│   │   ├── lib/                    # Utilities
│   │   │   └── api/               # API clients
│   │   │
│   │   ├── hooks/                  # React hooks
│   │   ├── stores/                 # Zustand stores
│   │   ├── types/                 # TypeScript types
│   │   └── styles/                # Global styles
│   │
│   ├── public/                     # Static assets
│   ├── Dockerfile
│   ├── next.config.js
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── sandbox/                         # Docker sandbox environment
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── playwright.config.js
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
│
├── docs/                            # Documentation
│   ├── architecture/
│   ├── api/
│   └── plugins/
│
├── scripts/                         # Build/deploy scripts
│   ├── dev.sh
│   ├── build.sh
│   ├── deploy.sh
│   ├── test.sh
│   ├── lint.sh
│   └── format.sh
│
├── .github/
│   └── workflows/                  # CI/CD pipelines
│
├── docker-compose.yml              # Local development
├── docker-compose.prod.yml         # Production deployment
├── Makefile                        # Build commands
├── README.md
└── .env.example
```

## File Count Summary

| Directory | Files | Description |
|-----------|-------|-------------|
| `backend/app/` | 50 | Backend application modules |
| `backend/tests/` | 6 | Backend test suite |
| `frontend/src/` | 50+ | Frontend components & pages |
| `sandbox/` | 10+ | Sandbox configuration |
| `docs/` | 8 | Documentation files |
| `scripts/` | 6 | Build scripts |
| **Total** | **130+** | All project files |

## Quick Start Commands

```bash
# Development
make dev              # Start all services
make dev-backend      # Backend only
make dev-frontend     # Frontend only

# Build
make build           # Build all containers
make build-backend   # Backend only
make build-frontend  # Frontend only

# Testing
make test           # Run all tests
make test-backend   # Backend tests
make test-frontend  # Frontend tests
make lint           # Run linters

# Production
make deploy         # Deploy to production
```
