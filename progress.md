# Implementation Progress

## Phase 1: Skeleton & Database
- [x] Create parent POM (Maven multi-module)
- [x] Create module directories (catalog-service, order-service, inventory-service)
- [x] Write `observability/init-databases.sql` (3 databases)
- [x] Implement catalog-service (entity, repo, service, controller, data.sql seed)
- [x] Test catalog-service against Dockerized PostgreSQL

## Phase 2: Remaining Services
- [x] Implement inventory-service (entity, repo, service, controller, data.sql seed)
- [x] Implement order-service (entity, repo, service, controller, CatalogClient, InventoryClient)
- [x] Test full inter-service flow locally

## Phase 3: Dockerize
- [x] Write Dockerfile for catalog-service (with OTel Java Agent)
- [x] Write Dockerfile for inventory-service
- [x] Write Dockerfile for order-service
- [x] Add all 3 services to docker-compose.yml with OTel env vars
- [x] Verify full application works via `docker compose up --build`

## Phase 4: Observability Stack
- [x] Add OTel Collector to docker-compose
- [x] Add Grafana Tempo (pinned 2.7.2) + configure trace exporter in collector
- [x] Add Grafana Loki + configure log exporter (otlphttp to Loki's native OTLP endpoint)
- [x] Add Prometheus + configure metrics exporter in collector
- [x] Add Grafana with provisioned datasources (Prometheus, Tempo, Loki with cross-linking)

## Phase 5: Dashboard & Polish
- [x] Build and export Grafana dashboard JSON (8 panels, provisioned automatically)
- [x] Add `@WithSpan("order.place")` custom annotation in order-service with business attributes
- [x] Test error scenarios and verify error traces in Tempo
- [x] Verified all 3 observability pillars: metrics in Prometheus, traces in Tempo, logs in Loki
