# Switch setup and protocol notes

MergeMind registers five independent agents and connects them to one Switch room.

## Required Switch details

- **Agent bridge base URL:** use the server address whose public health endpoint responds at GET /health. The Gateway URL and agent bridge URL may differ.
- **Registration key:** a registration-type bearer key created in the Switch Gateway. It is used only for POST /agents.
- **Room ID:** the Switch room in which all five agents will collaborate.

Do not paste these credentials into GitHub issues, commits, or chat messages. Enter the registration key only in the local dashboard over localhost.

## What MergeMind registers

Each agent uses connector_type mergemind and an integration profile with:
- connection_model: always_on
- message_exchange: true
- pre_invocation_mediation: []
- post_invocation_mediation: []
- event_reporting: []

The five names are:
- mergemind-coordinator
- mergemind-planner
- mergemind-researcher
- mergemind-implementer
- mergemind-reviewer

After registration, MergeMind sets addressing to owner_and_owner_agents so the agents registered by the same owner can hand work to each other.

Agent API keys are encrypted in the local SQLite database using MERGEMIND_ENCRYPTION_KEY. The registration key is not stored. Losing the encryption key makes the stored agent keys unrecoverable.

## Connection protocol

MergeMind uses the current Switch agent protocol:
- Authenticated WebSocket: /agents/{agent_id}/connection/ws
- Authorization: Bearer <agent API key>
- A persistent client-generated connection_id
- Room claim through the rooms query parameter
- JSON event frames with event and data fields
- Application-level ping frames answered with {"type":"pong","cursor":n}
- HTTP agent operations at /agents/{agent_id}/ops/{operation}
- X-Switch-Connection-Id header for operations that depend on the connected room

SSE is deprecated in the current Switch documentation; MergeMind uses WebSocket.

The client handles message events only when payload.addressed is true. It routes task handoffs through send_targeted_message and publishes the final review summary through post_message.

## Important room setup step

Registering an agent does not automatically make it a member of an existing room. After registration, invite all five agents to the room in Switch. MergeMind will retry connections while an agent is not yet able to claim the room. The dashboard should show five connected agents before starting a workflow.

## Troubleshooting

| Symptom | Check |
|---|---|
| Health check fails | The URL is the agent bridge base URL, not the Gateway URL; GET /health must work. |
| Registration returns 401 | Use a registration key, not an agent API key. |
| Registration returns 409 | The agent name already exists. Do not enable overwrite casually; it rotates the API key. |
| Agent remains disconnected | Invite it to the selected room; check the server URL and room ID. |
| Agent refuses another agent's message | Verify all five agents belong to the same owner and addressing is owner_and_owner_agents. |
| Workflow fails at LLM stage | Confirm Ollama is running, the configured model is pulled, or the hosted OpenAI-compatible endpoint is reachable. |
| Reconnect repeatedly fails | Check Switch logs and whether another process is taking over the same connection. Only one MergeMind app instance should use a given local agent configuration. |

## Official references

- [Switch agent protocol](https://docs.switchagents.ai/switch-rooms/internals/agent-protocol)
- [Agent connection and WebSocket](https://docs.switchagents.ai/switch-rooms/internals/agent-connection)
- [Agent event catalog](https://docs.switchagents.ai/switch-rooms/internals/agent-events)
- [Work in a room](https://docs.switchagents.ai/switch-rooms/using/work-in-a-room)
