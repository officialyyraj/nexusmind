# Advanced LangGraph Workflow Documentation

The advanced workflow system provides parallel execution, dependency management, failure recovery, and progress tracking for multi-agent orchestration.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Planner                                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
    ┌──────────────────────────────────────────────────────┐
    │  Research  │  Backend  │  Frontend  │  Database  │ Docs │
    │    ██      │    ██     │     ██     │     ██    │  ██  │
    └──────────────────────────────────────────────────────┘
                          │
                          ▼
                     Reviewer
                          │
                          ▼
                       Tester
                          │
                          ▼
                       Manager
```

## Workflow Phases

| Phase | Agent | Description |
|-------|-------|-------------|
| `planning` | PlannerAgent | Decompose task into structured plan |
| `research` | ResearcherAgent | Gather information |
| `backend` | CoderAgent | Implement backend code |
| `frontend` | CoderAgent | Implement frontend code |
| `database` | CoderAgent | Implement database layer |
| `documentation` | DocumentationAgent | Generate documentation |
| `review` | ReviewerAgent | Review all implementations |
| `test` | TesterAgent | Run tests |
| `manager` | ManagerAgent | Final summary and reporting |

## Phase Dependencies

```
planning → research, backend, frontend, database, documentation (parallel)
       ↓
     review
       ↓
     test
       ↓
    manager
```

## Usage

### Basic Workflow

```python
from app.agents.advanced_workflow import AdvancedAgentWorkflow, PhaseType

# Create workflow with all phases
workflow = AdvancedAgentWorkflow()

# Run workflow
result, progress = await workflow.run(
    task="Build a complete web application",
    session_id="session-123",
    context={"requirements": {...}},
)

print(f"Progress: {progress.progress_percent}%")
print(f"Completed phases: {progress.completed_phases}")
```

### Custom Phases

```python
# Run only specific phases
workflow = AdvancedAgentWorkflow(
    include_phases=[
        PhaseType.PLANNING,
        PhaseType.BACKEND,
        PhaseType.REVIEW,
    ]
)
```

### With Failure Recovery

```python
# Run with automatic retries
result, progress = await workflow.run_with_recovery(
    task="Build API service",
    session_id="session-123",
)
```

## Progress Tracking

### WorkflowProgress

```python
progress = WorkflowProgress(
    workflow_id="wf-123",
    task="Build app",
    total_phases=9,
    completed_phases=5,
    current_phase=PhaseType.REVIEW,
    phase_results={...},
    errors=[],
)
```

### Properties

```python
# Progress percentage
print(f"{progress.progress_percent:.1f}% complete")

# Check completion
if progress.is_complete:
    print("Workflow finished!")

# Get failed phases
failed = progress.get_failed_phases()
print(f"Failed: {[p.value for p in failed]}")
```

### Phase Results

```python
for phase, result in progress.phase_results.items():
    print(f"{phase.value}: {result.status.value}")
    if result.error:
        print(f"  Error: {result.error}")
    print(f"  Duration: {result.duration:.2f}s")
```

## Parallel Execution

### ParallelTaskExecutor

Execute multiple tasks concurrently with dependency management:

```python
from app.agents.advanced_workflow import ParallelTaskExecutor

executor = ParallelTaskExecutor(max_concurrent=5)

tasks = [
    {"id": "task1", "func": async_func1},
    {"id": "task2", "func": async_func2},
    {"id": "task3", "func": async_func3},
]

# task3 depends on task1 and task2
dependencies = {
    "task3": ["task1", "task2"],
}

results = await executor.execute(tasks, dependencies)
```

## Configuration

### PhaseConfig

Configure individual phase behavior:

```python
from app.agents.advanced_workflow import PhaseConfig, PhaseType

config = PhaseConfig(
    phase=PhaseType.BACKEND,
    agent_type=AgentType.CODER,
    required=True,
    max_retries=3,
    retry_delay=1.0,
    timeout=300.0,
    depends_on=[PhaseType.PLANNING],
    parallel_with=[PhaseType.FRONTEND, PhaseType.DATABASE],
)
```

## PhaseResult

Each phase returns a PhaseResult:

```python
@dataclass
class PhaseResult:
    phase: PhaseType
    status: TaskStatus  # pending, running, completed, failed, retrying
    result: dict[str, Any]
    error: str | None
    retry_count: int
    started_at: datetime
    completed_at: datetime
    duration: float  # seconds
```

## TaskStatus

| Status | Description |
|--------|-------------|
| `pending` | Phase not yet started |
| `running` | Phase currently executing |
| `completed` | Phase finished successfully |
| `failed` | Phase encountered an error |
| `retrying` | Phase is being retried |
| `cancelled` | Phase was cancelled |

## Advanced Usage

### Task Priorities

```python
result, progress = await workflow.run(
    task="Build app",
    session_id="session-123",
    priorities={
        "backend": 1,
        "frontend": 2,  # Higher priority
        "database": 1,
    },
)
```

### Custom Dependencies

```python
result, progress = await workflow.run(
    task="Build app",
    session_id="session-123",
    dependencies={
        "backend": ["research"],  # Backend needs research
        "frontend": ["research"],  # Frontend needs research
    },
)
```

### Custom Workflow Graph

```python
from langgraph.graph import END, StateGraph

workflow = create_advanced_workflow([
    PhaseType.PLANNING,
    PhaseType.BACKEND,
    PhaseType.FRONTEND,
    PhaseType.REVIEW,
])
```

## API Reference

### AdvancedAgentWorkflow

| Method | Description |
|--------|-------------|
| `run(task, session_id, context, priorities, dependencies)` | Execute workflow |
| `run_with_recovery(task, session_id, context)` | Execute with auto-retry |
| `get_progress(workflow_id)` | Get workflow progress |
| `list_active_workflows()` | List running workflows |

### ParallelTaskExecutor

| Method | Description |
|--------|-------------|
| `execute(tasks, dependencies)` | Execute tasks in parallel |

### create_advanced_workflow

| Parameter | Type | Description |
|-----------|------|-------------|
| `include_phases` | `list[PhaseType]` | Phases to include |

## Integration

### With Existing Agents

The workflow maintains compatibility with existing agents:

```python
from app.agents.implementations import (
    PlannerAgent,
    CoderAgent,
    ResearcherAgent,
)

# Agents are called with their standard interface
agent = PlannerAgent(session_id="session-123")
result = await agent.execute(state)
```

### With LangSmith (Optional)

Enable LangSmith tracing:

```python
import os
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "your-api-key"

# Workflow will automatically use LangSmith
workflow = AdvancedAgentWorkflow()
```

## Error Handling

### Automatic Retries

```python
workflow = AdvancedAgentWorkflow(
    max_retries=3,
    retry_delay=1.0,
)

result, progress = await workflow.run_with_recovery(task, session_id)
```

### Manual Recovery

```python
result, progress = await workflow.run(task, session_id)

failed = progress.get_failed_phases()
if failed:
    # Manually retry failed phases
    for phase in failed:
        print(f"Retry {phase.value}")
```

## Best Practices

1. **Always check progress**: Monitor `progress.progress_percent` during execution
2. **Handle failures**: Check `progress.get_failed_phases()` after completion
3. **Use timeouts**: Set appropriate timeouts for long-running phases
4. **Limit concurrency**: Don't run too many parallel tasks (max 5-10)
5. **Clear dependencies**: Define dependencies to avoid race conditions
