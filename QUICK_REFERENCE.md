# NexusMind - Developer Quick Reference

## Project Overview

NexusMind is an autonomous multi-agent AI platform that orchestrates specialized agents to complete complex software engineering tasks.

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or Docker)
- Redis 7+

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/nexusmind.git
cd nexusmind

# Backend setup
cd backend
cp .env.example .env
docker-compose up -d db redis
pip install -r requirements.txt
alembic upgrade head

# Frontend setup
cd ../frontend
npm install

# Start development
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

### Environment Variables

```bash
# Backend (.env)
DATABASE_URL=postgresql://user:pass@localhost:5432/nexusmind
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_API_KEY=sk-...

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## API Reference

### Sessions

```bash
# Create session
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title": "Build API", "context": {"language": "python"}}'

# Execute task
curl -X POST http://localhost:8000/api/v1/sessions/{id}/execute \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "task": "Create REST API for user management",
    "goals": ["CRUD endpoints", "Authentication"],
    "constraints": ["Use FastAPI", "Include tests"]
  }'

# List sessions
curl http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN"

# Get session
curl http://localhost:8000/api/v1/sessions/{id} \
  -H "Authorization: Bearer $TOKEN"
```

### WebSocket Streaming

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/sessions/{session_id}');

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  switch(msg.type) {
    case 'log_entry': console.log(msg.data); break;
    case 'agent_status': updateAgentUI(msg.data); break;
    case 'message_created': appendMessage(msg.data); break;
  }
};

// Send message
ws.send(JSON.stringify({
  type: 'user_message',
  content: 'Create a calculator app'
}));
```

### Messages

```bash
# Send message
curl -X POST http://localhost:8000/api/v1/sessions/{id}/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"content": "Build a todo app", "role": "user"}'

# List messages
curl http://localhost:8000/api/v1/sessions/{id}/messages \
  -H "Authorization: Bearer $TOKEN"
```

### Memory

```bash
# Search memory
curl -X POST http://localhost:8000/api/v1/memory/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "authentication patterns", "limit": 5}'

# Store memory
curl -X POST http://localhost:8000/api/v1/memory/store \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"content": "JWT token validation", "metadata": {"type": "pattern"}}'
```

---

## Agent Types

| Agent | Purpose | Key Methods |
|-------|---------|-------------|
| `planner` | Task decomposition | `plan()`, `create_roadmap()` |
| `researcher` | Context gathering | `search()`, `gather_context()` |
| `coder` | Code implementation | `implement()`, `modify()` |
| `reviewer` | Code quality | `review()`, `suggest_fixes()` |
| `tester` | Validation | `test()`, `validate()` |
| `documentation` | Doc generation | `document()`, `generate_md()` |
| `manager` | Coordination | `coordinate()`, `delegate()` |

---

## Message Format

```python
from nexusmind.agents.messages import Message, MessageType, Priority

# Create task message
msg = Message(
    type=MessageType.TASK,
    session_id="sess_123",
    to_agent="coder",
    content={
        "task_id": "task_456",
        "description": "Create user model",
        "goals": ["Define schema", "Add validation"],
        "constraints": ["Use Pydantic", "Include typing"]
    },
    priority=Priority.HIGH
)
```

---

## Tool Registry

| Tool | Capabilities |
|------|-------------|
| `terminal` | Execute shell commands |
| `file_editor` | Read/write/edit files |
| `browser` | Playwright automation |
| `search` | Web search via Tavily/SerpAPI |
| `github` | PR creation, reviews, issues |
| `git` | Version control operations |
| `docker` | Container management |
| `memory` | Semantic search & storage |

---

## Plugin Development

```python
# plugins/my-plugin/plugin.json
{
    "name": "my-plugin",
    "version": "1.0.0",
    "entry_point": "plugins:MyPlugin",
    "tools": [{"name": "custom_tool", "description": "..."}]
}

# plugins/my-plugin/__init__.py
from nexusmind.plugins.base import Plugin

class MyPlugin(Plugin):
    async def initialize(self):
        self.register_tool("custom_tool", self.custom_tool)
    
    async def custom_tool(self, params):
        # Implementation
        return {"result": "success"}
```

---

## Database Models

### Session
```python
class Session:
    id: UUID
    title: str
    status: SessionStatus
    agent_states: dict
    context: dict
    created_at: datetime
```

### Message
```python
class Message:
    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    agent_type: Optional[AgentType]
    metadata: dict
```

---

## LangGraph Integration

```python
from nexusmind.orchestration import create_graph

# Create and compile graph
graph = create_graph()

# Execute with streaming
async for chunk in graph.astream(
    {"task": "Build API", "session_id": "123"},
    stream_mode="updates"
):
    print(chunk)
```

---

## Docker Sandbox

```bash
# Allocate sandbox
curl -X POST http://localhost:8000/api/v1/sandbox/allocate \
  -H "Authorization: Bearer $TOKEN"

# Execute code
curl -X POST http://localhost:8000/api/v1/sandbox/{id}/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print('hello')", "language": "python"}'

# Terminal command
curl -X POST http://localhost:8000/api/v1/sandbox/{id}/terminal \
  -H "Content-Type: application/json" \
  -d '{"command": "ls -la"}'
```

---

## Frontend State

```typescript
// stores/sessionStore.ts
import { create } from 'zustand';

interface SessionStore {
  sessions: Session[];
  currentSession: Session | null;
  addMessage: (msg: Message) => void;
  updateStatus: (status: string) => void;
}

export const useSessionStore = create<SessionStore>((set) => ({
  sessions: [],
  currentSession: null,
  addMessage: (msg) => set((s) => ({
    currentSession: {
      ...s.currentSession!,
      messages: [...s.currentSession!.messages, msg]
    }
  })),
  updateStatus: (status) => set((s) => ({
    currentSession: {...s.currentSession!, status}
  }))
}));
```

---

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test

# Integration tests
cd backend
pytest tests/integration/ -v

# E2E tests
cd frontend
npx playwright test
```

---

## Deployment

### Development
```bash
docker-compose up
```

### Production
```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Deploy
kubectl apply -f k8s/

# Scale
kubectl scale deployment api --replicas=3
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Sandbox timeout | Increase timeout in config or optimize code |
| LLM rate limit | Add rate limiting or use local Ollama |
| Memory errors | Clear ChromaDB or increase container memory |
| WebSocket disconnect | Check nginx proxy timeouts |
| Agent loops | Implement cycle detection in graph |

---

## Key Files

```
nexusmind/
├── backend/app/
│   ├── main.py           # FastAPI app entry
│   ├── api/v1/           # API routes
│   ├── agents/           # Agent implementations
│   ├── orchestration/    # LangGraph setup
│   ├── sandbox/          # Docker execution
│   └── memory/           # ChromaDB integration
│
├── frontend/src/
│   ├── app/              # Next.js pages
│   ├── components/       # React components
│   ├── stores/           # Zustand stores
│   └── lib/              # API clients
│
└── sandbox/
    └── Dockerfile         # Execution environment
```
