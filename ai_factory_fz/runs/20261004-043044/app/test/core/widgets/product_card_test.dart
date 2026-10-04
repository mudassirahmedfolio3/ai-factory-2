import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/core/widgets/out_of_stock_badge.dart';
import 'package:shopease_app/core/widgets/product_card.dart';
import 'package:shopease_app/core/widgets/sale_badge.dart';
import 'package:shopease_app/features/catalog/domain/models/catalog_money.dart';
import 'package:shopease_app/features/catalog/domain/models/category.dart';
import 'package:shopease_app/features/catalog/domain/models/product.dart';
import 'package:shopease_app/features/catalog/domain/models/rating_summary.dart';

void main() {
  const category = CategorySummary(
    id: 'c1',
    name: 'Ceiling Lights',
    slug: 'ceiling-lights',
  );

  ProductSummary sampleSummary({required bool inStock, bool onSale = false}) {
    return ProductSummary(
      id: 'p1',
      name: 'Sample Light',
      brand: 'Luminex',
      slug: 'sample-light',
      category: category,
      price: CatalogMoney.gbp(4999),
      compareAtPrice: onSale ? CatalogMoney.gbp(5999) : null,
      primaryImageUrl: 'assets/images/products/placeholder.png',
      inStock: inStock,
      rating: const RatingSummary(averageRating: 4.5, reviewCount: 2),
    );
  }

  testWidgets('ProductCard shows Out of stock badge when not in stock', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light(),
        home: Scaffold(
          body: ProductCard(
            width: 180,
            product: sampleSummary(inStock: false),
            onTap: () {},
          ),
        ),
      ),
    );

    expect(find.byType(OutOfStockBadge), findsOneWidget);
    expect(find.byType(SaleBadge), findsNothing);
  });

  testWidgets('ProductCard shows sale badge when in stock and on sale', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light(),
        home: Scaffold(
          body: ProductCard(
            width: 180,
            product: sampleSummary(inStock: true, onSale: true),
            onTap: () {},
          ),
        ),
      ),
    );

    expect(find.byType(SaleBadge), findsOneWidget);
    expect(find.byType(OutOfStockBadge), findsNothing);
  });
}
