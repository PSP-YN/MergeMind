# From One Coding Agent to an Engineering Team: Building MergeMind with Switch

*Best Blog entry draft · Flip the Switch Hackathon 2026 · Best Business Workflow*

> Editorial status: complete first draft, pending a live Switch demonstration. Before publication, replace the evidence notes with real screenshots, test results, and observations from the final run. Do not present the current implementation as live-verified until that run succeeds.

## The problem: coding agents still need a team

A software change rarely consists of one action. Someone needs to understand the request, break it into manageable work, inspect the codebase, propose a change, and independently review the result. A single coding agent can attempt all of those steps, but the process becomes difficult to inspect: the same agent plans, implements, and approves its own work.

MergeMind explores a different model. Instead of asking one agent to do everything, it coordinates five specialist agents and makes their handoffs visible in a shared Switch room.

## Why Switch is the foundation

Switch provides the shared collaboration surface. MergeMind registers five independent agents—Coordinator, Planner, Researcher, Implementer, and Reviewer—and connects each one to the same room.

The application uses the current Switch agent protocol: authenticated WebSocket connections for incoming room events and HTTP operations for agent actions. Each worker responds to addressed messages and hands work to another agent using Switch's targeted-message operation. This makes Switch the coordination layer rather than a decorative notification channel.

The registration flow creates each agent once, retains its agent API key encrypted locally, and configures owner-and-owner-agents addressing so the team can delegate internally.

## The workflow

A developer submits a task, a short description, and a public GitHub repository.

1. **Coordinator** accepts the task and delegates planning.
2. **Planner** creates ordered implementation steps, assumptions, risks, and acceptance criteria.
3. **Researcher** reads repository metadata and selected source files through GitHub's read-only API. It reports file paths and evidence rather than inventing repository behavior.
4. **Implementer** uses the plan and repository excerpts to produce a proposed unified diff.
5. **Reviewer** independently inspects the proposal for correctness, security, scope, and missing tests.
6. **Human reviewer** inspects the artifacts in the dashboard and records approval or rejection.

The patch is never applied automatically. Approval is a decision record, not permission for the application to modify a repository.

## Architecture and safety choices

MergeMind uses FastAPI for the local dashboard and API, SQLite for workflow persistence, an OpenAI-compatible model endpoint for the specialist reasoning steps, and the Switch WebSocket/HTTP protocol for agent coordination.

The default model configuration points to local Ollama, so a developer can run the workflow without a hosted model key. The dashboard can be configured to use another compatible endpoint when required.

Credentials have separate lifecycles. The Switch registration key is used transiently and is not saved. Each returned agent API key is encrypted at rest with a Fernet key stored in the local environment file. The local admin token protects dashboard API actions.

Repository inspection is read-only. Model-generated patches are validated as unified diffs and checked for unsafe paths. The application does not execute arbitrary model-generated shell commands, apply diffs, commit, merge, or deploy.

## What is deliberately not claimed

This project distinguishes generated recommendations from verified execution. The current workflow does not yet apply patches or execute the repository's test suite in an isolated sandbox. The Reviewer receives no test output and must say that tests were not run. The app is a local hackathon build, not a certified multi-user production service.

This boundary matters: a convincing demo should show what the system actually did, not what a roadmap says it might do.

## What the live demo must prove

The final demo should show the five agents connected to one Switch room, a task dispatched from the MergeMind dashboard, addressed handoffs between roles, a repository-backed research report, a proposed patch, an independent review, and the human approval gate.

Evidence to insert before publication:
- Screenshot of the five registered agents and room membership.
- Screenshot or recording of actual addressed agent handoffs in Switch.
- Dashboard screenshot showing the workflow timeline and artifacts.
- Passing automated test and CI results.
- A short explanation of any failure encountered during the live run and how it was corrected.

## Lessons and next steps

The main design lesson is that multi-agent work needs explicit boundaries. Roles should have bounded responsibilities, each handoff should carry enough context to be useful, and the review stage should be independent of implementation. Switch makes the collaboration trace visible; the dashboard makes the result inspectable.

The next engineering step is an isolated execution sandbox that can apply a proposed patch to a disposable worktree, run a constrained test command, and return verifiable test output without exposing the host. That should be added only with resource limits, network restrictions, and a human-controlled path for any change to the real repository.

MergeMind's goal is not to remove the engineer from the loop. It is to make the work between request and review more coordinated, inspectable, and accountable.
