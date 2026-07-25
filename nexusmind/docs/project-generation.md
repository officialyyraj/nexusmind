# Project Generation Documentation

Autonomous project generation from natural language prompts.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Autonomous Project Generator                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Planner    │───▶│   Analyzer   │───▶│   Generator  │ │
│  │  (Prompt)    │    │ (Tech Stack) │    │   (Files)    │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│          │                  │                  │            │
│          ▼                  ▼                  ▼            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  Milestones  │    │   Tasks      │    │  Code Gen    │ │
│  │  & Roadmap   │    │ & Assign     │    │  + Tests     │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Project Types

| Type | Description |
|------|-------------|
| `web_app` | Web application |
| `api_service` | REST API service |
| `cli_tool` | Command-line tool |
| `library` | Library/package |
| `microservice` | Microservice |
| `fullstack_app` | Full-stack application |
| `data_pipeline` | Data pipeline |

## Supported Tech Stacks

### Languages
- Python
- TypeScript/JavaScript
- Go
- Rust
- Java
- Ruby

### Frameworks
- Python: FastAPI, Flask, Django
- TypeScript: Express, Next.js, NestJS
- Go: Gin
- Rust: Actix

### Databases
- PostgreSQL
- MySQL
- MongoDB
- SQLite
- Redis

## Usage

### Basic Generation

```python
from app.orchestration import ProjectGenerator, GenerationConfig

generator = ProjectGenerator()

config = GenerationConfig(
    project_name="My Project",
    project_type=ProjectType.WEB_APP,
    description="A FastAPI application",
)

result = await generator.generate(config)

print(f"Status: {result.status}")
print(f"Files: {len(result.generated_files)}")
```

### Streaming Generation

```python
async def on_progress(progress, message):
    print(f"[{progress}%] {message}")

result = await generator.generate(config, progress_callback=on_progress)
```

### Generate Only Plan

```python
plan = await generator.generate_plan(config)

print(f"Milestones: {len(plan.milestones)}")
print(f"Tasks: {len(plan.tasks)}")
print(f"Dependencies: {len(plan.dependencies)}")
```

## Generated Outputs

### Project Structure
```
project_name/
├── app/                  # Source code
│   ├── api/             # API routes
│   ├── core/            # Core logic
│   ├── models/          # Data models
│   └── services/        # Business logic
├── tests/               # Test files
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose
├── README.md           # Documentation
├── requirements.txt     # Dependencies
├── .gitignore          # Git ignore
└── .github/
    └── workflows/
        └── ci.yml      # CI pipeline
```

### Generated Files

| File | Description |
|------|-------------|
| `main.py` / `src/index.ts` | Main application entry |
| `requirements.txt` / `package.json` | Dependencies |
| `config.py` / `config.yaml` | Configuration |
| `README.md` | Project documentation |
| `.gitignore` | Git ignore rules |
| `Dockerfile` | Container definition |
| `docker-compose.yml` | Multi-container setup |
| `.github/workflows/ci.yml` | GitHub Actions CI |
| `tests/test_main.py` | Unit tests |

## Configuration

### GenerationConfig

```python
config = GenerationConfig(
    project_name="My Project",
    project_type=ProjectType.WEB_APP,
    description="A FastAPI web application",
    tech_stack=TechStack(
        language="python",
        framework="fastapi",
        database="postgresql",
    ),
    auto_assign_agents=True,    # Assign tasks to agents
    generate_docker=True,       # Generate Dockerfile
    generate_readme=True,       # Generate README.md
    generate_tests=True,        # Generate test files
    generate_ci=True,           # Generate CI pipeline
    output_directory="/tmp/projects",
)
```

### TechStack

```python
stack = TechStack(
    language="python",
    framework="fastapi",
    backend="fastapi",
    frontend="react",
    database="postgresql",
    cache="redis",
    container="docker",
    testing=["pytest", "pytest-cov"],
    ci_cd=["github-actions"],
    cloud="aws",
)
```

## REST API

### Generate Project

```bash
POST /api/v1/projects/generate
Content-Type: application/json

{
    "project_name": "My FastAPI App",
    "project_type": "web_app",
    "description": "A FastAPI application with PostgreSQL",
    "generate_docker": true,
    "generate_tests": true
}
```

### Generate with Streaming

```bash
POST /api/v1/projects/generate/stream
```

Returns Server-Sent Events with progress updates.

### Get Generation Status

```bash
GET /api/v1/projects/{generation_id}
```

### Get Project Plan

```bash
GET /api/v1/projects/{generation_id}/plan
```

### List Generated Files

```bash
GET /api/v1/projects/{generation_id}/files
```

### Get File Content

```bash
GET /api/v1/projects/{generation_id}/files/path/to/file.py
```

### Create Plan Only

```bash
POST /api/v1/projects/plan
```

### List All Generations

```bash
GET /api/v1/projects/?status=completed&limit=20
```

## Agent Assignment

Tasks are automatically assigned to agents based on type:

| Task | Assigned Agent |
|------|---------------|
| Initialize project | Coder |
| Configure environment | Coder |
| Implement models | Coder |
| Implement API | Coder |
| Implement services | Coder |
| Write tests | Tester |
| Write documentation | Documentation |

## Planning

### Milestones

Projects are divided into milestones:

1. **Project Setup** - Initialize structure, configure tools
2. **Core Implementation** - Implement main features
3. **Testing & Documentation** - Write tests and docs
4. **Deployment** - Docker and CI/CD setup

### Tasks

Each milestone contains tasks with:
- Title and description
- Priority (1-5)
- Estimated hours
- Assigned agent
- Files to create/modify
- Dependencies

## Example: Complete Workflow

```python
from app.orchestration import ProjectGenerator, GenerationConfig, ProjectType

async def main():
    generator = ProjectGenerator()
    
    config = GenerationConfig(
        project_name="E-commerce API",
        project_type=ProjectType.API_SERVICE,
        description="""
            Build a REST API for an e-commerce platform.
            Use FastAPI with PostgreSQL and Redis.
            Include endpoints for products, orders, and users.
        """,
        output_directory="/workspace/projects",
        generate_docker=True,
        generate_tests=True,
        generate_ci=True,
    )
    
    # Generate with progress tracking
    async def progress(percent, message):
        print(f"[{percent}%] {message}")
    
    result = await generator.generate(config, progress_callback=progress)
    
    if result.status == "completed":
        print(f"\nGenerated {len(result.generated_files)} files")
        print(f"Project: {result.plan.project_name}")
        print(f"Milestones: {len(result.plan.milestones)}")
        print(f"Tasks: {len(result.plan.tasks)}")
```

## CLI Usage

```bash
# Generate a project
curl -X POST http://localhost:8000/api/v1/projects/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "My API",
    "project_type": "api_service",
    "description": "A REST API service"
  }'

# Stream generation progress
curl -N -X POST http://localhost:8000/api/v1/projects/generate/stream \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "My API",
    "project_type": "api_service"
  }'
```

## Templates

### Python FastAPI

```python
# Auto-generated structure
app/
├── __init__.py
├── main.py          # FastAPI app
├── api/
├── core/
├── models/
├── schemas/
└── services/
```

### TypeScript Express

```typescript
// Auto-generated structure
src/
├── index.ts         # Express app
├── routes/
├── controllers/
└── models/
```

### Go Gin

```go
// Auto-generated structure
cmd/
└── main.go         # Entry point
internal/
├── handlers/
└── models/
pkg/
```

## Best Practices

1. **Be specific in descriptions** - More detail = better generation
2. **Specify tech stack** - Or let the system infer from keywords
3. **Include database** - Specify if needed
4. **Enable all generators** - Docker, tests, CI are important
5. **Review generated plan** - Check milestones and tasks before generation

## Error Handling

```python
try:
    result = await generator.generate(config)
    if result.status == "failed":
        print(f"Errors: {result.errors}")
except Exception as e:
    print(f"Error: {e}")
```
