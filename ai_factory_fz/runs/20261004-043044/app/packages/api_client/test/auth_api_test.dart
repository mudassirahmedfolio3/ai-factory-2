import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for AuthApi
void main() {
  final instance = ApiClient().getAuthApi();

  group(AuthApi, () {
    // Request password reset
    //
    //Future<MessageResponse> forgotPassword(ForgotPasswordRequest forgotPasswordRequest) async
    test('test forgotPassword', () async {
      // TODO
    });

    // Login
    //
    //Future<AuthTokensResponse> loginUser(LoginRequest loginRequest) async
    test('test loginUser', () async {
      // TODO
    });

    // Logout
    //
    //Future logoutUser(RefreshRequest refreshRequest) async
    test('test logoutUser', () async {
      // TODO
    });

    // Refresh JWT
    //
    //Future<AuthTokensResponse> refreshTokens(RefreshRequest refreshRequest) async
    test('test refreshTokens', () async {
      // TODO
    });

    // Register account
    //
    //Future<AuthTokensResponse> registerUser(RegisterRequest registerRequest) async
    test('test registerUser', () async {
      // TODO
    });

    // Reset password with token
    //
    //Future<MessageResponse> resetPassword(ResetPasswordRequest resetPasswordRequest) async
    test('test resetPassword', () async {
      // TODO
    });

  });
}
