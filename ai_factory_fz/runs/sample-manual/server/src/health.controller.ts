// SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline.
import { Controller, Get } from '@nestjs/common';
import { Public } from './auth/public.decorator';

@Controller('health')
export class HealthController {
  /** getHealth: liveness check used by staging and the smoke test. */
  @Public()
  @Get()
  get() {
    return { status: 'ok' };
  }
}
