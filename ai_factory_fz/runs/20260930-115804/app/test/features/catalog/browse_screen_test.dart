import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/misc.dart' show Override;
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/app.dart';
import 'package:shopease_app/core/router/app_router.dart';
import 'package:shopease_app/core/theme/app_colors.dart';
import 'package:shopease_app/features/catalog/data/local_catalog_repository.dart';
import 'package:shopease_app/features/catalog/domain/catalog_repository.dart';
import 'package:shopease_app/features/catalog/domain/product.dart';
import 'package:shopease_app/features/catalog/presentation/catalog_providers.dart';
import 'package:shopease_app/features/catalog/presentation/widgets/product_tile.dart';

class _EmptyRepo implements CatalogRepository {
  @override
  Product? findById(String id) => null;
  @override
  List<Product> listProducts() => const [];
}

/// Fails on the first load, succeeds afterwards (to exercise Retry).
class _FlakyRepo implements CatalogRepository {
  int calls = 0;

  @override
  Product? findById(String id) => const LocalCatalogRepository().findById(id);

  @override
  List<Product> listProducts() {
    calls++;
    if (calls == 1) throw StateError('boom');
    return const LocalCatalogRepository().listProducts();
  }
}

Future<void> _pumpApp(
  WidgetTester tester, {
  List<Override> overrides = const [],
  String initialLocation = '/',
  Size physicalSize = const Size(1080, 4000),
}) async {
  // Tall phone-sized viewport so all 8 tiles are built.
  tester.view.physicalSize = physicalSize;
  tester.view.devicePixelRatio = 2.5;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    ProviderScope(
      overrides: overrides,
      child: BeautyMiniApp(
        router: createAppRouter(initialLocation: initialLocation),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('shows exactly 8 product tiles with names and USD prices', (
    tester,
  ) async {
    await _pumpApp(tester);

    expect(find.text('beauty-mini'), findsOneWidget);
    expect(find.byType(ProductTile), findsNWidgets(8));
    for (final p in kLocalProducts) {
      expect(find.text(p.name), findsOneWidget);
    }
    expect(find.text(r'$19.99'), findsOneWidget);
    expect(find.text(r'$34.50'), findsOneWidget);
    expect(find.text(r'$9.99'), findsOneWidget);
    expect(find.text(r'$65.00'), findsOneWidget);
  });

  testWidgets('each tile has a themed placeholder color block', (tester) async {
    await _pumpApp(tester);

    final lipstickBlock = tester.widget<DecoratedBox>(
      find.byKey(const ValueKey('placeholder-rose')),
    );
    final decoration = lipstickBlock.decoration as BoxDecoration;
    expect(decoration.color, AppColorTokens.light.placeholderLipstick);
    expect(find.byType(Image), findsNothing);
  });

  testWidgets('tiles expose "<name>, <price>" button semantics', (
    tester,
  ) async {
    final handle = tester.ensureSemantics();
    await _pumpApp(tester);

    expect(
      find.bySemanticsLabel(r'Velvet Matte Lipstick, $19.99'),
      findsOneWidget,
    );
    await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
    handle.dispose();
  });

  testWidgets('tapping a tile opens product detail and back returns', (
    tester,
  ) async {
    await _pumpApp(tester);

    await tester.tap(find.byKey(const ValueKey('product-tile-perfume')));
    await tester.pumpAndSettle();
    expect(find.text('Bloom Eau de Parfum'), findsWidgets);
    expect(find.text(r'$65.00'), findsOneWidget);
    expect(find.byType(ProductTile), findsNothing);

    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(find.byType(ProductTile), findsNWidgets(8));
  });

  testWidgets('empty catalog shows "No products yet"', (tester) async {
    await _pumpApp(
      tester,
      overrides: [catalogRepositoryProvider.overrideWithValue(_EmptyRepo())],
    );
    expect(find.text('No products yet'), findsOneWidget);
    expect(find.byType(ProductTile), findsNothing);
  });

  testWidgets('load error shows Retry, which reloads the grid', (tester) async {
    final repo = _FlakyRepo();
    await _pumpApp(
      tester,
      overrides: [catalogRepositoryProvider.overrideWithValue(repo)],
    );
    expect(find.text('Could not load products'), findsOneWidget);
    expect(find.byType(ProductTile), findsNothing);

    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();
    expect(find.text('Could not load products'), findsNothing);
    expect(find.byType(ProductTile), findsNWidgets(8));
  });

  testWidgets('unknown product id shows not-found and goes back home', (
    tester,
  ) async {
    await _pumpApp(tester, initialLocation: '/products/nope');
    expect(find.text('Product not found'), findsOneWidget);
    await tester.tap(find.text('Back to products'));
    await tester.pumpAndSettle();
    expect(find.byType(ProductTile), findsNWidgets(8));
  });

  testWidgets('grid does not overflow at 200% text scale', (tester) async {
    tester.platformDispatcher.textScaleFactorTestValue = 2;
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
    await _pumpApp(tester, physicalSize: const Size(1080, 2400));

    expect(tester.takeException(), isNull);
    expect(find.byType(ProductTile), findsWidgets);
  });
}
