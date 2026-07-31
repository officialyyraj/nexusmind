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
│   │   │   ├── types.py              # AgentType enum
│   │   │   ├── implementations.py    # Baseline agent implementations
│   │   │   ├── autonomous.py         # Advanced, tool-using agents
│   │   │   ├── execution_engine.py   # Agent tool invocation logic
│   │   │   └── reasoning_loop.py     # Core agent reasoning cycle
│   │   │
│   │   ├── orchestration/            # Orchestration layer
│   │   │   ├── executor.py           # Sequential agent executor
│   │   │   ├── supervisor.py         # Complex multi-agent coordinator
│   │   │   └── project_generator.py  # Autonomous project generation
│   │   │
│   │   ├── sandbox/                  # Docker sandbox
│   │   │   └── docker.py             # Docker operations
│   │   │
│   │   ├── memory/                   # Memory system
│   │   │   └── chromadb.py           # ChromaDB integration
│   │   │
│   │   ├── llm/                      # LLM integration
│   │   │   ├── routing/              # Intelligent model routing
│   │   │   └── byok/                 # Bring-Your-Own-Key service
│   │   │
│   │   ├── mcp/                      # MCP support
│   │   │   ├── manager.py            # Manages external tool servers
│   │   │   ├── client.py             # Client for a single tool server
│   │   │   └── registry.py           # Central tool registry
│   │   │
│   │   ├── plugins/                  # Plugin system
│   │   │   ├── manager.py            # Plugin lifecycle
│   │   │   ├── loader.py             # Plugin discovery
│   │   │   └── registry.py           # Plugin registry
│   │   │
│   │   ├── db/                       # Database layer
│   │   │   ├── database.py           # Database connection
│   │   │   ├── session.py            # Session models
│   │   │   ├── message.py            # Message models
│   │   │   └── artifact.py           # Artifact models
│   │   │
│   │   ├── streaming/                # Real-time streaming
│   │   │   ├── ws_manager.py         # WebSocket manager
│   │   │   ├── sse.py                # SSE handler
│   │   │   └── events.py             # Event definitions
│   │   │
│   │   └── utils/                    # Utilities
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
