#!/usr/bin/env bash
# Generates mixed traffic across all 3 Coffee Shop services.
# Usage: ./generate-traffic.sh [iterations]   (default: 20)

set -euo pipefail

ITERATIONS=${1:-20}
ORDER_URL="http://localhost:8082"
CATALOG_URL="http://localhost:8081"
INVENTORY_URL="http://localhost:8083"

PRODUCTS=(
  "11111111-1111-1111-1111-111111111111"  # Espresso
  "22222222-2222-2222-2222-222222222222"  # Cappuccino
  "33333333-3333-3333-3333-333333333333"  # Latte
  "44444444-4444-4444-4444-444444444444"  # Cold Brew
  "55555555-5555-5555-5555-555555555555"  # Matcha Latte
)

NONEXISTENT="00000000-0000-0000-0000-000000000000"

echo "==> Generating $ITERATIONS rounds of traffic..."

for i in $(seq 1 "$ITERATIONS"); do
  PRODUCT=${PRODUCTS[$((RANDOM % ${#PRODUCTS[@]}))]}
  QTY=$((RANDOM % 5 + 1))

  # Place a valid order
  curl -sf -X POST "$ORDER_URL/api/orders" \
    -H "Content-Type: application/json" \
    -d "{\"productId\":\"$PRODUCT\",\"quantity\":$QTY}" > /dev/null

  # Occasionally trigger an error trace (unknown product)
  if (( i % 5 == 0 )); then
    curl -sf -X POST "$ORDER_URL/api/orders" \
      -H "Content-Type: application/json" \
      -d "{\"productId\":\"$NONEXISTENT\",\"quantity\":1}" > /dev/null || true
  fi

  # Hit catalog and inventory directly for more span variety
  curl -sf "$CATALOG_URL/api/products" > /dev/null
  curl -sf "$CATALOG_URL/api/products/$PRODUCT" > /dev/null
  curl -sf "$INVENTORY_URL/api/inventory/$PRODUCT" > /dev/null

  echo "  round $i/$ITERATIONS done"
done

echo "==> Done. Check Grafana at http://localhost:3000"
