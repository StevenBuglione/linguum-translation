# M1-WP02: prove the minimal native ABI translation canary

## Scope

- implement the locked ABI 1.0 version/runtime/model/translator/result/error/info minimum;
- bridge that ABI to the exact Firefox-pinned Mozilla/Bergamot source;
- materialize hash-locked native tools and the Firefox-approved es→en canary model;
- build a macOS arm64 dylib with an exact export surface and macOS 13 minimum;
- translate the fixed canary and repeat the complete lifecycle 100 times;
- exercise malformed UTF-8, embedded NUL, oversize, unsupported-format, and short-struct failures;
- record the external MPL patch queue and executable verification evidence.

## Local gate

- two independent clean native builds/canary runs passed and produced identical dylib SHA-256;
- exact 20-symbol export allowlist and ABI 1.0 probes passed;
- `./gradlew clean verificationGate --warning-mode=fail` passed;
- all 17 routed Unix M1 scopes passed;
- actionlint, YAML/JSON parsing, shell syntax, source integrity, and helper safety tests passed.

The standalone native-safety workflow independently rebuilds and runs the same
100-cycle canary on a macOS arm64 GitHub-hosted runner.

## Boundaries

This PR does not claim the WP03–WP10 platform/package proofs, stable Kotlin/Java/Swift
API, sanitizer/fuzz completion, or a protected native ABI baseline. It does not edit
the immutable upstream tree or change the Firefox pin, public API, dependencies,
minimum platform matrix, or any quality baseline.

Full evidence: `reports/work-packages/M1-WP02-VERIFICATION.md`.
