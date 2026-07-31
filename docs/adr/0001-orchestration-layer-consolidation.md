# ADR-0001: Orchestration Layer Consolidation

## Status

Accepted

---

## Context

The `backend/app/orchestration/` directory contains several Python modules that collectively manage task execution and control flow. The repository's structure points to an imperative, multi-faceted orchestration model rather than a single, monolithic one. The key modules are `executor.py`, `project_generator.py`, and `supervisor.py`. Inspection of the directory shows no evidence of a formal graph-based orchestration system (e.g., no files such as `graph.py` or `nodes.py` exist).

---

## Decision

The canonical implementation for the orchestration layer is a multi-part, imperative system distributed across three specialized modules:

-   `app/orchestration/executor.py`: Provides a direct, executor-based pattern for sequential agent workflows.
-   `app/orchestration/project_generator.py`: Implements a dedicated workflow for autonomously generating complete software projects from high-level specifications.
-   `app/orchestration/supervisor.py`: Manages the coordination of complex, asynchronous, and interdependent tasks across multiple agents.

This set of modules constitutes the official architectural pattern for orchestration.

---

## Alternatives Considered

An alternative is a graph-based orchestration model, where execution flow is defined as a directed acyclic graph (DAG) of nodes and edges.

**Decision:** Rejected for the current architecture.

**Reason:** The repository contains no implementation evidence of a graph-based system. The existing orchestration logic is found exclusively within the `executor.py`, `project_generator.py`, and `supervisor.py` modules, which follow an imperative pattern.

---

## Consequences

### Positive

-   The documented architecture accurately reflects the implemented code, providing clarity to developers.
-   The separation of concerns allows for specialized and focused logic: `executor.py` for simple sequences, `supervisor.py` for complex coordination, and `project_generator.py` for project scaffolding.

### Negative

-   The existence of three distinct orchestration modules may increase the initial cognitive load for developers attempting to understand the system's overall control flow.
-   Coordination between the different orchestration modules is not explicitly defined, which may lead to ambiguity.

---

## Evidence

-   `backend/app/orchestration/executor.py`: This file contains the `ProductionExecutor` class, which executes a linear sequence of agent tasks.
-   `backend/app/orchestration/project_generator.py`: This file contains the `ProjectGenerator` class, which implements the logic for scaffolding new projects.
-   `backend/app/orchestration/supervisor.py`: This file contains the `Supervisor` class, responsible for managing and dispatching asynchronous agent tasks with dependencies.
-   The file listing of the `backend/app/orchestration/` directory confirms the presence of these files and the absence of any files related to a graph-based framework.

---

## Future Considerations

This ADR documents the current architecture only.

Future architectural changes require a new ADR.
