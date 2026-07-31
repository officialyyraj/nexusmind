# ADR-0002: Agent Framework Consolidation

## Status

Accepted

---

## Context

The `backend/app/agents/` directory houses the logic defining the system's agentic capabilities. An inspection of this directory reveals a consolidated framework. The file `app/agents/types.py` serves as the definitional source of truth, establishing the different agent roles via the `AgentType` enumeration.

The implementation of these roles is found in two key files:
1.  `app/agents/implementations.py`, which contains baseline agent classes.
2.  `app/agents/autonomous.py`, which provides more advanced, tool-using agent implementations.

The repository does not contain a directory structure that separates each agent type into its own file (e.g., `app/agents/types/`).

---

## Decision

The canonical agent framework is a consolidated, multi-faceted implementation centered around three key files:

-   `app/agents/types.py`: Provides the definitive enumeration of agent types (`AgentType`) and their corresponding capabilities. It is the architectural source of truth for agent roles.
-   `app/agents/implementations.py`: Contains the baseline class-based implementations for the agent types defined in `types.py`.
-   `app/agents/autonomous.py`: Contains advanced agent implementations that are capable of tool use, inheriting from an `AutonomousAgentMixin`.

This centralized approach is the accepted architecture. The conceptual agent roles (e.g., Planner, Coder) are realized as classes within these modules, not as individual files.

---

## Alternatives Considered

An alternative is a decoupled, file-based structure where each agent type has its own dedicated Python module within a directory like `app/agents/types/`.

**Decision:** Rejected for the current architecture.

**Reason:** The repository shows no evidence of this pattern. There is no `app/agents/types/` directory, and the existing agent logic is implemented centrally in `implementations.py` and `autonomous.py`.

---

## Consequences

### Positive

-   Centralizing agent logic in a few key files improves discoverability and simplifies cross-agent refactoring and comparison.
-   The `types.py` file provides a single, clear reference for all available agent roles and their intended capabilities.

### Negative

-   The parallel implementation patterns in `implementations.py` (basic) and `autonomous.py` (tool-using) may create confusion for developers regarding which to use or extend.
-   The consolidated files have the potential to grow large and become difficult to navigate as more agent logic is added.

---

## Evidence

-   `backend/app/agents/types.py`: This file defines the `AgentType` enum, which is consistently used across the codebase to identify agent roles.
-   `backend/app/agents/implementations.py`: This file contains agent classes such as `PlannerAgent` and `CoderAgent`, along with a factory function `create_agent`.
-   `backend/app/agents/autonomous.py`: This file contains enhanced agent classes like `ToolUsingPlannerAgent` and a corresponding `create_autonomous_agent` factory.
-   The file listing of `backend/app/agents/` confirms the presence of these files and the absence of a `types` subdirectory for individual agent files.

---

## Future Considerations

This ADR documents the current architecture only.

Future architectural changes require a new ADR.
