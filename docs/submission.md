# Flip the Switch Hackathon — Submission Draft

## Project
**MergeMind — A Switch-powered AI software engineering team**

## Track
Best Business Workflow

## Short description
MergeMind turns a software engineering task into a coordinated, reviewable workflow across five specialist AI agents. A developer submits a task and a public GitHub repository. The Coordinator delegates to the Planner, Researcher, Implementer, and Reviewer. Each role is a separately registered Switch agent, and all handoffs happen through a shared Switch room using the authenticated agent protocol. The dashboard records the workflow, artifacts, and human decision.

## Problem
A single coding agent often plans, investigates, implements, and reviews its own work. The result can be difficult to inspect and easy to over-trust. Engineering work needs clear role boundaries, evidence from the repository, independent review, and a human decision before changes are applied.

## Solution
MergeMind separates those responsibilities into five Switch agents:
- Coordinator: receives tasks and delegates the workflow.
- Planner: creates scoped steps and acceptance criteria.
- Researcher: inspects public GitHub source files read-only.
- Implementer: proposes a unified diff without modifying the repository.
- Reviewer: independently checks the proposed change and reports findings.

Switch is the core coordination layer. Every role is registered independently, joins the same room, receives addressed events over WebSocket, and delegates with Switch's targeted-message operation. The dashboard is for task intake and result inspection, not a replacement for Switch.

## Technical implementation
FastAPI, SQLite, an OpenAI-compatible model endpoint (local Ollama by default), GitHub REST API for read-only repository context, and the current Switch WebSocket/HTTP agent protocol. Agent credentials are encrypted at rest; the registration key is not persisted.

## Safety
No patch is automatically applied, committed, merged, deployed, or submitted. The dashboard's approval action records the human decision only. Test execution in an isolated sandbox is not yet implemented and must not be claimed in the final demo.

## Demo evidence to capture before submission
- All five agents registered and connected in one Switch room.
- An actual task dispatched from the dashboard.
- Addressed handoffs visible in the Switch room.
- Repository-backed research, proposed diff, and independent review in the dashboard.
- CI passing and a clear statement of what was and was not executed.

## Final verification gate
This draft is not a declaration that the live workflow has passed. Replace or remove any claim not demonstrated by the final run. Do not submit until the owner has reviewed and explicitly approved the final submission.
