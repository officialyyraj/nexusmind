# Self-Improvement Loop Documentation

The self-improvement loop enables coding agents to iteratively generate, critique, and improve solutions until quality thresholds are met.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Self-Improvement Loop                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│   │ Generate │───▶│ Critique │───▶│ Improve  │            │
│   └──────────┘    └──────────┘    └──────────┘            │
│        │              │              │                     │
│        │              │              │                     │
│        └──────────────┴──────────────┘                     │
│                         │                                  │
│                    Loop until:                              │
│                    - Tests pass                             │
│                    - Quality threshold                      │
│                    - Max iterations                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Loop Phases

| Phase | Description |
|-------|-------------|
| `generate` | Create initial or improved solution |
| `critique` | Analyze solution, identify issues |
| `improve` | Apply suggestions, fix issues |

## Termination Conditions

| Condition | Description |
|-----------|-------------|
| `converged` | Quality threshold reached |
| `tests_passing` | All tests pass |
| `max_iterations` | Reached maximum iterations |
| `failed` | Unrecoverable error |

## Usage

### Basic Loop

```python
from app.agents.improvement import SelfImprovementLoop, ImprovementConfig

loop = SelfImprovementLoop(
    generator=my_generator,
    critic=my_critic,
    config=ImprovementConfig(max_iterations=5),
)

result = await loop.run(task="Implement sorting algorithm")
print(f"Quality: {result.latest_quality}")
print(f"Iterations: {result.current_iteration}")
```

### Custom Generator

```python
async def my_generator(task: str) -> str:
    """Generate solution based on task."""
    return f'''
def solution():
    """Solution for: {task}"""
    # TODO: implement
    pass
'''

loop = SelfImprovementLoop(generator=my_generator)
```

### Custom Critic

```python
from app.agents.improvement import CritiqueResult

def my_critic(solution: str) -> CritiqueResult:
    """Critique the solution."""
    issues = []
    suggestions = []
    score = 0.5
    
    # Check for function definition
    if "def " in solution:
        score += 0.2
        suggestions.append("Add type hints")
    
    # Check for documentation
    if '"""' in solution or "'''" in solution:
        score += 0.1
    else:
        issues.append("Missing docstrings")
    
    # Check for tests
    if "test" in solution.lower():
        score += 0.2
        suggestions.append("Add edge case tests")
    
    return CritiqueResult(
        issues=issues,
        suggestions=suggestions,
        quality_score=min(score, 1.0),
        passed_tests=["syntax"],
        failed_tests=[],
    )
```

## Configuration

```python
config = ImprovementConfig(
    max_iterations=10,       # Max iterations
    quality_threshold=0.9,   # Quality to stop at (0.0-1.0)
    test_timeout=60,        # Seconds to run tests
    auto_critique=True,      # Auto-critique solutions
    save_iterations=True,    # Save to ChromaDB
)
```

## Storage (ChromaDB)

### Save Iterations

```python
from app.agents.improvement import IterationStorage

storage = IterationStorage(persist_directory="/data/improvements")

# Save loop
storage.save_loop(result)

# Get loop
loop = storage.get_loop(loop_id)

# Search loops
loops = storage.search_loops(
    task_query="sorting",
    min_quality=0.8,
    status=ImprovementStatus.CONVERGED,
)

# Statistics
stats = storage.get_statistics()
print(f"Total loops: {stats['total_loops']}")
print(f"Total iterations: {stats['total_iterations']}")
```

## REST API

### Run Improvement Loop

```bash
POST /api/v1/improvement/run
Content-Type: application/json

{
    "task": "Implement binary search",
    "initial_solution": "def search(): pass",
    "max_iterations": 5,
    "quality_threshold": 0.9
}
```

### List Recent Loops

```bash
GET /api/v1/improvement/loops?limit=10
```

### Get Loop by ID

```bash
GET /api/v1/improvement/loops/{loop_id}
```

### Get Loop Iterations

```bash
GET /api/v1/improvement/loops/{loop_id}/iterations
```

### Search Loops

```bash
GET /api/v1/improvement/search?min_quality=0.8&status=converged
```

### Get Statistics

```bash
GET /api/v1/improvement/statistics
```

### Continue a Loop

```bash
POST /api/v1/improvement/loops/{loop_id}/continue
```

### Delete a Loop

```bash
DELETE /api/v1/improvement/loops/{loop_id}
```

## Progress Tracking

```python
result = await loop.run(
    task="Build feature",
    on_iteration=lambda iter: print(f"Iteration {iter.iteration}: {iter.phase}")
)

# Check progress
print(f"Progress: {result.quality_scores}")
print(f"Improved: {result.has_improved}")
```

## Iteration History

```python
for iteration in result.iterations:
    print(f"Iteration {iteration.iteration}")
    print(f"Phase: {iteration.phase.value}")
    print(f"Quality: {iteration.critique.quality_score if iteration.critique else 'N/A'}")
    print(f"Changes: {iteration.changes}")
    print(f"Duration: {iteration.execution_time:.2f}s")
```

## Integration with Coder Agent

```python
from app.agents.improvement import SelfImprovementLoop
from app.agents.improvement.schemas import ImprovementConfig

loop = SelfImprovementLoop(
    generator=coder.generate,
    critic=coder.critique,
    config=ImprovementConfig(max_iterations=10),
)

# Run loop for a coding task
result = await loop.run(
    task="Create a REST API for user management",
    initial_solution=coder.get_scaffold(),
)

# Use final solution
coder.write_file(result.final_solution)
```

## Mock Implementations

For testing and development:

```python
from app.agents.improvement import mock_generator, mock_critic

loop = SelfImprovementLoop(
    generator=mock_generator,
    critic=mock_critic,
)

result = await loop.run(task="Test task")
```

## Best Practices

1. **Set realistic thresholds**: Quality 1.0 is often impossible
2. **Limit iterations**: Set max_iterations to avoid infinite loops
3. **Provide good critics**: Better critique = better improvements
4. **Save iterations**: Enable debugging and analysis
5. **Monitor progress**: Use callbacks for real-time updates

## Example: Complete Workflow

```python
from app.agents.improvement import SelfImprovementLoop, ImprovementConfig

async def main():
    # Create loop
    loop = SelfImprovementLoop(
        generator=my_generator,
        critic=my_critic,
        config=ImprovementConfig(
            max_iterations=10,
            quality_threshold=0.95,
        ),
    )
    
    # Run with progress tracking
    iterations = []
    
    def track(iteration):
        iterations.append(iteration)
        print(f"[{iteration.phase.value}] Quality: {iteration.critique.quality_score if iteration.critique else 'N/A'}")
    
    result = await loop.run(
        task="Implement authentication system",
        on_iteration=track,
    )
    
    # Report
    print(f"\nCompleted: {result.status.value}")
    print(f"Iterations: {result.current_iteration}")
    print(f"Final Quality: {result.latest_quality}")
    print(f"Improved: {result.has_improved}")
    
    # Save final solution
    with open("solution.py", "w") as f:
        f.write(result.final_solution)

# Run
asyncio.run(main())
```
