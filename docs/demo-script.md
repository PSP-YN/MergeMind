# MergeMind Demo Script

**Target duration:** 2 minutes 30 seconds  
**Track:** Best Business Workflow  
**Prerequisite:** all five agents are connected to the same Switch room and the model endpoint is responding.

## 0:00–0:20 — The problem
Show the dashboard and explain: a real engineering change needs planning, repository investigation, implementation, independent review, and a human decision. A single agent doing all five jobs is difficult to audit.

## 0:20–0:40 — Switch is the coordination layer
Show the Switch room with the five registered MergeMind agents. Explain that each is a separate agent connection, and role-to-role handoffs use Switch addressed messages over its agent protocol.

## 0:40–1:00 — Submit a task
In the MergeMind dashboard, enter a concise engineering task and a public GitHub repository. Dispatch it through Switch. Show the Coordinator handing it to the Planner.

## 1:00–1:35 — Show the agent handoffs
Show Planner output, Researcher file evidence, Implementer proposed diff, and Reviewer findings. Switch room messages should visibly show the addressed handoffs between agents.

## 1:35–2:05 — Inspect the artifacts
Return to the dashboard. Open plan, research, patch, and review artifacts. State clearly that the Researcher is read-only and the proposed patch has not been applied. If tests have not been executed, say so.

## 2:05–2:30 — Human decision and close
Show the approve/reject gate. Explain that approval records a human decision but does not silently apply or merge code. Close with the value: specialist agents coordinated through a shared Switch room, with evidence and human oversight.

## Recording checklist
- Use a real task and a repository you are authorized to share with the configured model provider.
- Do not expose registration keys, agent API keys, admin tokens, or model API keys.
- Keep the Switch room and dashboard visible in the recording.
- Do not show simulated messages as real Switch traffic.
- Record the actual CI result and actual model/agent outcomes.
- Rehearse once before recording; remove idle waits and any failed setup attempts from the final edit, but do not fabricate results.
