# Agentic Incident Response

A small portfolio project for learning how LLM agents work under the hood and demonstrating modern AI engineering patterns.

The project simulates a production incident where an API service becomes slow and starts returning errors. A Qwen3-based agent investigates the issue using metrics, deployment information and service logs, then produces a diagnosis from the collected evidence.

The project is intentionally built without an agent framework so the orchestration, tool calling and MCP integration remain explicit and understandable.

## How it works

```text
Incident
   ↓
Qwen3 agent
   ↓
MCP tool discovery
   ↓
Native tool call
   ↓
MCP client → MCP server
   ↓
Metrics / deployment data / service logs
   ↓
Tool result added to conversation
   ↓
Agent continues investigating or gives a final diagnosis
```

The agent can make multiple tool calls across several reasoning steps. A maximum iteration limit prevents infinite loops.

## Current tools

- `get_metrics()` — returns simulated latency, GPU utilization and queue length
- `get_deployment()` — returns deployment and configuration changes
- `get_logs(service, limit)` — reads recent log entries for `api`, `db` or `worker`

The available tools and their input schemas are discovered dynamically from the MCP server with `list_tools()`. Tool execution is performed through MCP with `call_tool()`.

This keeps the agent decoupled from the underlying Python tool implementations.

## Project progression

```text
manual JSON tool selection
→ native function calling
→ multi-step agent loop
→ real log files
→ MCP discovery
→ MCP execution
→ RAG
→ evals
```

The goal is to understand each layer rather than hiding the agent logic behind a framework.

## Stack

- Python
- Qwen3-8B
- vLLM
- RunPod Serverless
- Model Context Protocol (MCP)
- AnyIO
- native function calling
- JSON Schema

## Current status

Implemented:

- native tool calling
- multi-step agent loop
- multiple tool calls per model response
- real service log files
- MCP server
- dynamic MCP tool discovery
- automatic conversion of MCP schemas to Qwen tool definitions
- MCP tool execution
- separation between agent orchestration and tool implementations

## Next steps

- RAG over runbooks and incident documentation
- systematic evaluation of tool selection and diagnosis quality
- evaluation of observed evidence vs unsupported hypotheses
- latency and token usage measurements
