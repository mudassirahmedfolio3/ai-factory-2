import { Controller, Get, Param, ParseUUIDPipe, Query, UseGuards } from '@nestjs/common';
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
import { OrderDetailDto } from './dto/order-detail.dto';
import { OrderListResponseDto } from './dto/order-list-response.dto';
import { OrdersService } from './orders.service';

@ApiTags('Orders')
@Controller('orders')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class OrdersController {
  constructor(private readonly ordersService: OrdersService) {}

  @Get()
  @ApiOperation({ operationId: 'listOrders', summary: 'Order history' })
  @ApiResponse({ status: 200, type: OrderListResponseDto })
  @ApiResponse({ status: 401, description: 'Unauthorized' })
  listOrders(
    @CurrentUser() user: AuthenticatedUser,
    @Query() query: PaginationQueryDto,
  ): Promise<OrderListResponseDto> {
    return this.ordersService.listOrders(user.id, query);
  }

  @Get(':orderId')
  @ApiOperation({ operationId: 'getOrderById', summary: 'Order detail' })
  @ApiParam({ name: 'orderId', schema: { type: 'string', format: 'uuid' } })
  @ApiResponse({ status: 200, type: OrderDetailDto })
  @ApiResponse({ status: 404, description: 'Not found' })
  getOrderById(
    @CurrentUser() user: AuthenticatedUser,
    @Param('orderId', ParseUUIDPipe) orderId: string,
  ): Promise<OrderDetailDto> {
    return this.ordersService.getOrderById(user.id, orderId);
  }
}
