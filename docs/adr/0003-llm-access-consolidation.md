# ADR-0003: LLM Access Consolidation

## Status

Accepted

---

## Context

The repository's architecture for Large Language Model (LLM) access is implemented within the `backend/app/llm/` directory and its sub-modules. An inspection of these files reveals a sophisticated, dual-system approach rather than a simple, singular one. The implementation is split between two complementary functionalities: dynamic model routing and user-specific provider configurations. There is no evidence in the repository of a classic factory pattern for instantiating LLM providers (e.g., no `factory.py` or individual provider files at the top level of `app/llm/`).

---

## Decision

The canonical implementation for LLM provider access is a dual system that combines criteria-based routing with a "Bring Your Own Key" (BYOK) model. The two key components of this architecture are:

-   `app/llm/routing/`: This module contains the logic for an intelligent routing system that selects the appropriate LLM provider based on defined criteria, such as cost, performance, or capabilities.
-   `app/llm/byok/`: This module implements the "Bring Your Own Key" functionality, which allows authenticated users to configure and use their own LLM provider credentials for their requests.

This combined, feature-rich approach is the official architectural standard for all LLM interactions.

---

## Alternatives Considered

An alternative is a classic factory design pattern, where a single factory module would be responsible for instantiating different LLM provider clients.

**Decision:** Rejected for the current architecture.

**Reason:** The repository contains no evidence of this pattern. The implemented architecture is significantly more advanced, providing both dynamic routing and user-scoped BYOK capabilities, which a simple factory pattern would not address. The existing code is built entirely around the routing and BYOK modules.

---

## Consequences

### Positive

-   The architecture offers high flexibility, allowing the system to optimize for cost and performance via routing while enabling user-specific models and enhanced security through the BYOK system.
-   It aligns with modern, multi-provider LLM strategies and provides a robust foundation for future expansion.

### Negative

-   The complexity of managing two interconnected systems for LLM access increases the cognitive load for developers and can make debugging more challenging.
-   The distinction between a system-routed call and a user-specific BYOK call must be carefully managed throughout the application.

---

## Evidence

-   `backend/app/llm/routing/router.py`: This file contains the `LLMRouter` class, which is the core of the dynamic provider selection system.
-   `backend/app/llm/byok/service.py` and `executor.py`: These files contain the primary logic for the BYOK system, handling user-specific provider configurations and execution.
-   `backend/app/agents/autonomous.py`: The `UserScopedLLMService` class in this file demonstrates the practical application of the BYOK system for agentic workflows.
-   The file listings of `backend/app/llm/`, `backend/app/llm/routing/`, and `backend/app/llm/byok/` confirm the existence of these systems and the absence of a factory-based implementation.

---

## Future Considerations

This ADR documents the current architecture only.

Future architectural changes require a new ADR.
