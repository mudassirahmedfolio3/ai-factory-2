import 'dart:convert';
import 'dart:io';

import 'package:shopease_app/features/catalog/data/seed/default_catalog_seed.dart';

/// Regenerates assets/data/catalog.json from the Dart seed (OpenAPI-aligned).
void main() {
  final seed = buildDefaultCatalogSeed();
  final json = const JsonEncoder.withIndent('  ').convert(seed.toJson());
  final file = File('assets/data/catalog.json');
  file.parent.createSync(recursive: true);
  file.writeAsStringSync('$json\n');
  stdout.writeln('Wrote ${file.path} (${seed.products.length} products)');
}
