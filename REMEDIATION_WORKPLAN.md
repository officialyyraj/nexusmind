# NexusMind V3 Remediation Workplan

---

# Executive Summary

**Current repository health:** NexusMind is a partially-abandoned refactor sitting on top of a genuinely competent security and orchestration foundation. The repository contains **two nested copies of the project** (a root-level `ARCHITECTURE.md` / `docs/` / `deployment/` tree, and the real, working project inside `nexusmind/`), and inside the real project, **97 files are empty (0 bytes)**, concentrated almost exactly in the subsystems the documentation calls the product's core differentiators: sandboxed code execution (`app/sandbox/executor.py`, `manager.py`, `terminal.py`, `browser.py`, and `sandbox/Dockerfile` itself), agent orchestration (`app/orchestration/graph.py`, `nodes.py`, `edges.py`, `state.py`), the seven agent-type files under `app/agents/types/`, the MCP protocol layer (`app/mcp/protocol.py`, `server.py`, `tools.py`), and the LLM factory layer (`app/llm/factory.py`, `base.py`, `openai.py`, `ollama.py`).

Crucially, **this is not a hollow project.** Real, substantial, overlapping implementations exist elsewhere: `app/orchestration/executor.py` (1,176 LOC) and `project_generator.py` (1,188 LOC) do the work `graph.py`/`nodes.py` were presumably meant to do; `app/agents/implementations.py` (1,049 LOC) and `autonomous.py` (822 LOC) do the work of the seven empty `agents/types/*.py` files; `app/llm/byok/*` (~2,700 LOC) and `app/llm/routing/*` do the work of the empty `llm/factory.py`; `app/mcp/manager.py` (622 LOC) plus `client.py`, `registry.py`, and `transports/*` do real MCP work despite `protocol.py`/`server.py`/`tools.py` sitting empty next to them. The security module (`rbac.py`, `audit.py`, `deployment_gate.py` at 993 LOC, `startup_validator.py`) is the most mature part of the codebase and shows real engineering intent.

**Biggest architectural issues:**
1. **Duplicated project root** — a full second copy of top-level docs/deployment/architecture files sits outside `nexusmind/`, of unclear authority relative to the real thing inside it.
2. **Two generations of the same subsystem coexisting** — old, empty stub files from an earlier per-file design next to new monolithic files that actually do the work, with no canonical entry point and no documentation update to match.
3. **Three separate `docker-compose*.yml` files** (`nexusmind/docker-compose.yml`, `nexusmind/backend/docker-compose.yml`, `nexusmind/deployment/docker-compose.yml`) with unclear precedence for production.

**Biggest technical risks:**
1. The flagship "sandboxed code execution" feature cannot build (`sandbox/Dockerfile` is empty) or run (`sandbox/executor.py`/`manager.py` are empty) as shipped — yet `config.py` still points at `nexusmind-sandbox:latest` as the default image, and the command-validation logic that does exist (`sandbox/docker.py`, 1,175 LOC) uses an incomplete denylist-regex approach.
2. Multi-replica/production auth will break silently: `SECRET_KEY` enforcement is gated on `ENVIRONMENT=production`, but the shipped compose file defaults to `development`, and `AUTO_GENERATE_SECRETS=true` will mint a fresh key per container start.
3. The in-process rate limiter is meaningless under horizontal scaling and is bypassable via an untrusted `X-Forwarded-For` header — the one visible anti-abuse control does not function as intended.
4. No dependency pinning (`requirements.txt` uses `>=` throughout, no lockfile) — every build is non-reproducible.
5. Documentation volume (82KB `ARCHITECTURE.md`, plus `SPEC.md`, `QUICK_REFERENCE.md`, `TREE.md`, `PROJECT_STRUCTURE.md`) significantly outpaces working code, and large sections almost certainly describe files that don't exist.

**Why phased remediation is required:** The empty files and duplicated structures are not randomly distributed — they cluster around the product's core value proposition, meaning any single "quick fix" pass risks either (a) deleting code that's secretly load-bearing, or (b) papering over the sandbox/orchestration gap instead of resolving it. A six-week rewrite executed as one undifferentiated effort would leave the repo in a broken, non-buildable state for most of that time. Phased remediation — cleanup → consolidation → stabilization → feature completion → hardening → launch-readiness — guarantees the repository is runnable and testable at the end of every phase, lets each phase be handed to a different engineer or AI agent without re-deriving context, and lets go/no-go decisions (particularly "does the sandbox get rebuilt or removed from scope") be made early, before dependent work is planned on top of an assumption that turns out wrong.

---

# Guiding Principles

- **Never break working functionality.** Every phase must leave `docker compose up`, `pytest`, and `npm run build` in a working (or explicitly, narrowly, documented-as-broken) state. No phase may introduce a regression in a previously-working subsystem.
- **Remove duplication before adding features.** The duplicated root-level tree and the empty-vs-monolithic file pairs must be resolved before any new capability is built on top of either copy, or new work will silently target the wrong one.
- **Every phase must compile / build.** `python -m py_compile`, `npm run build`, and `docker compose config` must succeed at the end of every phase, not just at the end of the project.
- **Documentation always matches implementation.** A phase that changes code structure is not complete until the docs referencing that structure are updated in the same phase. Docs are not a follow-up task.
- **Delete dead code instead of hiding it.** Empty stub files, superseded modules, and orphaned directories are deleted outright once their replacement is confirmed canonical — never `.bak`'d, commented out, or left importable-but-empty.
- **One canonical implementation per responsibility.** Where two implementations of the same concern exist (e.g., `llm/factory.py` vs `llm/routing/router.py`), a phase must explicitly choose one, migrate all call sites to it, and delete the other — not let both coexist "for now."
- **Security fixes are load-bearing, not polish.** SECRET_KEY enforcement, rate limiting, and sandbox command validation are treated as blocking correctness issues, not hardening tasks to defer to the end.
- **Production readiness over feature count.** No new agent types, tools, or integrations are added until the existing, advertised feature set (sandbox execution, MCP, orchestration) is real, tested, and documented accurately.
- **Small, verifiable increments.** Each phase should be completable and independently verifiable by a different engineer without needing private context from the engineer who did the previous phase.
- **No phase depends on a broken intermediate state.** If a phase requires functionality that doesn't yet exist, that functionality is either pulled forward into this phase's scope or the phase is resequenced.

---

# Phases

## Phase 0 — Repository Consolidation & Dead Code Removal

### Objective
Establish a single, unambiguous source of truth for the codebase before any other work begins. Right now there are two nested project roots and dozens of empty files masquerading as implemented modules; no other phase can be planned reliably until this is resolved, because "where does this code live" currently has more than one answer.

### Files / Areas Affected
- Repository root (`ARCHITECTURE.md`, `ARCHITECTURE_DIAGRAM.txt`, `SPEC.md`, `QUICK_REFERENCE.md`, `docs/`, `deployment/`) vs. `nexusmind/` (the real project)
- All 97 empty files across `nexusmind/backend/app/**`, `nexusmind/sandbox/**`, `nexusmind/scripts/**`, `nexusmind/frontend/**` config files, `nexusmind/docs/**`
- `nexusmind/backend/data/chromadb/` (committed runtime data directory)
- `.gitignore` files (root and nested)

### Tasks
- [ ] Confirm with the team/owner which top-level tree is authoritative: the root (`ARCHITECTURE.md`, `deployment/`, `docs/`) or `nexusmind/`. All directory evidence (working `backend/`, `frontend/`, `sandbox/`, real CI workflows) indicates `nexusmind/` is the real project and the root-level files are an earlier, superseded scaffold — but this must be confirmed before deletion, not assumed by an automated pass.
- [ ] Move the repository so `nexusmind/` becomes the actual repository root; archive or delete the outer duplicate tree (`ARCHITECTURE.md`, `ARCHITECTURE_DIAGRAM.txt`, `SPEC.md`, `QUICK_REFERENCE.md`, root `docs/`, root `deployment/`) after confirming no unique content is lost.
- [ ] Diff the two `ARCHITECTURE.md` files (root vs. `nexusmind/ARCHITECTURE.md`) and the two `docker-compose.yml`-style trees (`deployment/` at root vs. `nexusmind/deployment/`) to confirm nothing unique needs to be preserved before deletion.
- [ ] Classify every one of the 97 empty files into exactly one of: (a) genuinely obsolete stub from a superseded per-file architecture — delete; (b) intentional placeholder for Phase 3+ work — keep, but track explicitly in the Technical Debt Register below, do not leave silently empty; (c) legitimate empty marker file (`.gitkeep`, empty `__init__.py` used only as a package marker) — keep, no action needed.
- [ ] Delete category (a) files outright: `app/sandbox/executor.py`, `manager.py`, `terminal.py`, `browser.py`; `app/orchestration/graph.py`, `nodes.py`, `edges.py`, `state.py`; all seven `app/agents/types/*.py`; `app/agents/tools/*.py` (5 files); `app/agents/supervisor.py`; `app/llm/factory.py`, `base.py`, `openai.py`, `ollama.py`; `app/mcp/protocol.py`, `server.py`, `tools.py`; `app/memory/semantic_cache.py`, `vector_store.py`, `session_memory.py`; `app/plugins/manager.py`, `loader.py`, `registry.py`, `templates/example.py`.
- [ ] Populate or delete empty config/script files that are not dead code but are simply unfinished: `sandbox/Dockerfile`, `sandbox/entrypoint.sh`, `sandbox/playwright.config.js` and `sandbox/config/playwright.config.js`, `sandbox/packages/**/*.sh` and `*.js`, `scripts/build.sh`, `deploy.sh`, `dev.sh`, `format.sh`, `lint.sh`, `test.sh`, `frontend/next.config.mjs`, `frontend/tailwind.config.ts`, `frontend/jest.config.js`, `.env.example` (root and `nexusmind/.env.example`), `Makefile`, `README.md`. These are addressed for real in Phase 1 (sandbox) and Phase 2 (backend/frontend config); this phase only inventories and flags them so nothing is missed later.
- [ ] Remove the committed `backend/data/chromadb/` directory from version control; add `backend/data/` to `.gitignore`; purge from git history if this repository has already been pushed publicly.
- [ ] Reconcile the three `docker-compose*.yml` files (`nexusmind/docker-compose.yml`, `nexusmind/backend/docker-compose.yml`, `nexusmind/deployment/docker-compose.yml`) into a documented single-source-of-truth structure (base + override pattern, or explicit "this one is for local dev, this one is prod" naming) — full content reconciliation happens in Phase 5 (Deployment), this phase only documents which file currently does what and flags conflicts.
- [ ] Rename `app/__init__.py`/`app/init.py` collision (verify both exist and cannot be confused) — pick one canonical name, delete or merge the other, add a comment if the second file is intentionally distinct.
- [ ] Fix the duplicated `chmod\s+[0-7][0-7][0-7]` regex line in `sandbox/docker.py`'s `DANGEROUS_PATTERNS` (copy-paste artifact, not functional yet but should not ship duplicated even as dead weight).

### Expected Deliverables
- A single repository root with one `ARCHITECTURE.md`, one `docs/` tree, one `deployment/` tree.
- Zero files remaining that are empty without an explicit, tracked reason (either deleted, or logged in the Technical Debt Register as an intentional placeholder for a specific later phase).
- No committed runtime data directories.
- A short `CONSOLIDATION_NOTES.md` documenting what was deleted and why, for audit purposes.

### Verification Checklist
- `find . -type f -empty | grep -v -E '\.gitkeep$|__init__\.py$'` returns nothing unexplained.
- Only one `ARCHITECTURE.md` exists in the repository.
- `git log --diff-filter=D --summary` (or equivalent) shows the deletions are recorded, not silently squashed.
- `docker compose config` (against the retained compose file) parses without error.
- No `backend/data/` contents tracked by git (`git ls-files backend/data/` returns nothing).

### Risks
- Deleting a file that turns out to be dynamically imported somewhere (e.g., via `importlib` or a plugin loader) and only discovered at runtime. Mitigate by grepping for string-based imports of each deleted module name before removal, not just static `import` statements.
- Team disagreement on which top-level tree is canonical, stalling the phase. Mitigate by treating this as a go/no-go decision gate requiring explicit sign-off before deletion, not an automated judgment call.

### Dependencies
None — this is the first phase.

### Estimated Effort
**Medium**, 3–5 days (mostly diffing, inventory, and getting sign-off on the canonical-root decision; the deletions themselves are mechanical).

---

## Phase 1 — Core Architecture Consolidation

### Objective
Resolve every case where two implementations of the same responsibility exist side by side, so there is exactly one canonical module per concern before any bug-fixing or feature work begins. Phase 0 deleted the *empty* half of these pairs; this phase confirms the *surviving* half is genuinely the right long-term home and updates every reference to point at it.

### Files / Areas Affected
- `app/orchestration/` (executor.py, project_generator.py, supervisor.py, generation_schemas.py, api.py)
- `app/agents/` (implementations.py, autonomous.py, execution_engine.py, reasoning_loop.py, advanced_workflow.py, workflow.py, registry.py, base.py, types.py)
- `app/llm/` (routing/, byok/, providers.py, service.py)
- `app/mcp/` (manager.py, client.py, registry.py, transports/, schemas.py, exceptions.py)
- `app/dependencies.py` and every service currently calling `get_settings()` directly instead of via constructor injection

### Tasks
- [ ] Formally designate `app/orchestration/executor.py` + `project_generator.py` + `supervisor.py` as the canonical orchestration layer (replacing the deleted `graph.py`/`nodes.py`/`edges.py`/`state.py` concept); write a short `ADR` (architecture decision record) explaining the shift away from a formal LangGraph-style graph module to the current executor-based design, so future contributors understand this was a deliberate choice, not an accident.
- [ ] Formally designate `app/agents/implementations.py` + `autonomous.py` as canonical for agent-type behavior (replacing the deleted `agents/types/*.py` per-type files); document how each of the seven conceptual agent types (planner, coder, tester, reviewer, researcher, documentation, manager) now maps to code inside these consolidated files.
- [ ] Formally designate `app/llm/routing/router.py` + `app/llm/byok/*` as canonical for LLM provider access (replacing the deleted `llm/factory.py`/`base.py`/`openai.py`/`ollama.py`); confirm every call site imports from `routing`/`byok`, not the deleted paths.
- [ ] Formally designate `app/mcp/manager.py` + `client.py` + `transports/` as canonical for MCP handling (replacing the deleted `protocol.py`/`server.py`/`tools.py`); this is the module the original review flagged as unauditable because the docs pointed at empty files — this task makes the real location explicit and reviewable.
- [ ] Audit `app/dependencies.py` and refactor services that currently call `get_settings()` globally (confirmed in `auth/service.py` and sandbox code) to receive configuration via constructor injection instead, for testability and to remove hidden global-state coupling.
- [ ] Update `ARCHITECTURE.md`, `TREE.md`, and `PROJECT_STRUCTURE.md` to reflect the consolidated module layout — remove every reference to the deleted files.
- [ ] Run a full grep for `from app.orchestration.graph`, `from app.agents.types.`, `from app.llm.factory`, `from app.mcp.protocol`, `from app.mcp.server`, `from app.mcp.tools` across the codebase (including tests) and fix any lingering imports.

### Expected Deliverables
- One documented, canonical module per responsibility (orchestration, agent behavior, LLM access, MCP handling).
- `docs/architecture/*.md` and root `ARCHITECTURE.md` accurately describing the current module layout, with no references to deleted files.
- A short ADR log (`docs/adr/`) capturing the "why" behind each consolidation decision.
- `app/dependencies.py`-based constructor injection used consistently in `auth/service.py` and sandbox-related services.

### Verification Checklist
- `grep -rn "orchestration.graph\|agents.types\.\|llm.factory\|mcp.protocol\|mcp\.server\b\|mcp\.tools\b" --include="*.py"` returns zero results outside of the ADR/docs explaining the historical names.
- `python -c "import app.main"` (or equivalent app entrypoint) succeeds with no import errors.
- `pytest` collects all tests with no collection errors.
- Manual doc review: every module path mentioned in `ARCHITECTURE.md` exists on disk.

### Risks
- Consolidating around the wrong "winner" module if the 1000+ LOC executor/agent files turn out to have their own undiscovered bugs — this phase intentionally does *not* audit correctness of those files line-by-line (that's Phase 2/3), only confirms they are the structurally canonical home.
- Constructor-injection refactor touching many call sites risks introducing subtle bugs; mitigate with characterization tests (Phase 2) before large refactors, not after.

### Dependencies
Phase 0 (empty files must be deleted first, or "canonical" designation is ambiguous).

### Estimated Effort
**Large**, 5–7 days.

---

## Phase 2 — Backend Stabilization (Security & Reliability Fixes)

### Objective
Fix the specific, concrete bugs that will break the backend the moment it runs under any realistic condition (multiple replicas, a restart, an unbounded attacker), independent of the larger sandbox rebuild. These are correctness bugs, not "hardening" — they must be fixed before the backend can be considered functionally stable, and they do not require the sandbox to be rebuilt first.

### Repository Invariants
The following architectural elements are considered stable and **must not** be changed during Phase 2:
- All existing Architecture Decision Records (ADRs).
- The canonical module locations established in Phase 1 (e.g., for orchestration, agents, LLM access, MCP).
- The existing REST API endpoint structure and public-facing OpenAPI schema.
- The existing database schema.
- The core orchestration architecture (executor/supervisor/project_generator).
- Any other consolidation decisions made during Phase 1.

### Execution Constraints
Each execution cycle should modify only one logical task. The maximum recommended scope is one task, delivered in one commit, touching the minimal necessary file set. Implementation must be validated after every completed task.

If repository evidence conflicts with `REMEDIATION_WORKPLAN.md` or this specification, **repository evidence wins**. The discrepancy must be documented, and work should proceed based on the repository's actual state, not on outdated planning assumptions.

### Files / Areas Affected
- `app/config.py`
- `app/security/startup_validator.py`, `secrets.py`, `middleware.py`
- `app/auth/service.py`
- `docker-compose.yml` (reconciled per Phase 0 findings)
- `backend/requirements.txt`, `backend/pyproject.toml`
- `.env.example` files
- `backend/Dockerfile`
- `.github/workflows/*.yml`

### Tasks
- [ ] **T2.1: Dependency Management:** Use the repository's existing dependency management strategy to pin all backend dependencies to exact versions and generate a lockfile. If no strategy exists, document the decision-making process for the chosen tooling before implementation.
- [ ] **T2.2: Container Hardening:** Add a non-root `USER` directive to `backend/Dockerfile` so the container does not run as root by default.
- [ ] **T2.3: Mandatory SECRET_KEY:** Make `SECRET_KEY` mandatory (fail-hard at startup) in every environment except an explicitly-named local/dev-only mode. Remove the current behavior where enforcement only triggers when `ENVIRONMENT=="production"`.
- [ ] **T2.4: AUTO_GENERATE_SECRETS:** Disable or explicitly gate `AUTO_GENERATE_SECRETS=true` so it cannot apply to any environment where JWTs need to remain valid across restarts or multiple replicas.
- [ ] **T2.5: CI Secret Updates:** Update the GitHub Actions workflow (`backend-tests.yml`) to source its `SECRET_KEY` value from GitHub Actions secrets rather than a hardcoded literal.
- [ ] **T2.6: Redis-Backed Rate Limiter:** Replace the in-process, dict-based `RateLimitMiddleware` with a Redis-backed implementation. The Redis client **must** be managed via dependency injection and must not be instantiated directly within the middleware or as a hidden global singleton.
- [ ] **T2.7: Trusted Proxy Validation:** Add a trusted-proxy allowlist check before trusting the `X-Forwarded-For` header. If the app is not behind a known reverse proxy, ignore the header entirely and use the direct connecting IP.
- [ ] **T2.8: Authentication Lockout:** Add lockout/backoff logic at the service layer in `auth/service.py`'s `authenticate_user`. This is a behavioral change; the public API shape, including request and response schemas, must remain compatible.
- [ ] **T2.9: Populate .env.example:** Populate all `.env.example` files with every variable read in `config.py`, providing safe placeholder values and inline comments explaining each.

### Expected Deliverables
- A locked, reproducible dependency set for the backend.
- A backend container that runs as a non-root user.
- A backend that produces a hard startup failure when `SECRET_KEY` is unset outside an explicit local dev mode.
- A rate limiter that behaves correctly with 2+ backend replicas running concurrently.
- Fully populated `.env.example` files.
- CI workflows that use secrets for sensitive variables.

### Verification Checklist
- The lockfile-based installation (`pip install -r requirements.lock` or equivalent) produces an identical dependency tree on a clean machine on two separate runs.
- `docker inspect` on the running backend container shows a non-root `USER`. The application must start successfully, and previously-working functionality (e.g., writing to mounted volumes, creating temp files) must remain operational.
- Starting the backend with `ENVIRONMENT` unset and no `SECRET_KEY` set fails fast with a clear error.
- The CI workflow file (`backend-tests.yml`) contains no hardcoded secret literals for `SECRET_KEY`.
- Run 2 backend replicas behind the rate limiter and confirm a client is throttled at the intended aggregate limit, not per-replica.
- Send requests with spoofed `X-Forwarded-For` values and confirm rate limiting is not bypassed.
- All `.env.example` files are populated and reflect the variables used in `config.py`.

### Risks
- **Dependency Pinning:** Pinning dependencies may surface version conflicts that were previously masked by floating `>=` ranges; these must be resolved before merging.
- **Redis Dependency:** The Redis-backed rate limiter adds a hard runtime dependency on Redis. The application's behavior during a Redis outage (fail-open vs. fail-closed) must be explicitly decided and documented.
- **Permissions:** Changing the container user to non-root may cause runtime permission errors. Verification must include checks for file system access to logs, volumes, and temporary directories.

### Dependencies
- **Phase 0:** Consolidated `docker-compose.yml` files are required.
- **Phase 1:** A stable `app/dependencies.py` injection pattern is required to implement the rate-limiter and auth fixes cleanly.

### Estimated Effort
**Medium**, 4–6 days.

---

## Phase 3 — Sandbox Execution Rebuild

### Objective
The sandbox is the product's advertised core differentiator ("safe autonomous code execution") and is currently non-functional: the Dockerfile is empty, `executor.py`/`manager.py`/`terminal.py`/`browser.py` are empty, and the command-validation logic that does exist is an incomplete denylist. This phase either makes the sandbox real and safe, or makes an explicit, documented decision to descope it — but the current state (advertised as core, silently absent, defaulting to a nonexistent image) cannot continue.

### Files / Areas Affected
- `sandbox/Dockerfile`, `sandbox/entrypoint.sh`, `sandbox/packages/**`
- `app/sandbox/docker.py`, `executor.py`, `manager.py`, `terminal.py`, `browser.py`
- `app/config.py` (`sandbox_docker_image` default)
- `app/orchestration/executor.py` and `app/agents/*` wherever they invoke sandbox execution

### Tasks
- [ ] Make an explicit go/no-go decision: rebuild the sandbox for this release, or descope it and clearly mark "code execution" as not-yet-available in all user-facing docs/UI. Do not proceed with the remaining tasks in this phase until this decision is recorded.
- [ ] If rebuilding: write a real `sandbox/Dockerfile` that produces the `nexusmind-sandbox:latest` image referenced in `config.py`, including the terminal/browser tooling implied by `sandbox/packages/**`.
- [ ] Implement `app/sandbox/executor.py` and `manager.py` for real, using `app/sandbox/docker.py`'s existing container-management code as the base.
- [ ] Replace the denylist-regex `CommandValidator` in `sandbox/docker.py` with an allowlisted command grammar, or (preferred) remove shell-string interpretation entirely and pass `argv` arrays directly into a syscall-filtered sandbox (seccomp profile or gVisor runtime).
- [ ] Explicitly verify there is no fallback code path anywhere in `app/orchestration/executor.py` or `app/agents/*` that executes user/agent-generated code *outside* the sandbox wrapper when the sandbox is unavailable — this was flagged as an unverified RCE-by-omission risk and must be closed out with evidence, not assumption.
- [ ] Implement `terminal.py` and `browser.py` against the now-real sandbox image, wiring them to the existing `sandbox/packages/terminal/*` and `sandbox/packages/browser/*` configs.
- [ ] Add integration tests that actually build the sandbox image and execute representative commands (including deliberately malicious ones — path traversal, `$IFS` substitution, base64-encoded payloads, backticks, newline-chained commands) to confirm the allowlist rejects them.
- [ ] Update `ARCHITECTURE.md` and `docs/architecture/*.md` to describe the sandbox exactly as implemented, including its actual isolation guarantees and known limitations.

### Expected Deliverables
- A buildable `nexusmind-sandbox:latest` image.
- Functioning `executor.py`/`manager.py`/`terminal.py`/`browser.py`.
- An allowlist-based (not denylist-based) command validation layer with test coverage against known bypass techniques.
- Documented, verified absence of any non-sandboxed code-execution fallback path.
- Docs that accurately describe what the sandbox does and does not protect against.

### Verification Checklist
- `docker build` on `sandbox/Dockerfile` succeeds.
- A full agent run that invokes terminal/browser tools actually executes inside the sandbox container (verified via container logs/process inspection, not just "no error thrown").
- The new integration test suite (malicious command corpus) passes — every attempted bypass is rejected.
- `grep` across `app/orchestration/` and `app/agents/` confirms no direct `subprocess`/`os.system`/shell-exec call bypasses the sandbox wrapper.
- Security review sign-off on the sandbox isolation model before this phase is marked complete.

### Risks
- This is the highest-effort, highest-uncertainty phase in the roadmap; if descoped instead of rebuilt, significant downstream product-messaging and roadmap consequences follow and should be raised to product/leadership immediately, not absorbed silently by engineering.
- Seccomp/gVisor integration may require infrastructure changes (privileged containers, host kernel support) beyond application code — confirm target deployment environment supports the chosen isolation mechanism before committing to it.

### Dependencies
Phase 0 (dead files removed so there's a clean slate), Phase 1 (orchestration/agent call sites are consolidated, so there's one place to verify no bypass exists), Phase 2 (backend is otherwise stable, so sandbox bugs aren't confused with unrelated backend bugs).

### Estimated Effort
**Large**, 3–4 weeks (this is the single largest phase in the roadmap; the original audit estimated "1 month" for this work in isolation).

---

## Phase 4 — MCP Protocol & Agent Framework Completion

### Objective
Complete and verify the MCP integration and agent framework so that the tool-execution authorization boundaries the original review flagged as "unauditable because the code isn't where the docs say it is" can actually be audited. This phase assumes Phase 1 has already established `app/mcp/manager.py`/`client.py`/`transports/` as canonical; here the goal is closing functional and security gaps in that real implementation, plus finishing the 1000+ line orchestration/agent files that were previously flagged as unverified.

### Files / Areas Affected
- `app/mcp/manager.py`, `client.py`, `registry.py`, `transports/`, `schemas.py`, `exceptions.py`
- `app/orchestration/executor.py`, `project_generator.py`
- `app/agents/implementations.py`, `autonomous.py`, `execution_engine.py`, `reasoning_loop.py`, `advanced_workflow.py`

### Tasks
- [ ] Line-by-line review of `app/orchestration/executor.py` (1,176 LOC) and `project_generator.py` (1,188 LOC) — the follow-up work explicitly deferred in the original audit — verifying retry logic, hallucination/error handling, and token-cost controls.
- [ ] Line-by-line review of `app/agents/implementations.py` (1,049 LOC) and `autonomous.py` (822 LOC) for the same categories of correctness issues.
- [ ] Audit MCP tool-call authorization: confirm every tool invocation path in `app/mcp/manager.py`/`client.py` enforces the RBAC boundaries defined in `app/security/rbac.py`, and there is no path where an MCP tool call executes without an authorization check.
- [ ] Add missing test coverage for MCP transports (`transports/http.py`, `transports/stdio.py`) and the manager/client/registry trio — current test-file-to-source-file ratio is roughly 1:4 by file count, and MCP-specific coverage should be confirmed explicitly, not assumed from the aggregate number.
- [ ] Verify and document circuit-breaker behavior for external LLM API failures (previously flagged as "not visibly verified") — implement if absent.
- [ ] Verify and document cost-tracking/budget-cap enforcement in `app/llm/byok/*` (previously flagged as possibly present but unverified) — implement if absent.
- [ ] Update `docs/architecture/agents.md`, `docs/architecture/orchestration.md`, and MCP-specific docs to match the now-verified implementation.

### Expected Deliverables
- A written audit report (can live in `docs/audits/`) covering the reviewed orchestration/agent files, listing any bugs found and their resolution status.
- Confirmed, tested MCP authorization boundaries.
- Circuit breakers and budget-cap enforcement either verified-present or newly implemented.
- Accurate architecture docs for orchestration, agents, and MCP.

### Verification Checklist
- Test coverage report shows meaningful (not just file-count) coverage for `orchestration/executor.py`, `agents/implementations.py`, and `mcp/manager.py`.
- A deliberately unauthorized MCP tool call (test harness impersonating a role without permission) is rejected.
- Simulated LLM provider failure (mocked timeout/500) triggers the circuit breaker instead of cascading.
- Simulated budget-cap breach halts further LLM calls for the session/user in question.

### Risks
- Line-by-line review of ~5,000 LOC of orchestration/agent code may surface deeper design issues than simple bugs, potentially requiring a scope increase mid-phase — budget contingency time.
- **Deferred Work:** The Content-Security-Policy (CSP) task, originally in Phase 2, is deferred here. It requires removing `'unsafe-inline'` and `'unsafe-eval'` from `script-src`, which may involve frontend changes.

### Dependencies
Phase 1 (canonical modules established), Phase 3 (sandbox real, so agent execution paths being audited actually run against a real sandbox rather than a stub).

### Estimated Effort
**Large**, 2–3 weeks.

---

## Phase 5 — Deployment & Infrastructure Hardening

### Objective
Make the deployment configuration match production reality: one canonical compose/deployment path, non-default secrets, and no accidental "staging box running the dev compose file" incidents.

### Files / Areas Affected
- `docker-compose.yml`, `docker-compose.prod.yml`, `backend/docker-compose.yml`, `deployment/docker-compose.yml`
- `deployment/nginx/nginx.conf`, `deployment/prometheus/prometheus.yml`, `deployment/grafana/**`, `deployment/northflank.yaml`
- `backend/Dockerfile`, `frontend/Dockerfile`
- `.github/workflows/*.yml`

### Tasks
- [ ] Reconcile the (now, post-Phase-0, single canonical) compose structure into a clear base/override pattern: one file for local dev, one explicit prod override, with README guidance on which to use when.
- [ ] Remove hardcoded `POSTGRES_PASSWORD=postgres` and hardcoded port exposure (`5432:5432`) from any file that could plausibly be copy-pasted into a staging/production context; require explicit secrets injection instead.
- [ ] Add a compose profile or clearly-named file split so "local dev, safe to hardcode passwords" and "production-like, must use real secrets" are structurally distinct, not just documented-and-hoped-for.
- [ ] Verify monitoring stack (`prometheus.yml`, `grafana/provisioning/**`) actually scrapes the app's real metrics endpoints post-Phase-2 changes (rate limiter, auth) — update dashboards if metric names changed.
- [ ] Confirm `deployment/northflank.yaml` (or equivalent platform config) references the correct, consolidated image build paths after Phase 0/3 changes.
- [ ] Add a rollback runbook (referenced but not present in depth per the original audit) covering: bad deploy detection, rollback trigger, and rollback execution steps.
- [ ] Add dependency-vulnerability scanning (Dependabot or Snyk) as a CI job.
- [ ] **Deferred Work:** The Content-Security-Policy (CSP) task may be implemented here if not completed in Phase 4, as it has deployment-wide implications.

### Expected Deliverables
- One clearly-documented compose/deployment path per environment (local, staging, prod).
- No hardcoded production-unsafe defaults reachable via the primary deployment files.
- A rollback runbook.
- Automated dependency-vulnerability scanning in CI.

### Verification Checklist
- `docker compose -f docker-compose.yml up` succeeds locally with dev-safe defaults.
- `docker compose -f docker-compose.prod.yml config` fails loudly if required secrets are unset (no silent fallback to insecure defaults).
- Grafana dashboards render real data against the Phase-2-updated metrics.
- CI shows a passing dependency-scan job.

### Risks
- Changing compose file structure can break existing local dev muscle-memory for the team; communicate the new file layout clearly in the PR description and README.

### Dependencies
Phase 0 (consolidated compose files), Phase 2 (backend security fixes that the deployment config needs to enforce, like mandatory SECRET_KEY).

### Estimated Effort
**Medium**, 1 week.

---

## Phase 6 — Testing & Quality Gate Hardening

### Objective
Bring test coverage and CI enforcement up to a level that matches the codebase's actual (post-consolidation) size and criticality, closing the gap between the previously-measured ~18% file-level test coverage and a defensible production bar.

### Files / Areas Affected
- `backend/tests/**`
- `.github/workflows/backend-tests.yml`, `frontend-tests.yml`
- `frontend/src/tests/**`

### Tasks
- [ ] Establish a minimum line-coverage threshold (not just file-count ratio) for `app/security/`, `app/sandbox/`, `app/orchestration/`, `app/mcp/`, and `app/agents/` specifically — these are the highest-risk modules per the security audit and deserve a higher bar than the codebase average.
- [ ] Add missing unit tests for every module touched in Phases 2–4 (rate limiter, SECRET_KEY enforcement, sandbox command validation, MCP authorization, orchestration retry logic).
- [ ] Add the malicious-command integration test corpus from Phase 3 permanently to CI (not a one-off manual verification).
- [ ] Enforce coverage thresholds as a CI gate (fail the build below threshold) rather than an informational report.
- [ ] Add load-testing artifacts (previously absent) for the rate limiter and sandbox execution paths specifically, since those are the two subsystems most likely to behave differently under load than in unit tests.
- [ ] Confirm CI runs against the consolidated repository structure (post Phase 0) with no references to deleted paths.

### Expected Deliverables
- A CI pipeline that fails the build on coverage regression in security-critical modules.
- A permanent, CI-run malicious-command test corpus for the sandbox.
- Load-test artifacts and a documented baseline for rate limiter and sandbox throughput.

### Verification Checklist
- `pytest --cov` shows the agreed threshold met for `app/security/`, `app/sandbox/`, `app/mcp/`.
- CI fails intentionally when a coverage-reducing change is introduced in a test PR (verify the gate actually blocks, don't just trust the config).
- Load test run produces a documented baseline (requests/sec, error rate) checked into `docs/`.

### Risks
- Retrofitting tests onto large, previously-unaudited files (`orchestration/executor.py`, `agents/implementations.py`) may surface bugs found in Phase 4 that need re-opening; budget for this overlap rather than treating Phase 4 and 6 as fully sequential/disjoint.

### Dependencies
Phases 2, 3, 4 (the code being tested must be stabilized/rebuilt first, or tests would need rewriting immediately after).

### Estimated Effort
**Medium**, 1–2 weeks.

---

## Phase 7 — Documentation Reconciliation & Launch Readiness

### Objective
Bring the (currently oversized relative to working code) documentation set back into alignment with the now-consolidated, stabilized, tested codebase, and perform a final go/no-go production-readiness review.

### Files / Areas Affected
- `ARCHITECTURE.md`, `SPEC.md`, `QUICK_REFERENCE.md`, `TREE.md`, `PROJECT_STRUCTURE.md`
- `docs/**` (all subdirectories)
- `README.md` (currently empty)
- `LICENSE` (currently absent)

### Tasks
- [ ] Full re-read of `ARCHITECTURE.md` (82KB) against the final Phase-0-through-6 codebase; remove or rewrite every section describing a module that was deleted or restructured.
- [ ] Regenerate `TREE.md` and `PROJECT_STRUCTURE.md` programmatically from the actual final directory structure rather than hand-maintaining them, to prevent this exact drift from recurring.
- [ ] Write the currently-empty `README.md` with accurate setup, run, and test instructions verified against the final repository state.
- [ ] Add a `LICENSE` file (confirm license choice with the project owner before any OSS distribution claim).
- [ ] Reconcile `docs/api/*.md`, `docs/architecture/*.md`, `docs/plugins/*.md` (currently mostly empty) against the final API/plugin surface.
- [ ] Final end-to-end production-readiness review: re-run the original hostile audit's checklist (architecture, code quality, security, backend, frontend, database, AI system, production readiness, technical debt, risk) against the post-remediation codebase and confirm every "Critical" and "High" item from the original audit is closed.
- [ ] Confirm CI is fully green across all workflows on a clean clone.

### Expected Deliverables
- Documentation that accurately describes the shipped codebase, with no references to deleted or renamed modules.
- A populated `README.md` and `LICENSE`.
- A final production-readiness sign-off document referencing the original audit's findings and their resolution status.

### Verification Checklist
- Every file path mentioned anywhere in `docs/` or `ARCHITECTURE.md` exists on disk.
- `README.md` setup instructions succeed on a genuinely clean environment (new contributor test).
- All CI workflows green on a fresh clone/PR.
- Every Critical/High item from the original hostile audit has a documented resolution or an explicit, owner-approved deferral with reasoning.

### Risks
- Documentation work is often deprioritized under deadline pressure; treat this phase as a hard gate before any "V3 launched" claim, not an optional polish step, given that doc/code drift was one of the two most severe findings in the original audit.

### Dependencies
All previous phases.

### Estimated Effort
**Small–Medium**, 3–5 days.

---

# Cross-Phase Cleanup Matrix

| Area | Current Problem | Target State | Phase |
|---|---|---|---|
| Repository root | Two nested project copies (root vs. `nexusmind/`) | Single canonical root | 0 |
| Empty Python stub files (46+ in `app/`) | Dead files matching real module names, misleading grep/imports | Deleted or explicitly tracked as intentional placeholders | 0 |
| Sandbox Dockerfile | 0 bytes, image cannot build | Real, buildable image | 3 |
| `app/sandbox/executor.py`, `manager.py`, `terminal.py`, `browser.py` | Empty | Fully implemented, tested | 3 |
| `app/orchestration/graph.py`, `nodes.py`, `edges.py`, `state.py` | Empty, superseded by `executor.py`/`project_generator.py` | Deleted; executor/project_generator designated canonical | 0 → 1 |
| `app/agents/types/*.py` (7 files) | Empty, superseded by `implementations.py`/`autonomous.py` | Deleted; implementations/autonomous designated canonical | 0 → 1 |
| `app/llm/factory.py`, `base.py`, `openai.py`, `ollama.py` | Empty, superseded by `routing/`/`byok/` | Deleted; routing/byok designated canonical | 0 → 1 |
| `app/mcp/protocol.py`, `server.py`, `tools.py` | Empty, superseded by `manager.py`/`client.py` | Deleted; manager/client designated canonical, authorization audited | 0 → 1 → 4 |
| Sandbox command validation | Denylist regex, incomplete | Allowlist grammar or argv-only + seccomp/gVisor | 3 |
| `SECRET_KEY` enforcement | Only enforced when `ENVIRONMENT=="production"`, dev is the shipped default | Mandatory in all non-explicit-local environments | 2 |
| Rate limiter | In-process dict, spoofable via XFF, unbounded memory growth | Redis-backed, trusted-proxy XFF only | 2 |
| CSP | `unsafe-inline`/`unsafe-eval` present | Nonce/hash-based, no unsafe directives | 2 |
| Dependency pinning | `>=` everywhere, no lockfile | Exact pins + committed lockfile | 2 |
| `.env.example` files | Empty (root and `nexusmind/`) | Fully populated with every `config.py` variable | 2 |
| Container user | Root by default (no `USER` directive) | Non-root `USER` in Dockerfiles | 2 |
| `docker-compose*.yml` (3 files) | Unclear precedence, hardcoded prod-unsafe defaults | One documented base/override structure per environment | 0 → 5 |
| Committed `backend/data/chromadb/` | Runtime data shipped in source archive | Removed, gitignored | 0 |
| Test coverage | ~18% file-count ratio, unverified line coverage | Enforced coverage thresholds on security-critical modules | 6 |
| `orchestration/executor.py`, `project_generator.py`, `agents/implementations.py`, `autonomous.py` (1000+ LOC each) | Never line-by-line audited | Audited, bugs resolved, tests added | 4 |
| Documentation (`ARCHITECTURE.md` et al.) | Describes deleted/nonexistent modules | Fully reconciled with final codebase | 1 → 7 |
| `README.md` | Empty | Populated, verified setup instructions | 7 |
| `LICENSE` | Absent | Present, confirmed with owner | 7 |
| CI hardcoded test secret | `SECRET_KEY: test-secret-key-for-testing` literal in workflow | Sourced from GitHub Actions secrets | 2 |

---

# Technical Debt Register

| Item | Priority | Impact | Recommended Phase |
|---|---|---|---|
| Duplicated project root (outer tree vs. `nexusmind/`) | Critical | Ambiguous source of truth blocks all other work | 0 |
| Sandbox Dockerfile empty | Critical | Core product feature cannot build | 3 |
| Sandbox executor/manager/terminal/browser empty | Critical | Core product feature cannot run | 3 |
| Sandbox command validation is denylist-based | Critical | Known-insufficient security pattern; RCE risk if/when sandbox is built | 3 |
| SECRET_KEY enforcement gated on env string, dev is shipped default | Critical | Auth breaks unpredictably at scale/restart | 2 |
| Rate limiter in-process and XFF-spoofable | High | No real anti-abuse protection; unbounded memory DoS | 2 |
| No dependency pinning/lockfile | High | Non-reproducible builds, unreviewed upstream changes ship automatically | 2 |
| MCP protocol files empty while manager.py carries real logic | Medium | Authorization boundaries unauditable until relocated/documented | 1, 4 |
| Orchestration/agent 1000+ LOC files never audited | Medium | Unknown correctness risk in retry/hallucination/cost-control logic | 4 |
| CSP allows unsafe-inline/unsafe-eval | Medium | XSS mitigation largely nullified | 2 → 4/5 |
| Three docker-compose files, unclear precedence | Medium | Risk of dev config reaching staging/prod | 0, 5 |
| Committed chromadb data directory | Low–Medium | Possible data leak if repo made public; repo hygiene | 0 |
| Container runs as root | Medium | Compounds any RCE with easier lateral movement | 2 |
| Duplicate regex line in `DANGEROUS_PATTERNS` | Low | Cosmetic/maintainability, but signals low review rigor | 0 |
| Empty `.env.example` files | Low | New-operator onboarding friction, encourages hardcoded secrets | 2 |
| Hardcoded CI test secret literal | Low | Minor secret-hygiene smell, discipline issue | 2 |
| Documentation volume outpaces working code | Medium | Erodes trust, misleads engineers during incidents | 1, 7 |
| No LICENSE file | Low (until OSS distribution is intended) | Blocks any legitimate OSS distribution claim | 7 |
| Test coverage unverified/likely low on critical modules | High | Unknown regression risk on the exact subsystems most worth protecting | 6 |
| No circuit breakers verified for LLM API failures | Medium | Cascading failure risk under provider outages | 4 |
| No verified cost/budget-cap enforcement | Medium | Uncontrolled spend risk on BYOK/LLM usage | 4 |

---

# Documentation Plan

**Documents to be rewritten (kept, but substantially revised for accuracy):**
- `ARCHITECTURE.md` — rewritten post-Phase-1 to describe only the consolidated, canonical modules.
- `TREE.md` / `PROJECT_STRUCTURE.md` — regenerated programmatically from the final directory tree (Phase 7) rather than hand-maintained, specifically to prevent recurrence of this exact drift problem.
- `SPEC.md` / `QUICK_REFERENCE.md` — revised to match final feature scope, especially sandbox capabilities (Phase 3) and any features explicitly descoped.
- `docs/architecture/agents.md`, `docs/architecture/orchestration.md`, `docs/architecture/overview.md` — rewritten in Phase 1 (structure) and finalized in Phase 4 (behavior/correctness detail post-audit).
- `docs/deployment.md`, `docs/monitoring.md`, `docs/operations.md` — revised in Phase 5 to match the consolidated deployment/compose structure.
- `README.md` — currently empty; written fresh in Phase 7 with verified setup instructions.

**Documents to be deleted:**
- The entire outer, duplicate top-level tree (`ARCHITECTURE.md`, `ARCHITECTURE_DIAGRAM.txt`, `SPEC.md`, `QUICK_REFERENCE.md`, `docs/`, `deployment/` at repository root) once confirmed superseded by the equivalent files inside `nexusmind/` (Phase 0).
- Any doc file whose only content describes a deleted empty-stub module (to be identified during the Phase 0 empty-file inventory and Phase 1 consolidation).

**Documents to become canonical:**
- `nexusmind/ARCHITECTURE.md` as the single architecture reference (once reconciled in Phases 1 and 7).
- `nexusmind/docs/` as the single documentation tree (API docs, architecture docs, plugin docs).
- A new `docs/adr/` directory (introduced in Phase 1) as the canonical record of consolidation and design decisions, so future contributors understand *why* the current structure looks the way it does, not just *what* it is.

---

# Final Repository Vision

After all phases are complete, NexusMind V3 should look like this:

**Architecture:** A single, well-documented FastAPI backend + Next.js frontend monorepo with no duplicate top-level trees, no empty files masquerading as implemented modules, and one canonical module per responsibility. Architecture docs describe exactly what exists on disk — nothing more, nothing less.

**Folder structure:** One repository root (`nexusmind/`), with `backend/`, `frontend/`, `sandbox/`, `deployment/`, `docs/`, `scripts/` as clearly-scoped top-level directories. No parallel/duplicate structures at any level.

**Backend:** FastAPI app with SECRET_KEY mandatory in all non-local environments, Redis-backed rate limiting, pinned and locked dependencies, non-root containers, and a CSP that would pass a real security review.

**Frontend:** The existing, structurally healthy Next.js 15/React 19 app-router codebase, unchanged in its good parts (state stores with tests, separated API hooks), verified for accessibility and bundle size as part of Phase 6/7.

**Agent framework:** `app/agents/implementations.py` and `autonomous.py` as the audited, tested, canonical home for all seven conceptual agent types, with no orphaned per-type stub files.

**Orchestration:** `app/orchestration/executor.py` and `project_generator.py` as the audited, tested, canonical orchestration layer, with verified retry logic, error handling, and cost controls, and an ADR explaining the departure from the originally-planned graph-based design.

**Plugins:** Either a real, implemented plugin system (if kept in scope) or explicitly removed from documentation and roadmap (if descoped) — no more empty `manager.py`/`loader.py`/`registry.py` sitting unaddressed.

**Memory:** `session_memory.py` implemented and tested; vector store and semantic cache either implemented or explicitly descoped and documented as such, not left as silent empty files.

**Sandbox:** A real, buildable `nexusmind-sandbox:latest` image with allowlist-based (not denylist-based) command validation, verified isolation, and no non-sandboxed code-execution fallback path anywhere in the codebase.

**Deployment:** One documented compose structure per environment (local/staging/prod), no hardcoded production-unsafe defaults in files that could be copy-pasted into a real deployment, working monitoring dashboards, and a rollback runbook.

**Testing:** Enforced coverage thresholds on every security-critical module (security, sandbox, orchestration, MCP, agents), a permanent malicious-command test corpus in CI, and load-test baselines for the rate limiter and sandbox.

**Documentation:** Programmatically regenerated structure docs (`TREE.md`/`PROJECT_STRUCTURE.md`), a populated `README.md` and `LICENSE`, and an `docs/adr/` decision log explaining every major consolidation choice made during remediation.

---

# Success Criteria

NexusMind V3 remediation is considered complete when all of the following hold:

- [ ] No duplicate project roots or duplicate architecture documents exist in the repository.
- [ ] No empty Python files remain in `app/` without an explicit, documented reason tracked in the Technical Debt Register.
- [ ] The sandbox image builds successfully via `docker build`, and agent-invoked code execution is verifiably confined to it (or the feature is explicitly, publicly descoped with docs updated accordingly).
- [ ] Sandbox command validation is allowlist-based (or argv-only + syscall-filtered) and passes a dedicated malicious-command test corpus in CI.
- [ ] `SECRET_KEY` is mandatory and fails hard at startup in every non-explicit-local environment.
- [ ] The rate limiter functions correctly across multiple replicas and cannot be bypassed via `X-Forwarded-For` spoofing.
- [ ] All backend dependencies are pinned with a committed, reproducible lockfile.
- [ ] CSP contains no `unsafe-inline`/`unsafe-eval` directives.
- [ ] MCP tool-call authorization is enforced and covered by tests confirming unauthorized calls are rejected.
- [ ] The 1000+ LOC orchestration and agent files have been line-by-line audited, with findings resolved or explicitly tracked.
- [ ] CI is fully green (backend tests, frontend tests, security scan, dependency scan) on a clean clone.
- [ ] Coverage thresholds are enforced and met on `app/security/`, `app/sandbox/`, `app/mcp/`, `app/orchestration/`, and `app/agents/`.
- [ ] Every file path referenced in `ARCHITECTURE.md`, `TREE.md`, `PROJECT_STRUCTURE.md`, and `docs/` exists on disk and matches the described behavior.
- [ ] `README.md` setup instructions succeed for a genuinely new contributor on a clean environment.
- [ ] A `LICENSE` file is present (or its absence is an explicit, owner-approved decision for a closed-source repository).
- [ ] Only one canonical `docker-compose` structure exists per environment, with no hardcoded production-unsafe secrets in any file reachable from a real deployment path.
- [ ] A production-readiness review, re-running the original hostile audit's checklist against the final codebase, shows every originally-flagged Critical and High severity item closed or explicitly, knowingly deferred with owner sign-off.
