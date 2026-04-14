# Coffee Shop — Observability meets AI

A demo project showing how to connect the three pillars of OpenTelemetry (traces, metrics, logs) to an AI agent, giving
you the ability to query and talk with your platform instrumentation using natural language.

## Quick Start

```bash
docker compose up --build
```

This starts the entire stack: application services, observability infrastructure, and the AI chat agent.

## Architecture

### Application Services (Spring Boot + OTEL auto-instrumentation)

| Service             | Port | Description                                  |
|---------------------|------|----------------------------------------------|
| `catalog-service`   | 8081 | Product catalog                              |
| `inventory-service` | 8083 | Stock management                             |
| `order-service`     | 8082 | Order processing (calls catalog & inventory) |

### Observability Stack

| Component      | Port | Role                                        |
|----------------|------|---------------------------------------------|
| OTel Collector | 4317 | Receives traces, metrics, and logs via OTLP |
| Prometheus     | 9090 | Metrics storage & querying                  |
| Tempo          | 3200 | Distributed trace storage                   |
| Loki           | 3100 | Log aggregation                             |
| Grafana        | 3000 | Dashboards (anonymous admin access)         |

### AI Chat Agent

| Component            | Port | Role                                                      |
|----------------------|------|-----------------------------------------------------------|
| `observability-chat` | 8084 | Chat UI + backend that queries observability data via MCP |

The AI agent connects to backends like Tempo through [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
servers, allowing it to retrieve traces, metrics, and logs on your behalf and answer questions about system behavior in
plain English.

## Generating Traffic

```bash
./generate-traffic.sh
```

## Prerequisites

- Docker & Docker Compose
- An API key for the LLM provider (configured in `observability-chat/.env.example`)
