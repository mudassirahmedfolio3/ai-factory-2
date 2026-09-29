# Security Scanning (AppSec Worker Agent)

## Scans to run per release

| Scan | Tool / approach | Blocking? |
|------|-----------------|-----------|
| SCA (dependencies) | `dart pub outdated`, OSV/advisory lookup | Critical CVEs block |
| Secrets detection | grep patterns, no API keys in repo | Always block |
| SAST (Dart) | Static analysis rules for injection, insecure storage | High severity block |
| Mobile OWASP | Insecure data storage, weak crypto, cert pinning gaps | High block |
| Supply chain | pubspec.lock integrity, pinned versions | Medium warn |

## E-commerce specific risks

- Payment data must never be stored locally (use tokenization)
- PII encryption at rest for addresses
- Certificate pinning for API endpoints in production
- Secure token storage (flutter_secure_storage)

## Remediation output format

Each finding: ID, severity (critical/high/medium/low), file, description, remediation steps.

Verdict: **PASS** (no blocking findings) or **FAIL** (blocking findings listed).
