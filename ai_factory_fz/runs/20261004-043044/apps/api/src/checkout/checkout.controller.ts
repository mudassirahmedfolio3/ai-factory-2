import {
  Body,
  Controller,
  HttpCode,
  HttpStatus,
  Post,
  UseGuards,
} from '@nestjs/common';
import {
  ApiBearerAuth,
  ApiHeader,
  ApiOperation,
  ApiResponse,
  ApiTags,
} from '@nestjs/swagger';
import { AuthenticatedUser } from '../auth/auth-user.type';
import { CurrentUser } from '../auth/current-user.decorator';
import { OptionalJwtAuthGuard } from '../auth/optional-jwt-auth.guard';
import { GuestCartIdHeader } from '../cart/guest-cart-id.decorator';
import { CheckoutService } from './checkout.service';
import { CheckoutPreviewRequestDto } from './dto/checkout-preview-request.dto';
import { CheckoutPreviewResponseDto } from './dto/checkout-preview-response.dto';
import { CreateOrderRequestDto } from './dto/create-order-request.dto';
import { CreateOrderResponseDto } from './dto/create-order-response.dto';
import { IdempotencyKeyHeader } from './idempotency-key.decorator';

@ApiTags('Checkout')
@Controller('checkout')
export class CheckoutController {
  constructor(private readonly checkoutService: CheckoutService) {}

  @Post('preview')
  @HttpCode(HttpStatus.OK)
  @UseGuards(OptionalJwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ operationId: 'previewCheckout', summary: 'Preview totals and shipping' })
  @ApiHeader({
    name: 'X-Guest-Cart-Id',
    required: false,
    schema: { type: 'string', format: 'uuid' },
  })
  @ApiResponse({ status: 200, type: CheckoutPreviewResponseDto })
  @ApiResponse({ status: 400, description: 'Invalid address or coupon' })
  @ApiResponse({ status: 422, description: 'Cart empty or not found' })
  previewCheckout(
    @CurrentUser() user: AuthenticatedUser | null,
    @GuestCartIdHeader() guestCartId: string | undefined,
    @Body() dto: CheckoutPreviewRequestDto,
  ): Promise<CheckoutPreviewResponseDto> {
    return this.checkoutService.previewCheckout(user?.id ?? null, guestCartId, dto);
  }

  @Post('orders')
  @HttpCode(HttpStatus.CREATED)
  @UseGuards(OptionalJwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ operationId: 'createOrder', summary: 'Create order and reserve stock' })
  @ApiHeader({
    name: 'X-Guest-Cart-Id',
    required: false,
    schema: { type: 'string', format: 'uuid' },
  })
  @ApiHeader({
    name: 'Idempotency-Key',
    required: true,
    schema: { type: 'string', maxLength: 64 },
  })
  @ApiResponse({ status: 201, type: CreateOrderResponseDto })
  @ApiResponse({ status: 400, description: 'Invalid checkout' })
  @ApiResponse({ status: 409, description: 'Stock or cart conflict' })
  createOrder(
    @CurrentUser() user: AuthenticatedUser | null,
    @GuestCartIdHeader() guestCartId: string | undefined,
    @IdempotencyKeyHeader() idempotencyKey: string | undefined,
    @Body() dto: CreateOrderRequestDto,
  ): Promise<CreateOrderResponseDto> {
    return this.checkoutService.createOrder(
      user?.id ?? null,
      guestCartId,
      idempotencyKey,
      dto,
    );
  }
}
