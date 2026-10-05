import {
  Body,
  Controller,
  Delete,
  Get,
  HttpCode,
  HttpStatus,
  Param,
  ParseUUIDPipe,
  Patch,
  Post,
  UseGuards,
} from '@nestjs/common';
import {
  ApiBearerAuth,
  ApiHeader,
  ApiOperation,
  ApiParam,
  ApiResponse,
  ApiTags,
} from '@nestjs/swagger';
import { AuthenticatedUser } from '../auth/auth-user.type';
import { CurrentUser } from '../auth/current-user.decorator';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { OptionalJwtAuthGuard } from '../auth/optional-jwt-auth.guard';
import { CartService } from './cart.service';
import { GuestCartIdHeader } from './guest-cart-id.decorator';
import { AddCartItemRequestDto } from './dto/add-cart-item-request.dto';
import { CartResponseDto } from './dto/cart-response.dto';
import { UpdateCartItemRequestDto } from './dto/update-cart-item-request.dto';

@ApiTags('Cart')
@Controller('cart')
export class CartController {
  constructor(private readonly cartService: CartService) {}

  @Get()
  @UseGuards(OptionalJwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ operationId: 'getCart', summary: 'Get cart' })
  @ApiHeader({
    name: 'X-Guest-Cart-Id',
    required: false,
    schema: { type: 'string', format: 'uuid' },
  })
  @ApiResponse({ status: 200, type: CartResponseDto })
  @ApiResponse({ status: 400, description: 'Bad request' })
  getCart(
    @CurrentUser() user: AuthenticatedUser | null,
    @GuestCartIdHeader() guestCartId?: string,
  ): Promise<CartResponseDto> {
    return this.cartService.getCart(user?.id ?? null, guestCartId);
  }

  @Post('items')
  @HttpCode(HttpStatus.OK)
  @UseGuards(OptionalJwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ operationId: 'addCartItem', summary: 'Add cart line' })
  @ApiHeader({
    name: 'X-Guest-Cart-Id',
    required: false,
    schema: { type: 'string', format: 'uuid' },
  })
  @ApiResponse({ status: 200, type: CartResponseDto })
  @ApiResponse({ status: 409, description: 'Insufficient stock' })
  addCartItem(
    @CurrentUser() user: AuthenticatedUser | null,
    @GuestCartIdHeader() guestCartId: string | undefined,
    @Body() dto: AddCartItemRequestDto,
  ): Promise<CartResponseDto> {
    return this.cartService.addCartItem(user?.id ?? null, guestCartId, dto);
  }

  @Patch('items/:itemId')
  @UseGuards(OptionalJwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ operationId: 'updateCartItem', summary: 'Update quantity' })
  @ApiParam({ name: 'itemId', schema: { type: 'string', format: 'uuid' } })
  @ApiHeader({
    name: 'X-Guest-Cart-Id',
    required: false,
    schema: { type: 'string', format: 'uuid' },
  })
  @ApiResponse({ status: 200, type: CartResponseDto })
  @ApiResponse({ status: 404, description: 'Cart item not found' })
  @ApiResponse({ status: 409, description: 'Insufficient stock' })
  updateCartItem(
    @CurrentUser() user: AuthenticatedUser | null,
    @GuestCartIdHeader() guestCartId: string | undefined,
    @Param('itemId', ParseUUIDPipe) itemId: string,
    @Body() dto: UpdateCartItemRequestDto,
  ): Promise<CartResponseDto> {
    return this.cartService.updateCartItem(user?.id ?? null, guestCartId, itemId, dto);
  }

  @Delete('items/:itemId')
  @UseGuards(OptionalJwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ operationId: 'removeCartItem', summary: 'Remove line' })
  @ApiParam({ name: 'itemId', schema: { type: 'string', format: 'uuid' } })
  @ApiHeader({
    name: 'X-Guest-Cart-Id',
    required: false,
    schema: { type: 'string', format: 'uuid' },
  })
  @ApiResponse({ status: 200, type: CartResponseDto })
  @ApiResponse({ status: 404, description: 'Cart item not found' })
  removeCartItem(
    @CurrentUser() user: AuthenticatedUser | null,
    @GuestCartIdHeader() guestCartId: string | undefined,
    @Param('itemId', ParseUUIDPipe) itemId: string,
  ): Promise<CartResponseDto> {
    return this.cartService.removeCartItem(user?.id ?? null, guestCartId, itemId);
  }

  @Post('merge')
  @HttpCode(HttpStatus.OK)
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ operationId: 'mergeGuestCart', summary: 'Merge guest cart after login' })
  @ApiHeader({
    name: 'X-Guest-Cart-Id',
    required: false,
    schema: { type: 'string', format: 'uuid' },
  })
  @ApiResponse({ status: 200, type: CartResponseDto })
  @ApiResponse({ status: 400, description: 'Invalid guest cart' })
  @ApiResponse({ status: 401, description: 'Unauthorized' })
  mergeGuestCart(
    @CurrentUser() user: AuthenticatedUser,
    @GuestCartIdHeader() guestCartId?: string,
  ): Promise<CartResponseDto> {
    return this.cartService.mergeGuestCart(user.id, guestCartId);
  }
}
