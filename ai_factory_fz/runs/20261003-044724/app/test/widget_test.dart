import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shopease_app/app.dart';
import 'package:shopease_app/features/products/data/catalog_bootstrap_repository.dart';
import 'package:shopease_app/features/splash/data/app_initializer.dart';

void main() {
  testWidgets('App boots to splash screen', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          appInitializerProvider.overrideWithValue(
            AppInitializer(_NoopCatalogPrimer()),
          ),
        ],
        child: const ShopEaseApp(),
      ),
    );

    expect(find.text('Preparing your shopping experience'), findsOneWidget);
  });
}

class _NoopCatalogPrimer implements CatalogPrimer {
  @override
  Future<void> primeCatalog() async {}
}
