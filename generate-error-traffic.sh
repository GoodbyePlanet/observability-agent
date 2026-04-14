#!/usr/bin/env bash
# Generates error traffic across all 3 Coffee Shop services.
# Usage: ./generate-error-traffic.sh [iterations]   (default: 20)

set -euo pipefail

ITERATIONS=${1:-20}
ORDER_URL="http://localhost:8082"
CATALOG_URL="http://localhost:8081"
INVENTORY_URL="http://localhost:8083"

PRODUCTS=(
  "11111111-1111-1111-1111-111111111111"  # Espresso
  "22222222-2222-2222-2222-222222222222"  # Cappuccino
  "33333333-3333-3333-3333-333333333333"  # Latte
)

NONEXISTENT="00000000-0000-0000-0000-000000000000"

echo "==> Generating $ITERATIONS rounds of error traffic..."

for i in $(seq 1 "$ITERATIONS"); do
  PRODUCT=${PRODUCTS[$((RANDOM % ${#PRODUCTS[@]}))]}

  # Order for a non-existent product (ProductNotFoundInCatalog)
  curl -sf -X POST "$ORDER_URL/api/orders" \
    -H "Content-Type: application/json" \
    -d "{\"productId\":\"$NONEXISTENT\",\"quantity\":1}" > /dev/null || true

  # Order with insufficient stock
  curl -sf -X POST "$ORDER_URL/api/orders" \
    -H "Content-Type: application/json" \
    -d "{\"productId\":\"$PRODUCT\",\"quantity\":99999}" > /dev/null || true

  # Lookup non-existent resources (404s)
  curl -sf "$ORDER_URL/api/orders/$NONEXISTENT" > /dev/null || true
  curl -sf "$CATALOG_URL/api/products/$NONEXISTENT" > /dev/null || true
  curl -sf "$INVENTORY_URL/api/inventory/$NONEXISTENT" > /dev/null || true

  # Reserve stock for non-existent inventory
  curl -sf -X POST "$INVENTORY_URL/api/inventory/$NONEXISTENT/reserve" \
    -H "Content-Type: application/json" \
    -d '{"quantity":5}' > /dev/null || true

  # Invalid UUID format (400s)
  curl -sf "$CATALOG_URL/api/products/not-a-uuid" > /dev/null || true
  curl -sf "$ORDER_URL/api/orders/not-a-uuid" > /dev/null || true

  # Create product with missing required fields (500 - DB constraint violation)
  curl -sf -X POST "$CATALOG_URL/api/products" \
    -H "Content-Type: application/json" \
    -d '{}' > /dev/null || true

  # Malformed JSON (400s)
  curl -sf -X POST "$ORDER_URL/api/orders" \
    -H "Content-Type: application/json" \
    -d '{"broken json' > /dev/null || true

  echo "  round $i/$ITERATIONS done"
done

echo "==> Done. Check Grafana at http://localhost:3000"
