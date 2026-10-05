import { createParamDecorator, ExecutionContext } from '@nestjs/common';

export const IdempotencyKeyHeader = createParamDecorator(
  (_data: unknown, ctx: ExecutionContext): string | undefined => {
    const request = ctx.switchToHttp().getRequest<{ headers: Record<string, string | undefined> }>();
    const raw = request.headers['idempotency-key'];
    return typeof raw === 'string' && raw.trim().length > 0 ? raw.trim() : undefined;
  },
);
