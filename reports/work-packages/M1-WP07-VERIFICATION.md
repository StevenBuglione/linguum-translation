# M1-WP07 iOS Native Profiles Verification Report

## Result

```text
Status: PASS
Milestone/work package: M1-WP07
Branch: codex/M1-WP07-ios-native-profiles
Date/time UTC: 2026-08-21T12:43:45Z
Verifier: Codex
```

## Source and remote identity

```text
Repository: https://github.com/StevenBuglione/linguum-translation
Base main commit: 7cea7f1160d77a095e32c60cafbdac746be25eb8
Initial implementation checkpoint: 565129996eb8f392b798b0c90c320ecdf65986c8
Verified implementation checkpoint: 8233ee40633e1c9979d2551fc572e88e3305c74b
Remote branch SHA at implementation checkpoint: 8233ee40633e1c9979d2551fc572e88e3305c74b
Pull request: https://github.com/StevenBuglione/linguum-translation/pull/14
Working tree clean after verified checkpoint commit: YES
Shallow clone: NO
```

## Requirement traceability

| ID | Requirement | Implementation | Executable evidence | Result |
|---|---|---|---|---|
| WP07-IOS-01 | Build the exact Firefox-pinned source for device arm64, simulator arm64, and simulator x64 | external staged patch queue, iOS 15 deployment target, three locked profiles, statically merged private dependencies | two independent post-fix clean all-profile builds; immutable source digest `94e42bbd…182f` | PASS |
| WP07-IOS-02 | Use the required architecture-specific acceleration | arm64 Accelerate plus Ruy/NEON; x64 Accelerate plus intgemm runtime dispatch | compile database, linked-object/backend, target-triple, and Mach-O audits for all profiles | PASS |
| WP07-IOS-03 | Invoke the stable C ABI through minimal Kotlin/Native cinterop | standalone three-target fixture with one `.def` file and direct ABI calls | clean links for `iosArm64`, `iosSimulatorArm64`, and `iosX64`; no production module edge | PASS |
| WP07-IOS-04 | Exercise the exact lifecycle 100 times on supported simulator tiers | installed arm64 simulator app and Intel simulator executable use the pinned es→en model | local and hosted `iosSimulatorArm64` execution plus hosted `iosX64` execution, each 100 iterations and ABI 1.0 | PASS |
| WP07-IOS-05 | Produce deterministic static archives and packages | deterministic `libtool`/`ranlib`, atomic member-header normalization, sorted epoch ZIP entries | byte-for-byte comparison across independent clean local builds; hosted Xcode 16.4 normalization proof | PASS |
| WP07-IOS-06 | Keep platform, architecture, minimum OS, and C ABI exact | full archive parser plus `otool`, `nm`, and compile-command inspection | all objects match IOS/IOSSIMULATOR, arm64/x86_64, iOS 15.0, and the complete stable C ABI | PASS |
| WP07-IOS-07 | Preserve corresponding-source, license, and patch provenance | exact lock, source digest, licenses, patch manifest, profile lock, header, and one archive per ZIP | exact entry and content audit; patch SHA `5b630358…87e7` | PASS |
| WP07-IOS-08 | Add protected PR/Intel/device CI without fabricating unavailable proof | PR arm64 simulator, Native Safety Intel simulator, signed self-hosted nightly/release device flow | 23 exact-head checks pass; local device count and repository runner count are both zero; physical result explicitly unclaimed | PASS |
| WP07-IOS-09 | Fail closed on cross-Xcode archive metadata behavior | parser rejects nonzero timestamp/uid/gid and normalizer rewrites every final member header atomically | Xcode 16.4 rejected the initial checkpoint; regression test and corrected checkpoint pass Xcode 16.4 and local Xcode 26.6 | PASS |
| WP07-IOS-10 | Do not pull WP08 production/distribution scope forward | only `testing/platform-smoke/ios-canary` is architecture-exempt | architecture check passes; no `platform/apple`, XCFramework, Swift overlay, or `Package.swift` added | PASS |

## Changed modules and paths

| Path/module | Classification | Change | Dependency rule result |
|---|---|---|---|
| `scripts/native/ios_profiles.py` | build/evidence tooling | locked source, toolchain, build, archive, package, cinterop, simulator, signed-device, and evidence pipeline | build-time only; no production edge |
| `scripts/native/tests/test_ios_profiles.py` | internal test harness | 15 fail-closed lock, archive, package, backend, workflow, simulator, device, and normalization contracts | included in 106-test native suite |
| `toolchains/ios-native-profiles.lock.json` | toolchain/profile policy | iOS 15, Kotlin/CMake/Ninja, PCRE2, all targets/backends, runner tiers | no module edge |
| `native/runtime-build/CMakeLists.txt` | native build boundary | iOS-only static adapter path and Apple-safe export handling | public C ABI unchanged |
| `native/patches/*` | approved external upstream patch queue | iOS SentencePiece/PCRE2/cpuinfo/Accelerate support | immutable Mozilla source untouched; patch hash verified |
| `testing/platform-smoke/ios-canary/**` | standalone feasibility consumer | minimal direct cinterop executable and exact 100-cycle lifecycle | excluded from production architecture graph |
| `build-logic/**` and `scripts/ci/verify-scope.sh` | repository verification | narrow fixture exemption and exact iOS scope orchestration | protected architecture gate retained |
| `.github/workflows/{pr,native-safety,nightly,release}.yml` and runner lock | verification tooling | arm simulator PR, Intel simulator safety, signed physical nightly/release tiers | pinned actions and protected checks retained |

## Commands executed

| Command | Exit/result | Environment |
|---|---:|---|
| `LINGUUM_IOS_EXECUTION_TIER=simulator-arm64 bash scripts/ci/verify-scope.sh ios` | 0; 15 iOS contracts, three clean profiles, installed arm64 simulator 100-cycle execution, architecture gate | macOS arm64, local Xcode 26.6 |
| `python3 scripts/native/ios_profiles.py --profile all --clean --iterations 100 --execution-tier none` | 0; independent second clean all-profile build | macOS arm64, locked tools |
| direct comparison of the six first/second clean shipping outputs | all byte-identical | separate clean build trees |
| `python3 -m unittest discover -s scripts/native/tests -p 'test_*.py' -v` | 0; 106 tests | final post-fix implementation tree |
| `python3 -m unittest scripts.native.tests.test_ios_profiles -v` and Python compilation | 0; 15 tests plus syntax validation | final post-fix implementation tree |
| `./gradlew clean verificationGate --warning-mode=fail --no-build-cache --rerun-tasks --no-configuration-cache` | 0; 21 tasks executed | clean post-fix implementation tree |
| hosted PR run `32479840927` | 0; 15/15 jobs passed | GitHub-hosted exact checkpoint `8233ee40…c74b` |
| hosted Native Safety run `32479840904` | 0; 7/7 jobs passed | GitHub-hosted exact checkpoint `8233ee40…c74b` |
| hosted Dependency Review run `32479840980` | 0; 1/1 job passed | GitHub-hosted exact checkpoint `8233ee40…c74b` |

The iOS implementation was also covered by the protected native scope, source
immutability checks, JSON validation, diff checks, `py_compile`, and the full
hosted cross-platform matrix. Generated Gradle state under the isolated fixture
remained ignored and was not committed.

## Local platform and artifact results

| Target/profile | Build/link | Run/canary | Compatibility/backend evidence | Archive SHA-256 | Package SHA-256 |
|---|---|---|---|---|---|
| `iosArm64` / device arm64 | PASS; one 271-member arm64 IOS archive; cinterop link PASS | physical execution unavailable and not claimed | iOS 15.0, Accelerate, Ruy, ARMv8-A/NEON, complete C ABI | `871283d14239344ed4cdfb7af328b56c49cd8ba3845005174dabc55af1d6c05e` | `8b231860641a00ff145f0ee61430ae990ff8ca5b1fd0bca1cf9e7e5d14a8272d` |
| `iosSimulatorArm64` / simulator arm64 | PASS; one 271-member arm64 IOSSIMULATOR archive; cinterop link PASS | PASS; installed app, 100 lifecycles, ABI 1.0 | iOS 15.0 simulator, Accelerate, Ruy, ARMv8-A/NEON, complete C ABI | `49135da1ec8e389069a217dfa31b076a6f01f352bd4f501a34c0f8f8157f41dd` | `c0a9e69eb2b80a4df879a5a307a161cf0a2731c2be6dd681b3c5c408c3a98bae` |
| `iosX64` / simulator x64 | PASS; one 234-member x86_64 IOSSIMULATOR archive; cinterop link PASS | local structural proof; hosted Intel run PASS, 100 lifecycles | iOS 15.0 simulator, Accelerate, intgemm runtime dispatch, SSE4.2, complete C ABI | `9c1ad37e379a3ce31251eaa7cdfb8a108104a9c5b3389843f318f64a22d5e8eb` | `9530935c43d918478261659e06dc952c4e92e37b828c111084e81d117e29ebce` |

All six local shipping hashes were reproduced byte-for-byte by a second
independent clean build. Each archive member header has normalized timestamp,
uid, gid, mode, and deterministic layout. Each ZIP has the exact provenance,
license, lock, header, and single-profile archive entry set with sorted epoch
timestamps.

Kotlin/Native canary executables are structurally and operationally verified,
but executable byte identity is not asserted because Mach-O link UUID and
ad-hoc simulator signature material are intentionally platform-generated. The
shipping static archives and ZIP packages are the reproducibility boundary.

## Hosted iOS results

The protected arm64 PR job `96763694966` passed on Xcode 16.4 build `16F6`,
AppleClang 17.0.0, CMake 4.0.2, Ninja 1.13.2, and Kotlin 2.4.10. It built all
three profiles, normalized and inspected every archive, linked every cinterop
target, and ran `iosSimulatorArm64` for 100 lifecycles. Its host-specific
artifact identities were:

```text
iosArm64 archive:          7bf3dcf18fc15ff367eae5f411f07633b6cfefad94bea77f8f94ac82417b0196
iosArm64 package:          75f79a3199df4fe3d20ff4c8feade4b8fdae2ccb27386ddc818a32b1006476f3
iosSimulatorArm64 archive: 9b23d252d82a77bbb7481baf2090221860560d2bb4384edb2bbbea5648249ed5
iosSimulatorArm64 package: 64aab2fe051a780291163269ec411ec12b8002a39fa5ecc72785d511c01c4ab5
iosX64 archive:            bce749715e8aad0453b4ef84e8537af2c25925a4988a72640b5a99e9aaa95d9a
iosX64 package:            a93d44653597bdfabd402572fae10153290702ab180a68a9bfb6fe25d21efa30
```

The protected Intel job `96763629193` passed on a real x86_64 runner in 17
minutes 54 seconds. It built, normalized, inspected, linked, and executed the
`iosX64` profile for 100 lifecycles. Its host-specific archive SHA-256 was
`0b9f116886ed17d41cb6b2704ca40dd157c6cce9bbd44f570cd83b755c7a22c6`
and package SHA-256 was
`ae3db0b425b1f2ffff719add71b54e6825ca15a19d7b90fdcb5e80fc07ddfa97`.

Hosted identities are recorded separately from local Xcode 26.6 identities.
Determinism is asserted across independent clean builds in the same locked
environment and by mandatory same-run double packaging; cross-Xcode byte
identity is not asserted.

## Hosted exact-head results

All 23 checks passed on implementation checkpoint
`8233ee40633e1c9979d2551fc572e88e3305c74b`:

| Workflow | Run | Jobs | Result | Completed UTC |
|---|---:|---:|---|---|
| PR | `32479840927` | 15/15 | PASS | 2026-08-21T12:26:36Z |
| Native Safety | `32479840904` | 7/7 | PASS | 2026-08-21T12:43:06Z |
| Dependency Review | `32479840980` | 1/1 | PASS | 2026-08-21T12:00:58Z |

The iOS job identities are `96763694966` for the arm64 PR simulator matrix and
`96763629193` for the Intel simulator safety tier. The remaining protected
matrix also passed macOS arm64/x64, Windows x64, Linux x64, Android arm64/x64,
Swift/Kotlin/Java consumers, both Linux sanitizer profiles, Ubuntu 24.04
compatibility, source/native safety, API/ABI, architecture, quality, license,
dependency, artifact, and model gates.

The report-only successor must repeat the complete matrix before PR readiness
and merge.

## Fail-closed hosted regression and correction

Initial checkpoint `565129996eb8f392b798b0c90c320ecdf65986c8`
passed the clean local Xcode 26.6 matrix, but hosted Xcode 16.4 jobs
`96759769037` and `96759768182` rejected the final archive with:

```text
iOS native profile gate failed: merged iOS archive retains non-deterministic time or owner metadata
```

The failure was accepted as a real portability defect in the archive producer,
not dismissed as infrastructure noise. The correction at
`8233ee40633e1c9979d2551fc572e88e3305c74b`:

- parses and atomically normalizes the timestamp, uid, and gid of every final
  archive member header after symbol indexing;
- adds a regression that first proves a non-normal archive is rejected and then
  proves normalization succeeds;
- excludes ExternalProject's duplicate PCRE2 build-tree archives and requires
  the two installed PCRE2 archives instead.

The corrected implementation then passed both hosted Xcode 16.4 iOS jobs and
the full 23-check matrix. No gate was suppressed, retried around, or weakened.

## Toolchain and source identity

```text
Local Xcode: 26.6 (build 17F113)
Local AppleClang: 21.0.0 (clang-2100.1.1.101)
Hosted Xcode: 16.4 (build 16F6)
Hosted AppleClang: 17.0.0
CMake: 4.0.2
Ninja: 1.13.2
Kotlin/Kotlin Native: 2.4.10
iOS deployment target: 15.0
mozilla/translations revision: eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d
Firefox pin revision: 48d55cf7ec80093903e2ef7f58b61a84a22ef716
Immutable source-tree SHA-256: 94e42bbd05187c94dbb8adc04074015faab65d8f648d583b7056e8e4cf59182f
External patch SHA-256: 5b6303587714a66a823fc45d454dfb8fd06bd8f8c1b5850c49cdc3004a1b87e7
PCRE2: 10.39 / 0781bd2536ef5279b1943471fdcdbd9961a2845e1d2c9ad849b9bd98ba1a9bd4
```

## Physical arm64 gate status

The physical path validates the exact device UDID, signing identity,
provisioning profile, team, and bundle identity; codesigns the app; uses
`devicectl` to install, launch, collect the current-run result, and uninstall;
and accepts only the exact 100-cycle ABI 1.0 success contract. Nightly and
release jobs require runner labels:

```text
self-hosted, macos, arm64, ios-device
```

At verification time, `xcrun devicectl list devices` returned `No devices
found.` and the GitHub Actions runner inventory returned `total_count: 0`.
Accordingly, no physical execution result is claimed. The unavailable external
hardware is reported rather than substituted with simulator evidence, and the
signed scheduled/release path remains a fail-closed requirement once a runner
is registered.

## Security, privacy, licensing, and compatibility

```text
User content handling: unchanged; fixed public canary model/text only, no user translation logging
Network access: locked build/model materialization only; no runtime translation network path added
Native boundary: unchanged stable C ABI 1.0, invoked directly through minimal cinterop
Signing inputs: environment/secrets only; no identity, profile, team, or bundle credential committed
Secrets/credentials: none introduced or committed
Production dependencies: none added
Mozilla source: immutable snapshot unchanged at locked digest 94e42bbd…182f
Corresponding source: upstream locks, source digest, patch metadata, and licenses packaged
Public Kotlin/Java/Swift API: unchanged
Model schema/persisted metadata: unchanged
Minimum platform promise: iOS 15.0, not raised
```

## Known limitations

- No physical iOS device or signed self-hosted runner is currently available,
  so device execution is not claimed. The required nightly/release gate is
  implemented and remains fail-closed.
- `iosX64` is a lower-support target. Its real Intel simulator proof passed on
  the protected `macos-15-intel` tier rather than on the local arm64 host.
- This work package proves isolated static/native linkage and minimal cinterop.
  XCFramework creation, `platform/apple`, Swift overlay, `Package.swift`, and
  the production Apple consumer surface remain M1-WP08 or later scope.
- Mach-O cinterop executable bytes are not a shipping reproducibility boundary;
  static archives and deterministic ZIPs are.

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
SAFE TO START NEXT WORK PACKAGE: YES, AFTER PR #14 MERGES
SAFE TO ADVANCE MILESTONE: NOT A MILESTONE BOUNDARY
```
