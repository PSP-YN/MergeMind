# Remaining owner actions before the final demo

The repository and application code are prepared. Local services, the private room, and the five registered agent identities have been provisioned. The remaining work is to fix and verify the live WebSocket workflow, then record and publish only the verified result. Credentials must not be shared in chat or committed.

## 1. Pull and configure locally

    git clone https://github.com/PSP-YN/MergeMind.git
    cd MergeMind
    bash scripts/setup.sh

This creates a private .env with a random admin token and encryption key. Keep the file and the database private. Do not upload them to GitHub.

## 2. Start the local model

Install/start Ollama if it is not already installed, then pull the configured model:

    ollama pull qwen2.5-coder:3b

If you use another OpenAI-compatible endpoint, edit the MERGEMIND_LLM_* values in .env before starting the app.

## 3. Start MergeMind

    bash scripts/run.sh

Open http://127.0.0.1:8000 and paste MERGEMIND_ADMIN_TOKEN from your local .env into the dashboard.

## 4. Connect your Switch workspace

The combined local stack is started with `bash scripts/start-demo.sh`; it starts Switch core, Gateway, MergeMind, and checks their health. In the current demo workspace, the five MergeMind agents have already been registered and added to the private room. Do not re-register or rotate their keys while debugging. Follow [the complete local demo guide](local-demo.md).

In Switch:
1. Start or select the Switch server for the hackathon.
2. Copy its agent bridge base URL. Confirm GET /health works; do not use the Gateway URL if it differs.
3. Create a registration-type API key in the Gateway.
4. Create or select a room for the MergeMind team and copy its room ID.

In the MergeMind dashboard:
1. Enter the agent bridge base URL, registration key, and room ID.
2. Select Register five agents.
3. Invite all five agents into the selected room:
   - mergemind-coordinator
   - mergemind-planner
   - mergemind-researcher
   - mergemind-implementer
   - mergemind-reviewer
4. Confirm all five sessions remain connected over multiple heartbeat intervals. In the current run they initially connected, then detached after roughly ten heartbeat cycles; this must be fixed before the workflow can be considered live.

The registration key is not saved. Returned agent API keys are encrypted in the local database. Keep the generated encryption key in .env safe; losing it makes the saved agent keys unrecoverable.

## 5. Run and verify the live workflow

Use a public GitHub repository you are authorized to send to the configured model provider. Submit one narrow engineering task from the dashboard.

Verify:
- the Coordinator receives the task in Switch;
- the Planner, Researcher, Implementer, and Reviewer each receive addressed handoffs;
- repository evidence appears in the dashboard;
- a proposed patch and review appear;
- the workflow reaches awaiting approval;
- no repository files were changed automatically.

The sandbox applies the proposed diff only to a disposable clone, checks patch applicability, and—if Docker plus the python:3.12-slim image are available locally—runs Python syntax compilation in a read-only, no-network container. To enable that syntax check on a machine with Docker, pull the image once with: docker pull python:3.12-slim. It does not execute the target project's tests.

The automated test suite does not replace this live integration run. The current test workflow is still at `created` with no agent outputs. The Switch logs show all five WebSockets were accepted, then detached and expired after heartbeat lapse. Debug the heartbeat/reconnect path and rerun the workflow before recording.

## 6. Final recording and approval

Record the demo using docs/demo-script.md. Update the verification sections in docs/blog-entry.md and docs/submission.md with evidence from the actual run.

Do not deploy or submit until the owner has reviewed the final build, blog, demo, and submission materials and explicitly approved those actions.

## 7. External blog and LinkedIn publication

The polished article is public in the repository at [docs/blog-entry.md](https://github.com/PSP-YN/MergeMind/blob/main/docs/blog-entry.md). It has not yet been published to an external blog platform. Choose the destination (for example, an existing WordPress site or the personal portfolio) and connect the publishing account before posting.

The LinkedIn announcement should link to the final published article and describe only verified results. No external blog post or LinkedIn post has been published from this session yet. The current five-agent heartbeat failure and workflow status are recorded in [local-demo.md](local-demo.md); do not publish claims of a completed live workflow until the verification checklist passes.
