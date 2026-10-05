# Regenerate app/packages/api_client from docs/openapi.yaml (the contract).
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$DocsOpenApi = Join-Path $Root "docs\openapi.yaml"
$AppDir = Join-Path $Root "app"
$GeneratorImage = if ($env:OPENAPI_GENERATOR_IMAGE) {
  $env:OPENAPI_GENERATOR_IMAGE
} else {
  "openapitools/openapi-generator-cli:v7.25.0"
}

if (-not (Test-Path $DocsOpenApi)) {
  throw "Missing contract: $DocsOpenApi"
}

Copy-Item -Force $DocsOpenApi (Join-Path $AppDir "openapi.yaml")
Copy-Item -Force $DocsOpenApi (Join-Path $Root "server\openapi.yaml")

docker run --rm `
  -v "${AppDir}:/local" `
  -w /local `
  $GeneratorImage generate `
  -c /local/openapi-generator-config.yaml `
  -o /local/packages/api_client

Push-Location (Join-Path $AppDir "packages\api_client")
try {
  dart pub get
  dart run build_runner build --delete-conflicting-outputs
} finally {
  Pop-Location
}

Write-Host "Dart API client regenerated at app/packages/api_client"
