# Plan: Semantic Code Search MCP Server (`code-search`)

## Context

The coffee-shop project is a microservices demo with 3 Spring Boot Java services, a Python FastAPI observability-chat
service (MCP client), and a Docker Compose orchestration stack. The user wants a **new Python service** that acts as an*
*MCP server** exposing semantic code search capabilities -- allowing natural language queries to find classes, methods,
packages, etc. across Java, Python, and TypeScript/React codebases. This bridges the gap between "I need to find where
order placement logic lives" and actually locating `OrderService.placeOrder`.

---

## Architecture Overview

```
code-search/                         # New service directory
├── pyproject.toml                   # UV/hatchling (matches observability-chat pattern)
├── config.yaml                      # Which services/repos to index
├── .env.example                     # API keys, Qdrant URL, etc.
├── Dockerfile
├── server/
│   ├── __init__.py
│   ├── main.py                      # FastMCP entrypoint (supports stdio + HTTP)
│   ├── config.py                    # Pydantic Settings
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search.py                # search_code, find_symbol, find_usages, get_code_context
│   │   ├── index.py                 # reindex
│   │   └── admin.py                 # list_indexed_services, index_stats
│   ├── indexer/
│   │   ├── __init__.py
│   │   ├── pipeline.py              # parse -> chunk -> embed -> store orchestration
│   │   ├── scheduler.py             # background scheduled reindexing
│   │   └── file_discovery.py        # directory walker with glob include/exclude
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── base.py                  # CodeSymbol dataclass, LanguageParser protocol
│   │   ├── java.py                  # Java tree-sitter parser
│   │   ├── python.py                # Python tree-sitter parser
│   │   ├── typescript.py            # TypeScript/React tree-sitter parser
│   │   └── registry.py              # extension -> parser mapping
│   ├── embeddings/
│   │   ├── __init__.py
│   │   ├── base.py                  # EmbeddingProvider protocol
│   │   └── jina.py                  # Jina Code V2 via TEI (OpenAI-compatible API)
│   └── store/
│       ├── __init__.py
│       └── qdrant.py                # Qdrant client, collection management, upsert/query
```

---

## Key Technology Choices

### Embedding Model: Jina Code V2 (`jina-embeddings-v2-base-code`) -- self-hosted via HuggingFace TEI

- Open-source, 161M params, 307 MB model size
- 768-dimensional vectors, 8192 token sequence length
- 30+ programming languages supported
- Self-hosted via `ghcr.io/huggingface/text-embeddings-inference:cpu` Docker image
- OpenAI-compatible REST API out of the box
- No API key needed, no GPU needed (~2-4 GB RAM on CPU)
- ~100-150ms per request on CPU (sufficient for this use case)

### Code Parsing: tree-sitter (py-tree-sitter)

- AST-based parsing, not regex -- reliable extraction of classes, methods, interfaces
- Grammars: tree-sitter-java, tree-sitter-python, tree-sitter-typescript, tree-sitter-javascript
- Extensible: add new languages by implementing `LanguageParser` protocol

### Vector Database: Qdrant

- Single collection `code_symbols` with payload filtering
- Deterministic UUID5 point IDs for idempotent upserts
- Payload indexes on: language, service, symbol_type, chunk_tier, annotations

### MCP Server: FastMCP (from `mcp` Python SDK)

- Dual transport: `streamable-http` (Docker) + `stdio` (Claude Code CLI)
- Same pattern as existing Tempo/Loki/Prometheus MCP servers in the stack

---

## MCP Tools Exposed

### Search Tools

1. **`search_code`** -- Semantic search with natural language queries
    - Params: `query`, `language?`, `service?`, `symbol_type?`, `limit?`
    - Returns ranked code snippets with file paths, line numbers, relevance scores

2. **`find_symbol`** -- Find class/method/interface by name (exact or fuzzy)
    - Params: `name`, `symbol_type?`, `service?`, `exact?`
    - Returns matching symbols with full source and location

3. **`find_usages`** -- Find references to a symbol across the codebase
    - Params: `symbol_name`, `service?`, `limit?`

4. **`get_code_context`** -- Get full source of a file or symbol with surrounding context
    - Params: `file_path`, `symbol_name?`, `lines_before?`, `lines_after?`

### Index Management Tools

5. **`reindex`** -- Trigger reindexing (one or all services)
    - Params: `service?`, `force?`
    - Incremental by default (skips unchanged files via SHA256 hash)

6. **`list_indexed_services`** -- Show indexed services with file/chunk counts and timestamps

7. **`index_stats`** -- Qdrant collection statistics

---

## Code Parsing Strategy

### Three-Tier Chunking

- **Tier 1 (File Summary)**: One per file -- imports, symbol inventory, package info
- **Tier 2 (Symbol)**: One per class/interface/enum/component -- full declaration or summary for large classes
- **Tier 3 (Method/Function)**: Individual methods/functions with parent class context header

### Java Parsing (tree-sitter-java)

- Extracts: classes, interfaces, enums, records, methods, constructors
- Spring metadata: `@RestController` -> controller, `@Service` -> service, etc.
- HTTP routes from `@GetMapping`/`@PostMapping` with class `@RequestMapping` base path
- Lombok awareness: detect annotations, note generated methods in description
- Inner class handling with qualified names

### Python Parsing (tree-sitter-python)

- Extracts: classes, functions, methods, decorated definitions, module-level assignments
- FastAPI routes from `@router.get`/`@router.post` decorators
- Pydantic model classification (BaseModel, BaseSettings)
- Module-level setup code (app.include_router, middleware)

### TypeScript/React Parsing (tree-sitter-typescript + tsx)

- Extracts: functions, arrow functions, interfaces, types, enums, exports
- React component detection: uppercase name + JSX return
- Hook detection: `use*` naming convention
- `memo()`/`forwardRef()` wrapper detection
- Props interface extraction

### Embedding Text Construction

Each chunk gets a structured `embedding_text`:

1. Natural language preamble (3-5 lines): language, type, name, context, purpose
2. Annotations/decorators (critical semantic information)
3. Source code (truncated if > 1500 tokens)

---

## Qdrant Payload Schema

```json
{
  "symbol_name": "placeOrder",
  "symbol_type": "method",
  "language": "java",
  "service": "order-service",
  "file_path": "order-service/src/main/java/.../OrderService.java",
  "package": "com.coffeeshop.order.service",
  "parent_name": "OrderService",
  "annotations": [
    "WithSpan",
    "Transactional"
  ],
  "signature": "public OrderResponse placeOrder(PlaceOrderRequest request)",
  "start_line": 52,
  "end_line": 96,
  "source": "...",
  "chunk_tier": "method",
  "docstring": "...",
  "indexed_at": "2026-04-18T12:00:00Z",
  "file_hash": "sha256..."
}
```

Keyword indexes: `language`, `service`, `symbol_type`, `chunk_tier`, `parent_name`, `annotations`

---

## Reindexing Strategy

1. **Incremental** (default): Compare file SHA256 hashes, skip unchanged files, delete removed files' chunks
2. **Manual trigger**: Via `reindex` MCP tool
3. **Scheduled**: Background asyncio task, configurable interval (default 1 hour, 0 to disable)
4. **Initial**: Full index on first startup when collection is empty

---

## Docker Compose Integration

### New services added to `docker-compose.yml`:

```yaml
jina-embeddings:
  image: ghcr.io/huggingface/text-embeddings-inference:cpu
  command: --model-id jinaai/jina-embeddings-v2-base-code
  ports: [ "8087:80" ]
  volumes: [ embeddings_cache:/data ]  # cache model downloads

qdrant:
  image: qdrant/qdrant:v1.14.0
  volumes: [ qdrant_data:/qdrant/storage ]
  ports: [ "6333:6333", "6334:6334" ]
  healthcheck: curl -f http://localhost:6333/healthz

code-search:
  build: ./code-search
  ports: [ "8090:8090" ]
  depends_on: [ qdrant (healthy), jina-embeddings ]
  volumes: [ ".:/code:ro" ]  # read-only mount of entire project
  environment:
    QDRANT_URL: http://qdrant:6333
    EMBEDDINGS_URL: http://jina-embeddings:80
    CODE_BASE_PATH: /code
    MCP_TRANSPORT: streamable-http
```

### New volumes: `qdrant_data`, `embeddings_cache`

### Update observability-chat MCP_SERVERS:

Add `{"name":"code-search","url":"http://code-search:8090/mcp"}` to the existing MCP_SERVERS list.

---

## Claude Code CLI Integration (stdio mode)

For local use from Claude Code, add to project `.mcp.json`:

```json
{
  "code-search": {
    "command": "uv",
    "args": [
      "run",
      "python",
      "-m",
      "server.main",
      "--transport",
      "stdio"
    ],
    "cwd": "./code-search"
  }
}
```

---

## Implementation Phases

### Phase 1: Foundation

- `pyproject.toml`, `.env.example`, `config.yaml`
- `server/config.py` -- Pydantic Settings
- `server/main.py` -- FastMCP entrypoint with transport selection
- `server/store/qdrant.py` -- Qdrant client wrapper

### Phase 2: Code Parsing

- `server/parser/base.py` -- CodeSymbol dataclass, LanguageParser protocol
- `server/parser/java.py` -- Java parser
- `server/parser/python.py` -- Python parser
- `server/parser/typescript.py` -- TypeScript/React parser
- `server/parser/registry.py` -- Extension mapping

### Phase 3: Embedding Pipeline

- `server/embeddings/base.py` -- EmbeddingProvider protocol
- `server/embeddings/jina.py` -- Jina Code V2 via TEI (OpenAI-compatible HTTP calls)
- `server/indexer/file_discovery.py` -- Directory walker
- `server/indexer/pipeline.py` -- Full pipeline orchestration

### Phase 4: MCP Tools

- `server/tools/search.py` -- search_code, find_symbol, find_usages, get_code_context
- `server/tools/index.py` -- reindex
- `server/tools/admin.py` -- list_indexed_services, index_stats

### Phase 5: Scheduling & Docker

- `server/indexer/scheduler.py` -- Background reindex task
- `Dockerfile`
- Update `docker-compose.yml` -- Add qdrant + code-search services
- Update observability-chat MCP_SERVERS

---

## Verification Plan

1. **Unit**: Parse each sample file with tree-sitter and verify extracted symbols
2. **Integration**: Index a service, query Qdrant, verify results match expectations
3. **End-to-end (stdio)**: Run MCP server in stdio mode, call `search_code` tool from Claude Code
4. **End-to-end (Docker)**: `docker compose up`, verify code-search connects to Qdrant, index completes, tools
   accessible from observability-chat
5. **Test queries**:
    - "how does order placement work" -> should find `OrderService.placeOrder`
    - "find the Product entity" -> should find `Product` class
    - "chat API endpoint" -> should find `chat.py` POST route
    - "React message component" -> should find `MessageBubble`

---

## Key Files to Reference/Modify

- `/Users/nemanjavasic/projects/coffee-shop/observability-chat/pyproject.toml` -- template for pyproject.toml
- `/Users/nemanjavasic/projects/coffee-shop/observability-chat/Dockerfile` -- template for Dockerfile
- `/Users/nemanjavasic/projects/coffee-shop/observability-chat/backend/config.py` -- template for config pattern
- `/Users/nemanjavasic/projects/coffee-shop/docker-compose.yml` -- add qdrant + code-search services
