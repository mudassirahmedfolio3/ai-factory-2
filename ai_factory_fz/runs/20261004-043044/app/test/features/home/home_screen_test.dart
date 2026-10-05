import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/app.dart';
import 'package:shopease_app/core/widgets/category_tile.dart';

import '../../helpers/catalog_test_overrides.dart';

void main() {
  testWidgets('HomeScreen shows category grid and featured carousel', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(overrides: catalogTestOverrides, child: const LumenApp()),
    );
    await pumpUntilSettled(tester);

    expect(find.text('Shop by room'), findsOneWidget);
    expect(find.byType(CategoryTile), findsNWidgets(7));
    expect(find.text('Ceiling Lights'), findsOneWidget);
  });

  testWidgets('Home search navigates to product listing with query', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(overrides: catalogTestOverrides, child: const LumenApp()),
    );
    await pumpUntilSettled(tester);

    await tester.enterText(
      find.bySemanticsLabel('Product search'),
      'CL-1001',
    );
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await pumpUntilSettled(tester);

    expect(find.text('Products'), findsWidgets);
    expect(find.text('Modern LED Ceiling Light'), findsOneWidget);
  });
}
