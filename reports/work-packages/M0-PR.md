# Work package

```text
Milestone / WP: M0 / M0-WP01 through M0-WP04
Requirement IDs: Q23, Q25, Q67, Q71, Q72
Architecture classifications: governance, build tooling, test harness, CI
```

## Summary

Establish the repository, pinned build/toolchain skeleton, architecture enforcement, local quality gate, and protected CI/governance workflow. M0 intentionally introduces no translation production implementation or stable public API.

## Compatibility impact

```text
Kotlin API: none
JVM binary API: none
Java facade: none
Swift facade: none
C ABI: none
Manifest/persisted schema: unchanged handoff schemas only
Minimum platform versions: preserved
Translation output: none
```

## Security, privacy, licensing

```text
Network behavior: build-time dependency resolution only
Sensitive text handling: no translation runtime exists
Native/unsafe changes: none
Dependencies/licenses: pinned tooling only; Apache-2.0 root license
Mozilla snapshot/patches: not introduced
Supply-chain artifacts: dependency locks and verification metadata in M0-WP02
```

## Verification

See `reports/work-packages/M0-WP*-VERIFICATION.md`.

```text
Verified implementation commit: 635d35e4bea91bce6b289abfee5a8b359d0652a1
Remote branch SHA: 635d35e4bea91bce6b289abfee5a8b359d0652a1
Clean gate command: ./gradlew clean verificationGate --warning-mode=fail
Clean gate result: PASS (21 tasks; Detekt, Kover, architecture, tests)
M0 scope checks: PASS locally and on hosted Linux, macOS, and Windows
Protected PR checks: PASS (15/15), run 32341484301
Dependency review/native safety: PASS, runs 32341484277 and 32341484310
Main ruleset: ACTIVE, ID 21078407
```

## Gate declaration

- [x] Protected architecture/product decisions are unchanged.
- [x] Tests, coverage, performance, API/ABI, sanitizer, fuzzing, dependency, license, and release gates are not weakened.
- [x] Only intentional paths are staged.
- [x] The verified branch remote SHA matches the verified local commit.
- [x] Required M0 documentation, artifacts, hosted evidence, and protection are complete.
- [x] The PR contains no production translation implementation or speculative modules.
