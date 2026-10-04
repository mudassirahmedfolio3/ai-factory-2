import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service.js';
import type {
  SupportMessageRequestDto,
  SupportMessageResponseDto,
} from './dto/support.dto.js';

@Injectable()
export class SupportService {
  constructor(private readonly prisma: PrismaService) {}

  async submitMessage(
    dto: SupportMessageRequestDto,
    userId?: string,
  ): Promise<SupportMessageResponseDto> {
    const record = await this.prisma.supportMessage.create({
      data: {
        email: dto.email,
        subject: dto.subject,
        body: dto.body,
        orderNumber: dto.orderNumber,
        userId,
      },
    });

    return {
      id: record.id,
      message:
        'Thank you for contacting ShopEase support. We aim to respond within one to two business days.',
    };
  }
}
