# MergeMind Demo Script

**Target duration:** 2 minutes 30 seconds  
**Track:** Best Business Workflow  
**Prerequisite:** all five agents are connected to the same live Switch room and the configured model endpoint is responding.

## 0:00–0:20 — The business problem

Show the dashboard. Explain that an engineering request needs clear ownership, scope, repository evidence, an implementation proposal, independent review, and a human decision. A single agent performing every step makes it difficult for a team to inspect the work and challenge its assumptions.

## 0:20–0:40 — Switch is the coordination layer

Show the live Switch room with all five registered MergeMind agents. Explain that each role has a separate agent identity and that role-to-role handoffs are addressed Switch messages over the authenticated agent protocol. Keep the room visible; do not substitute screenshots or synthetic messages.

## 0:40–1:00 — Submit a real change request

In the MergeMind dashboard, enter:
- a concise engineering task;
- the business outcome the change should support;
- the expected behavior and acceptance criteria in the task description;
- a public GitHub repository that you are authorized to share with the configured model provider.

Dispatch the request through Switch. Show the Coordinator handing it to the Planner.

## 1:00–1:35 — Show the specialist handoffs

Show the Planner's scope and acceptance criteria, the Researcher's repository-backed file evidence, the Implementer's proposed diff, the sandbox validation result, and the Reviewer's independent findings. Switch room messages should visibly show the addressed handoffs between agents.

## 1:35–2:05 — Inspect the decision package

Return to the dashboard. Open the plan, research, patch, sandbox, and review artifacts. State clearly that repository research is read-only and the proposed patch was applied only to a disposable clone for validation—not to the target repository. Explain that patch applicability and syntax-only checks are not a substitute for the target project's test suite.

## 2:05–2:30 — Human decision and close

Show the approve/reject gate. Explain that approval records a human decision but does not silently apply, commit, merge, or deploy code. Close with the business outcome: one request becomes a traceable work package with clear ownership, evidence, independent review, and an accountable human decision.

## Recording checklist

- Use a real task with a clear business outcome and acceptance criteria.
- Use a repository you are authorized to share with the configured model provider.
- Keep the live Switch room and dashboard visible in the recording.
- Do not expose registration keys, agent API keys, admin tokens, or model API keys.
- Do not show simulated messages as real Switch traffic.
- Record the actual CI result and actual model/agent outcomes.
- State which checks ran and which did not; do not imply that the target repository's test suite ran.
- Rehearse once before recording; remove idle waits and failed setup attempts from the final edit, but do not fabricate results.
