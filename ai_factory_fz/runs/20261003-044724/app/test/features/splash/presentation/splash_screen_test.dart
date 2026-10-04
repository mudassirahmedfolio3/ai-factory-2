import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shopease_app/app.dart';
import 'package:shopease_app/features/products/data/catalog_bootstrap_repository.dart';
import 'package:shopease_app/features/splash/data/app_initializer.dart';

void main() {
  testWidgets('navigates to product list after successful initialization', (
    tester,
  ) async {
    final initializer = _FakeAppInitializer(shouldFail: false);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [appInitializerProvider.overrideWithValue(initializer)],
        child: const ShopEaseApp(),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Featured'), findsOneWidget);
  });

  testWidgets('shows retry error state when initialization fails', (
    tester,
  ) async {
    final initializer = _FakeAppInitializer(shouldFail: true);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [appInitializerProvider.overrideWithValue(initializer)],
        child: const ShopEaseApp(),
      ),
    );

    await tester.pumpAndSettle();

    expect(
      find.text('We could not finish setup. Please try again.'),
      findsOneWidget,
    );
    expect(find.text('Try again'), findsOneWidget);
  });

  testWidgets('retry button reruns initialization and routes forward', (
    tester,
  ) async {
    final initializer = _FakeAppInitializer(shouldFail: true);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [appInitializerProvider.overrideWithValue(initializer)],
        child: const ShopEaseApp(),
      ),
    );

    await tester.pumpAndSettle();
    expect(find.text('Try again'), findsOneWidget);

    initializer.shouldFail = false;
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();

    expect(find.text('Featured'), findsOneWidget);
  });
}

class _FakeAppInitializer extends AppInitializer {
  _FakeAppInitializer({required this.shouldFail}) : super(_NoopCatalogPrimer());

  bool shouldFail;

  @override
  Future<void> initialize() async {
    if (shouldFail) {
      throw Exception('Initialization failed');
    }
  }
}

class _NoopCatalogPrimer implements CatalogPrimer {
  @override
  Future<void> primeCatalog() async {}
}
