# Mobile Release Checklist

## Pre-release

- [ ] All sprint acceptance criteria verified by QA
- [ ] Version bumped in `pubspec.yaml` (semver)
- [ ] CHANGELOG updated with user-facing changes
- [ ] Environment configs documented (.env.example, no secrets committed)
- [ ] Feature flags reviewed for production values

## Build

- [ ] `flutter analyze` — no errors
- [ ] `flutter test` — passing
- [ ] `flutter build apk` / `flutter build ios` (as applicable)
- [ ] Smoke test on physical device

## Store submission

- [ ] App icons and splash screens
- [ ] Store listing copy and screenshots
- [ ] Privacy policy URL
- [ ] Age rating / content questionnaire completed

## Post-release

- [ ] Release notes shared with client/stakeholders
- [ ] Monitor crash reports and API error rates
- [ ] Backlog updated for next sprint
