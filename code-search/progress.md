# Code Search MCP Server - Progress Tracker

## Phase 1: Foundation
- [x] `pyproject.toml` -- project config with dependencies
- [x] `.env.example` -- environment variable template
- [x] `config.yaml` -- service indexing configuration
- [x] `.dockerignore`
- [x] `server/__init__.py`
- [x] `server/config.py` -- Pydantic Settings
- [x] `server/main.py` -- FastMCP entrypoint (stdio + HTTP transport)
- [x] `server/store/__init__.py`
- [x] `server/store/qdrant.py` -- Qdrant client wrapper, collection management

## Phase 2: Code Parsing
- [x] `server/parser/__init__.py`
- [x] `server/parser/base.py` -- CodeSymbol dataclass, LanguageParser protocol
- [x] `server/parser/java.py` -- Java tree-sitter parser (classes, interfaces, enums, records, methods, Spring metadata, Lombok)
- [x] `server/parser/python.py` -- Python tree-sitter parser (classes, functions, FastAPI routes, Pydantic models)
- [x] `server/parser/typescript.py` -- TypeScript/React tree-sitter parser (components, hooks, interfaces, types)
- [x] `server/parser/registry.py` -- extension -> parser mapping

## Phase 3: Embedding Pipeline
- [x] `server/embeddings/__init__.py`
- [x] `server/embeddings/base.py` -- EmbeddingProvider protocol
- [x] `server/embeddings/jina.py` -- Jina Code V2 via TEI (OpenAI-compatible HTTP)
- [x] `server/indexer/__init__.py`
- [x] `server/indexer/file_discovery.py` -- directory walker with glob include/exclude
- [x] `server/indexer/pipeline.py` -- parse -> chunk -> embed -> store orchestration

## Phase 4: MCP Tools
- [x] `server/tools/__init__.py`
- [x] `server/tools/search.py` -- search_code, find_symbol, find_usages, get_code_context
- [x] `server/tools/index.py` -- reindex (manual trigger only)
- [x] `server/tools/admin.py` -- list_indexed_services, index_stats

## Phase 5: Docker Integration
- [x] `Dockerfile`
- [x] Update `docker-compose.yml` -- add jina-embeddings, qdrant, code-search services
- [x] Update observability-chat `MCP_SERVERS` env var
- [x] `uv.lock` generated

## Next Steps
- [ ] `docker compose up code-search qdrant jina-embeddings` -- bring up the stack
- [ ] Call `reindex` MCP tool to index the services
- [ ] Test with `search_code`, `find_symbol` queries
