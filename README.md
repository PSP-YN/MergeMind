# MergeMind

[![Backend CI](https://github.com/PSP-YN/MergeMind/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/PSP-YN/MergeMind/actions/workflows/backend-tests.yml)

**A Switch-powered AI software engineering team.** MergeMind turns an engineering task into a coordinated workflow across five specialist agents: Coordinator, Planner, Researcher, Implementer, and Reviewer. They communicate through a shared Switch room.

> Flip the Switch Hackathon · Best Business Workflow · 2026  
> **Current state:** core implementation and automated checks are in place; live Switch room and model validation remain.

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

To run the automated test suite:

    bash scripts/test.sh

Alternatively, use Docker Compose after creating .env with the setup command:

    docker compose up --build

Open http://127.0.0.1:8000. Copy the admin token from .env into the dashboard.

If using another OpenAI-compatible model endpoint, set MERGEMIND_LLM_BASE_URL, MERGEMIND_LLM_API_KEY, and MERGEMIND_LLM_MODEL in .env, then restart the app.

## Connect Switch

1. Run a Switch server and create a registration key in its Gateway.
2. Find the **agent bridge base URL**. It is not necessarily the Gateway URL.
3. Create or choose a Switch room.
4. In the MergeMind dashboard, enter the bridge URL, registration key, and room ID, then register the five agents.
5. Invite all five MergeMind agents into the selected room in Switch. Each role must be a member before it can connect.
6. Confirm all five agents show as connected, then submit a task from the dashboard.

See [Switch setup](docs/switch-setup.md) for protocol and troubleshooting details.

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

## Verification

Run tests locally:

    pytest backend/tests -q

GitHub Actions runs the backend test suite on pushes and pull requests to main. The latest verified CI run passed 26 tests and successfully built and smoke-tested the Docker image. The suite includes API/security checks, Switch cursor/queue checks, and a controlled end-to-end test of all five workflow handoffs. It does not replace a live Switch server test.

A passing CI run verifies the automated unit/API tests only. It does not substitute for a live Switch room, real model responses, or an end-to-end demonstration. Those must be verified with the user's Switch server and configured model.

## Hackathon preparation

- [Submission description](docs/submission.md)
- [Demo recording script](docs/demo-script.md)
- [Best Blog entry draft](docs/blog-entry.md)
- [Production readiness review](docs/production-readiness.md)
- [Remaining owner setup steps](docs/remaining-user-steps.md)

## Hackathon deliverables

- [x] Public GitHub repository
- [x] Five distinct agent roles and Switch registration flow
- [x] Official Switch WebSocket/HTTP protocol client implementation
- [x] Shared-room handoff design
- [x] Dashboard and persistent workflow records
- [x] Human review/approval gate
- [x] Best Blog draft
- [ ] Live Switch integration verified in a real room
- [ ] Live multi-agent workflow and model responses verified
- [ ] Full end-to-end demo and screenshots
- [x] Disposable patch-application and Python syntax-check sandbox\n- [ ] Target repository test-suite execution in an isolated sandbox
- [ ] Final blog evidence and demo video
- [ ] Final user review and explicit submission approval

## Production deployment note

This build is intended to run locally for the hackathon. It is not yet certified for public multi-user production deployment. Before public exposure, add a production database/migrations, per-user authentication and authorization, rate limiting, managed secret storage, observability, a hardened execution sandbox, and a reviewed deployment configuration. Do not expose the local dashboard directly to the internet.

## License

MIT
