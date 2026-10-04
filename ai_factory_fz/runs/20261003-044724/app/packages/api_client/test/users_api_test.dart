import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for UsersApi
void main() {
  final instance = ApiClient().getUsersApi();

  group(UsersApi, () {
    // Delete the signed-in account
    //
    //Future deleteAccount() async
    test('test deleteAccount', () async {
      // TODO
    });

  });
}
