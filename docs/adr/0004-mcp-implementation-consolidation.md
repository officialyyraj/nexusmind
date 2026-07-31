# ADR-0004: MCP Consolidation

## Status

Accepted

---

## Context

The implementation of the Multi-Contributor Protocol (MCP), a system for integrating external tools, is located in the `backend/app/mcp/` directory. The repository's evidence points to a distributed, manager-client architecture. The core logic is spread across three primary modules: `manager.py` for lifecycle management, `client.py` for communication, and `registry.py` for tool discovery and invocation. An inspection of the directory shows no evidence of a monolithic, server-centric implementation (e.g., no `protocol.py` or standalone `server.py` files are present). The existing `server_manager.py` file is a compatibility shim that re-exports from the canonical `manager.py`.

---

## Decision

The canonical MCP implementation is a manager-client architecture composed of three specialized modules:

-   `app/mcp/manager.py`: The `MCPServerManager` is the central coordinator responsible for managing the configuration and lifecycle of all external tool servers.
-   `app/mcp/client.py`: The `MCPClient` is the client-side implementation for connecting to and communicating with a single external tool server over a specified transport (e.g., stdio, HTTP).
-   `app/mcp/registry.py`: The `MCPRegistry` acts as a dynamic, central registry for all tools discovered from all connected clients, handling the invocation and routing of tool calls.

This modular architecture is the official pattern for all MCP functionality.

---

## Alternatives Considered

An alternative is a monolithic, server-based protocol implementation where a single `server.py` module would listen for connections and a `protocol.py` file would define the communication specification.

**Decision:** Rejected for the current architecture.

**Reason:** The repository contains no such implementation. The architecture is clearly based on a client-side manager (`MCPServerManager`) that connects to and manages multiple external processes. This is a more flexible and scalable pattern than a single, monolithic server. The `server_manager.py` file is a remnant for backward compatibility, not a functional server.

---

## Consequences

### Positive

-   The architecture is highly extensible, allowing new external tool servers to be added via configuration without changing the core application's code.
-   It effectively isolates transport-layer logic within `MCPClient` instances, making the system adaptable to different communication protocols.
-   The central registry provides a single, unified interface for discovering and invoking any registered tool.

### Negative

-   The distributed nature of the architecture can make debugging a tool call more complex, as a request must flow from the registry to a client and then to an external process.
-   Managing the state and health of multiple external server processes adds operational complexity.

---

## Evidence

-   `backend/app/mcp/manager.py`: This file contains the `MCPServerManager` class, which manages collections of `MCPClient` instances.
-   `backend/app/mcp/client.py`: This file contains the `MCPClient` class, which handles the protocol and transport for a single external server.
-   `backend/app/mcp/registry.py`: This file contains the `MCPRegistry` class for dynamic tool registration and invocation.
-   `backend/app/mcp/server_manager.py`: The content of this file confirms it is a backward-compatibility shim, re-exporting from `manager.py`.
-   The file listing of the `backend/app/mcp/` directory confirms the presence of these files and the absence of a monolithic `server.py` or `protocol.py`.

---

## Future Considerations

This ADR documents the current architecture only.

Future architectural changes require a new ADR.
