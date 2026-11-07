# LinkedIn and #HowISwitch post — review draft

**Do not publish until the public demo URL is available and the live-workflow claims have been checked.**

---

I built **MergeMind** for the Flip the Switch Hackathon: a reviewable software-engineering workflow where five specialist AI agents collaborate through a shared Switch room.

Instead of asking one agent to plan, research, implement and review its own work, MergeMind separates the responsibilities:

- **Coordinator** — owns intake and delegates the task.
- **Planner** — defines steps, risks and acceptance criteria.
- **Researcher** — gathers evidence from a public GitHub repository.
- **Implementer** — proposes a unified diff without changing the target repository.
- **Reviewer** — independently checks the proposal and calls out missing tests.

Switch is the coordination layer: each role is registered as a separate agent, and the handoffs use the authenticated agent protocol and a shared room. The dashboard keeps the plan, repository evidence, proposed diff, review and human decision together.

The design deliberately keeps a human in control. Approval records a decision; it does not silently apply, commit or merge the patch.

Project repository: https://github.com/PSP-YN/MergeMind

Live demo: [ADD PUBLIC DEPLOYMENT URL AFTER IT IS VERIFIED]

Demo video: [ADD PUBLIC YOUTUBE OR LOOM URL AFTER RECORDING]

I am submitting MergeMind to **Best Business Workflow** and **Best Blog**.

#HowISwitch #FlipTheSwitch #AIEngineering #OpenSource #MultiAgentSystems #DeveloperTools

---

## Before publishing

- Replace the live demo placeholder with a tested public URL.
- Add the demo video URL after the user records and publishes it.
- Keep the "five agents collaborate through a shared room" wording only if
  the real Switch room and all five agents have been demonstrated.
- Add the published DEV/Hashnode article link once available.
- Review the post in LinkedIn preview and publish manually.
