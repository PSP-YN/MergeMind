# MergeMind Architecture (Draft)

## Target design

- **Coordinator/API:** accepts work requests, tracks workflow status, enforces transitions and approval gates.
- **Switch:** shared room context and message delivery between agent participants. The Switch adapter is the boundary between local workflow logic and Switch's agent protocol.
- **Planner:** acceptance criteria and bounded sub-tasks.
- **Researcher:** evidence from the source repository (file paths, excerpts, constraints).
- **Implementer:** proposes changes only in a sandboxed branch/worktree.
- **Reviewer:** checks correctness, security, scope, and tests independently.
- **Human approval:** explicit gate before any patch is applied or PR/merge action is triggered.
- **Frontend:** workflow timeline, agent messages, diff preview, review, approval/rejection.

## Current implementation status

- FastAPI skeleton, role registry, basic workflow API, Switch configuration status, and tests.
- Workflow data is in-memory and is lost on restart.
- No real Switch connection, LLM calls, GitHub API calls, repository checkout, or patch execution yet.
- This draft must be updated as integrations are implemented and verified.

## Switch integration notes

The official protocol uses an authenticated WebSocket for room events and HTTP calls for operations. Older SSE clients are deprecated. Credentials are agent API keys (not registration keys) and must remain server-side.

Reference: [Switch agent protocol](https://docs.switchagents.ai/switch-rooms/internals/agent-protocol)
