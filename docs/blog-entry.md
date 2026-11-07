# Building MergeMind: A Reviewable Engineering Workflow with Five AI Agents and Switch

*Flip the Switch Hackathon 2026 · Best Business Workflow · Best Blog*

**Project:** [PSP-YN/MergeMind](https://github.com/PSP-YN/MergeMind)  
**Focus:** engineering change requests, specialist-agent handoffs, evidence, independent review, and human approval  
**Tags:** AI agents, Switch, software engineering, workflow automation, human-in-the-loop

## The problem is bigger than generating code

A software change is not one prompt. Before a team can safely ship it, someone has to understand the request, define its scope, inspect the repository, propose an implementation, check the result, and decide whether it is acceptable.

A single coding agent can attempt every step. That creates a process problem: the same agent may plan the work, implement it, and then review its own assumptions. Context gets copied between tools, decisions become difficult to trace, and a confident answer can look like verified work even when no tests were run.

MergeMind explores a more accountable model. It turns an engineering request into a review package produced by five specialist agents, coordinated through a shared Switch room. The outcome is not an automatically merged code change. It is a traceable proposal that a human can inspect and accept or reject.

## The business workflow

The workflow is designed for a product or engineering team that receives a change request and needs to move it from intake to a controlled decision.

| Stage | Owner | Output | Business value |
|---|---|---|---|
| Intake and coordination | Coordinator | Task record and delegated work | One clear entry point and an accountable workflow owner |
| Planning | Planner | Ordered steps, assumptions, risks, and acceptance criteria | Scope is agreed before implementation begins |
| Repository research | Researcher | Relevant file paths and source evidence | Decisions are grounded in the actual codebase |
| Implementation proposal | Implementer | A unified diff, not a repository mutation | The team can inspect the proposed change before it is applied |
| Independent review | Reviewer | Findings on correctness, security, scope, and missing tests | The implementer does not approve its own work |
| Human decision | Engineer or owner | Approval or rejection record | A person remains accountable for the decision |

Each stage has a bounded responsibility and a handoff. The dashboard stores the workflow state and artifacts so the team can see what was requested, what each role produced, and where the process stopped.

The practical benefit is not a claim that AI replaces an engineer. It is a way to reduce context switching, make handoffs inspectable, and prevent an unreviewed model-generated diff from silently becoming a production change.

## Why Switch is the coordination layer

Switch is not a notification add-on in MergeMind. It is the system that lets the five roles work as a team.

Each role is registered as a separate Switch agent:

1. Coordinator
2. Planner
3. Researcher
4. Implementer
5. Reviewer

All five join the same room. MergeMind uses the authenticated Switch agent protocol: WebSocket connections receive room events, while HTTP operations send targeted messages and perform agent actions. A handoff is addressed to the next role, so the work moves through the shared room rather than through hidden local function calls.

That design has two important consequences:

- **Shared context:** the room is the common collaboration surface for the agents and the human team.
- **Traceable delegation:** the dashboard records workflow artifacts, while the room carries the actual agent-to-agent handoffs.

The client also persists its connection identity and event cursor, acknowledges events after processing, and handles reconnects. This matters because a workflow is only useful if it can recover from a dropped connection without silently skipping work. MergeMind does not pretend that a local-only message path is equivalent to a working Switch connection.

## What the five agents do

### 1. Coordinator: own the request

The Coordinator receives the task and starts the workflow. It delegates planning rather than trying to solve the whole request itself. Its job is to keep the work moving and preserve the task context.

### 2. Planner: define what “done” means

The Planner turns the request into ordered steps, assumptions, risks, and acceptance criteria. This gives the next roles a bounded objective and gives the Reviewer something concrete to check against.

### 3. Researcher: bring evidence from the repository

The Researcher reads public GitHub repository metadata and selected source files through a read-only API. It reports relevant paths and excerpts. It does not invent repository behavior or write to the target repository.

### 4. Implementer: propose a change

The Implementer uses the plan and research evidence to produce a unified diff. It does not commit or apply that diff to the real repository.

The proposal is checked in a disposable clone. The sandbox verifies that the diff applies cleanly and checks whitespace. When Docker and the required image are available, it can also run Python syntax compilation in a no-network container with a read-only source mount.

### 5. Reviewer: challenge the proposal

The Reviewer inspects the proposed diff independently for correctness, security, scope, and missing tests. It must distinguish a syntax check from a test run. The repository's own test suite is not executed by the current sandbox, so the Reviewer cannot claim that the change passed those tests.

The human then inspects the plan, research, diff, and review in the dashboard and records approval or rejection. Approval is a decision record only; it does not apply the patch.

## Architecture and implementation

MergeMind uses:

- **FastAPI** for the local dashboard and API.
- **SQLite** for workflow state, event history, and artifacts.
- **Switch's authenticated WebSocket and HTTP agent protocol** for room membership, events, and targeted handoffs.
- **GitHub's REST API** for read-only access to public repositories.
- **An OpenAI-compatible model endpoint**, configured for local Ollama by default.
- **A disposable-clone sandbox** for patch applicability checks and optional Python syntax compilation.
- **A plain HTML, CSS, and JavaScript dashboard** for task intake and human review.

The default local model endpoint is configured for Ollama with qwen2.5-coder:3b. A different OpenAI-compatible endpoint can be configured in the local environment file.

Credentials have separate lifecycles. The Switch registration key is used for agent creation and is not persisted. Agent API keys are encrypted at rest with Fernet using a key stored in the local environment file. The dashboard API is protected by a locally generated admin token. The documented run configuration binds to localhost.

## Reproducing the local build

The repository contains the setup and run scripts:

    git clone https://github.com/PSP-YN/MergeMind.git
    cd MergeMind
    bash scripts/setup.sh

For the default local model, start Ollama and pull the configured model:

    ollama pull qwen2.5-coder:3b

Then start MergeMind:

    bash scripts/run.sh

Open http://127.0.0.1:8000 and enter the admin token from the local environment file.

To connect Switch:

1. Start a Switch server and create a room.
2. Create a registration key and identify the agent bridge base URL. The bridge URL is not necessarily the Gateway URL.
3. In the MergeMind dashboard, enter the bridge URL, registration key, and room ID.
4. Register the five roles.
5. Invite all five agent names into the selected Switch room.
6. Wait until all five connections show as connected.
7. Submit a real task against a public repository that you are authorized to share with the configured model provider.

The detailed steps and troubleshooting notes are in [Switch setup](switch-setup.md). The [demo script](demo-script.md) describes what to show without presenting simulated messages as live Switch traffic.

## Safety is part of the workflow

The system deliberately avoids silent side effects:

- Repository inspection is read-only and currently supports public GitHub repositories.
- Repository contents and task descriptions are treated as untrusted input.
- Proposed diffs are validated as unified diffs and checked for unsafe paths.
- Patch application happens only in a disposable clone.
- The current sandbox does not run arbitrary project commands or the target repository's test suite.
- No patch is applied to the target repository.
- No commit, pull request, merge, deployment, or hackathon submission is created.
- Human approval records a decision; it does not authorize an automatic write.
- Switch registration credentials are not stored, and agent API keys are encrypted at rest.

These are not temporary marketing claims. They define what the current implementation is allowed to do.

## What is verified, and what is not

The latest verified GitHub Actions run is [run #106](https://github.com/PSP-YN/MergeMind/actions/runs/42392532584). It completed successfully with 26 automated tests passing. The same run built the Docker image and completed a container health smoke test.

The automated suite covers API and security behavior, encrypted credential storage, Switch event queue and cursor handling, and a controlled end-to-end test of the five role handoffs.

There is an important limit: **a passing test suite is not the same as a live Switch demonstration**. At the time this article was prepared, the live Switch room and real model-response workflow still needed to be exercised. The code's protocol and workflow behavior are covered by automated tests, but a real server, room, and configured model must be used to verify the complete path. The sandbox also does not run the target repository's test suite.

MergeMind is a local, single-user hackathon build. It is not certified as a public multi-user production service. Public deployment would require user identity and tenant isolation, a production database and migrations, rate limiting, observability, secret rotation, and a more comprehensive execution sandbox.

## What I learned

**Multi-agent work needs explicit ownership.** Five agents are not automatically better than one. They become useful when each has a bounded job, a defined output, and a clear next handoff.

**The collaboration layer must be real.** If the room is only used to display notifications while the actual work happens elsewhere, the team is not truly collaborating through Switch. In MergeMind, the role handoffs are addressed Switch messages.

**Evidence is more useful than confidence.** The Researcher should point to repository files. The Implementer should produce a diff. The Reviewer should name missing tests. The dashboard should show the artifacts and the human decision.

**Human approval must have a real boundary.** An approval button is not meaningful if the application can silently write to the repository anyway. The current build records the decision and leaves repository changes under human control.

## Next steps

The next milestone is a recorded live run: connect all five agents to a real Switch room, dispatch a real task, inspect the handoffs and artifacts, and capture the result. After that, the sandbox can be extended to run explicitly approved test commands under strict dependency, network, time, filesystem, and resource limits.

MergeMind's goal is to make the path from request to review more coordinated and accountable—not to remove the engineer from the decision.
 
## Project links

- [Source repository](https://github.com/PSP-YN/MergeMind)
- [README and quick start](https://github.com/PSP-YN/MergeMind#readme)
- [Architecture](architecture.md)
- [Switch setup](switch-setup.md)
- [Demo script](demo-script.md)
- [Production readiness review](production-readiness.md)
- [Flip the Switch Hackathon](https://www.devtoolsacademy.com/hackathons/flip-the-switch)
