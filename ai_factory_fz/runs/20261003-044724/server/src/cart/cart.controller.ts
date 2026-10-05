import {
  Body,
  Controller,
  Get,
  HttpCode,
  HttpStatus,
  Post,
  Put,
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
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard.js';
import { CartService } from './cart.service.js';
import {
  CartResponseDto,
  MergeCartRequestDto,
  MergeCartStrategy,
  ReplaceCartRequestDto,
} from './dto/cart.dto.js';

@ApiTags('Cart')
@Controller('cart')
@UseGuards(JwtAuthGuard)
export class CartController {
  constructor(private readonly cartService: CartService) {}

  @Get()
  @ApiOperation({ operationId: 'getCart', summary: 'Get signed-in user cart' })
  @ApiOkResponse({ type: CartResponseDto, description: 'Cart' })
  @ApiUnauthorizedResponse({ type: ErrorResponseDto, description: 'Unauthorized' })
  getCart(@CurrentUser() user: { id: string }): Promise<CartResponseDto> {
    return this.cartService.getCart(user.id);
  }

  @Put()
  @ApiOperation({
    operationId: 'replaceCart',
    summary: 'Replace cart items (full sync)',
  })
  @ApiOkResponse({ type: CartResponseDto, description: 'Updated cart' })
  @ApiBadRequestResponse({
    type: ErrorResponseDto,
    description: 'Invalid items or insufficient stock',
  })
  @ApiUnauthorizedResponse({ type: ErrorResponseDto, description: 'Unauthorized' })
  replaceCart(
    @CurrentUser() user: { id: string },
    @Body() body: ReplaceCartRequestDto,
  ): Promise<CartResponseDto> {
    return this.cartService.replaceCart(user.id, body.items);
  }

  @Post('merge')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({
    operationId: 'mergeCart',
    summary: 'Merge guest cart lines into account cart',
  })
  @ApiOkResponse({ type: CartResponseDto, description: 'Merged cart' })
  @ApiUnauthorizedResponse({ type: ErrorResponseDto, description: 'Unauthorized' })
  mergeCart(
    @CurrentUser() user: { id: string },
    @Body() body: MergeCartRequestDto,
  ): Promise<CartResponseDto> {
    return this.cartService.mergeCart(
      user.id,
      body.guestItems,
      body.strategy ?? MergeCartStrategy.MERGE,
    );
  }
}
