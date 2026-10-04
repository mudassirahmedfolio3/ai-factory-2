import 'package:shopease_app/features/auth/domain/auth_models.dart';
import 'package:shopease_app/features/auth/presentation/auth_notifier.dart';

/// Auth notifier that skips secure-storage bootstrap for unit/widget tests.
class FixedAuthNotifier extends AuthNotifier {
  FixedAuthNotifier(this.user);

  final AuthUser? user;

  @override
  AuthUser? build() => user;
}

class GuestAuthNotifier extends FixedAuthNotifier {
  GuestAuthNotifier() : super(null);
}
