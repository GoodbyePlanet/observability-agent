# Coffee Shop Microservices with Full Observability

## Context

Build a learning experiment: 3 Java/Spring Boot microservices that communicate via REST, each with its own database, fully instrumented with OpenTelemetry. All three observability pillars (metrics, traces, logs) visualized in Grafana. Everything runs via Docker Compose.

The domain is a **Coffee Shop Order System** -- simple, realistic, and naturally demonstrates inter-service communication.

---

## Architecture

```
                          ┌──────────────────┐
                          │   order-service   │ :8082
                          │   (order_db)      │
                          └──┬─────────────┬──┘
                  GET /api/products/{id}   POST /api/inventory/{id}/reserve
                             │                 │
                    ┌────────▼──────┐   ┌──────▼──────────┐
                    │catalog-service│   │inventory-service │
                    │  (catalog_db) │   │  (inventory_db)  │
                    │    :8081      │   │     :8083        │
                    └───────────────┘   └─────────────────┘
```

**Order flow:** Customer places order -> order-service -> calls catalog-service (validate product, get price) -> calls inventory-service (reserve stock) -> saves order -> returns confirmation.

---

## Tech Stack

| Component | Choice |
|-----------|--------|
| Java | 25 (LTS) |
| Spring Boot | 4.0.5 (latest stable, based on Spring Framework 7) |
| Build tool | Maven multi-module |
| HTTP client | `RestClient` (modern, synchronous, auto-instrumented) |
| Database | PostgreSQL 17 (1 container, 3 databases) |
| Docker base image | `eclipse-temurin:25-jre-alpine` |
| OTel instrumentation | Java Agent (zero-code, auto-instruments everything) |

---

## Project Structure

```
coffee-shop/
├── pom.xml                          # parent POM (packaging=pom)
├── docker-compose.yml               # everything: infra + services
├── observability/
│   ├── init-databases.sql           # creates 3 databases
│   ├── otel-collector-config.yml
│   ├── prometheus.yml
│   ├── tempo.yml
│   ├── loki-config.yml
│   └── grafana/
│       └── provisioning/
│           ├── datasources/
│           │   └── datasources.yml  # Prometheus, Tempo, Loki
│           └── dashboards/
│               ├── dashboards.yml
│               └── coffee-shop-dashboard.json
├── catalog-service/
│   ├── pom.xml
│   ├── Dockerfile
│   └── src/main/java/com/coffeeshop/catalog/...
├── order-service/
│   ├── pom.xml
│   ├── Dockerfile
│   └── src/main/java/com/coffeeshop/order/...
└── inventory-service/
    ├── pom.xml
    ├── Dockerfile
    └── src/main/java/com/coffeeshop/inventory/...
```

---

## Service Details

### 1. catalog-service (port 8081)

Manages coffee products. Read-heavy, no outgoing REST calls.

**Entity: `Product`**
- `id` (UUID, PK), `name`, `description`, `price` (BigDecimal), `category`, `createdAt`, `updatedAt`

**Endpoints:**
- `GET /api/products` -- list all
- `GET /api/products/{id}` -- get by ID
- `POST /api/products` -- create
- `PUT /api/products/{id}` -- update
- `DELETE /api/products/{id}` -- delete

**Packages:** `controller`, `service`, `repository`, `model`, `dto`, `exception`, `config` (DataInitializer seeds ~5 sample products)

### 2. inventory-service (port 8083)

Tracks stock per product. Supports stock checks and reservations.

**Entity: `InventoryItem`**
- `id` (UUID, PK), `productId` (UUID, unique), `quantity`, `reserved`, `updatedAt`
- Available stock = `quantity - reserved`

**Endpoints:**
- `GET /api/inventory/{productId}` -- get stock
- `POST /api/inventory` -- add inventory for a product
- `POST /api/inventory/{productId}/reserve` -- reserve stock (body: `{"quantity": N}`)
- `PUT /api/inventory/{productId}` -- update stock level

**Packages:** same pattern as catalog-service. DataInitializer seeds stock matching catalog products.

### 3. order-service (port 8082)

Orchestrates order placement. Calls both other services.

**Entity: `Order`**
- `id` (UUID, PK), `productId`, `productName` (denormalized), `quantity`, `unitPrice`, `totalPrice`, `status` (PENDING/CONFIRMED/FAILED), `failureReason`, `createdAt`, `updatedAt`

**Endpoints:**
- `POST /api/orders` -- place order (body: `{"productId": "...", "quantity": N}`)
- `GET /api/orders` -- list all
- `GET /api/orders/{id}` -- get by ID

**Additional packages:** `client/` with `CatalogClient` and `InventoryClient` using Spring's `RestClient`

**Order flow logic:**
1. Call catalog-service to get product details and price
2. Call inventory-service to reserve stock
3. If both succeed -> save order as CONFIRMED
4. If product not found -> save as FAILED with reason
5. If insufficient stock -> save as FAILED with reason

---

## OpenTelemetry Setup

### Why Java Agent (not manual SDK)

The OTel Java Agent is attached at runtime via `-javaagent` -- zero code changes needed. It auto-instruments:
- Spring MVC (HTTP server spans)
- RestClient (HTTP client spans with trace context propagation)
- JDBC/Hibernate (database query spans)
- JVM metrics (memory, GC, threads)
- Logback (injects `trace_id` and `span_id` into MDC, exports logs via OTLP)

This means **no OTel dependencies in pom.xml** for basic instrumentation. The observability concern lives entirely in Docker config.

### Dockerfile Pattern (each service)

```dockerfile
FROM eclipse-temurin:25-jre-alpine
WORKDIR /app
ADD https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/latest/download/opentelemetry-javaagent.jar /app/opentelemetry-javaagent.jar
COPY target/*.jar app.jar
EXPOSE 808X
ENV JAVA_TOOL_OPTIONS="-javaagent:/app/opentelemetry-javaagent.jar"
ENTRYPOINT ["java", "-jar", "app.jar"]
```

### Agent Configuration (via env vars in docker-compose)

```yaml
OTEL_SERVICE_NAME: catalog-service
OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4317
OTEL_EXPORTER_OTLP_PROTOCOL: grpc
OTEL_METRICS_EXPORTER: otlp
OTEL_LOGS_EXPORTER: otlp
OTEL_TRACES_EXPORTER: otlp
OTEL_RESOURCE_ATTRIBUTES: "service.namespace=coffeeshop,deployment.environment=local"
```

### Optional: One Custom Span

Add `@WithSpan` annotation in order-service's `placeOrder()` method to show how to extend auto-instrumentation with business-specific detail. Requires one small dependency:
```xml
<dependency>
    <groupId>io.opentelemetry.instrumentation</groupId>
    <artifactId>opentelemetry-instrumentation-annotations</artifactId>
</dependency>
```
(Version managed by the OTel BOM or set to match the agent version used)

---

## Observability Stack

```
Services (OTel Agent) ──OTLP/gRPC──> OTel Collector
                                          │
                          ┌───────────────┼───────────────┐
                          ▼               ▼               ▼
                     Prometheus        Tempo            Loki
                     (metrics)        (traces)         (logs)
                          └───────────────┼───────────────┘
                                          ▼
                                       Grafana
```

### OTel Collector (`otel/opentelemetry-collector-contrib`)

Receives OTLP from all services, exports to:
- Prometheus exporter (scrape endpoint on :8889) for metrics
- OTLP exporter to Tempo for traces
- Loki exporter for logs
- Debug exporter to stdout for troubleshooting

### Grafana Datasource Provisioning

File-based provisioning. Configures:
- **Prometheus** as default datasource
- **Tempo** with trace-to-logs linking (click trace -> see correlated logs in Loki)
- **Loki** with derived fields (click traceId in log -> jump to trace in Tempo)

This bidirectional trace<->log linking is the key observability feature.

### Pre-provisioned Dashboard Panels

1. HTTP Request Rate by service and route (Prometheus)
2. HTTP P95 Latency (Prometheus)
3. Error Rate (Prometheus)
4. JVM Memory Usage by service (Prometheus)
5. Recent Traces (Tempo)
6. Application Logs (Loki)

---

## Docker Compose Overview

Single `docker-compose.yml` containing:

| Service | Image | Port |
|---------|-------|------|
| postgres | postgres:17 | 5432 |
| otel-collector | otel/opentelemetry-collector-contrib:latest | 4317, 4318, 8889 |
| prometheus | prom/prometheus:latest | 9090 |
| tempo | grafana/tempo:latest | 3200 |
| loki | grafana/loki:3.7.0 | 3100 |
| grafana | grafana/grafana:latest | 3000 |
| catalog-service | (built, eclipse-temurin:25-jre-alpine) | 8081 |
| order-service | (built, eclipse-temurin:25-jre-alpine) | 8082 |
| inventory-service | (built, eclipse-temurin:25-jre-alpine) | 8083 |

PostgreSQL uses health check with `depends_on: condition: service_healthy` for services.

---

## Implementation Order

### Phase 1: Skeleton & Database
1. Create parent POM and module directories (Maven multi-module)
2. Write `docker-compose.yml` with PostgreSQL only + init script for 3 databases
3. Implement **catalog-service** (entity, repo, service, controller, DataInitializer with sample products)
4. Test catalog-service against Dockerized PostgreSQL

### Phase 2: Remaining Services
5. Implement **inventory-service** (same pattern, DataInitializer seeds matching stock)
6. Implement **order-service** with `RestClient` beans, `CatalogClient`, `InventoryClient`, and the order placement flow with error handling
7. Test full flow locally (all 3 services running)

### Phase 3: Dockerize
8. Write Dockerfiles for each service (with OTel Java Agent)
9. Add all 3 services to docker-compose.yml with OTel env vars
10. Verify full application works via `docker compose up --build`

### Phase 4: Observability Stack
11. Add OTel Collector (start with debug exporter to verify telemetry flows)
12. Add Tempo + configure trace exporter in collector
13. Add Loki + configure log exporter in collector
14. Add Prometheus + configure metrics exporter in collector
15. Add Grafana with provisioned datasources (Prometheus, Tempo, Loki with cross-linking)

### Phase 5: Dashboard & Polish
16. Build Grafana dashboard (create in UI, export JSON, commit for provisioning)
17. Add optional `@WithSpan` custom annotation in order-service
18. Test error scenarios (non-existent product, insufficient stock) and verify they show as error traces

---

## Verification

```bash
# Build and start everything
mvn clean package -DskipTests
docker compose up --build -d

# Check health
curl http://localhost:8081/actuator/health
curl http://localhost:8082/actuator/health
curl http://localhost:8083/actuator/health

# Place an order (triggers full cross-service flow)
curl -X POST http://localhost:8082/api/orders \
  -H "Content-Type: application/json" \
  -d '{"productId":"<product-id-from-catalog>","quantity":2}'

# Verify in Grafana (http://localhost:3000):
# 1. Explore -> Tempo: search traces for service.name=order-service
#    -> See spans: HTTP POST /api/orders -> GET /api/products/{id} -> POST /api/inventory/{id}/reserve -> JDBC INSERT
# 2. Explore -> Prometheus: query http_server_request_duration_seconds_count
# 3. Explore -> Loki: query {service_name="order-service"} -> click traceId to jump to trace
# 4. Dashboard -> Coffee Shop: all panels populated

# Test error scenario
curl -X POST http://localhost:8082/api/orders \
  -H "Content-Type: application/json" \
  -d '{"productId":"00000000-0000-0000-0000-000000000000","quantity":1}'
# -> Returns FAILED order, error trace visible in Tempo
```

---

## Key Decisions Summary

| Decision | Choice | Why |
|----------|--------|-----|
| 1 PostgreSQL vs 3 | 1 container, 3 databases | Saves resources, still DB-per-service |
| OTel Agent vs SDK | Java Agent | Zero code, auto-instruments everything |
| RestClient vs WebClient | RestClient | Modern, synchronous, no webflux dependency |
| Log shipping | Agent OTLP export | No Loki/logging dependencies in Java code |
| Maven module for observability | No (config files only) | Agent removes need for in-code observability lib |
| Single docker-compose | Yes | Self-contained experiment |
