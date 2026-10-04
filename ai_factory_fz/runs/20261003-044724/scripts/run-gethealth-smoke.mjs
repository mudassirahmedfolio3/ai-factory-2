#!/usr/bin/env node
import { waitForGetHealth } from './health-smoke.mjs';

const url =
  process.argv[2] ??
  process.env.HEALTH_SMOKE_URL ??
  `http://127.0.0.1:${process.env.PORT ?? '3000'}/health`;

const result = await waitForGetHealth(url, { attempts: 45, intervalMs: 2000 });
if (!result.ok) {
  console.error('getHealth smoke failed:', result.reason ?? result);
  process.exit(1);
}
console.log('getHealth smoke passed:', JSON.stringify(result.body));
