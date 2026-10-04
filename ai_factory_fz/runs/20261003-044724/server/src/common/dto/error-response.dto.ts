import { ApiProperty } from '@nestjs/swagger';

export class ErrorResponseDto {
  @ApiProperty({ example: 503 })
  statusCode!: number;

  @ApiProperty({ example: 'Service Unavailable' })
  error!: string;

  @ApiProperty({ example: 'Database is unreachable' })
  message!: string;
}
