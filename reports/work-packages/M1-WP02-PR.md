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
100-cycle canary on a macOS arm64 GitHub-hosted runner. Hosted implementation
checkpoint `29a9d14b22839dea5661785d75bd46ce3cb4d7ea` passed all 15 protected PR
jobs, dependency review, and the dedicated 7m28s native build/canary run
`32388217207` (3/3 CTest tests, ABI 1.0, exact 20 exports, macOS 13.0 minimum,
and all 100 lifecycles).

An Ubuntu 22.04 x64 diagnostic build also compiled and linked the adapter and both
ABI consumers, then reached the pinned Marian configuration's expected runtime BLAS
requirement. Linux runtime feasibility remains WP05; the WP02 standalone acceptance
gate is deliberately pinned to its claimed macOS arm64 target, while the protected
Linux PR scope remains enabled and passing.

## Boundaries

This PR does not claim the WP03–WP10 platform/package proofs, stable Kotlin/Java/Swift
API, sanitizer/fuzz completion, or a protected native ABI baseline. It does not edit
the immutable upstream tree or change the Firefox pin, public API, dependencies,
minimum platform matrix, or any quality baseline.

Full evidence: `reports/work-packages/M1-WP02-VERIFICATION.md`.
