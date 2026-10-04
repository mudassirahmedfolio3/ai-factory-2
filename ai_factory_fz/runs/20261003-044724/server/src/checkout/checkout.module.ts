import { Module } from '@nestjs/common';
import { AuthModule } from '../auth/auth.module.js';
import { PrismaModule } from '../prisma/prisma.module.js';
import { CheckoutPricingService } from './checkout-pricing.service.js';
import { CheckoutController } from './checkout.controller.js';
import { CheckoutService } from './checkout.service.js';

@Module({
  imports: [PrismaModule, AuthModule],
  controllers: [CheckoutController],
  providers: [CheckoutService, CheckoutPricingService],
  exports: [CheckoutService, CheckoutPricingService],
})
export class CheckoutModule {}
