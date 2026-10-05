import { Module } from '@nestjs/common';
import { AuthModule } from '../auth/auth.module';
import { CartModule } from '../cart/cart.module';
import { CheckoutController } from './checkout.controller';
import { CheckoutCouponService } from './checkout-coupon.service';
import { CheckoutService } from './checkout.service';

@Module({
  imports: [AuthModule, CartModule],
  controllers: [CheckoutController],
  providers: [CheckoutService, CheckoutCouponService],
  exports: [CheckoutService],
})
export class CheckoutModule {}
