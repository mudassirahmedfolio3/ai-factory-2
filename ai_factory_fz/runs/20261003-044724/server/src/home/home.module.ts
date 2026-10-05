import { Module } from '@nestjs/common';
import { CatalogModule } from '../catalog/catalog.module.js';
import { HomeController } from './home.controller.js';
import { HomeService } from './home.service.js';

@Module({
  imports: [CatalogModule],
  controllers: [HomeController],
  providers: [HomeService],
})
export class HomeModule {}
