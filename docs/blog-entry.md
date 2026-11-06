# Blog Entry — Draft Outline

**Working title:** From One Coding Agent to an Engineering Team: Building MergeMind with Switch

**Track:** Best Blog (AirPods 5)

> Draft outline only. This must be rewritten with actual implementation details, screenshots, verified outcomes, and the real Switch workflow before it is considered submission-ready.

## 1. The problem: coding agents are powerful, but coordination is missing
Explain why an engineering task needs planning, repository research, implementation, independent review, and human decision-making—not just a single prompt.

## 2. Why Switch
Describe Switch as the shared room and coordination layer. Include concrete protocol details only after testing the real connection and agent messages.

## 3. MergeMind's workflow
- Issue/task intake
- Planner decomposes work
- Researcher gathers codebase context
- Implementer creates a proposed change
- Reviewer independently evaluates it
- Human reviews the diff and approves/rejects

## 4. Architecture and tradeoffs
Explain API, workflow state, Switch agent protocol, isolated execution, and why the approval gate is part of the design.

## 5. What worked, what failed, what changed
Include actual engineering challenges and decisions. Do not invent challenges or outcomes.

## 6. Demo walkthrough
Show a reproducible task, Switch room messages, workflow timeline, review findings, and human approval gate.

## 7. Lessons and next steps
Summarize measurable evidence, limitations, and future improvements.

## Evidence required before finalizing
- Switch room/agent screenshots
- A real task execution trace
- Test output and CI status
- Demo screenshots or video
- Accurate claims about the code actually implemented
