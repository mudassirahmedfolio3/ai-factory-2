#!/bin/sh
set -eu

npx prisma migrate deploy

if [ "${RUN_DB_SEED:-true}" != "false" ]; then
  node dist/seed/database-seed.js
fi

exec node dist/main.js
