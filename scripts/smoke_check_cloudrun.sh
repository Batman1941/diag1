#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-${CLOUDRUN_BASE_URL:-}}"

if [[ -z "$BASE_URL" ]]; then
  echo "Usage: ./scripts/smoke_check_cloudrun.sh https://app.example.com" >&2
  echo "or set CLOUDRUN_BASE_URL=https://app.example.com" >&2
  exit 1
fi

if [[ "$BASE_URL" == *"//"* ]]; then
  DOMAIN="$BASE_URL"
else
  DOMAIN="https://$BASE_URL"
fi

endpoints=(
  "/"
  "/api/healthz"
  "/api/health"
  "/api/docs"
)

printf "Sprawdzam endpointy na: %s\n" "$DOMAIN"
for path in "${endpoints[@]}"; do
  url="${DOMAIN%/}${path}"
  code="$(curl -k -sS -o /tmp/diag1_smoke_body.txt -w "%{http_code}" --max-time 20 "$url" || true)"
  body_preview="$(sed -n '1,2p' /tmp/diag1_smoke_body.txt | tr '\n' ' ' | cut -c1-120)"
  printf "%-20s %s\n" "$path" "$code"
  if [[ -n "$body_preview" ]]; then
    printf "  preview: %s\n" "$body_preview"
  fi
done

rm -f /tmp/diag1_smoke_body.txt

echo "Gotowe. Jeśli frontend działa poprawnie, '/' powinno zwrócić stronę HTML aplikacji, a '/api/healthz' JSON."
