import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for HomeApi
void main() {
  final instance = ApiClient().getHomeApi();

  group(HomeApi, () {
    // Merchandised home content
    //
    //Future<HomeResponse> getHome() async
    test('test getHome', () async {
      // TODO
    });

  });
}
