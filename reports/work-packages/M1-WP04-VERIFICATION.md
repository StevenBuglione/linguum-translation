# M1-WP04 macOS Native Profiles Verification Report

## Result

```text
Status: PASS — physical Apple Silicon and Intel build/run/ABI/backend/package proof verified
Milestone/work package: M1-WP04
Branch: codex/M1-WP04-macos-native-profiles
Date/time UTC: 2026-08-20
Verifier: Codex
```

## Source and remote identity

```text
Repository: https://github.com/StevenBuglione/linguum-translation
Base main commit: e14a479657ff683973fc2176891988907f1ad49c
Implementation commit: b7ea90778995c34259a682d1404c8048d87c178a
Protected-check correction commit: 8738c0a5c5c92354dc3d4492aba4058f49c91635
Remote branch SHA at hosted native proof: 8738c0a5c5c92354dc3d4492aba4058f49c91635
Pull request: https://github.com/StevenBuglione/linguum-translation/pull/11
Working tree clean after verified checkpoint commit: YES
Shallow clone: NO
```

## Requirement traceability

| ID | Requirement | Implementation | Executable evidence | Result |
|---|---|---|---|---|
| WP04-MAC-01 | Build exact Firefox-pinned source plus Linguum adapter for both desktop macOS architectures | explicit `macos-arm64` and `macos-x64` profiles | clean hosted builds on `macos-15` arm64 and `macos-15-intel` x86_64 | PASS |
| WP04-MAC-02 | Keep one exact C ABI and export surface | existing ABI 1.0 header and 20-symbol allowlist | C and C++ consumers plus `nm` exact-export audit | PASS |
| WP04-MAC-03 | Translate the approved es→en canary through a complete lifecycle 100 times | existing fixed model/config and C canary | 100 iterations on physical Apple Silicon and physical Intel | PASS |
| WP04-MAC-04 | Prove the arm64 backend | `armv8-a`, Accelerate SGEMM, upstream ARM/Ruy quantized path | compile database, runtime identity, and `otool -L` | PASS |
| WP04-MAC-05 | Prove a compatible x64 backend | Nehalem/SSE4.2 general-code floor, Accelerate SGEMM, intgemm runtime dispatch | compile database, physical Intel run, and `otool -L` | PASS |
| WP04-MAC-06 | Preserve macOS 13 minimum | explicit CMake deployment target for every profile | all compile commands plus Mach-O `LC_BUILD_VERSION` inspection | PASS |
| WP04-MAC-07 | Avoid host-dependent release compilation | explicit `armv8-a`/`nehalem`; reject `-march=native` | complete top-level compile-database audit | PASS |
| WP04-MAC-08 | Avoid build-host-only dylib dependencies | static non-system inputs; closed Apple-system allowlist | exact install name and `otool -L` dependency audit | PASS |
| WP04-MAC-09 | Package both profiles with corresponding-source metadata | deterministic architecture-specific candidate JARs | sorted epoch entries, repeated byte-for-byte creation, hashes | PASS |
| WP04-MAC-10 | Preserve all prior gates and the protected check contract | arm64 remains the protected PR macOS job; Intel is independent Native Safety proof | clean repository gate, every local scope, all hosted checks | PASS |

## Changed modules and paths

| Path/module | Classification | Change | Dependency rule result |
|---|---|---|---|
| `scripts/native/run_host_canary.py` | internal native test harness | explicit macOS profile configure arguments | no production dependency; PASS |
| `scripts/native/macos_profiles.py` | build/evidence tooling | host/toolchain, Mach-O, ABI, dependency, compile-command, and package gates | build-time only; PASS |
| `scripts/native/tests/test_macos_profiles.py` | internal test harness | fail-closed profile/parser/package/workflow contracts | build-time only; 55-test native suite PASS |
| `toolchains/macos-native-profiles.lock.json` | toolchain/profile policy | architecture, CPU floor, backend, runner, deployment, CMake, and Ninja identities | no production dependency; PASS |
| `toolchains/ci-runners.lock.yaml` | CI policy | exact Intel macOS runner label | no module edge; PASS |
| macOS CI dispatcher/workflows | verification tooling | protected arm64 and independent PR-triggered Intel native gates | exact 15-check protected contract retained; PASS |

## Commands executed

| Command | Exit/result | Environment |
|---|---:|---|
| `python3 -m unittest discover -s scripts/native/tests -v` | 0; 55 tests passed | local macOS arm64 |
| `python3 -m py_compile scripts/native/*.py scripts/native/tests/*.py` | 0 | local Python |
| workflow YAML parse with Ruby Psych | 0 | local macOS arm64 |
| `python3 scripts/native/macos_profiles.py --profile macos-arm64 --clean --iterations 100` | 0 after exact self-install-name parser correction; 293 build actions, ABI C/C++, 100-cycle canary, exports, architecture, minimum OS, dependencies, commands, package PASS | local Apple Silicon, Xcode 26.6 / AppleClang 21.0.0 |
| initial clean `macos-x64` attempt with `BUILD_ARCH=core2` | 1 at compile; AppleClang correctly rejected upstream SSE4.1 intrinsics without the required feature | local Apple Silicon cross-build; no artifact produced |
| `python3 scripts/native/macos_profiles.py --profile macos-x64 --clean --iterations 100` with explicit Nehalem floor | 0; 226 build actions, ABI C/C++, 100-cycle canary through Rosetta, exports, architecture, minimum OS, dependencies, commands, package PASS | local Apple Silicon plus Rosetta, Xcode 26.6 / AppleClang 21.0.0 |
| `./gradlew --no-daemon clean verificationGate --warning-mode=fail` before protected-check correction | 1; repository policy rejected a sixteenth PR check | fail-closed local policy gate; no baseline changed |
| same clean verification command after correction | 0; all 17 tasks passed | local Temurin JDK 21 / Gradle 9.5.0 |
| all non-macOS `scripts/ci/verify-scope.sh` M1 scopes | 0 each | exact implementation head |
| hosted Native Safety run `32428123309`, arm64 job `96614166904` | 0; clean physical arm64 profile proof | GitHub `macos-15` |
| hosted Native Safety run `32428123309`, Intel job `96614167142` | 0; clean physical x86_64 profile proof | GitHub `macos-15-intel` |
| hosted PR run `32428123324` | 0; all 15 protected jobs passed | exact implementation head |
| hosted Dependency Review run `32428123315` | 0 | exact implementation head |

## Platform and artifact results

| Target/profile | Build/link | Run/canary | Architecture/backend/minimum evidence | Hosted artifact SHA-256 |
|---|---|---|---|---|
| macOS arm64 / `apple-accelerate-arm64` | PASS; 267 audited compile commands; AppleClang 17.0.0, Xcode 16.4, SDK 15.5 | PASS; C ABI 0.01s, C++ ABI 0.00s, 100-cycle es→en 10.05s | thin arm64, `armv8-a`, macOS 13.0, Accelerate plus Apple system dylibs only, Ruy quantized path | dylib `30ab63a736fa9cc0d2685f5f2294cd838df16d1fc1c4cf033dab6ccc3afc71d6`; JAR `0bf0cd64b021044c481c3d3cf93237650ca516d8a7d9d116509c0bd278db8f64` |
| macOS x64 / `apple-accelerate-intgemm-runtime-x64` | PASS; 221 audited compile commands; AppleClang 17.0.0, Xcode 16.4, SDK 15.5 | PASS; C ABI 0.02s, C++ ABI 0.02s, 100-cycle es→en 14.35s on physical Intel | thin x86_64, Nehalem/SSE4.2 general floor, macOS 13.0, Accelerate plus Apple system dylibs only, intgemm runtime dispatch | dylib `d9243bfdf59d4b533d87a2699609d773d86d74e6037407d60aba51a6483be045`; JAR `7b22ed62ade57a8f86934b290033650bf0de9585adece5046ec6f3a5fa1c4314` |

Both hosted packages contain exactly 11 sorted, epoch-timestamped entries and include
the profile manifest, ABI header, upstream identities, patch metadata, MPL license,
project license/notice/third-party notice, and the one architecture-specific dylib.
The arm64 JAR is 3,375,736 bytes; the x64 JAR is 3,586,755 bytes. Recreating each
JAR from the same inputs produced the same bytes.

## Security, privacy, licensing, and compatibility

```text
User content handling: unchanged; fixed test canary only, no translation logging
Network access: build/model materializers only; packaged dylibs have no network module
Native boundary: unchanged ABI 1.0 opaque C handles and same-library destruction
Secrets/credentials: none introduced
Production dependencies: none added
Mozilla source: immutable snapshot unchanged; patches apply only in ignored staging
Corresponding source: upstream lock, patch metadata, ABI header, and licenses packaged
Public Kotlin/Java/Swift API: unchanged
Model schema/persisted metadata: unchanged
Minimum platform promise: unchanged; Mach-O minimum remains macOS 13.0
```

## Known limitations

- The hosted runners use macOS 15.7.7 rather than macOS 13. Runtime execution on the
  minimum OS remains release-tier evidence; every compile command and both dylibs were
  independently inspected for the 13.0 deployment floor.
- WP04 packages native-profile candidates. Plain one-dependency Maven/Gradle consumer
  resolution is deliberately not claimed until WP09.
- iOS slices and XCFramework/Swift consumption are separate WP07/WP08 gates.
- Sanitizer, fuzz, and long-soak expansion remains in the later native-safety roadmap;
  WP04 preserves the existing checks and proves the required build/ABI/lifecycle path.

## Gate immutability declaration

```text
[x] No coverage threshold was lowered.
[x] No performance threshold/baseline was weakened or regenerated.
[x] No API/ABI baseline was changed to hide incompatibility.
[x] No test, sanitizer, fuzz case, platform, or check was disabled/ignored.
[x] No Detekt baseline or broad suppression was added.
[x] No unapproved dependency or repository was added.
[x] Firefox pin and vendored source were not changed.
[x] Mozilla source was not directly edited.
[x] OS minimums and platform support were not raised.
[x] License, provenance, and dependency-verification gates were preserved.
```

## Final decision

```text
WORK PACKAGE GATE: PASS
SAFE TO START NEXT WORK PACKAGE: YES
SAFE TO ADVANCE MILESTONE: NOT A MILESTONE BOUNDARY
```
