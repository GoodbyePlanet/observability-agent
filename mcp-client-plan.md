# Observability Chat Agent — Implementation Plan

## Context

The coffee-shop project has 3 Spring Boot microservices with a full observability stack (Tempo, Loki, Prometheus,
Grafana). Tempo 2.10 already exposes an MCP server at `http://tempo:3200/mcp` with tools for TraceQL queries, attribute
discovery, and trace retrieval. The goal is to build a Chat UI / AI Agent that lets the user query observability data
conversationally, using OpenAI as the LLM provider and MCP to access Tempo's tools (with Loki and Prometheus MCP servers
coming later).

## Decisions

- **Tech stack**: Python (FastAPI) backend + React (Vite) frontend
- **MCP role**: Client/host only — connects to MCP servers, does not expose its own
- **Conversation history**: In-memory (v1)
- **Port**: 8084

## Architecture

```
Browser :8084 <---> FastAPI (Python 3.12)
                        |
                        +-- POST /api/chat (SSE streaming)
                        +-- GET  /api/mcp/servers
                        +-- GET  /api/mcp/tools
                        +-- GET  /api/health
                        +-- Static files (built React app)
                        |
                        +-- AgentLoop (OpenAI function calling)
                        |       |
                        +-- MCPManager (pool of MCP ClientSessions)
                                |
                                +---> Tempo MCP (http://tempo:3200/mcp)
                                +---> Loki MCP (future)
                                +---> Prometheus MCP (future)
```

## How the MCP-to-OpenAI Bridge Works

1. **Tool Discovery**: On startup, `MCPManager` connects to each configured MCP server via SSE, calls
   `session.list_tools()`, and caches the tool definitions
2. **Conversion**: MCP `Tool.inputSchema` (JSON Schema) maps directly to OpenAI's `tools` parameter. Tools are
   namespaced as `{server}__{tool_name}` to avoid collisions
3. **Agent Loop**: User message + history + tools go to OpenAI. If the LLM returns `tool_calls`, the agent parses the
   namespaced name, routes to the correct MCP session, executes `call_tool()`, appends results, and calls OpenAI again.
   Loop repeats until the LLM produces a text response (max 10 iterations)
4. **Streaming**: Responses stream to the browser via SSE — tool call status events during execution, token events
   during text generation

## File Structure

```
observability-chat/
├── Dockerfile                    # Multi-stage: Node build + Python runtime
├── pyproject.toml                # Python project config (managed by uv)
│
├── backend/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app, lifespan, static mount
│   ├── config.py                 # Pydantic Settings (env vars)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py               # POST /api/chat (SSE streaming)
│   │   ├── mcp_routes.py         # GET /api/mcp/servers, /api/mcp/tools
│   │   └── health.py             # GET /api/health
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── loop.py               # Core agent loop (OpenAI <-> MCP tool calls)
│   │   ├── tool_bridge.py        # MCP Tool -> OpenAI function def converter
│   │   ├── system_prompt.py      # System prompt template
│   │   └── conversation.py       # In-memory conversation history
│   │
│   └── mcp/
│       ├── __init__.py
│       └── manager.py            # MCPManager: connect, discover tools, call_tool()
│
└── frontend/
    ├── package.json
    ├── vite.config.ts            # Dev proxy to backend
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── components/
        │   ├── ChatWindow.tsx     # Main chat container
        │   ├── MessageList.tsx    # Scrollable message list
        │   ├── MessageBubble.tsx  # Single message (user/assistant)
        │   ├── ToolCallCard.tsx   # Inline tool invocation display
        │   ├── ChatInput.tsx      # Text input + send button
        │   └── StatusBar.tsx      # Connected MCP servers indicator
        ├── hooks/
        │   └── useChat.ts         # SSE hook: streaming + message state
        ├── types.ts
        └── styles/
            └── globals.css
```

## Existing Files to Modify

- `docker-compose.yml` — Add `observability-chat` service (port 8084, depends on tempo)
- `.gitignore` — Ensure `.env` and `node_modules/` are excluded

## Key Dependencies

**Python (`pyproject.toml`, managed by uv)**:

- `fastapi>=0.115.0`, `uvicorn[standard]>=0.34.0` — Web framework + ASGI server
- `openai>=1.60.0` — LLM calls with streaming function calling
- `mcp>=1.5.0` — MCP client SDK (SSE transport, ClientSession)
- `pydantic-settings>=2.7.0` — Config from env vars
- `httpx>=0.28.0` — Async HTTP (dependency of MCP SDK)

**Frontend (`package.json`)**:

- `react`, `react-dom` — UI framework
- `react-markdown`, `remark-gfm` — Render assistant markdown responses
- `tailwindcss` — Styling

## Implementation Phases

### Phase 1: Backend skeleton + MCP bridge

1. Create directory structure and `config.py`
2. Implement `mcp/manager.py` — connect to Tempo MCP, discover tools
3. Implement `agent/tool_bridge.py` — convert MCP tools to OpenAI format
4. Implement `api/health.py` and `api/mcp_routes.py`
5. Verify: start backend, confirm it connects to Tempo and lists tools

### Phase 2: Agent loop + chat endpoint

6. Implement `agent/system_prompt.py` with coffee-shop domain context
7. Implement `agent/loop.py` — core agent loop with streaming
8. Implement `agent/conversation.py` — in-memory session history
9. Implement `api/chat.py` — SSE streaming endpoint
10. Implement `main.py` — FastAPI app with lifespan
11. Verify: test with curl against `/api/chat`

### Phase 3: React frontend

12. Scaffold Vite + React + TypeScript project
13. Implement `useChat` hook with SSE parsing
14. Implement chat components (ChatWindow, MessageList, MessageBubble, ChatInput)
15. Implement `ToolCallCard` for inline tool call visualization
16. Implement `StatusBar` showing connected MCP servers
17. Style with Tailwind CSS

### Phase 4: Docker integration

18. Write multi-stage Dockerfile (Node build + Python runtime)
19. Add `observability-chat` service to `docker-compose.yml`
20. Add `.env.example` documenting `OPENAI_API_KEY`
21. Verify: `docker compose up --build`, test full flow end-to-end

## Verification

1. Start the stack: `docker compose up --build`
2. Open `http://localhost:8084` — chat UI should load
3. Check `http://localhost:8084/api/health` — should report healthy + connected MCP servers
4. Check `http://localhost:8084/api/mcp/tools` — should list Tempo's 7 tools
5. Ask: "What services are sending traces?" — agent should use `tempo__get-attribute-values` and respond
6. Ask: "Show me the slowest traces from order-service in the last hour" — agent should use `tempo__traceql-search`
7. Ask: "Get me the details of trace {trace_id}" — agent should use `tempo__get-trace`
