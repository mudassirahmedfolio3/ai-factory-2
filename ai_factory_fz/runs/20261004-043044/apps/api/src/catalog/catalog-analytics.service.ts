import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { PrismaService } from '../prisma/prisma.service';
import { ProductViewAnalyticsContext } from './catalog-analytics.types';

/**
 * NFR-10 browse funnel hook: logs product views and optionally persists ProductViewEvent rows.
 * Persistence is off by default so catalog reads stay lightweight in demo/staging.
 */
@Injectable()
export class CatalogAnalyticsService {
  private readonly logger = new Logger(CatalogAnalyticsService.name);
  private readonly persistProductViews: boolean;

  constructor(
    private readonly prisma: PrismaService,
    configService: ConfigService,
  ) {
    this.persistProductViews =
      configService.get<number>('ANALYTICS_PERSIST_PRODUCT_VIEWS') === 1;
  }

  recordProductView(
    productId: string,
    context?: ProductViewAnalyticsContext,
  ): void {
    const userId = context?.userId ?? null;
    const sessionId = this.normalizeSessionId(context?.sessionId);

    this.logger.log(
      `[Analytics] product_view productId=${productId} userId=${userId ?? 'guest'} sessionId=${sessionId ?? 'none'} persist=${this.persistProductViews}`,
    );

    if (!this.persistProductViews) {
      return;
    }

    void this.persistProductView(productId, userId, sessionId).catch((err) => {
      this.logger.warn(
        `[Analytics] product_view persistence failed productId=${productId}: ${
          err instanceof Error ? err.message : String(err)
        }`,
      );
    });
  }

  private normalizeSessionId(sessionId?: string | null): string | null {
    if (sessionId == null || sessionId.trim().length === 0) {
      return null;
    }
    return sessionId.trim().slice(0, 64);
  }

  private async persistProductView(
    productId: string,
    userId: string | null,
    sessionId: string | null,
  ): Promise<void> {
    await this.prisma.productViewEvent.create({
      data: {
        productId,
        userId: userId ?? undefined,
        sessionId: sessionId ?? undefined,
      },
    });
  }
}
