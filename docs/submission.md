# Flip the Switch Hackathon — Submission Draft

## Project

**MergeMind — A Switch-powered, reviewable engineering workflow**

## Track

Best Business Workflow

## Short description

MergeMind turns an engineering change request into a decision-ready work package through five specialist AI agents. A developer submits a task and a public GitHub repository. The Coordinator delegates to the Planner, Researcher, Implementer, and Reviewer. Each role is a separately registered Switch agent; all agent-to-agent handoffs use a shared Switch room and the authenticated agent protocol. The dashboard preserves the workflow state, evidence, proposed diff, review, and human decision.

## The business workflow

The workflow follows a controlled sequence:

1. **Intake:** the Coordinator accepts the request and owns the workflow.
2. **Scope:** the Planner defines steps, assumptions, risks, and acceptance criteria.
3. **Evidence:** the Researcher inspects the actual public repository and returns relevant file paths and excerpts.
4. **Proposal:** the Implementer produces a unified diff in a disposable workspace.
5. **Quality gate:** the Reviewer independently evaluates the proposal for correctness, security, scope, and missing tests.
6. **Decision:** a human reviews the artifacts and records approval or rejection.

The business value is traceability and clearer ownership: a team can follow a request from intake to decision without relying on copied context or trusting a single agent to review its own work. The workflow is designed to reduce context switching and make risks visible. It does not claim measured time savings or autonomous production delivery.

## Problem

A single coding agent often plans, investigates, implements, and reviews its own work. The result can be difficult to inspect and easy to over-trust. Engineering work needs clear role boundaries, evidence from the repository, independent review, and a human decision before changes are applied.

## Solution

MergeMind separates those responsibilities into five Switch agents:

- **Coordinator:** receives tasks and delegates the workflow.
- **Planner:** creates scoped steps and acceptance criteria.
- **Researcher:** inspects public GitHub source files read-only.
- **Implementer:** proposes a unified diff without modifying the repository.
- **Reviewer:** independently checks the proposed change and reports findings.

## Why Switch is essential

Switch is the coordination layer, not a decorative notification integration. Every role has its own Switch identity, joins the same room, receives room events over the authenticated WebSocket protocol, and delegates work through Switch's targeted-message operation. The room carries the agent handoffs and shared context; the dashboard is only the task-intake and review surface.

The client persists its connection identity and event cursor, acknowledges events after processing, and handles reconnects. Without Switch, the five agents would not share the room or perform the addressed handoffs that define this workflow.

## Technical implementation

FastAPI, SQLite, an OpenAI-compatible model endpoint (local Ollama by default), GitHub REST API for read-only repository context, the current Switch WebSocket/HTTP agent protocol, and a disposable-clone patch validation sandbox. Agent credentials are encrypted at rest; the registration key is not persisted.

## Safety

- No patch is automatically applied to the target repository.
- No commit, pull request, merge, deployment, or submission is automatically created.
- The dashboard's approval action records the human decision only.
- Patch paths and unified-diff applicability are checked in a disposable clone.
- Optional Python syntax compilation runs in a no-network, read-only container when Docker and the required image are already available.
- The target repository's own test suite is not executed. A syntax check must never be described as a passing project test suite.

## Verification status

The latest verified [GitHub Actions run #108](https://github.com/PSP-YN/MergeMind/actions/runs/42392812447) completed successfully: the Backend tests workflow passed on the submission-preparation pull request. Earlier verified CI also recorded **26 automated tests passed**, a successful Docker image build, and a container health smoke test. Treat the latest workflow result as CI evidence, not proof of a live Switch session.

This is automated implementation evidence, not proof of a live Switch session. The live Switch room, five connected agents, and real model-response workflow still need to be exercised and recorded. Do not claim those steps are complete until they have been demonstrated.

## Demo evidence to capture before submission

- All five agents registered and connected in one real Switch room.
- A real task dispatched from the dashboard.
- Addressed handoffs visible in the live Switch room.
- Repository-backed research, proposed diff, and independent review in the dashboard.
- The human approval or rejection action and the resulting decision record.
- The exact CI run and a clear statement of what was and was not executed.

Do not use synthetic room messages or a staged screenshot as evidence of a live run.

## Final verification gate

This draft is not a declaration that the live workflow has passed. Replace or remove any claim not demonstrated by the final run. Do not submit until the owner has reviewed and explicitly approved the final submission.
