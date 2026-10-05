// SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline.
import { IsInt, IsString, Min } from 'class-validator';

export class AddCartItemDto {
  @IsString()
  productId!: string;
}

export class UpdateQuantityDto {
  @IsInt()
  @Min(0)
  quantity!: number;
}
