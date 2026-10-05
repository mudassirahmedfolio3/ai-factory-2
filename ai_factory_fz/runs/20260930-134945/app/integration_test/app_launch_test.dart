import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:shopease_app/app.dart';
import 'package:shopease_app/features/cart/presentation/cart_screen.dart';
import 'package:shopease_app/features/catalog/presentation/product_list_screen.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('launches offline to Product List and navigates to Cart', (
    tester,
  ) async {
    await tester.pumpWidget(const ProviderScope(child: LightingShopApp()));
    await tester.pumpAndSettle();
    expect(find.byType(ProductListScreen), findsOneWidget);

    await tester.tap(find.byTooltip('Cart'));
    await tester.pumpAndSettle();
    expect(find.byType(CartScreen), findsOneWidget);

    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(find.byType(ProductListScreen), findsOneWidget);
  });
}
