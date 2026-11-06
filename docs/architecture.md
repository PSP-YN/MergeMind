# MergeMind Architecture

## Runtime topology

    Developer
       |
       v
    MergeMind Dashboard / FastAPI
       |
       | task dispatch (Switch operation)
       v
    Switch shared room
       |
       +--> Coordinator
       |       |
       |       +--> Planner
       |       |       |
       |       |       +--> Researcher ---- read-only GitHub REST API
       |       |                 |
       |       |                 +--> Implementer ---- LLM proposal
       |       |                           |
       |       |                           +--> Reviewer ---- LLM review
       |       |
       |       +<-------------------------- review handoff
       |
       +--> Human sees summary in the room and artifacts in dashboard

## Components

- **FastAPI:** dashboard API, admin-token guard, health endpoint, workflow lifecycle.
- **SQLite Store:** durable workflow records, event trace, artifacts, encrypted Switch agent credentials.
- **Switch registration:** registers five role agents once and updates their addressing policy.
- **Switch WebSocket client:** persistent connection, connection ID, room claim, ping/pong, cursor tracking, reconnect.
- **Workflow engine:** role prompts and explicit handoffs. Each specialist receives an addressed Switch message.
- **Repository reader:** read-only access to public GitHub repository metadata, recursive tree, and selected files.
- **LLM client:** OpenAI-compatible chat-completions endpoint; default is local Ollama.
- **Dashboard:** task intake, Switch status, workflow trace, artifacts, approval and rejection.

## Trust boundaries

- Switch registration key: transient credential; never stored.
- Switch agent API keys: encrypted at rest with Fernet.
- Admin token: local-only bearer-style header, generated during init and held in .env.
- Repository content and task descriptions: untrusted input; explicitly treated as data in role prompts.
- Patch output: validated as a unified diff and checked for path traversal; never applied by the application.
- LLM provider: receives task text and selected public repository excerpts. Do not send private source code to a hosted provider without authorization.

## Workflow state

CREATED -> PLANNING -> RESEARCH -> IMPLEMENTATION -> REVIEW -> AWAITING_APPROVAL -> APPROVED or REJECTED.

Any agent-stage exception marks the workflow FAILED and records a bounded error event. Human approval records a decision only. No repository mutation occurs.

## Switch protocol

The current implementation follows the documented WebSocket agent protocol. The client uses one authenticated socket per registered role, claims the configured room on connect, replies to ping frames immediately, and sends operations with X-Switch-Connection-Id. It processes only message events where payload.addressed is true.

References:
- https://docs.switchagents.ai/switch-rooms/internals/agent-protocol
- https://docs.switchagents.ai/switch-rooms/internals/agent-connection
- https://docs.switchagents.ai/switch-rooms/internals/agent-events

## Current limitations

- Public GitHub repositories only; private repository access is not implemented.
- GitHub source context is limited to selected text files and may be incomplete for large repositories.
- Patch application and isolated test execution are not implemented.
- SQLite and a single local admin token suit a local hackathon demo, not a multi-user public service.
- A live Switch server, room membership, and model endpoint are required for end-to-end validation.
