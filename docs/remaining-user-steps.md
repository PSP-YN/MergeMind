# Remaining owner actions before the final demo

The repository and application code are prepared. The following steps require access to your own machine and Switch workspace; credentials must not be shared in chat or committed.

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
4. Wait until the dashboard reports all five connected.

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

The automated test suite does not replace this live integration run. If any agent remains disconnected or a stage fails, capture the dashboard status and the relevant Switch error (redact all keys) so it can be debugged.

## 6. Final recording and approval

Record the demo using docs/demo-script.md. Replace draft-only claims in docs/blog-entry.md and docs/submission.md with evidence from the actual run.

Do not deploy or submit until the owner has reviewed the final build, blog, demo, and submission materials and explicitly approved those actions.
