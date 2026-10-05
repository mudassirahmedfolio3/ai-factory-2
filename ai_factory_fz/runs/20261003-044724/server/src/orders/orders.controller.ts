import {
  Body,
  Controller,
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
  ApiBadRequestResponse,
  ApiConflictResponse,
  ApiCreatedResponse,
  ApiNotFoundResponse,
  ApiOkResponse,
  ApiOperation,
  ApiTags,
  ApiUnauthorizedResponse,
} from '@nestjs/swagger';
import { ErrorResponseDto } from '../common/dto/error-response.dto.js';
import { CurrentUser } from '../auth/decorators/current-user.decorator.js';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard.js';
import {
  CreateOrderRequestDto,
  ListOrdersQueryDto,
  OrderDetailDto,
  OrderListResponseDto,
} from './dto/orders.dto.js';
import { OrdersService } from './orders.service.js';

@ApiTags('Orders')
@Controller('orders')
@UseGuards(JwtAuthGuard)
export class OrdersController {
  constructor(private readonly ordersService: OrdersService) {}

  @Post()
  @ApiOperation({
    operationId: 'createOrder',
    summary: 'Place order (pending_payment, reserves stock)',
  })
  @ApiCreatedResponse({ type: OrderDetailDto, description: 'Order created' })
  @ApiBadRequestResponse({
    type: ErrorResponseDto,
    description: 'Stock or validation error',
  })
  @ApiUnauthorizedResponse({ type: ErrorResponseDto, description: 'Unauthorized' })
  createOrder(
    @CurrentUser() user: { id: string },
    @Body() body: CreateOrderRequestDto,
  ): Promise<OrderDetailDto> {
    return this.ordersService.createOrder(user.id, body);
  }

  @Get()
  @ApiOperation({ operationId: 'listOrders', summary: 'List my orders' })
  @ApiOkResponse({ type: OrderListResponseDto, description: 'Paginated orders' })
  @ApiUnauthorizedResponse({ type: ErrorResponseDto, description: 'Unauthorized' })
  listOrders(
    @CurrentUser() user: { id: string },
    @Query() query: ListOrdersQueryDto,
  ): Promise<OrderListResponseDto> {
    const page = query.page ?? 1;
    const pageSize = query.pageSize ?? 20;
    return this.ordersService.listOrders(user.id, page, pageSize);
  }

  @Get(':orderId')
  @ApiOperation({ operationId: 'getOrderById', summary: 'Get order detail' })
  @ApiOkResponse({ type: OrderDetailDto, description: 'Order detail' })
  @ApiNotFoundResponse({ type: ErrorResponseDto, description: 'Not found' })
  @ApiUnauthorizedResponse({ type: ErrorResponseDto, description: 'Unauthorized' })
  getOrderById(
    @CurrentUser() user: { id: string },
    @Param('orderId', ParseUUIDPipe) orderId: string,
  ): Promise<OrderDetailDto> {
    return this.ordersService.getOrderById(user.id, orderId);
  }

  @Post(':orderId/complete-mock-payment')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({
    operationId: 'completeMockPayment',
    summary: 'Demo pay-now (marks order paid, no Stripe)',
  })
  @ApiOkResponse({ type: OrderDetailDto, description: 'Payment succeeded' })
  @ApiConflictResponse({
    type: ErrorResponseDto,
    description: 'Order not payable',
  })
  @ApiUnauthorizedResponse({ type: ErrorResponseDto, description: 'Unauthorized' })
  completeMockPayment(
    @CurrentUser() user: { id: string },
    @Param('orderId', ParseUUIDPipe) orderId: string,
  ): Promise<OrderDetailDto> {
    return this.ordersService.completeMockPayment(user.id, orderId);
  }

  @Post(':orderId/cancel')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({
    operationId: 'cancelOrder',
    summary: 'Cancel pending_payment order and release stock',
  })
  @ApiOkResponse({ type: OrderDetailDto, description: 'Cancelled order' })
  @ApiConflictResponse({
    type: ErrorResponseDto,
    description: 'Not cancellable',
  })
  @ApiUnauthorizedResponse({ type: ErrorResponseDto, description: 'Unauthorized' })
  cancelOrder(
    @CurrentUser() user: { id: string },
    @Param('orderId', ParseUUIDPipe) orderId: string,
  ): Promise<OrderDetailDto> {
    return this.ordersService.cancelOrder(user.id, orderId);
  }
}
