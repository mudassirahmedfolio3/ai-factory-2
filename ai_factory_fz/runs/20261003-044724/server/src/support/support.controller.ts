import { Body, Controller, HttpCode, HttpStatus, Post, UseGuards } from '@nestjs/common';
import {
  ApiBadRequestResponse,
  ApiCreatedResponse,
  ApiOperation,
  ApiTags,
} from '@nestjs/swagger';
import { ErrorResponseDto } from '../common/dto/error-response.dto.js';
import { CurrentUser } from '../auth/decorators/current-user.decorator.js';
import { OptionalJwtAuthGuard } from '../auth/guards/optional-jwt-auth.guard.js';
import {
  SupportMessageRequestDto,
  SupportMessageResponseDto,
} from './dto/support.dto.js';
import { SupportService } from './support.service.js';

@ApiTags('Support')
@Controller('support')
export class SupportController {
  constructor(private readonly supportService: SupportService) {}

  @Post('messages')
  @HttpCode(HttpStatus.CREATED)
  @UseGuards(OptionalJwtAuthGuard)
  @ApiOperation({
    operationId: 'submitSupportMessage',
    summary: 'Submit support form (simulated send)',
  })
  @ApiCreatedResponse({
    type: SupportMessageResponseDto,
    description: 'Message recorded',
  })
  @ApiBadRequestResponse({
    type: ErrorResponseDto,
    description: 'Validation error',
  })
  submitMessage(
    @CurrentUser() user: { id: string } | undefined,
    @Body() body: SupportMessageRequestDto,
  ): Promise<SupportMessageResponseDto> {
    return this.supportService.submitMessage(body, user?.id);
  }
}
