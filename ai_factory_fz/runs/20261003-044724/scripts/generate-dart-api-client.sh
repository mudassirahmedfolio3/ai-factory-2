#!/usr/bin/env bash
# Regenerate app/packages/api_client from docs/openapi.yaml (the contract).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOCS_OPENAPI="${ROOT}/docs/openapi.yaml"
APP_DIR="${ROOT}/app"
GENERATOR_IMAGE="${OPENAPI_GENERATOR_IMAGE:-openapitools/openapi-generator-cli:v7.25.0}"

if [[ ! -f "${DOCS_OPENAPI}" ]]; then
  echo "Missing contract: ${DOCS_OPENAPI}" >&2
  exit 1
fi

cp "${DOCS_OPENAPI}" "${APP_DIR}/openapi.yaml"
cp "${DOCS_OPENAPI}" "${ROOT}/server/openapi.yaml"

docker run --rm \
  -v "${APP_DIR}:/local" \
  -w /local \
  "${GENERATOR_IMAGE}" generate \
  -c /local/openapi-generator-config.yaml \
  -o /local/packages/api_client

(
  cd "${APP_DIR}/packages/api_client"
  dart pub get
  dart run build_runner build --delete-conflicting-outputs
)

echo "Dart API client regenerated at app/packages/api_client"
