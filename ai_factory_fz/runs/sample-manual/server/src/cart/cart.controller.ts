// SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline.
import { Body, Controller, Get, Param, Patch, Post, Req } from '@nestjs/common';
import { CartService } from './cart.service';
import { AddCartItemDto, UpdateQuantityDto } from './cart.dto';

@Controller('cart')
export class CartController {
  constructor(private readonly cart: CartService) {}

  @Get()
  get(@Req() req: { deviceId: string }) {
    return this.cart.getCart(req.deviceId);
  }

  @Post('items')
  add(@Req() req: { deviceId: string }, @Body() body: AddCartItemDto) {
    return this.cart.addItem(req.deviceId, body.productId);
  }

  @Patch('items/:productId')
  update(@Req() req: { deviceId: string }, @Param('productId') productId: string, @Body() body: UpdateQuantityDto) {
    return this.cart.setQuantity(req.deviceId, productId, body.quantity);
  }
}
