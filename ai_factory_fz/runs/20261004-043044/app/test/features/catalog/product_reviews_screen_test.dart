import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:shopease_app/core/router/app_routes.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/core/widgets/review_list_item.dart';
import 'package:shopease_app/features/catalog/presentation/product_reviews_screen.dart';

import '../../helpers/catalog_test_overrides.dart';

void main() {
  const productId = 'p1111111-1111-4111-8111-111111111101';

  testWidgets('Product reviews screen lists seeded reviews', (
    WidgetTester tester,
  ) async {
    final router = GoRouter(
      initialLocation: AppRoutes.productReviews(productId),
      routes: [
        GoRoute(
          path: '/products/:productId/reviews',
          builder: (context, state) => ProductReviewsScreen(
            productId: state.pathParameters['productId']!,
          ),
        ),
      ],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: catalogTestOverrides,
        child: MaterialApp.router(
          theme: AppTheme.light(),
          routerConfig: router,
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(ReviewListItem), findsNWidgets(2));
    expect(find.text('Bright and easy fit'), findsOneWidget);
  });
}
