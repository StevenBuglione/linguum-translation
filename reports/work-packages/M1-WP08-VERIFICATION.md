# M1-WP08 Apple XCFramework and Swift Export Verification Report

## Result

```text
Status: PASS
Milestone/work package: M1-WP08
Branch: codex/M1-WP08-apple-export-proof
Date/time UTC: 2026-08-21T15:46:08Z
Verifier: Codex
```

## Source and remote identity

```text
Repository: https://github.com/StevenBuglione/linguum-translation
Base main commit: 0e141ccc543eda2396ab6ed7724100be4b55f056
Initial implementation checkpoint: 0d9f44e71399b95d120a6df0f248728c421a9bed
Verified implementation checkpoint: 86fe51828221d6ea174a17b6fc0c7ee03048611a
Remote branch SHA at implementation checkpoint: 86fe51828221d6ea174a17b6fc0c7ee03048611a
Pull request: https://github.com/StevenBuglione/linguum-translation/pull/15
Working tree clean after verified checkpoint commit: YES
Shallow clone: NO
```

## Requirement traceability

| ID | Requirement | Implementation | Executable evidence | Result |
|---|---|---|---|---|
| WP08-APPLE-01 | Produce one umbrella XCFramework from every required Apple slice | static Kotlin/Native `LinguumTranslationCore` frameworks for `iosArm64`, `iosSimulatorArm64`, and `iosX64`; universal simulator merge; exact `xcodebuild -create-xcframework` assembly | two clean local all-slice builds plus hosted Xcode 16.4 all-slice build; final identifiers `ios-arm64` and `ios-arm64_x86_64-simulator` | PASS |
| WP08-APPLE-02 | Preserve the locked iOS 15 architecture and platform identities | archive-object `LC_BUILD_VERSION`, framework binary, header, module map, and XCFramework plist inspections | device arm64 IOS and simulator arm64/x86_64 IOSSIMULATOR objects all report minimum iOS 15.0 | PASS |
| WP08-APPLE-03 | Prove Objective-C export without leaking the raw native boundary | isolated Kotlin export service wraps the stable C ABI and exposes typed outcome/service declarations | exact declaration audit finds service/outcome/translate/support/close and rejects native pointers, `CPointer`, and `COpaquePointer` | PASS |
| WP08-APPLE-04 | Provide the minimum handwritten async Swift overlay | typed configuration, language pair, result, error, service, and translator surface using checked continuation and idempotent close | exact 13-declaration snapshot SHA-256 `d0ca52ba…1fe4`; Swift fixture compiles and executes | PASS |
| WP08-APPLE-05 | Prove SwiftPM consumption of the binary plus overlay | isolated package has one binary target, one handwritten overlay target, one library product, and one XCTest consumer | clean device-arm64 and simulator-x64 `build-for-testing` proofs plus live arm64 Simulator XCTest | PASS |
| WP08-APPLE-06 | Exercise async translation and lifecycle behavior 100 times | XCTest creates the service, translates the exact es→en canary asynchronously, closes twice, and requires the typed closed error afterward | local and hosted arm64 Simulator runs record `async=true`, 100 iterations, ABI 1.0; hosted Intel tier records 100 iterations | PASS |
| WP08-APPLE-07 | Make the candidate ZIP and SwiftPM checksum deterministic | sorted epoch ZIP writer, same-tree byte comparison, `swift package compute-checksum`, SHA-256 equality | two independent clean local builds produced identical ZIP `66487011…0af0`; hosted clean checksums equal their ZIP SHA-256 | PASS |
| WP08-APPLE-08 | Compile every unexecuted slice and correlate execution to the selected profile | full generic-device arm64 and generic-simulator x64 Xcode consumer builds; strict profile/tier validation | hosted arm64 evidence records compile proofs `ios-arm64` and `ios-simulator-x64`; Intel evidence records target `iosX64` | PASS |
| WP08-APPLE-09 | Add protected PR, Intel, and signed physical-device coverage without fabricating proof | PR arm64 all-slice Swift scope, Native Safety Intel x64 export, fail-closed signed nightly/release physical tier | 23 exact-head checks pass; local device inventory and repository self-hosted runner inventory are empty; physical result explicitly unclaimed | PASS |
| WP08-APPLE-10 | Preserve the M1 feasibility boundary | all Kotlin/Swift package code is isolated below `testing/platform-smoke/apple-export-canary`; architecture exemption is path-exact | architecture check reports 27 catalog modules, 1 active project, 0 dependency edges; no `platform/apple` or production API/publishing surface added | PASS |

## Changed modules and paths

| Path/module | Classification | Change | Dependency rule result |
|---|---|---|---|
| `scripts/native/apple_export.py` | build/evidence tooling | locked native-profile import, framework export, slice/header/plist inspection, universal merge, deterministic ZIP/checksum, Swift consumer compilation/execution, signing validation, and JSON evidence | build-time only; no production edge |
| `scripts/native/tests/test_apple_export.py` | internal test harness | 18 fail-closed export, packaging, execution, signing, portability, and boundary contracts | included in the 124-test native suite |
| `toolchains/apple-export.lock.json` | toolchain/export policy | iOS 15, Kotlin 2.4.10, exact modules, profiles, architectures, tiers, and package identities | no module edge |
| `testing/platform-smoke/apple-export-canary/kotlin-core/**` | standalone feasibility bridge | three-target Kotlin/Native static framework and minimal cinterop-backed Objective-C export | excluded from production architecture graph |
| `testing/platform-smoke/apple-export-canary/swift-package/**` | standalone feasibility consumer | local binary target, handwritten async Swift overlay, fixed model/config, and XCTest canary | not a companion publication repository |
| `testing/platform-smoke/apple-export-canary/swift-api.txt` | API feasibility snapshot | exact 13 declarations, with provider/Kotlin/core implementation types forbidden | not the production M3 API/ABI baseline |
| `scripts/ci/verify-scope.sh` and `build-logic/**` | repository verification | exact Swift scope and narrow feasibility-fixture classification | protected architecture gate retained |
| `.github/workflows/{pr,native-safety,nightly,release}.yml` | verification tooling | arm64 Simulator PR proof, Intel x64 safety proof, signed physical nightly/release proof | pinned actions and protected checks retained |

## Commands executed

| Command | Exit/result | Environment |
|---|---:|---|
| `python3 scripts/native/apple_export.py --profile all --clean --iterations 100 --execution-tier simulator-arm64` | 0 twice; all native profiles/frameworks, universal XCFramework, device/x64 consumer compile proofs, and live arm64 XCTest passed | macOS arm64, local Xcode 26.6, locked tools |
| direct byte comparison of the two clean `LinguumTranslation.xcframework.zip` outputs | identical; SHA-256 `66487011e242fadbd25c4a47c9f969b306a8efe6c41cff6b02b7f0276f3b0af0` | independent clean local build trees |
| `bash scripts/ci/verify-scope.sh swift` | 0; exact clean Apple export scope and architecture gate | final implementation logic on macOS arm64 |
| explicit generic iOS device and x86_64 Simulator `xcodebuild build-for-testing` commands | 0 for both unexecuted consumer slices | isolated staged Swift package and ephemeral DerivedData |
| `python3 -m unittest discover -s scripts/native/tests -p 'test_*.py' -v` | 0; 124 tests | final post-fix implementation tree |
| `bash scripts/ci/verify-scope.sh native` | 0; 124 native contracts, immutable source snapshot, and architecture gate | final post-fix implementation tree |
| `./gradlew clean verificationGate architectureCheck repositoryPolicyCheck qualityCheck --warning-mode=fail --no-build-cache --rerun-tasks --no-configuration-cache` | 0; 21 tasks executed | clean implementation tree |
| hosted PR run `32495332868` | 0; 15/15 jobs passed | GitHub-hosted exact checkpoint `86fe5182…11a` |
| hosted Native Safety run `32495332855` | 0; 7/7 jobs passed | GitHub-hosted exact checkpoint `86fe5182…11a` |
| hosted Dependency Review run `32495332803` | 0; 1/1 job passed | GitHub-hosted exact checkpoint `86fe5182…11a` |

The implementation was also covered by Python compilation, lock/JSON
validation, scope-diff checks, repository policy checks, immutable-source
verification, and staged-diff checks. Generated Gradle and Xcode build state
remained ignored and was not committed.

## Local Apple export results

| Slice | Framework build | Consumer proof | Identity | Clean framework binary SHA-256 |
|---|---|---|---|---|
| `iosArm64` | PASS | generic device `build-for-testing` PASS; physical run unavailable | arm64, IOS, iOS 15.0, pointer-free export header | `c3fa965ce5e4b2fbb73110de4128e5ed5060df682d6a0abff0254f03e598f698` |
| `iosSimulatorArm64` | PASS | live XCTest PASS, 100 async translations, ABI 1.0, double-close and typed closed error | arm64, IOSSIMULATOR, iOS 15.0, pointer-free export header | `f9d97da6e05eef06de304695592f0ae8d3b206c53a756aa037dfeffc5fc58a7d` |
| `iosX64` | PASS | generic x86_64 Simulator `build-for-testing` PASS | x86_64, IOSSIMULATOR, iOS 15.0, pointer-free export header | `4f3080ae41277a386c6e83d7099cfaaa4e9e86dd7b3684493ed84f0a3cc71a9c` |

The final local XCFramework has exactly two libraries: device `ios-arm64` and
universal simulator `ios-arm64_x86_64-simulator`. Its exact Objective-C header
SHA-256 is
`8ce14113c196a36666bd66dcd7641d6ec5ddb8ca5fdd9e24192c7d816d4d750b`;
the handwritten Swift API snapshot SHA-256 is
`d0ca52bab3ad6b755d76e293c1a09ad6ae40f7a5b2c98cedf27fb004200e1fe4`.
Both independent clean builds produced the same deterministic ZIP and SwiftPM
checksum:

```text
66487011e242fadbd25c4a47c9f969b306a8efe6c41cff6b02b7f0276f3b0af0
```

Reproducibility is asserted for independent clean builds in the same locked
environment and for the packager's mandatory same-tree double assembly.
Incremental native archive bytes and cross-Xcode framework bytes are not
claimed to be identical to clean local output.

## Hosted Apple results

The protected Apple Silicon job `96812378250` passed on Xcode 16.4 build
`16F6`, AppleClang 17.0.0, Swift 6.1.2, CMake 4.0.2, Ninja 1.13.2, and Kotlin
2.4.10. It built all three slices, assembled the exact two-library
XCFramework, compiled the unexecuted device-arm64 and simulator-x64 consumers,
and ran the `iosSimulatorArm64` async XCTest for 100 iterations. Its evidence
records `ephemeralDerivedData: true`, `async: true`, ABI 1.0, and exact iOS
15.0 identities. Host-specific artifact identities were:

```text
iosArm64 framework binary:          e3a887f946ce8cf1178558539cb395715eadc7af6cbca61befd5d95216c18043
iosSimulatorArm64 framework binary: 926d11506bd3d533095262e8d582e5928b4c4d1653c17c01f2791511cd166765
iosX64 framework binary:            d67e337d7964d0c083857cfc7d23f099a07d31f85be83f4568c091429511c949
Objective-C header:                 8ce14113c196a36666bd66dcd7641d6ec5ddb8ca5fdd9e24192c7d816d4d750b
Swift API snapshot:                 d0ca52bab3ad6b755d76e293c1a09ad6ae40f7a5b2c98cedf27fb004200e1fe4
XCFramework ZIP / Swift checksum:   69900190b4c76f7913a05738d4cba215e2f68f33125ce09d50e2ea6e9a4660ed
```

The protected Intel job `96812271323` passed on a real x86_64 Xcode 16.4
runner in 22 minutes 32 seconds. It built the locked `iosX64` native profile,
exported the static Kotlin framework, staged the SwiftPM consumer, and executed
100 translations under the x64 Simulator tier. Its framework binary SHA-256
was `510676592168ece99d018a7be78f24db1683546eb99e491e114ada10bce08d9c`;
its single-slice XCFramework ZIP and SwiftPM checksum were both
`5237208c862af2db91522dc41144fa8b0e79e69b16286fd9c12303b9b8e13ca1`.

Hosted identities are recorded separately from local Xcode 26.6 identities.
Cross-Xcode byte identity is not asserted; the semantic, architectural,
minimum-OS, API, packaging, checksum, and runtime contracts are asserted on
each host.

## Hosted exact-head results

All 23 checks passed on implementation checkpoint
`86fe51828221d6ea174a17b6fc0c7ee03048611a`:

| Workflow | Run | Jobs | Result | Completed UTC |
|---|---:|---:|---|---|
| PR | `32495332868` | 15/15 | PASS | 2026-08-21T15:44:38Z |
| Native Safety | `32495332855` | 7/7 | PASS | 2026-08-21T15:44:51Z |
| Dependency Review | `32495332803` | 1/1 | PASS | 2026-08-21T15:01:36Z |

The Apple job identities are `96812378250` for the all-slice arm64 PR consumer
and `96812271323` for the Intel x64 Native Safety tier. The remaining protected
matrix also passed macOS arm64/x64, Windows x64, Linux x64, Android arm64/x64,
iOS integration, Kotlin/Java consumers, both Linux sanitizer profiles and
Ubuntu 24.04 compatibility replays, source/native safety, API/ABI,
architecture, quality, license, dependency, artifact, and model gates.

The report-only successor must repeat the complete matrix before PR readiness
and merge.

## Fail-closed hosted regression and correction

Initial checkpoint `0d9f44e71399b95d120a6df0f248728c421a9bed` passed the
complete local macOS suite, but hosted Windows job `96811077153` rejected one
new contract test because it compared a generated Gradle argument with a
hard-coded POSIX `/tmp` string. Windows correctly rendered the same `Path` as
`\tmp\...`.

The correction at `86fe51828221d6ea174a17b6fc0c7ee03048611a` compares the
archive and build-directory arguments to the platform-native `Path` values and
strengthens the assertion to cover both arguments. All 124 native tests were
rerun locally, and the replacement Windows job `96812378094` plus the full
23-check matrix passed. No test, platform, or check was suppressed, retried
around, or weakened.

## Toolchain and source identity

```text
Local Xcode: 26.6 (build 17F113)
Local Swift: 6.3.3
Local AppleClang: 21.0.0
Hosted Xcode: 16.4 (build 16F6)
Hosted Swift: 6.1.2
Hosted AppleClang: 17.0.0
CMake: 4.0.2
Ninja: 1.13.2
Kotlin/Kotlin Native: 2.4.10
iOS deployment target: 15.0
mozilla/translations revision: eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d
Firefox pin revision: 48d55cf7ec80093903e2ef7f58b61a84a22ef716
Immutable source-tree SHA-256: 94e42bbd05187c94dbb8adc04074015faab65d8f648d583b7056e8e4cf59182f
```

## Physical arm64 gate status

The physical path requires the exact device UDID, signing identity, team,
provisioning profile, and bundle identity; decodes and validates the profile's
CMS content and application-identifier entitlement; uses manual signing; and
accepts only the exact 100-iteration physical-arm64 result. Nightly and release
jobs require runner labels:

```text
self-hosted, macos, arm64, ios-device
```

At verification time, `xcrun devicectl list devices` returned `No devices
found.` and the GitHub Actions runner inventory returned `total_count: 0`.
Accordingly, no physical-device execution result is claimed. The unavailable
external hardware is reported rather than substituted with simulator evidence,
and the signed scheduled/release path remains fail-closed when a runner is
registered.

## Security, privacy, licensing, and compatibility

```text
User content handling: unchanged; fixed public canary model/text only, no user translation logging
Network access: locked build/model materialization only; no runtime translation network path added
Native boundary: unchanged stable C ABI 1.0 behind the isolated Kotlin export service
Swift boundary: handwritten typed API; no native pointer, Kotlin, or core implementation type exposed
Signing inputs: environment/secrets only; no identity, profile, team, bundle, or device credential committed
Secrets/credentials: none introduced or committed
Production dependencies: none added
Mozilla source: immutable snapshot unchanged at locked digest 94e42bbd…182f
Corresponding source: inherited exact native source, patch, lock, and license evidence
Public production Kotlin/Java/Swift API: unchanged; feasibility snapshot only
Model schema/persisted metadata: unchanged
Minimum platform promise: iOS 15.0, not raised
```

## Known limitations

- No physical iOS device or signed self-hosted runner is currently available,
  so device execution is not claimed. The required nightly/release gate is
  implemented and remains fail-closed.
- `iosX64` is a lower-support target. Its real hosted proof passed on the
  protected `macos-15-intel` tier; local arm64 proof is structural and compile
  based.
- This work package proves an isolated feasibility XCFramework, Swift overlay,
  and SwiftPM consumer. The production `platform/apple` implementation and
  canonical API shape remain M3/M6 work; the companion SwiftPM publication
  repository and remote checksum resolution remain M9 work.
- Clean same-environment ZIP bytes are the reproducibility boundary.
  Incremental native output and cross-Xcode framework bytes are not asserted to
  be identical.

## Gate immutability declaration

```text
[x] No coverage threshold was lowered.
[x] No performance threshold/baseline was weakened or regenerated.
[x] No API/ABI baseline was changed to hide incompatibility.
[x] No test, platform, architecture, or check was disabled/ignored.
[x] No Detekt baseline or broad suppression was added.
[x] No unapproved production dependency or repository was added.
[x] Firefox pin and vendored source were not changed.
[x] Mozilla source was not directly edited.
[x] OS/API minimums and platform support were not raised.
[x] License, provenance, and dependency-verification gates were preserved.
```

## Final decision

```text
WORK PACKAGE GATE: PASS
SAFE TO START NEXT WORK PACKAGE: YES, AFTER PR #15 MERGES
SAFE TO ADVANCE MILESTONE: NOT A MILESTONE BOUNDARY
```
