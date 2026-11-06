# MergeMind

**A Switch-powered AI software engineering team.** MergeMind turns a GitHub issue into a coordinated, reviewable engineering workflow using specialized agents that share context through Switch.

> Flip the Switch Hackathon · Best Business Workflow · 2026  
> **Status:** implementation in progress. This repository is an early scaffold, not a finished product.

## Why MergeMind

Most coding-agent demos are a single prompt followed by a code dump. MergeMind demonstrates a team workflow: a task is planned, research and implementation are delegated, changes are reviewed, and a human approves before anything is applied.

## Planned workflow

1. A developer submits a GitHub issue or engineering task.
2. **Planner** converts it into bounded work items and acceptance criteria.
3. **Researcher** inspects the repository context and reports relevant files and constraints.
4. **Implementer** proposes a patch in an isolated workspace.
5. **Reviewer** evaluates the patch and test results.
6. A human reviews the proposed changes and explicitly approves or rejects them.
7. MergeMind records a final summary and workflow trace.

Switch is intended to be the shared coordination layer—not a decorative integration. Agent-to-agent handoffs and room context will use Switch. The local demo mode is clearly labeled and exists to make the workflow reproducible without credentials.

## Safety boundaries

- No automatic merge, deployment, or destructive repository operation.
- Human approval required before applying a patch.
- Repository content and issue text are treated as untrusted input.
- Secrets are read from environment variables and must never be committed.
- Demo mode must not claim that simulated agents actually ran tools or modified code.

## Architecture (planned)

- **API:** Python + FastAPI
- **Workflow engine:** explicit state machine and typed task/event models
- **Switch adapter:** bridge/agent protocol integration; see [Switch agent protocol](https://docs.switchagents.ai/switch-rooms/internals/agent-protocol)
- **Frontend:** React + TypeScript dashboard (next phase)
- **Execution:** isolated local workspaces; Docker support planned
- **Tests:** pytest; integration tests will be opt-in

## Repository layout

```
backend/
  app/
    api/          # FastAPI routes
    core/         # settings and workflow state
    agents/       # agent roles and registry
    switch/       # Switch integration boundary
    models/       # request/response models
  tests/
docs/
```

## Quick start

Requirements: Python 3.11+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
uvicorn backend.app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the API docs and http://127.0.0.1:8000/health for health status.

At this stage, only the API scaffold and workflow model are being built. Switch connectivity, real repository analysis, code execution, frontend, and end-to-end demo will be added and tested in subsequent phases.

## Hackathon deliverables checklist

- [x] Public repository initialized
- [ ] Switch integration used as the core coordination mechanism
- [ ] Multi-agent workflow end-to-end
- [ ] Interactive UI and working demo
- [ ] Reproducible setup and tests
- [ ] Demo video and final README walkthrough
- [ ] Best Blog entry drafted and reviewed
- [ ] User review before deployment or submission

## License

MIT
