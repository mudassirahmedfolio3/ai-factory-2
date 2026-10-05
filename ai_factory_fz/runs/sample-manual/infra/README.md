<!-- SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline. -->
# Staging runbook

## Run staging
1. `cd infra`
2. `docker compose -f docker-compose.staging.yml up --build`
3. The API is at http://localhost:3000 (health check: `GET /health`).

## Variables production needs
- `DATABASE_URL`: managed PostgreSQL connection string.
- `JWT_SECRET`: long random secret from your secret manager.
- `PORT`: port the API listens on.

Never commit real values; `staging.env` only holds placeholders.
