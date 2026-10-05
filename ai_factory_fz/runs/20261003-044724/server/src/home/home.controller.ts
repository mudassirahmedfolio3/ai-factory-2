import { Controller, Get } from '@nestjs/common';
import { ApiOkResponse, ApiOperation, ApiTags } from '@nestjs/swagger';
import { HomeResponse } from './dto/home.responses.js';
import { HomeService } from './home.service.js';

@ApiTags('Home')
@Controller()
export class HomeController {
  constructor(private readonly homeService: HomeService) {}

  @Get('home')
  @ApiOperation({
    operationId: 'getHome',
    summary: 'Merchandised home content',
  })
  @ApiOkResponse({
    type: HomeResponse,
    description: 'Home payload',
  })
  getHome(): Promise<HomeResponse> {
    return this.homeService.getHome();
  }
}
