Mobile conventions (Flutter):
- Feature-first folders: lib/features/<feature>/{data,domain,presentation}; shared code in lib/core (theme, router, network, widgets).
- State management with Riverpod (Notifier/AsyncNotifier); navigation with go_router; one route per screen spec.
- HTTP only through the API client generated from the OpenAPI document (packages/api_client, dart-dio). Do not hand-write endpoints.
- Theme built from design tokens in lib/core/theme; no hard-coded colors or sizes in widgets.
- Every screen handles loading, empty and error states.
- Access tokens stored with flutter_secure_storage.
- Tests: widget tests per screen; integration_test for critical journeys.
- Minimum touch target 48dp; all images and icons have semantic labels.
- Debug builds must reach local staging from the Android emulator at http://10.0.2.2:<port>: allow cleartext for 10.0.2.2 only in a debug network-security config (android/app/src/debug). Release builds stay https-only.
