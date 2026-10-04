import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:shopease_app/app.dart';

void main() {
  testWidgets('app launches on the browse screen with no setup', (
    tester,
  ) async {
    await tester.pumpWidget(const ProviderScope(child: BeautyMiniApp()));
    await tester.pumpAndSettle();

    expect(find.text('beauty-mini'), findsOneWidget);
    expect(find.byType(GridView), findsOneWidget);
    expect(find.text('Velvet Matte Lipstick'), findsOneWidget);
    expect(find.text(r'$19.99'), findsOneWidget);
  });
}
