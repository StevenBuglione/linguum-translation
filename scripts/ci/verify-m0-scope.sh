#!/usr/bin/env bash
set -euo pipefail

scope="${1:?usage: verify-m0-scope.sh <scope>}"
milestone="$(tr -d '[:space:]' < architecture/current-milestone.txt)"
[[ "$milestone" == "M0" ]] || {
  printf 'This scaffold check applies only to M0; found %s.\n' "$milestone" >&2
  exit 1
}

require_absent() {
  local path
  for path in "$@"; do
    [[ ! -e "$path" ]] || {
      printf 'M0 must not introduce %s.\n' "$path" >&2
      exit 1
    }
  done
}

case "$scope" in
  architecture)
    ./gradlew architectureCheck --warning-mode=fail
    ;;
  quality)
    ./gradlew qualityCheck --warning-mode=fail
    ;;
  api)
    require_absent translation translation-api translation-runtime translation-testing facades
    ./gradlew apiValidationCheck --warning-mode=fail
    ;;
  kotlin)
    ./gradlew :testing:architecture:test --warning-mode=fail
    ;;
  linux|macos)
    require_absent native/upstream native/runtime-build platform
    ./gradlew architectureCheck --warning-mode=fail
    ;;
  android)
    require_absent platform/android native/upstream native/runtime-build
    ./gradlew architectureCheck --warning-mode=fail
    ;;
  ios|swift)
    require_absent platform/apple facades/apple-export swift-overlay native/upstream native/runtime-build
    ./gradlew architectureCheck --warning-mode=fail
    ;;
  consumers)
    require_absent testing/consumer-kotlin testing/consumer-java testing/consumer-swift
    ./gradlew architectureCheck --warning-mode=fail
    ;;
  native)
    require_absent native/abi native/mozilla-adapter native/runtime-build native/upstream
    ./gradlew architectureCheck --warning-mode=fail
    ;;
  models)
    require_absent translation-model-contracts translation-model-management translation-model-manifest
    python3 -m json.tool schemas/model-manifest.schema.json >/dev/null
    python3 -m json.tool schemas/upstream-lock.schema.json >/dev/null
    ;;
  license)
    test -s LICENSE
    test -s NOTICE
    test -s THIRD_PARTY_LICENSES.md
    ./gradlew repositoryPolicyCheck --warning-mode=fail
    ;;
  artifacts)
    test -s gradle/wrapper/gradle-wrapper.jar
    grep -q '^distributionSha256Sum=[a-f0-9]\{64\}$' gradle/wrapper/gradle-wrapper.properties
    ./gradlew verifyToolchain --warning-mode=fail
    ;;
  upstream|performance|release)
    require_absent native/upstream publication
    test -s research/evidence/FINAL_BENCHMARK_REPORT.md
    ;;
  *)
    printf 'Unknown M0 scope: %s\n' "$scope" >&2
    exit 1
    ;;
esac
