import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lighting_retail_mobile/main.dart';

void main() {
  testWidgets('bootstrap screen shows API base URL', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: LightingRetailApp()));
    await tester.pumpAndSettle();
    expect(find.textContaining('10.0.2.2:3000'), findsOneWidget);
  });
}
