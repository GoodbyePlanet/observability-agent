# Observability Chat Agent — Progress

## Phase 1: Backend skeleton + MCP bridge
- [x] Create directory structure and `config.py`
- [x] Implement `mcp/manager.py` — connect to Tempo MCP, discover tools
- [x] Implement `agent/tool_bridge.py` — convert MCP tools to OpenAI format
- [x] Implement `api/health.py` and `api/mcp_routes.py`
- [x] Verify: start backend, confirm it connects to Tempo and lists tools

## Phase 2: Agent loop + chat endpoint
- [ ] Implement `agent/system_prompt.py` with coffee-shop domain context
- [ ] Implement `agent/loop.py` — core agent loop with streaming
- [ ] Implement `agent/conversation.py` — in-memory session history
- [ ] Implement `api/chat.py` — SSE streaming endpoint
- [ ] Implement `main.py` — FastAPI app with lifespan
- [ ] Verify: test with curl against `/api/chat`

## Phase 3: React frontend
- [ ] Scaffold Vite + React + TypeScript project
- [ ] Implement `useChat` hook with SSE parsing
- [ ] Implement chat components (ChatWindow, MessageList, MessageBubble, ChatInput)
- [ ] Implement `ToolCallCard` for inline tool call visualization
- [ ] Implement `StatusBar` showing connected MCP servers
- [ ] Style with Tailwind CSS

## Phase 4: Docker integration
- [ ] Write multi-stage Dockerfile (Node build + Python runtime)
- [ ] Add `observability-chat` service to `docker-compose.yml`
- [ ] Add `.env.example` documenting `OPENAI_API_KEY`
- [ ] Verify: `docker compose up --build`, test full flow end-to-end
