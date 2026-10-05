import { Module } from '@nestjs/common';
import { AuthModule } from '../auth/auth.module';
import { PrismaModule } from '../prisma/prisma.module';
import { CatalogAnalyticsService } from './catalog-analytics.service';
import { CatalogController } from './catalog.controller';
import { CatalogSeedService } from './catalog-seed.service';
import { CatalogService } from './catalog.service';

@Module({
  imports: [PrismaModule, AuthModule],
  controllers: [CatalogController],
  providers: [CatalogSeedService, CatalogAnalyticsService, CatalogService],
  exports: [CatalogSeedService, CatalogService, CatalogAnalyticsService],
})
export class CatalogModule {}
