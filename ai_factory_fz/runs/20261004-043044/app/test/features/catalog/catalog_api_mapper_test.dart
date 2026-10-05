import 'package:api_client/api_client.dart' as api;
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/catalog/data/api/catalog_api_mapper.dart';
import 'package:shopease_app/features/catalog/domain/models/product.dart';

void main() {
  test('mapMoney preserves integer pence and GBP currency', () {
    final money = mapMoney(
      api.Money((b) => b
        ..amountCents = 4999
        ..currency = 'GBP'),
    );
    expect(money.priceMinorUnits, 4999);
    expect(money.currency, 'GBP');
  });

  test('mapRatingSummary coerces average rating to double', () {
    final rating = mapRatingSummary(
      api.RatingSummary(
        (r) => r
          ..averageRating = 4
          ..reviewCount = 1,
      ),
    );
    expect(rating.averageRating, 4.0);
    expect(rating.reviewCount, 1);
  });

  test('mapProductSort aligns domain and OpenAPI enums', () {
    expect(mapProductSort(ProductSort.popularity), api.ProductSort.popularity);
    expect(mapProductSort(ProductSort.priceAsc), api.ProductSort.priceAsc);
  });

  test('mapHomeResponse maps banners and newArrivals from OpenAPI HomeResponse', () {
    final home = mapHomeResponse(
      api.HomeResponse(
        (b) => b
          ..categories.replace([])
          ..banners.replace([
            api.HomeBanner(
              (banner) => banner
                ..id = '00000000-0000-4000-8000-000000000099'
                ..title = 'Winter Sale'
                ..imageUrl = 'https://example.com/banner.jpg'
                ..ctaLabel = 'Shop now'
                ..categorySlug = 'ceiling-lights',
            ),
          ])
          ..featuredProducts.replace([])
          ..newArrivals.replace([]),
      ),
    );

    expect(home.banners, hasLength(1));
    expect(home.banners.first.title, 'Winter Sale');
    expect(home.newArrivals, isEmpty);
  });
}
