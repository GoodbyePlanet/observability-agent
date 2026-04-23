# Coffee Shop: Observability, MCPs & AI Agents

Excalidraw: https://excalidraw.com/#json=tDw5wf64-4Ns3Dwo5mdtV,rW21pxrC5MEW5TLzKMzoTA

---

## Agenda

1. **Observability** — OpenTelemetry and the 3 Pillars
2. **MCPs** — Model Context Protocol: Host, Client, Servers
3. **AI Agents** — The Agent Loop and Why It Matters

---

# Part 1: Observability with OpenTelemetry

---

## What is Observability?

Observability is the ability to understand **what is happening inside a system** by looking at its outputs — without having to deploy new code or reproduce bugs.

Think of it like a doctor's toolkit:
- **Logs** = Patient's medical history (what happened)
- **Metrics** = Vital signs monitor (heart rate, temperature — is something abnormal?)
- **Traces** = MRI scan (follow the full path of a request through the body)

Together, they let you **diagnose problems fast** — often in minutes instead of hours.

---

## The 3 Pillars of Observability

### Traces
A **trace** follows a single request as it travels across multiple services. Each step in the journey is called a **span**.

Example: "Place Order" trace:
```
order-service (200ms total)
  ├── GET catalog-service/api/products/42   (30ms)
  ├── POST inventory-service/api/reserve    (45ms)
  └── INSERT into orders table              (15ms)
```

Traces answer: **Where did the time go? Which service is slow? Where did the error happen?**

### Metrics
**Metrics** are numerical measurements over time — counters, gauges, histograms.

Examples:
- HTTP request rate: 150 req/s
- P95 latency: 230ms
- Error rate: 2.3%
- JVM memory usage: 256MB

Metrics answer: **Is the system healthy right now? Are things getting worse?**

### Logs
**Logs** are timestamped text messages from the application.

Examples:
- `INFO  order-service: Order created for product 42, quantity 2`
- `ERROR inventory-service: Insufficient stock for product 42`

Logs answer: **What exactly happened? What was the error message?**

---

## OpenTelemetry (OTEL)

**OpenTelemetry** is an open-source, vendor-neutral standard for collecting all three signals (traces, metrics, logs) from your applications.

Key idea: **Instrument once, send to any backend** — Grafana, Datadog, New Relic, Jaeger, etc.

```mermaid
graph LR
    A[Your Application] -->|OTEL Protocol| B[OTEL Collector]
    B --> C[Tempo / Jaeger]
    B --> D[Prometheus / Datadog]
    B --> E[Loki / Elasticsearch]
    
    style A fill:#4a90d9,color:#fff
    style B fill:#f5a623,color:#fff
    style C fill:#e74c3c,color:#fff
    style D fill:#2ecc71,color:#fff
    style E fill:#9b59b6,color:#fff
```

---

## OpenTelemetry Java Agent

The **OTEL Java Agent** is a JAR file that you attach to any Java application at startup. It **automatically instruments** your code — no code changes needed.

### How it works

```mermaid
graph TD
    A["Java Application<br/>(Spring Boot JAR)"] --> B["JVM Startup"]
    B -->|"-javaagent:opentelemetry-javaagent.jar"| C["OTEL Agent Loads"]
    C --> D["Bytecode Instrumentation"]
    D --> E["Auto-captures:<br/>HTTP requests<br/>Database queries<br/>REST client calls<br/>JVM metrics<br/>Application logs"]
    E -->|"OTLP (gRPC/HTTP)"| F["OTEL Collector"]

    style A fill:#4a90d9,color:#fff
    style C fill:#f5a623,color:#fff
    style F fill:#2ecc71,color:#fff
```

### What gets auto-instrumented
- **HTTP server** spans (every incoming request)
- **HTTP client** spans (every outgoing REST call)
- **Database** spans (every SQL query via JDBC/Hibernate)
- **JVM metrics** (memory, GC, threads, connection pools)
- **Logs** (SLF4J/Logback are captured and enriched with trace context)

### Pros
- **Zero code changes** — just add the JAR at startup
- **Comprehensive** — covers HTTP, DB, messaging, gRPC, and more out of the box
- **Trace context propagation** — automatically links spans across services
- **Vendor neutral** — works with any OTLP-compatible backend
- **Community maintained** — backed by CNCF with wide industry adoption

### Cons
- **Startup overhead** — agent needs time to instrument bytecode (a few seconds)
- **Memory overhead** — small additional memory usage for span/metric buffers
- **Limited control** — auto-generated spans may not capture business-specific context
- **Version coupling** — agent version must be compatible with your libraries
- **"Magic"** — can be hard to debug when something goes wrong (invisible bytecode changes)

> In our app, we use **custom annotations** (`@WithSpan`) in the Order Service for business logic visibility, on top of auto-instrumentation.

### Alternatives to the Java Agent

The OTEL Java Agent isn't the only way to instrument Java applications. Here's how the main approaches compare:

| Approach | Code Changes | Startup Cost | Control | Cost / Overhead | Cloud Hosting Cost (AWS etc.) | Best For |
|----------|-------------|-------------|---------|----------------|-------------------------------|----------|
| **Java Agent** (runtime bytecode) | None | Higher (bytecode rewrite at startup) | Low — you get what the agent gives you | ~50-100MB extra memory, 3-10s slower startup, agent JAR versioning | **Highest** — generates the most telemetry data (every HTTP call, every DB query, every log). Trace ingestion is the main cost driver | Quick adoption, brownfield apps |
| **Spring Boot Starter** (`opentelemetry-spring-boot-starter`) | Minimal — add dependency + config | Low | Medium — configure via `application.yml` | Build dependency management, less library coverage than agent | **Medium-High** — similar data volume for Spring-covered libraries, but fewer auto-instrumented libs means fewer spans overall. Container size stays normal. ~10-20% less trace data than agent. | Spring Boot apps that want agent-free setup |
| **Manual SDK** (`opentelemetry-api` + `opentelemetry-sdk`) | High — instrument each call site | None | Full — you decide every span | High dev time to write & maintain, risk of missing spans, boilerplate in every service | **Lowest runtime** — you only emit what you explicitly instrument, so data volume is minimal. Near-zero container overhead. But **high engineering cost**: developer hours to instrument, review, and maintain. | Libraries, frameworks, fine-grained control |

> **The real cost isn't the instrumentation — it's the data.**
> Traces are by far the most expensive signal. A single HTTP request can generate 5-20 spans, each stored and indexed.

#### Spring Boot Starter (agent-free auto-instrumentation)
Uses Spring's own extension points (interceptors, filters) instead of bytecode manipulation. No `-javaagent` flag needed — just add the Maven/Gradle dependency. Trade-off: covers fewer libraries than the agent (mostly Spring-specific).

#### Manual SDK
You write the instrumentation yourself using the OpenTelemetry API:
```java
Tracer tracer = GlobalOpenTelemetry.getTracer("order-service");
Span span = tracer.spanBuilder("placeOrder").startSpan();
try (Scope scope = span.makeCurrent()) {
    // your business logic
    span.setAttribute("order.product_id", productId);
} finally {
    span.end();
}
```
Maximum control, but significantly more code to write and maintain.

---

## How Coffee Shop Uses OTEL

Three Spring Boot microservices, each with the Java Agent attached via Dockerfile:

```dockerfile
# Every service Dockerfile includes:
ADD https://github.com/.../opentelemetry-javaagent.jar /app/opentelemetry-javaagent.jar
ENV JAVA_TOOL_OPTIONS="-javaagent:/app/opentelemetry-javaagent.jar"
```

Configuration is purely via environment variables:
```
OTEL_SERVICE_NAME: order-service
OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4317
OTEL_EXPORTER_OTLP_PROTOCOL: grpc
OTEL_METRICS_EXPORTER: otlp
OTEL_LOGS_EXPORTER: otlp
OTEL_TRACES_EXPORTER: otlp
```

---

## Complete Telemetry Data Flow

```mermaid
graph TB
    subgraph services ["Application Services"]
        CS["Catalog Service<br/>(Spring Boot + OTEL Agent)"]
        OS["Order Service<br/>(Spring Boot + OTEL Agent)"]
        IS["Inventory Service<br/>(Spring Boot + OTEL Agent)"]
    end

    subgraph collector ["OpenTelemetry Collector"]
        RX["Receiver<br/>OTLP gRPC :4317"]
        PM["Processor: batch"]
        PF["Processor: filter<br/>(drop DB root spans)"]
        PT["Processor: transform<br/>(extract log level)"]
    end

    subgraph backends ["Observability Backends"]
        TEMPO["Tempo<br/>(Traces)"]
        PROM["Prometheus<br/>(Metrics)"]
        LOKI["Loki<br/>(Logs)"]
    end

    GRAFANA["Grafana<br/>(Dashboards & Explore)"]

    CS -->|"traces + metrics + logs<br/>OTLP gRPC"| RX
    OS -->|"traces + metrics + logs<br/>OTLP gRPC"| RX
    IS -->|"traces + metrics + logs<br/>OTLP gRPC"| RX

    RX --> PF
    RX --> PM
    RX --> PT

    PF -->|"OTLP gRPC"| TEMPO
    PM -->|"scrape :8889"| PROM
    PT -->|"OTLP HTTP /otlp"| LOKI

    TEMPO --> GRAFANA
    PROM --> GRAFANA
    LOKI --> GRAFANA

    style services fill:#e8f4f8,stroke:#4a90d9
    style collector fill:#fff3e0,stroke:#f5a623
    style backends fill:#e8f8e8,stroke:#2ecc71
    style GRAFANA fill:#f5e6ff,stroke:#9b59b6
```

### OTEL Collector — The Traffic Router

The Collector receives **all** telemetry data and routes each signal type to the right backend:

| Signal | Processor | Exporter | Backend |
|--------|-----------|----------|---------|
| **Traces** | filter (drop DB root spans) + batch | OTLP gRPC | **Tempo** |
| **Metrics** | batch | Prometheus scrape endpoint | **Prometheus** |
| **Logs** | transform (extract log level) + batch | OTLP HTTP | **Loki** |

---

## Grafana — Connecting the Dots

Grafana doesn't just display data — it **links signals together**:

```mermaid
graph LR
    T["Trace in Tempo"] -->|"trace_id"| L["Logs in Loki"]
    T -->|"service + route"| M["Metrics in Prometheus"]
    L -->|"trace_id extracted<br/>from log attributes"| T

    style T fill:#e74c3c,color:#fff
    style L fill:#9b59b6,color:#fff
    style M fill:#2ecc71,color:#fff
```

- From a **trace**, click to see the **logs** for that exact request
- From a **log line**, click the trace ID to see the **full trace**
- From a **trace**, see the **metrics** for that service and route

This cross-signal correlation is what makes observability powerful — you can jump from "what's slow?" (metrics) to "where's the bottleneck?" (traces) to "what's the error?" (logs) in seconds.

---

# Part 2: MCPs — Model Context Protocol

---

## What is MCP?

**MCP (Model Context Protocol)** is an open standard that lets AI models (like Claude or GPT) **use external tools** through a standardized interface.

Think of it like **USB for AI** — a universal plug that connects any AI model to any data source or tool.

Before MCP, every AI integration was custom. With MCP, you build a tool **once** and **any** AI model can use it.

---

## MCP Architecture — The Concepts

```mermaid
graph TB
    subgraph host ["MCP Host"]
        UI["User Interface<br/>(chat, IDE, CLI)"]
        CLIENT["MCP Client<br/>(manages connections)"]
    end
    
    subgraph servers ["MCP Servers"]
        S1["MCP Server A<br/>(e.g., database tools)"]
        S2["MCP Server B<br/>(e.g., file system tools)"]
        S3["MCP Server C<br/>(e.g., API tools)"]
    end

    UI --> CLIENT
    CLIENT <-->|"MCP Protocol<br/>(JSON-RPC over HTTP)"| S1
    CLIENT <-->|"MCP Protocol"| S2
    CLIENT <-->|"MCP Protocol"| S3

    S1 <--> D1["Database"]
    S2 <--> D2["File System"]
    S3 <--> D3["External API"]

    style host fill:#e8f4f8,stroke:#4a90d9
    style servers fill:#fff3e0,stroke:#f5a623
```

### Key Concepts

| Concept | What it is | Analogy |
|---------|-----------|---------|
| **Host** | The application that contains the AI model | Your computer |
| **Client** | Manages connections to MCP servers | USB controller |
| **Server** | Exposes tools and data to the AI | USB device |
| **Tool** | A specific action the AI can invoke | A function on the device |
| **Transport** | How messages are sent (HTTP, stdio, SSE) | The cable type |

### MCP Protocol Flow

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as MCP Server

    Note over Client,Server: Connection Phase
    Client->>Server: Connect (HTTP/stdio/SSE)
    Client->>Server: initialize()
    Server-->>Client: Server capabilities

    Note over Client,Server: Discovery Phase
    Client->>Server: list_tools()
    Server-->>Client: Available tools with schemas

    Note over Client,Server: Execution Phase
    Client->>Server: call_tool(name, arguments)
    Server-->>Client: Tool result (text/data)
```

The protocol is simple:
1. **Connect** — establish communication
2. **Discover** — ask "what tools do you have?"
3. **Execute** — call a specific tool with arguments and get results

---

## How Coffee Shop Implements MCP

Our **observability-chat** service is the **MCP Host + Client**. It connects to **4 MCP Servers**:

```mermaid
graph TB
    subgraph host ["observability-chat (MCP Host + Client)"]
        REACT["React Frontend<br/>(Chat UI)"]
        API["FastAPI Backend"]
        LLM["LLM<br/>(Claude / GPT)"]
        MGR["MCP Manager<br/>(Client)"]
    end

    subgraph mcp_servers ["MCP Servers"]
        TEMPO_MCP["Tempo MCP<br/>:3200/api/mcp<br/>(built-in)"]
        LOKI_MCP["Loki MCP<br/>:8080/stream<br/>(grafana/loki-mcp)"]
        PROM_MCP["Prometheus MCP<br/>:8080/mcp<br/>(pab1it0)"]
        CS_MCP["Code-Search MCP<br/>:8090/mcp<br/>(custom-built)"]
    end

    subgraph backends ["Data Sources"]
        TEMPO_DB["Tempo<br/>(Traces)"]
        LOKI_DB["Loki<br/>(Logs)"]
        PROM_DB["Prometheus<br/>(Metrics)"]
        QDRANT["Qdrant<br/>(Code Vectors)"]
    end

    REACT <-->|"SSE stream"| API
    API <--> LLM
    API <--> MGR
    MGR <-->|"streamable-http"| TEMPO_MCP
    MGR <-->|"SSE"| LOKI_MCP
    MGR <-->|"streamable-http"| PROM_MCP
    MGR <-->|"streamable-http"| CS_MCP

    TEMPO_MCP <--> TEMPO_DB
    LOKI_MCP <--> LOKI_DB
    PROM_MCP <--> PROM_DB
    CS_MCP <--> QDRANT

    style host fill:#e8f4f8,stroke:#4a90d9
    style mcp_servers fill:#fff3e0,stroke:#f5a623
    style backends fill:#e8f8e8,stroke:#2ecc71
```

### MCP Server Configuration

```json
[
  {"name": "tempo",       "url": "http://tempo:3200/api/mcp"},
  {"name": "loki",        "url": "http://loki-mcp:8080/stream"},
  {"name": "prometheus",  "url": "http://prometheus-mcp:8080/mcp"},
  {"name": "code-search", "url": "http://code-search:8090/mcp"}
]
```

### Tool Namespacing

When multiple MCP servers have tools, names could collide. Our app solves this with **namespacing**:

```
tempo__traceql-search          → calls "traceql-search" on Tempo
loki__loki_query               → calls "loki_query" on Loki
prometheus__execute_query      → calls "execute_query" on Prometheus
code-search__search_code       → calls "search_code" on Code-Search
```

The LLM sees all tools from all servers in one flat list, prefixed with `[server_name]` in descriptions.

---

## MCP Server: Tempo (Traces)

Tempo has a **built-in MCP server** (enabled in config). No separate container needed.

```yaml
# tempo.yml
query_frontend:
  mcp_server:
    enabled: true
```

### Tools Available
- `traceql-search` — execute TraceQL queries to find traces
- `get-trace` — fetch a specific trace by ID
- `get-attribute-names` — discover available trace attributes
- `get-attribute-values` — list values for a given attribute
- `docs-traceql` — get TraceQL syntax documentation
- `traceql-metrics-instant` / `traceql-metrics-range` — compute metrics from traces

### How a Trace Query Works

```mermaid
sequenceDiagram
    actor User
    participant Chat as observability-chat
    participant LLM as Claude / GPT
    participant MGR as MCP Manager
    participant Tempo as Tempo MCP Server
    participant DB as Tempo Storage

    User->>Chat: "Show me slow requests in order-service"
    Chat->>LLM: User message + available tools
    
    Note over LLM: Decides to use tempo__get-attribute-names first
    LLM->>Chat: tool_call: tempo__get-attribute-names
    Chat->>MGR: call_tool("tempo", "get-attribute-names", {})
    MGR->>Tempo: MCP call_tool (HTTP)
    Tempo->>DB: Query attribute catalog
    DB-->>Tempo: Attribute list
    Tempo-->>MGR: Result: [resource.service.name, span.http.route, ...]
    MGR-->>Chat: Tool result
    Chat->>LLM: Here are the attributes...

    Note over LLM: Now builds a TraceQL query
    LLM->>Chat: tool_call: tempo__traceql-search<br/>{query: '{ resource.service.name = "order-service" } | max(span:duration) > 500ms'}
    Chat->>MGR: call_tool("tempo", "traceql-search", {...})
    MGR->>Tempo: MCP call_tool (HTTP)
    Tempo->>DB: Execute TraceQL
    DB-->>Tempo: Matching traces
    Tempo-->>MGR: Trace results
    MGR-->>Chat: Tool result
    Chat->>LLM: Here are the slow traces...

    LLM->>Chat: "I found 3 traces slower than 500ms..."
    Chat->>User: Formatted response with trace details
```

---

## MCP Server: Loki (Logs)

Loki MCP runs as a **separate container** (`grafana/loki-mcp`) that bridges MCP protocol to Loki's API.

### Tools Available
- `loki_query` — execute LogQL queries
- `loki_label_names` — discover available log labels
- `loki_label_values` — list values for a label

### How a Log Query Works

```mermaid
sequenceDiagram
    actor User
    participant Chat as observability-chat
    participant LLM as Claude / GPT
    participant MGR as MCP Manager
    participant LokiMCP as Loki MCP Server
    participant Loki as Loki Storage

    User->>Chat: "Show me errors in inventory-service"
    Chat->>LLM: User message + available tools
    
    Note over LLM: Uses loki tools to query logs
    LLM->>Chat: tool_call: loki__loki_query<br/>{query: '{service_name="inventory-service", level="ERROR"}'}
    Chat->>MGR: call_tool("loki", "loki_query", {...})
    MGR->>LokiMCP: MCP call_tool (SSE)
    LokiMCP->>Loki: LogQL HTTP query
    Loki-->>LokiMCP: Log entries
    LokiMCP-->>MGR: Formatted log results
    MGR-->>Chat: Tool result
    Chat->>LLM: Here are the error logs...

    LLM->>Chat: "Found 5 errors: Insufficient stock for product 42..."
    Chat->>User: Formatted error log analysis
```

---

## MCP Server: Prometheus (Metrics)

Prometheus MCP runs as a **separate container** (`pab1it0/prometheus-mcp-server`) bridging MCP to Prometheus.

### Tools Available
- `execute_query` — run PromQL instant queries
- `execute_range_query` — run PromQL range queries
- `get_metric_metadata` — discover available metrics
- `get_targets` — list scrape targets

### How a Metrics Query Works

```mermaid
sequenceDiagram
    actor User
    participant Chat as observability-chat
    participant LLM as Claude / GPT
    participant MGR as MCP Manager
    participant PromMCP as Prometheus MCP Server
    participant Prom as Prometheus

    User->>Chat: "What's the error rate for order-service?"
    Chat->>LLM: User message + available tools
    
    Note over LLM: Constructs PromQL for error rate
    LLM->>Chat: tool_call: prometheus__execute_query<br/>{query: 'rate(http_server_request_duration_seconds_count{service_name="order-service",http_response_status_code=~"5.."}[5m])'}
    Chat->>MGR: call_tool("prometheus", "execute_query", {...})
    MGR->>PromMCP: MCP call_tool (HTTP)
    PromMCP->>Prom: PromQL HTTP query
    Prom-->>PromMCP: Metric values
    PromMCP-->>MGR: Formatted metrics
    MGR-->>Chat: Tool result
    Chat->>LLM: Here are the metrics...

    LLM->>Chat: "Order-service has a 2.3% error rate over the last 5 minutes"
    Chat->>User: Error rate analysis with context
```

---

## MCP Server: Code-Search (Custom Built)

Code-Search is a **custom MCP server** built specifically for this app. It provides **semantic code search** across all microservices — the AI can search and read code to understand the system.

### Architecture

```mermaid
graph TB
    subgraph indexing ["Indexing Pipeline (runs on reindex)"]
        FILES["Source Files<br/>(.java, .py, .ts)"]
        DISC["File Discovery<br/>(glob patterns)"]
        PARSE["AST Parsing<br/>(Tree-Sitter)"]
        SYMBOLS["Code Symbols<br/>(classes, methods,<br/>functions, components)"]
        EMBED["Jina Code V2<br/>Embeddings<br/>(768 dimensions)"]
        STORE["Qdrant Vector DB<br/>(cosine similarity)"]
    end

    subgraph querying ["Search (on tool call)"]
        QUERY["Natural Language Query"]
        QEMBED["Embed Query"]
        SEARCH["Vector Similarity Search<br/>+ Metadata Filters"]
        RESULTS["Ranked Code Results<br/>with locations & snippets"]
    end

    FILES --> DISC
    DISC --> PARSE
    PARSE --> SYMBOLS
    SYMBOLS --> EMBED
    EMBED --> STORE

    QUERY --> QEMBED
    QEMBED --> SEARCH
    STORE -.->|"vectors"| SEARCH
    SEARCH --> RESULTS

    style indexing fill:#e8f4f8,stroke:#4a90d9
    style querying fill:#fff3e0,stroke:#f5a623
```

### What Gets Indexed

The code-search service parses source code using **Tree-Sitter** (the same AST parser used in VS Code, Neovim, GitHub) to extract meaningful symbols:

| Language | Symbols Extracted | Special Detection |
|----------|-------------------|-------------------|
| **Java** | Classes, interfaces, enums, records, methods | Spring stereotypes, HTTP routes, Lombok |
| **Python** | Classes, functions | Pydantic models, FastAPI routes, async |
| **TypeScript** | Functions, interfaces, types, components | React components, hooks, memo |

### Indexed Services

```yaml
# config.yaml
services:
  - catalog-service   (Java)
  - order-service     (Java)
  - inventory-service (Java)
  - observability-chat (Python + TypeScript)
```

### 7 Tools Exposed

| Tool | Purpose |
|------|---------|
| `search_code` | Semantic search — "find order placement logic" |
| `find_symbol` | Lookup by name — "find OrderService class" |
| `find_usages` | Find references — "who calls placeOrder?" |
| `get_code_context` | Read full source file or symbol |
| `reindex` | Rebuild the search index |
| `list_indexed_services` | Show indexed services and stats |
| `index_stats` | Show vector DB statistics |

### Indexing Flow (Detailed)

```mermaid
sequenceDiagram
    participant Tool as reindex tool
    participant Disc as File Discovery
    participant Parser as Tree-Sitter Parser
    participant Embed as Jina Embeddings
    participant DB as Qdrant Vector DB

    Note over Tool: reindex(service="order-service")
    Tool->>Disc: Discover files (src/main/java/**/*.java)
    Disc-->>Tool: 12 Java files found

    loop For each file
        Tool->>Tool: Compute SHA256 hash
        Tool->>DB: Check if file hash changed
        alt File unchanged
            Note over Tool: Skip (incremental)
        else File new or changed
            Tool->>DB: Delete old chunks for this file
            Tool->>Parser: Parse file (Tree-Sitter AST)
            Parser-->>Tool: CodeSymbols (classes, methods)
            
            Note over Tool: Build embedding text per symbol:<br/>language + type + name + annotations<br/>+ signature + docstring + source code
            
            Tool->>Embed: Batch embed symbols (32 per batch)
            Embed-->>Tool: 768-dim vectors
            Tool->>DB: Upsert chunks with vectors + metadata
        end
    end

    Tool-->>Tool: "Indexed 12 files, 47 symbols, skipped 3"
```

### Search Flow (Detailed)

```mermaid
sequenceDiagram
    participant LLM as Claude / GPT
    participant Tool as search_code tool
    participant Embed as Jina Embeddings
    participant DB as Qdrant Vector DB

    LLM->>Tool: search_code("how does order placement work?",<br/>service="order-service")
    Tool->>Embed: Embed query text
    Embed-->>Tool: 768-dim query vector
    
    Tool->>DB: Vector similarity search<br/>(cosine distance, filter: service=order-service)
    DB-->>Tool: Top 10 results with scores

    Note over Tool: Format results with:<br/>- Symbol name & type<br/>- File path & line numbers<br/>- Score & annotations<br/>- Code snippet

    Tool-->>LLM: "1. OrderService.placeOrder() [0.89]<br/>order-service/.../OrderService.java:45-78<br/>@WithSpan, @Transactional<br/>POST /api/orders<br/>..."
```

### Why Code-Search Matters

When the AI finds a bug through traces/logs, it can **immediately look at the code** to understand why:

1. Tempo says: "order-service errors on POST /api/orders"
2. Loki says: "NullPointerException in OrderService.placeOrder"
3. Code-Search says: "Here's the placeOrder method — line 67 accesses product.getPrice() without null check"

**The AI connects the dots that would take a developer minutes of clicking through Grafana, grep-ing code, and reading stack traces.**

---

# Part 3: AI Agents

---

## Chatbot vs. AI Agent

| | Chatbot | AI Agent |
|---|---------|----------|
| **Input** | User message | User message |
| **Process** | Generate one response | Reason, use tools, iterate |
| **Tools** | None | Yes — can call external systems |
| **Iterations** | 1 | Multiple (loops until done) |
| **Output** | Static text | Informed answer after investigation |

A **chatbot** gives you its best guess from training data.
An **agent** goes and **looks things up** before answering.

---

## The Agent Loop in Our App

The core of our observability-chat is an **agent loop** — the AI doesn't just respond, it thinks, acts, observes, and repeats.

```mermaid
graph TD
    A["User asks a question"] --> B["Add message to conversation"]
    B --> C["Send to LLM with<br/>all available tools"]
    C --> D{"LLM Response"}
    D -->|"Text only"| E["Stream text to user<br/>(SSE tokens)"]
    D -->|"Tool calls"| F["Execute each tool call"]
    F --> G["1. Parse namespaced tool<br/>tempo__traceql-search<br/>→ (tempo, traceql-search)"]
    G --> H["2. MCP Manager calls<br/>the right server"]
    H --> I["3. Get tool result"]
    I --> J["4. Add result to<br/>conversation history"]
    J --> K{"Iteration < 10?"}
    K -->|"Yes"| C
    K -->|"No"| L["Return what we have"]
    E --> M["Done"]

    style A fill:#4a90d9,color:#fff
    style D fill:#f5a623,color:#fff
    style F fill:#e74c3c,color:#fff
    style M fill:#2ecc71,color:#fff
```

### Key Details
- **Max 10 iterations** — safety limit to prevent infinite loops
- **Streaming** — text tokens are streamed to the UI in real-time via SSE (Server-Sent Events)
- **Multi-provider** — supports both Claude (Anthropic) and GPT (OpenAI)
- **Conversation memory** — the full history (including tool results) is sent to the LLM each iteration

---

## The Agent Loop — Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant React as React Frontend
    participant API as FastAPI Backend
    participant LLM as LLM (Claude/GPT)
    participant MGR as MCP Manager
    participant MCP as MCP Servers

    User->>React: "Why are orders failing?"
    React->>API: POST /api/chat {message, session_id}
    
    Note over API: Start agent loop (max 10 iterations)
    
    Note over API,MCP: Iteration 1: Discover the problem
    API->>LLM: Messages + tools (system prompt + history)
    LLM-->>API: tool_call: tempo__traceql-search<br/>{query: '{ resource.service.name = "order-service" && span:status = error }'}
    API-->>React: SSE: tool_call_start
    API->>MGR: call_tool("tempo", "traceql-search", ...)
    MGR->>MCP: HTTP → Tempo MCP
    MCP-->>MGR: 3 error traces found
    MGR-->>API: trace results
    API-->>React: SSE: tool_call_end {result}

    Note over API,MCP: Iteration 2: Check the logs
    API->>LLM: Messages + tool results from iteration 1
    LLM-->>API: tool_call: loki__loki_query<br/>{query: '{service_name="order-service", level="ERROR"}'}
    API-->>React: SSE: tool_call_start
    API->>MGR: call_tool("loki", "loki_query", ...)
    MGR->>MCP: HTTP → Loki MCP
    MCP-->>MGR: Error logs: "NullPointerException in placeOrder"
    MGR-->>API: log results
    API-->>React: SSE: tool_call_end {result}

    Note over API,MCP: Iteration 3: Look at the code
    API->>LLM: Messages + tool results from iterations 1-2
    LLM-->>API: tool_call: code-search__find_symbol<br/>{name: "placeOrder", service: "order-service"}
    API-->>React: SSE: tool_call_start
    API->>MGR: call_tool("code-search", "find_symbol", ...)
    MGR->>MCP: HTTP → Code-Search MCP
    MCP-->>MGR: OrderService.placeOrder() source code
    MGR-->>API: code results
    API-->>React: SSE: tool_call_end {result}

    Note over API,MCP: Iteration 4: Final answer
    API->>LLM: Messages + all tool results
    LLM-->>API: "Orders are failing because..."
    API-->>React: SSE: token, token, token...
    API-->>React: SSE: done

    React->>User: Complete analysis with traces, logs, and code
```

---

## Why This Matters: Fast Bug Finding

### Traditional Debugging Flow (Manual)

```mermaid
graph LR
    A["Alert: orders failing"] --> B["Open Grafana"]
    B --> C["Check dashboard<br/>metrics"]
    C --> D["Switch to Tempo<br/>search traces"]
    D --> E["Find error trace<br/>read spans"]
    E --> F["Switch to Loki<br/>search logs"]
    F --> G["Find error message"]
    G --> H["Open IDE<br/>find the file"]
    H --> I["Read the code<br/>find the bug"]

    style A fill:#e74c3c,color:#fff
    style I fill:#2ecc71,color:#fff
```

**Time: 10-30 minutes** of switching between tools, copy-pasting trace IDs, grep-ing code.

### AI Agent Debugging Flow

```mermaid
graph LR
    A["Ask: Why are<br/>orders failing?"] --> B["Agent investigates<br/>traces + logs +<br/>metrics + code"]
    B --> C["Complete answer<br/>with root cause<br/>and code location"]

    style A fill:#e74c3c,color:#fff
    style B fill:#f5a623,color:#fff
    style C fill:#2ecc71,color:#fff
```

**Time: 30-60 seconds.** The AI does the same investigation a developer would, but in parallel and without context-switching.

### The Key Insight

The power isn't in any single component — it's in the **combination**:

```mermaid
graph TB
    OTEL["OpenTelemetry<br/>(auto-captures everything)"]
    MCP_PROTO["MCP Protocol<br/>(standardized tool access)"]
    AGENT["AI Agent<br/>(reasons and investigates)"]
    
    OTEL --> |"rich data without<br/>code changes"| MCP_PROTO
    MCP_PROTO --> |"AI can query any<br/>observability backend"| AGENT
    AGENT --> |"connects traces +<br/>logs + metrics + code<br/>in one answer"| RESULT["Fast Root Cause Analysis"]

    style OTEL fill:#4a90d9,color:#fff
    style MCP_PROTO fill:#f5a623,color:#fff
    style AGENT fill:#e74c3c,color:#fff
    style RESULT fill:#2ecc71,color:#fff
```

1. **OTEL** captures rich telemetry with zero code changes
2. **MCP** gives the AI standardized access to all that data
3. **The Agent** reasons across all signals to find the root cause

---

## Full System Architecture

```mermaid
graph TB
    subgraph app ["Coffee Shop Application"]
        CS["Catalog<br/>Service<br/>:8081"]
        OS["Order<br/>Service<br/>:8082"]
        IS["Inventory<br/>Service<br/>:8083"]
        PG["PostgreSQL<br/>:5432"]
    end

    subgraph otel ["OpenTelemetry"]
        COLL["OTEL Collector<br/>:4317"]
    end

    subgraph obs ["Observability Backends"]
        TEMPO["Tempo<br/>:3200"]
        PROM["Prometheus<br/>:9090"]
        LOKI["Loki<br/>:3100"]
    end

    subgraph viz ["Visualization"]
        GRAF["Grafana<br/>:3000"]
    end

    subgraph mcp ["MCP Servers"]
        TMCP["Tempo MCP<br/>(built-in)"]
        LMCP["Loki MCP<br/>:8085"]
        PMCP["Prometheus MCP<br/>:8086"]
        CMCP["Code-Search MCP<br/>:8090"]
    end

    subgraph ai ["AI Chat"]
        CHAT["observability-chat<br/>:8084<br/>(React + FastAPI + LLM)"]
    end

    subgraph vector ["Code Intelligence"]
        QDRANT["Qdrant<br/>:6333"]
        JINA["Jina Embeddings<br/>:8087"]
    end

    OS --> CS
    OS --> IS
    CS --> PG
    OS --> PG
    IS --> PG

    CS --> COLL
    OS --> COLL
    IS --> COLL

    COLL --> TEMPO
    COLL --> PROM
    COLL --> LOKI

    TEMPO --> GRAF
    PROM --> GRAF
    LOKI --> GRAF

    TEMPO --> TMCP
    LOKI -.-> LMCP
    PROM -.-> PMCP

    TMCP --> CHAT
    LMCP --> CHAT
    PMCP --> CHAT
    CMCP --> CHAT

    CMCP --> QDRANT
    CMCP --> JINA

    style app fill:#e8f4f8,stroke:#4a90d9
    style otel fill:#fff3e0,stroke:#f5a623
    style obs fill:#e8f8e8,stroke:#2ecc71
    style viz fill:#f5e6ff,stroke:#9b59b6
    style mcp fill:#ffeaa7,stroke:#fdcb6e
    style ai fill:#fab1a0,stroke:#e17055
    style vector fill:#dfe6e9,stroke:#636e72
```

---

## Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Instrumentation** | OTEL Java Agent | Auto-capture traces, metrics, logs |
| **Collection** | OTEL Collector | Route signals to the right backend |
| **Storage** | Tempo, Prometheus, Loki | Store traces, metrics, logs |
| **Visualization** | Grafana | Dashboards, cross-signal correlation |
| **AI Access** | MCP Protocol | Standardized tool interface for AI |
| **AI Reasoning** | Agent Loop (Claude/GPT) | Multi-step investigation |
| **Code Intelligence** | Code-Search + Qdrant | Semantic code search |

**The result:** Ask a question in plain English, get a root-cause analysis that would normally take a developer 10-30 minutes of manual investigation.
