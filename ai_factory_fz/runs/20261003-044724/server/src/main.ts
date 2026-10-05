import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module.js';
import { setupApplication } from './app.setup.js';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  await setupApplication(app);
  await app.listen(process.env.PORT ?? 3000);
}
await bootstrap();
