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
  ApiOkResponse,
  ApiOperation,
  ApiTags,
  ApiUnauthorizedResponse,
} from '@nestjs/swagger';
import { CurrentUser } from '../auth/decorators/current-user.decorator.js';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard.js';
import { ErrorResponseDto } from '../common/dto/error-response.dto.js';
import {
  ImportWishlistRequestDto,
  ReplaceWishlistRequestDto,
  WishlistResponseDto,
} from './dto/wishlist.dto.js';
import { WishlistService } from './wishlist.service.js';

@ApiTags('Wishlist')
@Controller('wishlist')
@UseGuards(JwtAuthGuard)
export class WishlistController {
  constructor(private readonly wishlistService: WishlistService) {}

  @Get()
  @ApiOperation({
    operationId: 'getWishlist',
    summary: 'Get signed-in wishlist',
  })
  @ApiOkResponse({ type: WishlistResponseDto, description: 'Wishlist' })
  @ApiUnauthorizedResponse({ type: ErrorResponseDto, description: 'Unauthorized' })
  getWishlist(@CurrentUser() user: { id: string }): Promise<WishlistResponseDto> {
    return this.wishlistService.getWishlist(user.id);
  }

  @Put()
  @ApiOperation({
    operationId: 'replaceWishlist',
    summary: 'Replace wishlist product IDs',
  })
  @ApiOkResponse({ type: WishlistResponseDto, description: 'Updated wishlist' })
  @ApiUnauthorizedResponse({ type: ErrorResponseDto, description: 'Unauthorized' })
  replaceWishlist(
    @CurrentUser() user: { id: string },
    @Body() body: ReplaceWishlistRequestDto,
  ): Promise<WishlistResponseDto> {
    return this.wishlistService.replaceWishlist(user.id, body.productIds);
  }

  @Post('import')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({
    operationId: 'importWishlist',
    summary: 'Import local guest wishlist product IDs',
  })
  @ApiOkResponse({ type: WishlistResponseDto, description: 'Merged wishlist' })
  @ApiUnauthorizedResponse({ type: ErrorResponseDto, description: 'Unauthorized' })
  importWishlist(
    @CurrentUser() user: { id: string },
    @Body() body: ImportWishlistRequestDto,
  ): Promise<WishlistResponseDto> {
    return this.wishlistService.importWishlist(user.id, body.productIds);
  }
}
