import { createParamDecorator, ExecutionContext } from '@nestjs/common';

export const GuestCartIdHeader = createParamDecorator(
  (_data: unknown, ctx: ExecutionContext): string | undefined => {
    const request = ctx.switchToHttp().getRequest<{ headers: Record<string, string | undefined> }>();
    const raw = request.headers['x-guest-cart-id'];
    return typeof raw === 'string' && raw.trim().length > 0 ? raw.trim() : undefined;
  },
);
