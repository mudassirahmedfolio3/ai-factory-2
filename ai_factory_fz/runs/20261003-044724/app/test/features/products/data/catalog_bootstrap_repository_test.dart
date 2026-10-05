import 'dart:io';

import 'package:api_client/api_client.dart';
import 'package:dio/dio.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/products/data/catalog_bootstrap_repository.dart';

class _FileAssetBundle extends AssetBundle {
  @override
  Future<ByteData> load(String key) async {
    final bytes = await File(key).readAsBytes();
    return ByteData.view(bytes.buffer);
  }
}

void main() {
  test(
    'CatalogBootstrapRepository completes when getHealth succeeds',
    () async {
      final dio = Dio(
        BaseOptions(baseUrl: 'http://test.local/api/v1'),
      );
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            expect(options.path, '/health');
            handler.resolve(
              Response<Map<String, dynamic>>(
                requestOptions: options,
                statusCode: 200,
                data: {
                  'status': 'ok',
                  'database': 'up',
                  'timestamp': '2026-01-01T00:00:00.000Z',
                },
              ),
            );
          },
        ),
      );

      final client = ApiClient(
        dio: dio,
        basePathOverride: 'http://test.local/api/v1',
      );
      final repository = CatalogBootstrapRepository(client);

      await expectLater(repository.primeCatalog(), completes);
    },
  );

  test(
    'CatalogBootstrapRepository falls back to bundled seed when getHealth fails (US-006 AC2)',
    () async {
      final dio = Dio(
        BaseOptions(baseUrl: 'http://test.local/api/v1'),
      );
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            handler.reject(
              DioException(
                requestOptions: options,
                type: DioExceptionType.connectionError,
              ),
            );
          },
        ),
      );

      final client = ApiClient(
        dio: dio,
        basePathOverride: 'http://test.local/api/v1',
      );
      final repository = CatalogBootstrapRepository(
        client,
        assetBundle: _FileAssetBundle(),
      );

      await expectLater(repository.primeCatalog(), completes);
    },
  );
}
