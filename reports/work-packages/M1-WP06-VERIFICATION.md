# M1-WP06 Android Native Profiles Verification Report

## Result

```text
Status: PASS
Milestone/work package: M1-WP06
Branch: codex/M1-WP06-android-native-profiles
Date/time UTC: 2026-08-21T08:55:19Z
Verifier: Codex
```

## Source and remote identity

```text
Repository: https://github.com/StevenBuglione/linguum-translation
Base main commit: 8fbd827f06f5e9b2bd7d21ef19cbc6b279d8626f
Implementation checkpoint: 5dd9bc71f6161461f17ae49b9b2cb8e99950d6ae
Remote branch SHA at implementation checkpoint: 5dd9bc71f6161461f17ae49b9b2cb8e99950d6ae
Pull request: https://github.com/StevenBuglione/linguum-translation/pull/13
Working tree clean after verified checkpoint commit: YES
Shallow clone: NO
```

## Requirement traceability

| ID | Requirement | Implementation | Executable evidence | Result |
|---|---|---|---|---|
| WP06-ANDROID-01 | Build the exact Firefox-pinned source for `arm64-v8a` and `x86_64` | external staged patch queue, NDK `28.2.13676358`, API 26, static private dependencies | three independent clean two-ABI builds; immutable digest `94e42bbd…182f` | PASS |
| WP06-ANDROID-02 | Prove real arm64 Ruy/NEON rather than compile-only support | `armv8-a`, Ruy and Ruy SGEMM enabled, FBGEMM disabled | compile database and linked NEON evidence; physical `arm64-v8a`/`aarch64` 100-cycle execution | PASS |
| WP06-ANDROID-03 | Keep x86_64 compatible with the official API-26 emulator | x86-64-v2, baseline intgemm, ONNX SGEMM, global `-mno-avx -mno-avx2` | complete linked disassembly rejects every AVX-family instruction; hosted minimum-API execution | PASS |
| WP06-ANDROID-04 | Package one JNI library per ABI in one deterministic canary AAR | static adapter/private libraries plus one `linguum_translation_jni` shared bridge per ABI | exact two-ABI AAR entry audit, sorted epoch timestamps, same-input and cross-clean byte comparisons | PASS |
| WP06-ANDROID-05 | Keep JNI and C ABI surfaces exact | `JNI_OnLoad` plus explicit `RegisterNatives`; stable ABI 1.0 adapter hidden inside the bridge | exact one-export ELF audits, Java bridge compile, C ABI lifecycle/rejection checks | PASS |
| WP06-ANDROID-06 | Run the exact model lifecycle and translation canary 100 times | isolated launcher/game-loop fixture using the pinned es→en model and one AAR dependency | physical log `PASS … 100 iterations, ABI 1.0`; hosted API-26 tokenized emulator job | PASS |
| WP06-ANDROID-07 | Prove minimum API and a physical arm64 device | protected API-26 x86_64 PR job; physical game-loop completion contract | Firebase matrix `matrix-3p9hhd7brxn1d` on physical F-01L/API 27; hosted API-26 job | PASS |
| WP06-ANDROID-08 | Reject build-host dependencies, excess exports, and undeclared ISA | closed DT_NEEDED allowlist, SONAME/RUNPATH checks, compile DB and full ELF disassembly | both clean JNI ELFs pass architecture, export, dependency, path, backend, API, and ISA audits | PASS |
| WP06-ANDROID-09 | Include corresponding-source and license identity in the artifact | exact license/notice, upstream locks, source digest, patch metadata, and profile lock under `META-INF` | AAR content bytes and entry set checked; immutable source and patch hashes reverified | PASS |
| WP06-ANDROID-10 | Preserve architecture and protected CI without creating the M6 Android module | standalone `testing/platform-smoke/android-canary`; PR emulator plus nightly/release physical jobs | 91 native contracts, clean repository gate, workflow contracts, and exact-head hosted matrix | PASS |

## Changed modules and paths

| Path/module | Classification | Change | Dependency rule result |
|---|---|---|---|
| `scripts/native/android_profiles.py` | build/evidence tooling | locked source/build/package/consumer/device pipeline; ELF/ISA/dependency/export inspection; tokenized device completion | build-time only; no production edge |
| `scripts/native/tests/test_android_profiles.py` | internal test harness | 19 fail-closed Android profile, AAR, workflow, NDK, device, and transient-log contracts | included in 91-test native suite |
| `toolchains/android-native-profiles.lock.json` | toolchain/profile policy | exact NDK, Build Tools, API, ABI, CPU/backend, emulator, and physical tiers | no module edge |
| `native/runtime-build/CMakeLists.txt` and `exports/android.map` | native build boundary | Android static adapter, one JNI shared object, x64 ISA cap, exact export map | public C ABI unchanged |
| `native/patches/*` | approved external upstream patch queue | Android path compatibility and guarded x86 intrinsics | immutable Mozilla source untouched; patch hash verified |
| `testing/native/android_canary_jni.cpp` | internal JNI harness | explicit native registration and exact 100-cycle C ABI/model/translation lifecycle | not shipped as a production module |
| `testing/platform-smoke/android-canary/**` | standalone feasibility consumer | one-AAR consumer APK, fixed model assets, ADB launcher, authoritative Test Lab game-loop completion | excluded from production architecture graph |
| `.github/workflows/{pr,nightly,release}.yml` and runner lock | verification tooling | API-26 x86_64 PR emulator; physical arm64 nightly/release tiers | pinned actions; protected check name retained |

## Commands executed

| Command | Exit/result | Environment |
|---|---:|---|
| `python3 scripts/native/android_profiles.py --profile all --clean --iterations 100 --device-mode none` | 0 three times; both ABIs built, inspected, packaged, and consumed | macOS arm64 host, exact NDK `28.2.13676358`, API 26 |
| direct `cmp` across independent clean arm64, x86_64, and AAR outputs | 0 for all three artifacts | separate clean build trees |
| `python3 -m unittest discover -s scripts/native/tests -p 'test_*.py' -v` | 0; 91 tests | final local tree |
| `bash scripts/ci/verify-scope.sh native` | 0; 9 upstream plus 91 native tests, compilation/JSON/source/architecture gates | final local tree |
| `./gradlew --no-daemon clean verificationGate --warning-mode=fail --no-build-cache --rerun-tasks --no-configuration-cache` | 0; 21 tasks executed | clean final local tree |
| standalone canary `clean :app:assembleDebug --warning-mode=fail` | 0; exactly one APK from one AAR dependency | exact Build Tools `36.0.0`, minSdk 26 |
| Firebase Test Lab game-loop matrix `matrix-3p9hhd7brxn1d` | PASS; one physical F-01L/API-27 axis, 89-second test | physical arm64-v8a/aarch64/64-bit device |
| uploaded/downloaded physical-test APK `cmp` | 0; exact bytes preserved | local candidate versus Test Lab raw result |
| hosted PR run `32462042222` | 0; 15/15 jobs passed | GitHub-hosted exact checkpoint `5dd9bc71…d6ae` |
| hosted Native Safety run `32462042197` | 0; 6/6 jobs passed | GitHub-hosted exact checkpoint `5dd9bc71…d6ae` |
| hosted Dependency Review run `32462042201` | 0 | GitHub-hosted exact checkpoint `5dd9bc71…d6ae` |

## Platform and artifact results

| Target/profile | Build/link | Run/canary | Compatibility/ISA evidence | Artifact SHA-256 |
|---|---|---|---|---|
| Android arm64-v8a / `ruy-neon-arm64` | PASS; real AArch64 ELF, Ruy compile/link evidence | PASS; physical API 27, 100 lifecycles, ABI 1.0 | ARMv8-A and linked NEON; exact API-26 target; system dependencies only | `.so` `d69f8577ca4dd574e554acd73c992afc9322971e32c14fc6d7a384cdcb74a2df` |
| Android x86_64 / `intgemm-ssse3-onnx-sgemm-baseline` | PASS; x86-64-v2 ELF | PASS; hosted API-26 emulator, 100 lifecycles | complete disassembly has no AVX/AVX2/AVX-512; exact API-26 target; system dependencies only | `.so` `efe8493827beaec5d24ef3fbf6fb82b3089cf0575f18fa59a37c20a50d1c6caa` |
| two-ABI canary AAR | PASS; 12 exact sorted epoch entries | clean one-dependency consumer assembly PASS | one JNI library per ABI; licenses, source lock/digest, patches, and profile lock included | `f79afcc0031fc6597fa93f4c3a5a56211788b810067108883f15f1544ea31800` |
| tokenized physical consumer APK | PASS; API-26-compatible package | PASS on physical F-01L/API 27 | downloaded Test Lab APK byte-identical; no Linguum failure or crash | `2b01e05a4839dbf1b8a6326f0405ffbb77c4ef20115bbb34a51a2bbc77a27e42` |

The clean arm64 JNI library is 8,333,232 bytes, the clean x86_64 JNI
library is 8,524,096 bytes, and the AAR is 16,904,261 bytes. Two completely
independent clean builds and a third exact-checkpoint clean build produced the
same three hashes. Recreating the AAR twice inside each run also produced
identical bytes.

## Physical arm64 proof

Firebase Test Lab catalog data identifies model F-01L as `PHYSICAL`, API 27,
with `arm64-v8a` as its first supported ABI. Final matrix
`matrix-3p9hhd7brxn1d` executed the authoritative game-loop fixture on axis
`F01L-27-en-portrait`. Raw logcat recorded:

```text
LINGUUM_ANDROID_CANARY_START runToken=test-lab iterations=100 sdk=27 primaryAbi=arm64-v8a osArch=aarch64 is64Bit=true
LINGUUM_ANDROID_CANARY_PASS runToken=test-lab canary lifecycle PASS: 100 iterations, ABI 1.0
```

The markers are 87 seconds apart. There is no
`LINGUUM_ANDROID_CANARY_FAIL`, `UnsatisfiedLinkError`, or crash for the Linguum
process. The one unrelated device launcher crash occurred before the Linguum
process started and does not involve the app package. The raw logcat SHA-256 is
`36673c552357f028193d630b7ec47bb685a2bcfc13d7627f57ee0ef01236b532`;
the Test Lab device-catalog JSON SHA-256 is
`6118fe4de7f0abd61b37272bd58f340a48497e13dcd92a7aea14aae68297a2e7`.

An earlier Robo matrix was deliberately rejected as proof even though its
matrix outcome passed: Robo ended after UI discovery before the app emitted a
completion marker. The fixture therefore added Test Lab's dedicated game-loop
intent contract, and the accepted matrices wait for the activity's `finish()`,
which occurs only after PASS or FAIL logging. ADB-driven jobs additionally use
a random 128-bit run token and accept only token-correlated log lines, so stale
device logs cannot create a false pass.

## Hosted exact-head results

All 22 protected checks passed on implementation checkpoint
`5dd9bc71f6161461f17ae49b9b2cb8e99950d6ae`:

| Workflow | Run | Jobs | Result | Completed UTC |
|---|---:|---:|---|---|
| PR | `32462042222` | 15/15 | PASS | 2026-08-21T08:54:49Z |
| Native Safety | `32462042197` | 6/6 | PASS | 2026-08-21T08:54:46Z |
| Dependency Review | `32462042201` | 1/1 | PASS | 2026-08-21T08:11:53Z |

The protected Android job `96710825316` completed successfully in 24 minutes
55 seconds. It built both ABIs with NDK `28.2.13676358`, assembled a clean
one-AAR consumer, and accepted only the token-correlated device result for
run token `1b3c05a2f6430d73f3cc46cc7395e65c`. Its evidence records API 26,
`x86_64`, `qemu=1`, 100 iterations, and
`LINGUUM_ANDROID_CANARY_PASS`. The hosted outputs were:

```text
arm64-v8a JNI SHA-256: e83ebdeda36717346aa3f55c470262869fb995d60aae2184d92344385cb820c3
x86_64 JNI SHA-256:    2ef86b2d3ac77e625ec42aac5dd5bc07e4472cf907f7b3dc02e04bce2ff08b7b
two-ABI AAR SHA-256:   df13078a4d3d95a4ba79d485ed87ca0197f47b0114be78927475a00f025ae6e5
consumer APK SHA-256:  ef58d5d40d96cc7d13b3b370fb509302358c06db201c49f47d79a8dfc65e2573
downloaded job-log SHA-256: 74a372599b5b9bbd07e47a75042fff02274196632ba29b44456ea72898a1653c
```

The hosted artifact identities are recorded separately from the macOS-hosted
clean-build identities above. Determinism was proved by byte comparison across
independent clean builds in the same locked environment and by the packager's
mandatory same-run double assembly; cross-host byte identity is not asserted.

The report-only successor must repeat the complete matrix before PR readiness
and merge.

## Security, privacy, licensing, and compatibility

```text
User content handling: unchanged; fixed public canary model/text only, no user translation logging
Network access: locked build/model materialization and authorized Firebase device testing only
Native boundary: unchanged ABI 1.0; JNI bridge exports only JNI_OnLoad and registers natives explicitly
Device evidence: random non-secret correlation token; no credential or user-data logging
Secrets/credentials: none introduced or committed; cloud credentials remain outside the repository
Production dependencies: none added
Mozilla source: immutable snapshot unchanged at locked digest 94e42bbd…182f
Corresponding source: upstream locks, source digest, external patch metadata, and licenses packaged
Public Kotlin/Java/Swift API: unchanged
Model schema/persisted metadata: unchanged
Minimum platform promise: unchanged; API 26 compile/package/emulator target
```

## Known limitations

- The physical F-01L is API 27; the exact API-26 minimum is independently
  exercised by the protected x86_64 emulator job.
- Recurring nightly/release physical jobs require a runner carrying the locked
  `self-hosted`, `linux`, `arm64`, and `android-device` labels. The feasibility
  hard gate was independently completed on Firebase Test Lab physical hardware.
- This is an isolated feasibility AAR and consumer. The production Android
  module is deliberately deferred to M6, and Maven publication remains WP09.
- Performance baselines are not created or changed by this work package.

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
SAFE TO START NEXT WORK PACKAGE: YES, AFTER PR #13 MERGES
SAFE TO ADVANCE MILESTONE: NOT A MILESTONE BOUNDARY
```
