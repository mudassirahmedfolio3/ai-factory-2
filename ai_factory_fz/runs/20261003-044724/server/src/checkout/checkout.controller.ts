import {
  Body,
  Controller,
  HttpCode,
  HttpStatus,
  Post,
  UseGuards,
} from '@nestjs/common';
import {
  ApiBadRequestResponse,
  ApiOkResponse,
  ApiOperation,
  ApiTags,
  ApiUnauthorizedResponse,
} from '@nestjs/swagger';
import { ErrorResponseDto } from '../common/dto/error-response.dto.js';
import { CurrentUser } from '../auth/decorators/current-user.decorator.js';
import { OptionalJwtAuthGuard } from '../auth/guards/optional-jwt-auth.guard.js';
import { CheckoutService } from './checkout.service.js';
import {
  CheckoutQuoteRequestDto,
  CheckoutQuoteResponseDto,
} from './dto/checkout.dto.js';

@ApiTags('Checkout')
@Controller('checkout')
export class CheckoutController {
  constructor(private readonly checkoutService: CheckoutService) {}

  @Post('quote')
  @HttpCode(HttpStatus.OK)
  @UseGuards(OptionalJwtAuthGuard)
  @ApiOperation({
    operationId: 'createCheckoutQuote',
    summary: 'Compute shipping, tax, coupon, and totals',
  })
  @ApiOkResponse({ type: CheckoutQuoteResponseDto, description: 'Quote' })
  @ApiBadRequestResponse({
    type: ErrorResponseDto,
    description: 'Invalid address or coupon',
  })
  @ApiUnauthorizedResponse({
    type: ErrorResponseDto,
    description: 'Unauthorized when using server cart',
  })
  createQuote(
    @CurrentUser() user: { id: string } | undefined,
    @Body() body: CheckoutQuoteRequestDto,
  ): Promise<CheckoutQuoteResponseDto> {
    return this.checkoutService.createQuote(user?.id, body);
  }
}
