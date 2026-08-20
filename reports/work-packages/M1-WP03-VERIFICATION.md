# M1-WP03 Windows Native Profiles Verification Report

## Result

```text
Status: LOCAL TOOLING PASS — hosted Windows build/run/package evidence pending
Milestone/work package: M1-WP03
Branch: codex/M1-WP03-windows-native-canary
Date/time UTC: 2026-08-20
Verifier: Codex
```

## Source and remote identity

```text
Repository: https://github.com/StevenBuglione/linguum-translation
Base main commit: 0bcb8479f98e4a973f04dd2c676c0e12f3ff6dae
Implementation commit: 6d694e3af4dee2572109212c4a1508c4bd474139
Hosted evidence commit: pending
Remote branch SHA: pending
Pull request: https://github.com/StevenBuglione/linguum-translation/pull/10
Working tree clean: YES after verified checkpoint commit
Shallow clone: NO
```

## Requirement traceability

| ID | Requirement | Implementation | Executable evidence | Result |
|---|---|---|---|---|
| WP03-WIN-01 | Build exact Firefox-pinned source and Linguum ABI as Windows x64 DLL | locked staged source and shared CMake target | hosted MSVC build | PENDING HOSTED |
| WP03-WIN-02 | Prove optimized x64 AVX2 profile | `/arch:AVX2`, FBGEMM, intgemm, ONNX SGEMM | compiler-command and PE-disassembly audit | PENDING HOSTED |
| WP03-WIN-03 | Prove a non-AVX2 fallback candidate | `/arch:SSE2`, no FBGEMM, SSSE3/SSE2-only intgemm, ONNX SGEMM | reject all AVX-family instructions in complete DLL disassembly | PENDING HOSTED |
| WP03-WIN-04 | Keep one exact C ABI and export surface | existing ABI 1.0 header and 20-symbol allowlist | C/C++ consumers plus `dumpbin /exports` | PENDING HOSTED |
| WP03-WIN-05 | Translate Firefox-approved es→en canary | same v2.0 model/config and exact expected text | 100 lifecycle/translation iterations per profile | PENDING HOSTED |
| WP03-WIN-06 | Record backend/toolchain/runtime identity | immutable profile lock and generated runtime metadata | exact MSVC/SDK/CMake/Ninja checks | PENDING HOSTED |
| WP03-WIN-07 | Package both DLL profiles | deterministic profile-specific candidate JARs | entry/notice/provenance inspection and SHA-256 | PENDING HOSTED |
| WP03-WIN-08 | Avoid build-host-only DLL dependencies | statically linked non-system libraries | `dumpbin /dependents` system allowlist | PENDING HOSTED |
| WP03-WIN-09 | Preserve corresponding-source obligations | MPL license, upstream lock, patch metadata in each package | package entry inspection | PENDING HOSTED |
| WP03-WIN-10 | Preserve all prior milestone gates | Windows proof is added to the stable Windows PR scope | clean local and hosted repository gates | PENDING |

## Changed modules and paths

| Path/module | Classification | Change | Dependency rule result |
|---|---|---|---|
| `native/runtime-build` | internal native bridge | locked Windows profile switches | allowed `native-bridge`; pending gate |
| `native/patches` | MPL external patch queue | exclude AVX/AVX-512 intgemm kernels only in baseline staging | upstream tree untouched; pending gate |
| `scripts/native` | build/evidence tooling | MSVC activation, two-profile build, PE/ISA/dependency audit, deterministic packages | build-time only; pending gate |
| `scripts/native/tests` | internal test harness | offline profile, ISA, dependency, and package invariants | build-time only; local PASS |
| `toolchains` | toolchain policy | exact Windows profile/MSVC/SDK/backend lock | no production dependency; pending hosted identity |
| Windows CI dispatcher/workflow | verification tooling | make two-profile proof part of the stable protected Windows job | no module edge; pending hosted gate |

## Commands executed

| Command | Exit/result | Environment |
|---|---:|---|
| `python3 -m unittest discover -s scripts/native/tests -v` | 0; 33 tests passed | local macOS arm64 |
| `python3 -m py_compile scripts/native/*.py scripts/native/tests/*.py` | 0 | local Python |
| `python3 scripts/native/stage_source.py --clean` | 0; external patch applied in ignored staging only | local macOS arm64 |
| `python3 scripts/upstream/snapshot.py verify` | 0; 31 submodules and 88 licenses | immutable source unchanged |
| `python3 scripts/native/run_host_canary.py --clean --iterations 100` | 0; ABI C/C++ and 100-cycle es→en canary passed; dylib SHA-256 `ff85f29e52de1bc7bf8b349834e31fc98aa99edd965c17aacc255418adf745e0` | macOS 13 arm64 regression profile, CMake 4.0.2, Ninja 1.13.2 |
| `./gradlew clean verificationGate --warning-mode=fail` | 0; 17 tasks, architecture/policy/API/format/coverage/quality passed | local Temurin JDK 21 / Gradle 9.5.0 |
| all 17 `scripts/ci/verify-scope.sh` M1 scopes | 0 each | architecture, quality, API, Kotlin, native, upstream, platform, consumer, model, license, artifact, release, performance |
| workflow YAML parse | 0 | all GitHub workflow YAML loaded with aliases enabled |
| hosted PR run `32392262528`, Windows job `96500930701` | 1 before compilation; mutable `windows-2025` selected the new VS 2026 image while the initial lock named VS 2022 | fail-closed runner discovery; removed ambiguous `-latest` selection |
| hosted PR run `32392539956`, Windows job `96501807295` | 1 before compilation; exact VS 17 selection proved absent on image `windows-2025-vs2026` `20260818.207.1` | official image manifest verified; exact VS 2026 install identity added while retaining legacy MSVC 14.44 |
| hosted PR run `32392944640`, Windows job `96503094811` | 1 before compilation; exact VS 2026 path resolved, but inline `cmd /s /c` quoting treated the quoted batch path literally | temporary activation batch script added with exact-content regression test |
| hosted PR run `32393175982`, Windows job `96503848960` | 1 before compilation; activation completed but the case-sensitive toolset lookup returned no value and exposed no related-key diagnostics | case-insensitive Windows environment lookup added with fail-closed related-variable diagnostics |
| hosted PR run `32393470949`, Windows job `96504800219` | 1 before compilation; case-insensitive inspection proved `VCToolsVersion` was genuinely absent after vcvars returned, with only unrelated `VCPKG_INSTALLATION_ROOT` present | activation batch now reports the vcvars exit code and installed MSVC toolset directories before failing closed |
| hosted PR run `32393848450`, Windows job `96505999675` | 1 before compilation; a second runner region served official rolling image `20260810.198.2` with VS `18.8.12023.21` instead of image `20260818.207.1` with VS `18.9.12112.369` | both finite official rollout identities locked; exact compiler, MSVC toolset, SDK, CMake, and Ninja locks remain singular |
| hosted PR run `32394104132`, Windows job `96506822256` | 1 before compilation; diagnostics proved VS 2026 rejects the named `-winsdk` form and listed exact installed legacy toolset directory `14.44.35207` | SDK changed to the supported positional argument; exact full legacy toolset requested and locked |
| hosted PR run `32394364835`, Windows job `96507654648` | 1 before compilation; exact SDK and legacy toolset activation succeeded, then the compiler banner differed from the provisional compiler lock | compiler-banner parser and fail-closed expected/actual diagnostic added before changing the lock |
| hosted PR run `32394570521`, Windows job `96508383645` | 1 before compilation; exact activation proved the legacy toolset compiler banner is `19.44.35228` | observed compiler identity locked exactly |
| hosted PR run `32394796302`, Windows job `96509086153` | 1 during optimized-profile CMake configuration; installed Doxygen activated an optional upstream docs branch whose input is absent from the pinned snapshot | upstream documentation forced off so host tool presence cannot change the native build graph |
| hosted PR run `32395376300`, Windows job `96510842275` | 1 at optimized-profile object 318/319; `/WX` promoted warnings emitted from pinned upstream headers while compiling the Linguum adapter | external target/include boundary marked `SYSTEM`; first-party adapter remains `/W4 /WX` |

## Local test and policy results

The offline suite proves the profile lock is exact, Windows profile configuration is
not host-ambiguous, the baseline patch disables all high intgemm kernels, malformed
tool metadata fails closed, AVX evidence parsing distinguishes optimized and baseline
artifacts, non-system DLL dependencies fail, compiler flags are profile-specific,
compiler command evidence is emitted, and package generation is byte-reproducible
with sorted fixed-metadata entries. The complete pre-WP03 macOS native profile was
also rebuilt from clean staging and passed its exact ABI/export/minimum-OS and
100-cycle translation regression.

## Platform and artifact results

| Target/profile | Build/link | Run/canary | ISA evidence | Package/artifact SHA-256 |
|---|---|---|---|---|
| Windows x64 AVX2 / `fbgemm-intgemm-avx2` | PENDING HOSTED | PENDING HOSTED | PENDING HOSTED | PENDING HOSTED |
| Windows x64 baseline / `intgemm-ssse3-onnx-sgemm-baseline` | PENDING HOSTED | PENDING HOSTED | PENDING HOSTED | PENDING HOSTED |

## Security, privacy, licensing, and compatibility

```text
User content handling: unchanged; fixed test canary only, no translation logging
Network access: build/model materializers only; packaged DLL has no network module
Native boundary: unchanged ABI 1.0 opaque C handles and same-library destruction
Secrets/credentials: none introduced
Production dependencies: none added
Mozilla source: immutable snapshot unchanged; patch applies only in ignored staging
Patch license: MPL-2.0 with exact affected path, SHA-256, approval, and removal rule
Public Kotlin/Java/Swift API: unchanged
Model schema/persisted metadata: unchanged
Minimum platform promise: unchanged; Windows 10 22H2 remains the floor
```

## Known limitations

- WP03 packages native-profile candidates; plain one-dependency Maven/Gradle consumer
  resolution is deliberately not claimed until WP09.
- Hosted Windows Server proves the compiler, DLL, ABI, ISA, package, and translation
  behavior. Windows 10 22H2 and Windows 11 physical/VM minimum-version smoke remain
  required release-tier evidence and are not claimed by this hosted runner alone.
- JVM/JNI loading belongs to later feasibility/binding packages; WP03 exercises the C
  ABI consumers directly.

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
WORK PACKAGE GATE: PENDING HOSTED WINDOWS PROOF
SAFE TO START NEXT WORK PACKAGE: NO
SAFE TO ADVANCE MILESTONE: NOT A MILESTONE BOUNDARY
```
