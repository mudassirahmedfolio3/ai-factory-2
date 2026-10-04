import { Module } from '@nestjs/common';
import { AuthModule } from '../auth/auth.module.js';
import { CheckoutModule } from '../checkout/checkout.module.js';
import { PrismaModule } from '../prisma/prisma.module.js';
import { OrdersController } from './orders.controller.js';
import { OrdersService } from './orders.service.js';

@Module({
  imports: [PrismaModule, AuthModule, CheckoutModule],
  controllers: [OrdersController],
  providers: [OrdersService],
})
export class OrdersModule {}
