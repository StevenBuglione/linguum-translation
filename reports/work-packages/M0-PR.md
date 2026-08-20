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
Local HEAD: pending M0-WP04 checkpoint commit
Remote branch SHA: pending M0-WP04 checkpoint push
Clean gate command: ./gradlew clean verificationGate --warning-mode=fail
Clean gate result: PASS (21 tasks; Detekt, Kover, architecture, tests)
M0 scope checks: PASS locally; hosted cross-platform CI pending
```

## Gate declaration

- [x] Protected architecture/product decisions are unchanged.
- [x] Tests, coverage, performance, API/ABI, sanitizer, fuzzing, dependency, license, and release gates are not weakened.
- [x] Only intentional paths are staged.
- [ ] The final branch remote SHA matches the verified local commit.
- [x] Required M0 documentation and artifacts are present; remote evidence is pending.
- [x] The PR contains no production translation implementation or speculative modules.
