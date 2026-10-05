#!/usr/bin/env bash
# Staging smoke: GET /health (operationId getHealth) against docker-compose API.
# Requires: Node 18+, optional docker compose stack already up (see --up).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HEALTH_URL="${HEALTH_SMOKE_URL:-http://127.0.0.1:${PORT:-3000}/health}"
COMPOSE_UP=false

usage() {
  echo "Usage: $0 [--up] [--url <health-url>]" >&2
  echo "  --up    docker compose up -d --build --wait (from repo root)" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --up) COMPOSE_UP=true; shift ;;
    --url) HEALTH_URL="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ "$COMPOSE_UP" == true ]]; then
  cd "${ROOT}"
  docker compose up -d --build --wait
fi

node "${ROOT}/scripts/run-gethealth-smoke.mjs" "${HEALTH_URL}"
