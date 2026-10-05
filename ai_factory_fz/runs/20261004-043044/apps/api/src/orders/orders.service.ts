import { Injectable, NotFoundException } from '@nestjs/common';
import { Prisma } from '@prisma/client';
import { PaginationQueryDto } from '../catalog/dto/pagination-query.dto';
import { PrismaService } from '../prisma/prisma.service';
import { OrderDetailDto } from './dto/order-detail.dto';
import { OrderListResponseDto } from './dto/order-list-response.dto';
import { ORDER_NOT_FOUND_MESSAGE } from './orders.constants';
import { toOrderDetail, toOrderSummary } from './orders.mapper';

const orderItemsInclude = {
  items: { orderBy: { createdAt: Prisma.SortOrder.asc } },
} satisfies Prisma.OrderInclude;

@Injectable()
export class OrdersService {
  constructor(private readonly prisma: PrismaService) {}

  async listOrders(
    userId: string,
    query: PaginationQueryDto,
  ): Promise<OrderListResponseDto> {
    const skip = (query.page - 1) * query.pageSize;
    const where = { userId };

    const [total, rows] = await Promise.all([
      this.prisma.order.count({ where }),
      this.prisma.order.findMany({
        where,
        skip,
        take: query.pageSize,
        orderBy: { createdAt: Prisma.SortOrder.desc },
      }),
    ]);

    return {
      items: rows.map(toOrderSummary),
      total,
      page: query.page,
      pageSize: query.pageSize,
    };
  }

  async getOrderById(userId: string, orderId: string): Promise<OrderDetailDto> {
    const order = await this.prisma.order.findFirst({
      where: { id: orderId, userId },
      include: orderItemsInclude,
    });

    if (!order) {
      throw new NotFoundException({
        statusCode: 404,
        error: 'Not Found',
        message: ORDER_NOT_FOUND_MESSAGE,
      });
    }

    return toOrderDetail(order);
  }
}
