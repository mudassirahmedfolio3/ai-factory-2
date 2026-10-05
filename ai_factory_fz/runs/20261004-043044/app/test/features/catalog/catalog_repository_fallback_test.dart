import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/network/api_health_probe.dart';
import 'package:shopease_app/features/catalog/data/catalog_data_source.dart';
import 'package:shopease_app/features/catalog/data/catalog_repository_impl.dart';
import 'package:shopease_app/features/catalog/data/local_catalog_data_source.dart';
import 'package:shopease_app/features/catalog/data/seed/default_catalog_seed.dart';
import 'package:shopease_app/features/catalog/domain/catalog_list_query.dart';
import 'package:shopease_app/features/catalog/domain/catalog_repository.dart';
import 'package:shopease_app/features/catalog/domain/models/category.dart';
import 'package:shopease_app/features/catalog/domain/models/product.dart';

class _AlwaysRemoteHealthProbe extends ApiHealthProbe {
  const _AlwaysRemoteHealthProbe();

  @override
  Future<bool> isHealthy() async => true;
}

class _UnhealthyHealthProbe extends ApiHealthProbe {
  const _UnhealthyHealthProbe();

  @override
  Future<bool> isHealthy() async => false;
}

class _RemoteShouldNotBeCalled implements CatalogDataSource {
  @override
  Future<HomeData> getHome() => _fail();

  @override
  Future<List<CategorySummary>> listCategories({int depth = 2}) => _fail();

  @override
  Future<CategoryDetail> getCategoryBySlug(String slug) => _fail();

  @override
  Future<CatalogFacets> getCatalogFacets({String? categorySlug}) => _fail();

  @override
  Future<ProductListResponse> listProducts(CatalogListQuery query) => _fail();

  @override
  Future<ProductDetail> getProductById(String productId) => _fail();

  @override
  Future<ReviewListResponse> listProductReviews(
    String productId, {
    int page = 1,
    int pageSize = 20,
  }) => _fail();

  Never _fail() => throw StateError('remote catalog must not be used');
}

class _FailingRemoteCatalogDataSource implements CatalogDataSource {
  @override
  Future<HomeData> getHome() => throw Exception('network down');

  @override
  Future<List<CategorySummary>> listCategories({int depth = 2}) =>
      throw UnimplementedError();

  @override
  Future<CategoryDetail> getCategoryBySlug(String slug) =>
      throw UnimplementedError();

  @override
  Future<CatalogFacets> getCatalogFacets({String? categorySlug}) =>
      throw UnimplementedError();

  @override
  Future<ProductListResponse> listProducts(CatalogListQuery query) =>
      throw UnimplementedError();

  @override
  Future<ProductDetail> getProductById(String productId) =>
      throw UnimplementedError();

  @override
  Future<ReviewListResponse> listProductReviews(
    String productId, {
    int page = 1,
    int pageSize = 20,
  }) => throw UnimplementedError();
}

void main() {
  test('uses local catalog when health probe fails (API down)', () async {
    var usesRemote = true;
    final repository = CatalogRepositoryImpl(
      local: LocalCatalogDataSource(seedOverride: buildDefaultCatalogSeed()),
      remote: _RemoteShouldNotBeCalled(),
      healthProbe: const _UnhealthyHealthProbe(),
      onSourceResolved: ({required bool usesRemoteApi}) {
        usesRemote = usesRemoteApi;
      },
    );

    final home = await repository.getHome();
    expect(home.featuredProducts, isNotEmpty);
    expect(usesRemote, isFalse);
  });

  test('falls back to local catalog when remote fails after healthy probe', () async {
    var usesRemote = false;
    final repository = CatalogRepositoryImpl(
      local: LocalCatalogDataSource(seedOverride: buildDefaultCatalogSeed()),
      remote: _FailingRemoteCatalogDataSource(),
      healthProbe: const _AlwaysRemoteHealthProbe(),
      onSourceResolved: ({required bool usesRemoteApi}) {
        usesRemote = usesRemoteApi;
      },
    );

    final home = await repository.getHome();
    expect(home.featuredProducts, isNotEmpty);
    expect(usesRemote, isFalse);

    final listing = await repository.listProducts(const CatalogListQuery());
    expect(listing.total, 16);
  });

  test('CatalogNotFoundException from remote is not masked by local fallback', () async {
    final repository = CatalogRepositoryImpl(
      local: LocalCatalogDataSource(seedOverride: buildDefaultCatalogSeed()),
      remote: _NotFoundRemoteCatalogDataSource(),
      healthProbe: const _AlwaysRemoteHealthProbe(),
    );

    expect(
      () => repository.getProductById('missing-id'),
      throwsA(isA<CatalogNotFoundException>()),
    );
  });
}

class _NotFoundRemoteCatalogDataSource implements CatalogDataSource {
  @override
  Future<HomeData> getHome() => throw UnimplementedError();

  @override
  Future<List<CategorySummary>> listCategories({int depth = 2}) =>
      throw UnimplementedError();

  @override
  Future<CategoryDetail> getCategoryBySlug(String slug) =>
      throw UnimplementedError();

  @override
  Future<CatalogFacets> getCatalogFacets({String? categorySlug}) =>
      throw UnimplementedError();

  @override
  Future<ProductListResponse> listProducts(CatalogListQuery query) =>
      throw UnimplementedError();

  @override
  Future<ProductDetail> getProductById(String productId) async {
    throw CatalogNotFoundException('Product not found: $productId');
  }

  @override
  Future<ReviewListResponse> listProductReviews(
    String productId, {
    int page = 1,
    int pageSize = 20,
  }) => throw UnimplementedError();
}
