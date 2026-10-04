import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for AuthApi
void main() {
  final instance = ApiClient().getAuthApi();

  group(AuthApi, () {
    // Mock forgot-password (always 200 for privacy)
    //
    //Future<ForgotPasswordResponse> forgotPassword(ForgotPasswordRequest forgotPasswordRequest) async
    test('test forgotPassword', () async {
      // TODO
    });

    // Log in with email and password
    //
    //Future<AuthResponse> login(LoginRequest loginRequest) async
    test('test login', () async {
      // TODO
    });

    // Log out and revoke refresh token
    //
    //Future logout(LogoutRequest logoutRequest) async
    test('test logout', () async {
      // TODO
    });

    // Exchange refresh token for new access token
    //
    //Future<AuthResponse> refreshTokens(RefreshRequest refreshRequest) async
    test('test refreshTokens', () async {
      // TODO
    });

    // Register a new shopper account
    //
    //Future<AuthResponse> register(RegisterRequest registerRequest) async
    test('test register', () async {
      // TODO
    });

    // Mock reset password with demo token
    //
    //Future<MessageResponse> resetPassword(ResetPasswordRequest resetPasswordRequest) async
    test('test resetPassword', () async {
      // TODO
    });

  });
}
