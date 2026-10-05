import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for UsersApi
void main() {
  final instance = ApiClient().getUsersApi();

  group(UsersApi, () {
    // Delete account
    //
    //Future deleteCurrentUser() async
    test('test deleteCurrentUser', () async {
      // TODO
    });

    // Current profile
    //
    //Future<UserProfile> getCurrentUser() async
    test('test getCurrentUser', () async {
      // TODO
    });

  });
}
