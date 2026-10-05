jest.mock('@nestjs/common', () => ({
  Controller: () => (target: unknown) => target,
  Get: () => () => undefined,
  Param: () => () => undefined,
  Query: () => () => undefined,
  Injectable: () => (target: unknown) => target,
  UseGuards: () => () => undefined,
}));

jest.mock('@nestjs/swagger', () => ({
  ApiTags: () => () => undefined,
  ApiOperation: () => () => undefined,
  ApiResponse: () => () => undefined,
  ApiParam: () => () => undefined,
  ApiProperty: () => () => undefined,
  ApiPropertyOptional: () => () => undefined,
  ApiBearerAuth: () => () => undefined,
  ApiHeader: () => () => undefined,
}));

jest.mock('../auth/optional-jwt-auth.guard', () => ({
  OptionalJwtAuthGuard: class OptionalJwtAuthGuard {},
}));

jest.mock('../auth/current-user.decorator', () => ({
  CurrentUser: () => () => undefined,
}));

jest.mock('../cart/guest-cart-id.decorator', () => ({
  GuestCartIdHeader: () => () => undefined,
}));

jest.mock('./catalog.service', () => ({
  CatalogService: class CatalogService {},
}));

import { CatalogController } from './catalog.controller';
import { CatalogService } from './catalog.service';

describe('CatalogController', () => {
  it('delegates catalog read operations to CatalogService', async () => {
    const homePayload = { categories: [], featuredProducts: [] };
    const listPayload = { items: [] };
    const detailPayload = { id: 'c1', name: 'Ceiling', slug: 'ceiling-lights' };

    const catalogService = {
      getHome: jest.fn().mockResolvedValue(homePayload),
      listCategories: jest.fn().mockResolvedValue(listPayload),
      getCategoryBySlug: jest.fn().mockResolvedValue(detailPayload),
      getCatalogFacets: jest.fn().mockResolvedValue({ brands: [], finishes: [], wattage: { minW: 0, maxW: 0 }, price: { minPriceCents: 0, maxPriceCents: 0 }, categories: [] }),
      listProducts: jest.fn().mockResolvedValue({ items: [], total: 0, page: 1, pageSize: 20 }),
      getProductById: jest.fn().mockResolvedValue({ id: 'p1' }),
      listProductReviews: jest.fn().mockResolvedValue({ items: [], total: 0, page: 1, pageSize: 20, rating: { averageRating: 0, reviewCount: 0 } }),
    };

    const controller = new CatalogController(
      catalogService as unknown as CatalogService,
    );

    await expect(controller.getHome()).resolves.toEqual(homePayload);
    await expect(controller.listCategories({ depth: 2 })).resolves.toEqual(
      listPayload,
    );
    await expect(controller.getCategoryBySlug('ceiling-lights')).resolves.toEqual(
      detailPayload,
    );

    expect(catalogService.getHome).toHaveBeenCalledTimes(1);
    expect(catalogService.listCategories).toHaveBeenCalledWith(2);
    expect(catalogService.getCategoryBySlug).toHaveBeenCalledWith(
      'ceiling-lights',
    );

    await expect(
      controller.getCatalogFacets({}),
    ).resolves.toEqual(expect.objectContaining({ brands: [] }));
    await expect(
      controller.listProducts({ page: 1, pageSize: 20, sort: 'popularity' as never, inStockOnly: false }),
    ).resolves.toEqual(expect.objectContaining({ total: 0 }));
    await expect(
      controller.getProductById(
        'p1111111-1111-4111-8111-111111111101',
        null,
        undefined,
      ),
    ).resolves.toEqual({ id: 'p1' });
    expect(catalogService.getProductById).toHaveBeenCalledWith(
      'p1111111-1111-4111-8111-111111111101',
      { userId: null, sessionId: null },
    );
    await expect(
      controller.listProductReviews('p1111111-1111-4111-8111-111111111101', { page: 1, pageSize: 10 }),
    ).resolves.toEqual(expect.objectContaining({ total: 0 }));
  });
});
