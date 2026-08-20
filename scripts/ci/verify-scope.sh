#!/usr/bin/env bash
set -euo pipefail

scope="${1:?usage: verify-scope.sh <scope>}"
milestone="$(tr -d '[:space:]' < architecture/current-milestone.txt)"

if [[ "$milestone" == "M0" ]]; then
  exec bash scripts/ci/verify-m0-scope.sh "$scope"
fi

[[ "$milestone" == "M1" ]] || {
  printf 'No CI scope dispatcher is implemented for %s.\n' "$milestone" >&2
  exit 1
}

python3 scripts/upstream/snapshot.py prepare

require_absent() {
  local path
  for path in "$@"; do
    [[ ! -e "$path" ]] || {
      printf 'M1 must not introduce stable post-feasibility module %s.\n' "$path" >&2
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
    require_absent translation translation-api translation-runtime translation-model-contracts facades
    ./gradlew apiValidationCheck --warning-mode=fail
    ;;
  kotlin)
    ./gradlew :testing:architecture:test --warning-mode=fail
    ;;
  native|upstream)
    python3 -m unittest discover -s scripts/upstream/tests -v
    python3 -m py_compile scripts/upstream/snapshot.py scripts/upstream/tests/test_snapshot.py
    python3 scripts/upstream/snapshot.py verify
    ./gradlew architectureCheck --warning-mode=fail
    ;;
  linux|macos|android|ios|swift|consumers|performance|release)
    ./gradlew architectureCheck --warning-mode=fail
    ;;
  models)
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
  *)
    printf 'Unknown repository verification scope: %s\n' "$scope" >&2
    exit 1
    ;;
esac
