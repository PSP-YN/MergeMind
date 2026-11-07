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

The latest verified [GitHub Actions run #106](https://github.com/PSP-YN/MergeMind/actions/runs/42392532584) completed successfully: **26 automated tests passed**, the Docker image built, and the container health smoke test passed.

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


---

## Ready-to-paste submission form

**Team:** CHAKRAVYUHA  
**Team code:** WXT2YB  
**Project title:** MergeMind — A Reviewable Engineering Workflow with Five AI Agents

**Tracks:** Best Business Workflow; Best Blog

### Project description

MergeMind turns a software change request into a reviewable work package using five specialist AI agents coordinated through Switch. The Coordinator delegates to the Planner, Researcher, Implementer and Reviewer. Each role is a separately registered Switch agent in a shared room. The workflow produces a scoped plan, repository-backed evidence, a proposed unified diff, an independent review and a human approval or rejection record. It is designed for engineering teams that need clearer ownership, traceable handoffs and a review boundary before code changes are applied. MergeMind does not silently write to, commit, merge or deploy changes to the target repository.

### GitHub repository

https://github.com/PSP-YN/MergeMind

### Demo video

**Pending owner recording.** Record a video under three minutes, upload it to YouTube or Loom as public/unlisted, then paste the final URL here. Use [demo-script.md](demo-script.md).

### Live demo or deployment

**Pending public deployment and end-to-end verification.** Do not paste a local URL or an unverified preview. The public URL must be reachable by a judge without signing in and must not expose admin credentials or agent secrets.

### Pull requests

Add the URLs of genuine upstream pull requests to `sandbox-quantum/switch` only after they have been opened. Do not use fork branch URLs as substitutes for PR URLs. Current prepared contribution branch: [hackathon/808-contributor-quickstart](https://github.com/PSP-YN/switch/tree/hackathon/808-contributor-quickstart); an upstream PR has not yet been opened.

### Blog post

Publish [blog-entry.md](blog-entry.md) on DEV Community first (recommended) or Hashnode. Follow [blog-publishing-guide.md](blog-publishing-guide.md), then paste the public article URL. The repository copy is not an externally published blog URL.

### Your Wispr usage card

Leave blank. This submission is not entering Code with Wispr.

### Your #HowISwitch post

Publish the reviewed text in [linkedin-post.md](linkedin-post.md) after replacing the live demo and video placeholders with verified public URLs. Paste the resulting public LinkedIn post URL into this field.

### How did you use Switch in your project?

MergeMind uses Switch as its agent-to-agent coordination layer. It registers five distinct roles—Coordinator, Planner, Researcher, Implementer and Reviewer—as separate Switch agents and connects them to one shared room. Each agent receives room events through Switch's authenticated WebSocket agent protocol. Handoffs are addressed messages sent through Switch's HTTP agent operations, rather than hidden local function calls. The dashboard handles task intake and human review; Switch carries the collaboration and handoffs. The workflow is designed to take a change request through planning, public-repository research, a proposed diff and independent review, then stop for a human decision. The current implementation supports the Switch agent protocol and automated handoff tests; the real Switch room, all five live connections and configured-model run must be demonstrated in the final video before claiming live verification.

### What did you like about Switch, and what would you improve?

Switch makes agents participants in the team's existing collaboration space instead of isolated chat windows. The shared room gives the workflow a visible handoff trail, and the provider-agnostic agent protocol makes it practical to assign different responsibilities to different agent runtimes. The part that matters most to MergeMind is that the collaboration layer is real: agents can be addressed as teammates and share room context. The setup experience could be improved with a shorter contributor quickstart, clearer visibility into agent connection and message-delivery state, and more guided troubleshooting when an agent has not joined a room or cannot accept a handoff. Better end-to-end test fixtures for real provider CLIs and messaging platforms would also make new integrations easier to validate.

## Final owner checklist

- [ ] Review the final public deployment and verify it in a signed-out browser.
- [ ] Connect and verify all five agents in one real Switch room.
- [ ] Run a real model-backed workflow and capture the handoffs.
- [ ] Record and publish the demo video (under three minutes).
- [ ] Publish the blog article and add its public URL.
- [ ] Publish the #HowISwitch post and add its public URL.
- [ ] Add only real upstream PR URLs.
- [ ] Review every field and explicitly approve the hackathon submission.
