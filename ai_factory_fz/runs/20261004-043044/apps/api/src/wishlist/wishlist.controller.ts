import {
  Body,
  Controller,
  Delete,
  Get,
  HttpCode,
  HttpStatus,
  Param,
  ParseUUIDPipe,
  Post,
  Query,
  UseGuards,
} from '@nestjs/common';
import {
  ApiBearerAuth,
  ApiOperation,
  ApiParam,
  ApiResponse,
  ApiTags,
} from '@nestjs/swagger';
import { AuthenticatedUser } from '../auth/auth-user.type';
import { CurrentUser } from '../auth/current-user.decorator';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { PaginationQueryDto } from '../catalog/dto/pagination-query.dto';
import { AddWishlistItemRequestDto } from './dto/add-wishlist-item-request.dto';
import { WishlistItemDto } from './dto/wishlist-item.dto';
import { WishlistListResponseDto } from './dto/wishlist-list-response.dto';
import { WishlistService } from './wishlist.service';

@ApiTags('Wishlist')
@Controller('wishlist')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class WishlistController {
  constructor(private readonly wishlistService: WishlistService) {}

  @Get()
  @ApiOperation({ operationId: 'listWishlist', summary: 'List wishlist' })
  @ApiResponse({ status: 200, type: WishlistListResponseDto })
  @ApiResponse({ status: 401, description: 'Unauthorized' })
  listWishlist(
    @CurrentUser() user: AuthenticatedUser,
    @Query() query: PaginationQueryDto,
  ): Promise<WishlistListResponseDto> {
    return this.wishlistService.listWishlist(user.id, query);
  }

  @Post('items')
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ operationId: 'addWishlistItem', summary: 'Add wishlist item' })
  @ApiResponse({ status: 201, type: WishlistItemDto })
  @ApiResponse({ status: 401, description: 'Unauthorized' })
  @ApiResponse({ status: 404, description: 'Product not found' })
  addWishlistItem(
    @CurrentUser() user: AuthenticatedUser,
    @Body() dto: AddWishlistItemRequestDto,
  ): Promise<WishlistItemDto> {
    return this.wishlistService.addWishlistItem(user.id, dto);
  }

  @Delete('items/:productId')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({ operationId: 'removeWishlistItem', summary: 'Remove wishlist item' })
  @ApiParam({ name: 'productId', schema: { type: 'string', format: 'uuid' } })
  @ApiResponse({ status: 204, description: 'Removed' })
  @ApiResponse({ status: 401, description: 'Unauthorized' })
  @ApiResponse({ status: 404, description: 'Wishlist item not found' })
  removeWishlistItem(
    @CurrentUser() user: AuthenticatedUser,
    @Param('productId', ParseUUIDPipe) productId: string,
  ): Promise<void> {
    return this.wishlistService.removeWishlistItem(user.id, productId);
  }
}
