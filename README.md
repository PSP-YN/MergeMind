# MergeMind

[![Backend CI](https://github.com/PSP-YN/MergeMind/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/PSP-YN/MergeMind/actions/workflows/backend-tests.yml)

**A Switch-powered AI software engineering team.** MergeMind turns an engineering task into a coordinated workflow across five specialist agents: Coordinator, Planner, Researcher, Implementer, and Reviewer. They communicate through a shared Switch room.

> Flip the Switch Hackathon · Best Business Workflow · 2026  
> **Current local verification (7 Nov 2026):** Switch core, Gateway, and MergeMind are running locally. All five MergeMind agents are registered, joined to one real Switch room, and report connected (5/5). A real workflow has been dispatched, but the downstream Planner → Researcher → Implementer → Reviewer handoffs and final human-review state have not yet been verified. This is not a completed end-to-end demo.

## What makes it a Switch workflow

Switch is the coordination layer, not a decorative chat integration. Each MergeMind role is registered as its own Switch agent. Agents connect to the same room over the official authenticated WebSocket protocol, receive addressed messages, and hand work to the next specialist using Switch's agent operations.

The workflow is:

1. A developer submits an engineering task and public GitHub repository.
2. The Coordinator delegates to the Planner.
3. The Planner creates scoped steps and acceptance criteria.
4. The Researcher reads repository metadata and selected source files.
5. The Implementer proposes a unified diff; it does not change the repository.
6. The Reviewer independently inspects the proposal and reports findings.
7. A human approves or rejects the review in the dashboard.

The workflow is designed around explicit handoffs and shared room context. It does not silently fall back to local-only messaging when Switch is unavailable.

## Business workflow and decision control

MergeMind turns an engineering request into a decision-ready work package. It is designed for a team that needs to know who owns each step, what evidence supports the proposed change, and who made the final decision.

| Stage | Owner | Persisted output | Control |
|---|---|---|---|
| Intake | Coordinator | Task record and delegated work | One accountable workflow owner |
| Scope | Planner | Steps, assumptions, risks, acceptance criteria | Scope is explicit before implementation |
| Evidence | Researcher | Repository paths and source excerpts | Claims are tied to the actual codebase |
| Proposal | Implementer | Unified diff and validation result | The target repository is not modified |
| Quality gate | Reviewer | Independent findings and missing-test notes | The implementer does not approve its own work |
| Decision | Human | Approval or rejection record | A person remains accountable |

The workflow's business outcome is traceability: a request can be followed from intake through evidence, proposal, review, and decision. It is not an autonomous merge pipeline. Approval records the decision; it does not apply the patch.

## Safety and honesty boundaries

- No patch is applied to the target repository; no commit, pull request, merge, deployment, or hackathon submission is created.
- Human approval is required before any future repository-changing action.
- The current approval action records a decision; it does not apply the patch.
- Repository contents and issue text are untrusted input.
- The researcher is read-only and currently supports public GitHub repositories.
- The proposed patch is path-validated and remains an artifact for review.
- Proposed diffs are applied only to a disposable clone for applicability checks; Python syntax compilation can run in a no-network Docker container with a read-only source mount. The project test suite is not executed.
- Switch agent API keys are encrypted in SQLite with a Fernet key stored outside the repository.
- Registration keys are used for agent creation and are not persisted.
- The app binds to localhost by default in the documented setup.

## Stack

- Python 3.11+
- FastAPI
- SQLite for local workflow persistence
- Switch agent protocol (authenticated WebSocket + HTTP operations)
- OpenAI-compatible model API (default: local Ollama)
- Plain HTML/CSS/JavaScript dashboard
- pytest and GitHub Actions

## Quick start

    git clone https://github.com/PSP-YN/MergeMind.git
    cd MergeMind
    bash scripts/setup.sh

The init command creates a local .env containing a random admin token and encryption key. It refuses to overwrite an existing .env. Keep that file private.

Start a local Ollama server and pull the default model:

    ollama pull qwen2.5-coder:3b

Then run the app:

    bash scripts/run.sh

For a combined local Switch + MergeMind demonstration, use the full-stack launcher instead (requires a Switch source checkout at `~/projects/hackathon/switch`, or set `SWITCH_DIR`):

    bash scripts/start-demo.sh

This starts Switch core on port 8000, the Gateway on port 5173, and MergeMind on port 8001. The port split is intentional: Switch owns the agent bridge port 8000. Stop the app processes with `bash scripts/stop-demo.sh`; Switch database volumes are retained.

To run the automated test suite:

    bash scripts/test.sh

Alternatively, use Docker Compose after creating .env with the setup command:

    docker compose up --build

Open http://127.0.0.1:8000. Copy the admin token from .env into the dashboard.

If using another OpenAI-compatible model endpoint, set MERGEMIND_LLM_BASE_URL, MERGEMIND_LLM_API_KEY, and MERGEMIND_LLM_MODEL in .env, then restart the app.

## Connect Switch

1. Start the combined stack with `bash scripts/start-demo.sh` (or run Switch separately).
2. Sign in to the Switch Gateway and create a Registration Key. Do not use an agent API key.
3. Create a private internal room. Switch requires at least one initial agent to create an internal-only room; use a temporary external bootstrap agent, then remove it after adding the five MergeMind agents.
4. Run `bash scripts/register-switch.sh` and enter the bridge URL, room ID, and registration key when prompted. The key input is hidden and is not stored by the script.
5. Add all five MergeMind agents to the selected room in Switch.
6. Unlock MergeMind with `MERGEMIND_ADMIN_TOKEN` from the local `.env`, and verify 5/5 agents are connected before submitting a task.

See [Local five-agent demo](docs/local-demo.md) for the full setup, room provisioning, demo flow, verification checklist, and troubleshooting. See [Switch setup](docs/switch-setup.md) for protocol details.

## API

- GET /health — public health check
- GET /api/switch/status — local admin authentication required
- POST /api/switch/register — register the five Switch agents
- POST /api/workflows — dispatch a task through the Coordinator
- GET /api/workflows and GET /api/workflows/{id} — inspect workflow and artifacts
- POST /api/workflows/{id}/approve — record human approval; does not apply the patch
- POST /api/workflows/{id}/reject — reject a proposed patch

All dashboard/API routes other than /health require the X-MergeMind-Admin-Token header.

## Project structure

    backend/app/
      agents/       # LLM provider, repository reader, role prompts, patch validation
      core/         # settings, SQLite persistence
      models/       # workflow schemas and statuses
      static/       # dashboard
      switch/       # registration, WebSocket client, worker manager
      workflow_engine.py
      main.py
    backend/tests/
    docs/
    scripts/       # local setup, start/stop, tests, Switch registration

## Verification

Run the same test command used by the project helper script:

    bash scripts/test.sh

This invokes `python -m pytest` from the repository root so the `backend` package is resolved consistently.

GitHub Actions runs the backend test suite on pushes and pull requests to main. The latest verified CI run passed 26 tests and successfully built and smoke-tested the Docker image. The suite includes API/security checks, Switch cursor/queue checks, and a controlled end-to-end test of all five workflow handoffs. It does not replace a live Switch server test.
See [run #108](https://github.com/PSP-YN/MergeMind/actions/runs/42392812447) for the latest passing CI run.

A passing CI run verifies the automated unit/API tests only. The local session has verified five real Switch agent connections in one room, but the full multi-stage workflow, real model responses, and end-to-end demonstration remain pending verification.

## Hackathon preparation

- [Submission description](docs/submission.md)
- [Demo recording script](docs/demo-script.md)
- [Best Blog article](docs/blog-entry.md)
- [Production readiness review](docs/production-readiness.md)
- [Remaining owner setup steps](docs/remaining-user-steps.md)
- [Full local Switch + MergeMind demo setup](docs/local-demo.md)

## Hackathon deliverables

- [x] Public GitHub repository
- [x] Five distinct agent roles and Switch registration flow
- [x] Official Switch WebSocket/HTTP protocol client implementation
- [x] Shared-room handoff design
- [x] Dashboard and persistent workflow records
- [x] Human review/approval gate
- [x] Publication-ready Best Blog article
- [x] Five registered MergeMind agents connected to one real Switch room (local verification)
- [ ] Live multi-agent workflow and model responses verified
- [ ] Full end-to-end demo and screenshots
- [x] Disposable patch-application and Python syntax-check sandbox
- [ ] Target repository test-suite execution in an isolated sandbox
- [ ] Live Switch demonstration, demo video, and external publication link
- [ ] Final user review and explicit submission approval

## Production deployment note

This build is intended to run locally for the hackathon. It is not yet certified for public multi-user production deployment. Before public exposure, add a production database/migrations, per-user authentication and authorization, rate limiting, managed secret storage, observability, a hardened execution sandbox, and a reviewed deployment configuration. Do not expose the local dashboard directly to the internet.

## License

MIT
