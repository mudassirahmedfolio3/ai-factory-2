// SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline.
import { Module } from '@nestjs/common';
import { APP_GUARD } from '@nestjs/core';
import { JwtModule } from '@nestjs/jwt';
import { AuthController } from './auth/auth.controller';
import { JwtGuard } from './auth/jwt.guard';
import { CartController } from './cart/cart.controller';
import { CartService } from './cart/cart.service';
import { HealthController } from './health.controller';
import { PrismaService } from './prisma.service';
import { ProductsController } from './products/products.controller';
import { ProductsService } from './products/products.service';

@Module({
  imports: [JwtModule.register({ global: true, secret: process.env.JWT_SECRET, signOptions: { expiresIn: '30d' } })],
  controllers: [AuthController, HealthController, ProductsController, CartController],
  providers: [PrismaService, ProductsService, CartService, { provide: APP_GUARD, useClass: JwtGuard }],
})
export class AppModule {}
