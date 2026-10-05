import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:shopease_app/core/router/app_router.dart';
import 'package:shopease_app/features/account/presentation/account_screen.dart';
import 'package:shopease_app/features/auth/presentation/auth_screen.dart';
import 'package:shopease_app/features/cart/presentation/cart_screen.dart';
import 'package:shopease_app/features/home/presentation/home_screen.dart';
import 'package:shopease_app/features/orders/presentation/orders_screen.dart';
import 'package:shopease_app/features/products/presentation/product_detail_screen.dart';
import 'package:shopease_app/features/products/presentation/search_results_screen.dart';
import 'package:shopease_app/features/splash/presentation/splash_screen.dart';
import 'package:shopease_app/features/wishlist/presentation/wishlist_screen.dart';

void main() {
  test('app router exposes guest shopping and auth routes', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    final router = container.read(appRouterProvider);
    final paths = <String>[];
    for (final route in router.configuration.routes) {
      _collectRoutePaths(route, paths);
    }

    expect(paths, contains(SplashScreen.routePath));
    expect(paths, contains(HomeScreen.routePath));
    expect(paths, contains(SearchResultsScreen.routePath));
    expect(paths, contains(ProductDetailScreen.routePath));
    expect(paths, contains(CartScreen.routePath));
    expect(paths, contains(AccountScreen.routePath));
    expect(paths, contains(AuthScreen.routePath));
    expect(paths, contains(OrdersScreen.routePath));
    expect(paths, contains(WishlistScreen.routePath));
  });
}

void _collectRoutePaths(RouteBase route, List<String> paths) {
  if (route is GoRoute) {
    paths.add(route.path);
    for (final child in route.routes) {
      _collectRoutePaths(child, paths);
    }
  } else if (route is StatefulShellRoute) {
    for (final branch in route.branches) {
      for (final child in branch.routes) {
        _collectRoutePaths(child, paths);
      }
    }
  }
}
