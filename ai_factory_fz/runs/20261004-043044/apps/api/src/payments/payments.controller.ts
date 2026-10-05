import { Body, Controller, HttpCode, HttpStatus, Post, UseGuards } from '@nestjs/common';
import {
  ApiBearerAuth,
  ApiOperation,
  ApiResponse,
  ApiTags,
} from '@nestjs/swagger';
import { AuthenticatedUser } from '../auth/auth-user.type';
import { CurrentUser } from '../auth/current-user.decorator';
import { OptionalJwtAuthGuard } from '../auth/optional-jwt-auth.guard';
import { MockPaymentConfirmRequestDto } from './dto/mock-payment-confirm-request.dto';
import { MockPaymentConfirmResponseDto } from './dto/mock-payment-confirm-response.dto';
import { PaymentsService } from './payments.service';

@ApiTags('Payments')
@Controller('payments')
export class PaymentsController {
  constructor(private readonly paymentsService: PaymentsService) {}

  @Post('mock/confirm')
  @HttpCode(HttpStatus.OK)
  @UseGuards(OptionalJwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({
    operationId: 'confirmMockPayment',
    summary: 'Confirm mock payment',
    description: 'No card PAN/CVV fields accepted.',
  })
  @ApiResponse({ status: 200, type: MockPaymentConfirmResponseDto })
  @ApiResponse({ status: 402, description: 'Payment failed' })
  confirmMockPayment(
    @CurrentUser() user: AuthenticatedUser | null,
    @Body() dto: MockPaymentConfirmRequestDto,
  ): Promise<MockPaymentConfirmResponseDto> {
    return this.paymentsService.confirmMockPayment(user?.id ?? null, dto);
  }
}
