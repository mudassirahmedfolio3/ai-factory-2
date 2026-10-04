import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/features/home/data/home_repository.dart';
import 'package:shopease_app/features/home/domain/home_models.dart';
import 'package:shopease_app/features/home/presentation/home_screen.dart';
import 'package:shopease_app/features/products/domain/catalog_models.dart';
import 'package:shopease_app/features/wishlist/presentation/wishlist_notifier.dart';

void main() {
  testWidgets('home screen shows featured, new arrivals, and categories', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          homeRepositoryProvider.overrideWithValue(_FakeHomeRepository()),
          wishlistNotifierProvider.overrideWith(_EmptyWishlistNotifier.new),
        ],
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: const HomeScreen(),
        ),
      ),
    );

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    await tester.pumpAndSettle();

    expect(find.text('ShopEase'), findsWidgets);
    expect(find.text('Featured'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('New arrivals'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('New arrivals'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Categories'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Categories'), findsOneWidget);
    expect(find.text('Clothing'), findsOneWidget);
    expect(find.text('Electronics'), findsOneWidget);
    expect(find.text('Citrus Hand Soap'), findsWidgets);
  });
}

class _FakeHomeRepository implements HomeRepository {
  @override
  Future<HomeData> fetchHome() async {
    const product = CatalogProduct(
      id: '1',
      name: 'Citrus Hand Soap',
      categorySlug: 'personal-care',
      categoryName: 'Personal Care',
      imageUrl: 'https://example.com/soap.jpg',
      amountCents: 799,
      currencyCode: 'USD',
      isAvailable: true,
    );
    return HomeData(
      banners: const [
        HomeBannerModel(
          id: 'b1',
          title: 'Spring refresh sale',
          imageUrl: 'https://example.com/banner.jpg',
        ),
      ],
      featured: const [product],
      newArrivals: const [product],
      categories: const [
        CatalogCategoryModel(id: '1', name: 'Clothing', slug: 'clothing'),
        CatalogCategoryModel(id: '2', name: 'Electronics', slug: 'electronics'),
      ],
    );
  }
}

class _EmptyWishlistNotifier extends WishlistNotifier {
  @override
  Future<Set<String>> build() async => {};
}
