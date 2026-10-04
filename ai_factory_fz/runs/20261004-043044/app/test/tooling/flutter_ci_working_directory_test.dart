import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// Guards BUG-002: CI must analyze/test the M1 deliverable (`app/`), not `apps/mobile`.
void main() {
  test('GitHub CI Flutter job targets M1 shopease_app at app/', () {
    final ciPath = File(
      '${Directory.current.path}${Platform.pathSeparator}..'
      '${Platform.pathSeparator}.github${Platform.pathSeparator}workflows'
      '${Platform.pathSeparator}ci.yml',
    );
    expect(
      ciPath.existsSync(),
      isTrue,
      reason: 'CI workflow should be reachable from app/ test working directory',
    );

    final yaml = ciPath.readAsStringSync();
    final flutterJob = _extractTopLevelJob(yaml, 'flutter');
    expect(flutterJob, isNotNull, reason: 'ci.yml must define a flutter job');
    expect(flutterJob, contains('working-directory: app'));
    expect(flutterJob, isNot(contains('working-directory: apps/mobile')));
  });
}

String? _extractTopLevelJob(String yaml, String jobId) {
  final marker = '\n  $jobId:';
  var start = yaml.indexOf(marker);
  if (start < 0) {
    if (yaml.startsWith('  $jobId:')) {
      start = 0;
    } else {
      return null;
    }
  } else {
    start += 1; // drop leading newline so slice starts at job indent
  }

  final tail = yaml.substring(start + jobId.length + 3);
  final nextJob = RegExp(r'\n  [a-zA-Z0-9_-]+:').firstMatch(tail);
  final end = nextJob == null
      ? yaml.length
      : start + jobId.length + 3 + nextJob.start;

  return yaml.substring(start, end);
}
