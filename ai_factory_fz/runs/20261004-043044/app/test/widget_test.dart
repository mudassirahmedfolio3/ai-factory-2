import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shopease_app/app.dart';

import 'helpers/catalog_test_overrides.dart';

void main() {
  testWidgets('App launches with Lumen home content', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(overrides: catalogTestOverrides, child: const LumenApp()),
    );
    await pumpUntilSettled(tester);

    expect(find.text('Lumen Home'), findsOneWidget);
    expect(find.text('Shop by room'), findsOneWidget);
  });
}
