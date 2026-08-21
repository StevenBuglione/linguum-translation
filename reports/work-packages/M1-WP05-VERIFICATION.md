# M1-WP05 Linux Native Profiles Verification Report

## Result

```text
Status: PASS
Milestone/work package: M1-WP05
Branch: codex/M1-WP05-linux-native-profiles
Date/time UTC: 2026-08-21T04:35:04Z
Verifier: Codex
```

## Source and remote identity

```text
Repository: https://github.com/StevenBuglione/linguum-translation
Base main commit: 4cbee007688bc447cbc9e6a4fb547ee3cb8d16ef
Implementation checkpoint: c4ae16d45c1307f25585cfd3dbedaf0ecde9ae4d
Remote branch SHA at hosted checkpoint: c4ae16d45c1307f25585cfd3dbedaf0ecde9ae4d
Pull request: https://github.com/StevenBuglione/linguum-translation/pull/12
Working tree clean after verified checkpoint commit: YES
Shallow clone: NO
```

## Requirement traceability

| ID | Requirement | Implementation | Executable evidence | Result |
|---|---|---|---|---|
| WP05-LINUX-01 | Build exact Firefox-pinned source plus Linguum adapter on Linux x64 and arm64 | three explicit locked profiles and external staging patch queue | clean Ubuntu 22.04 x64/arm64 builds; immutable digest `94e42bbd…182f` | PASS |
| WP05-LINUX-02 | Preserve ABI 1.0 and the exact C surface | existing stable header and linker allowlist | C/C++ ABI tests and exact 20-export ELF audits on every profile | PASS |
| WP05-LINUX-03 | Prove optimized x64 without an undeclared CPU requirement | Haswell general floor, FBGEMM, intgemm capped at AVX2 | 2,253,133-instruction ELF audit: AVX2 present, AVX-512/EVEX count zero | PASS |
| WP05-LINUX-04 | Prove a broadly compatible x64 fallback | Nehalem/SSE4.2 general floor, FBGEMM off, baseline intgemm plus ONNX SGEMM | 1,771,151-instruction ELF audit: all AVX-family counts zero | PASS |
| WP05-LINUX-05 | Prove real arm64 Ruy/NEON | `armv8-a`, Ruy enabled, FBGEMM/ONNX SGEMM disabled | native AArch64 runner, compile database, linked NEON evidence, 100-cycle canary | PASS |
| WP05-LINUX-06 | Build against the glibc 2.35 baseline and run on current Ubuntu | Ubuntu 22.04 builders plus Ubuntu 24.04 consumers | all release ELFs require at most GLIBC 2.34; exact bundles run 100 cycles on both OS versions | PASS |
| WP05-LINUX-07 | Reject build-host dependencies and paths | closed DT_NEEDED/system-root allowlists and RPATH/RUNPATH rejection | `readelf` plus `ldd` audits on release, sanitizer, and compatibility executions | PASS |
| WP05-LINUX-08 | Detect native memory and undefined-behavior defects | ASan+UBSan build mode, fail-fast environment, two-job memory ceiling | instrumented native tests plus 10 lifecycle translations on x64 and real arm64 | PASS |
| WP05-LINUX-09 | Package reproducible profile artifacts and corresponding-source metadata | deterministic JAR and authenticated compatibility bundle builders | repeated byte-for-byte JAR creation; artifact hashes below | PASS |
| WP05-LINUX-10 | Preserve protected CI and add independent architecture proof | protected x64 PR job plus four Native Safety build/compatibility jobs | workflow tests, YAML parse, actionlint, and 22 hosted checks at exact checkpoint `c4ae16d4…ae4d` | PASS |

## Changed modules and paths

| Path/module | Classification | Change | Dependency rule result |
|---|---|---|---|
| `scripts/native/linux_profiles.py` | build/evidence tooling | locked build, ELF/ISA/ABI/dependency inspection, sanitizers, deterministic packaging, compatibility execution | build-time only; no production edge |
| `scripts/native/run_host_canary.py` | internal native harness | explicit Linux profiles, additional CMake arguments, validated parallelism | no production dependency |
| `scripts/native/tests/test_linux_profiles.py` | internal test harness | fail-closed Linux profile, parser, packaging, sanitizer, workflow, and artifact-transport contracts | 17 tests pass |
| `toolchains/linux-native-profiles.lock.json` | toolchain/profile policy | exact runners, glibc baseline, architectures, backends, CPU floors, sanitizer set | no module edge |
| `native/runtime-build/CMakeLists.txt` | native build boundary | Linux x64 profile caps, Linux sanitizers, scoped GNU arm vector compatibility | no public API change |
| `native/patches/*` | approved external upstream patch queue | AVX2 structural caps and alignment-safe model reads | immutable source untouched; patch hash verified |
| `scripts/upstream/snapshot.py` and tests | supply-chain guard | avoid false-dirty rewrites and reject all untracked immutable-source files, including ignored files | locked digest preserved |
| Linux CI dispatcher/workflows and runner lock | verification tooling | protected x64 proof plus x64/arm64 sanitizer and Ubuntu compatibility jobs | pinned actions; protected check name retained |

## Commands executed

| Command | Exit/result | Environment |
|---|---:|---|
| `python3 scripts/native/linux_profiles.py --profile linux-x64-avx2 --clean --iterations 100` | 0; 329 build actions, 3 native tests, exact ABI/ELF/backend/package audit, 100-cycle canary | Ubuntu 22.04 x86_64, glibc 2.35, GCC 11.4.0 |
| `python3 scripts/native/linux_profiles.py --profile linux-x64-baseline --clean --iterations 100` | 0; 231 build actions, 3 native tests, zero-AVX audit, deterministic package, 100-cycle canary | Ubuntu 22.04 x86_64, glibc 2.35, GCC 11.4.0 |
| `python3 scripts/native/linux_profiles.py --profile linux-x64-baseline --clean --iterations 10 --sanitizers address,undefined` | 0; explicit `--parallel 2`, instrumented native tests and 10-cycle canary | Ubuntu 22.04 x86_64, ASan+UBSan |
| `python3 scripts/native/linux_profiles.py --profile linux-arm64 --clean --iterations 100` | 0; 302 build actions, native tests, Ruy/NEON audit, 100-cycle canary | real Ubuntu 22.04 AArch64, glibc 2.35 |
| `python3 scripts/native/linux_profiles.py --profile linux-arm64 --clean --iterations 10 --sanitizers address,undefined` | 0 after two fail-closed alignment corrections; instrumented native tests and 10-cycle canary | real Ubuntu 22.04 AArch64, ASan+UBSan |
| three `--verify-only` compatibility commands with `--iterations 100` | 0 each | Ubuntu 24.04 x86_64 (AVX2/baseline) and real Ubuntu 24.04 AArch64 |
| `python3 -m unittest discover -s scripts/native/tests -p 'test_*.py' -v` | 0; 72 tests | local macOS arm64 |
| `python3 -m unittest discover -s scripts/upstream/tests -p 'test_*.py' -v` | 0; 9 tests | local macOS arm64 |
| `bash scripts/ci/verify-scope.sh native` | 0; all Python/JSON/patch/snapshot/architecture checks | final local tree |
| all non-platform `scripts/ci/verify-scope.sh` M1 scopes | 0 each | final local tree |
| `./gradlew --no-daemon clean verificationGate --warning-mode=fail --no-build-cache --rerun-tasks` | 0; 21 tasks executed | Temurin JDK 21 / Gradle 9.5.0 |
| Ruby Psych parse of all workflows | 0 | local macOS arm64 |
| checksum-verified actionlint 1.7.7, ignoring only its stale `macos-15-intel` runner catalog entry | 0 | all repository workflows |
| `python3 scripts/native/stage_source.py --clean` | 0; complete external queue reapplied | final patch bytes |
| hosted PR run `32445016292` | 0; all 15 protected PR jobs pass, including Windows in 14m07s and Linux x64 in 40m25s | GitHub-hosted exact checkpoint `c4ae16d4…ae4d` |
| hosted Native Safety run `32445016218` | 0; macOS arm64/x64 plus Linux x64/arm64 build, sanitizer, artifact, and Ubuntu 24.04 compatibility jobs pass | GitHub-hosted exact checkpoint `c4ae16d4…ae4d` |
| hosted Dependency Review run `32445016212` | 0; policy check passes | GitHub-hosted exact checkpoint `c4ae16d4…ae4d` |

## Platform and artifact results

| Target/profile | Build/link | Run/canary | Compatibility/ISA/minimum evidence | Artifact SHA-256 |
|---|---|---|---|---|
| Linux x64 AVX2 / `fbgemm-intgemm-avx2` | PASS; 402 audited compile commands | PASS; ABI C/C++, 100 es→en lifecycles | Ubuntu 22.04→24.04; GLIBC max 2.34; AVX2 present; zero AVX-512; system dependencies only | `.so` `7eac77d477f98c28789cb0fb790898317fd2a7486a5501ecae8cf30921049b34`; JAR `0266a43e00574f2e7a630fbf4c71c791ecb01cd4718b80e28430649f83392985` |
| Linux x64 baseline / `intgemm-ssse3-onnx-sgemm-baseline` | PASS; 288 audited compile commands | PASS; ABI C/C++, 100 es→en lifecycles | Ubuntu 22.04→24.04; GLIBC max 2.34; zero AVX/AVX2/AVX-512; system dependencies only | `.so` `395418c79e628290c3d4a59ec97dc33979ec5220732a486330f372d957216166`; JAR `1d759691daf10f5d80b9bf1f36107cb045fc74f9c7e47d0cce0bc2f692a9ee57` |
| Linux arm64 / `ruy-neon-arm64` | PASS; real AArch64 build and link | PASS; ABI C/C++, 100 es→en lifecycles | Ubuntu 22.04→24.04; GLIBC max 2.34; Ruy and linked NEON/ASIMD; system dependencies only | `.so` `190f1ba06b4c4ad6398ca8a6845c4d75010c5dfde08f168e548da79809316bf6`; JAR `1bea916358f97abdce9895063b973823297cf45fc0e8bacf31785ca3002c0c47` |
| x64 baseline ASan+UBSan | PASS | PASS; 3 native tests plus 10 lifecycles | sanitizer flags/dependencies present; zero AVX across 7,811,025 disassembled instructions | `.so` `bd78344c04afff9f01daacaab1beecf4cd0bec477c96a64e3486de23f03167c7` |
| arm64 ASan+UBSan | PASS | PASS; 3 native tests plus 10 lifecycles | real AArch64 execution; Ruy/NEON; leak and undefined checks halt on error | `.so` `215abf1c8454172d732ff105741e9ba498904adc0bcd76402441c64b795a80be` |

The x64 AVX2 JAR is 5,563,981 bytes and the x64 baseline JAR is 4,769,069
bytes. Each package contains sorted epoch-timestamped entries for the profile
manifest, ABI header, upstream identities, patch metadata, licenses/notices,
and the profile-specific ELF. Recreating each JAR from the same inputs produced
identical bytes.

## Hosted exact-head results

The implementation checkpoint `c4ae16d45c1307f25585cfd3dbedaf0ecde9ae4d`
passed all 22 hosted checks. Native Safety run `32445016218` built each Linux
profile on its real architecture, repeated both sanitizer proofs, uploaded the
authenticated bundles, and consumed those exact bundles on Ubuntu 24.04.
PR run `32445016292` independently repeated the protected Linux x64 sequence
and every cross-platform repository scope. Dependency Review run `32445016212`
also passed. The final report-only successor is accepted only after GitHub
repeats the complete exact-head matrix; PR #12 check history is authoritative
for that non-self-referential final SHA.

| Hosted target/profile | Result and evidence | Hosted artifact SHA-256 |
|---|---|---|
| Linux x64 AVX2 release | PASS; 100 lifecycles, exact ABI/ELF audit, 2,253,133 instructions, AVX2 present, zero AVX-512, GLIBC max 2.34 | `.so` `6bba0169d2a2f31eed2c695de528d54575fbcb56a57741bc89289a95d39aea34`; JAR `9fcc867ffe58d60a2156302d97e4ea17df6e4add147abc6fa692d78a038e2ae4` |
| Linux x64 baseline release | PASS; 100 lifecycles, exact ABI/ELF audit, 1,771,151 instructions, zero AVX-family instructions, GLIBC max 2.34 | `.so` `df2ed27273787883ca17254fa9d0ac1896de2f7bc53275178acc7dabe395571e`; JAR `9be881bb4a3448b3a552fc5928c5dbfc2783444815991b50a09f0e2c9def5464` |
| Linux arm64 release | PASS; real AArch64/Ruy/NEON build, 100 lifecycles, 1,693,603 instructions, GLIBC max 2.34 | `.so` `43a8d30a6f1724507f37761ea94221e22faac49f7da2457c8aca85cf13c1987c`; JAR `5a984a14153910c2f6eaa002e953368a78be9557b808bc95a12b4fbcde1707c0` |
| Linux x64 baseline ASan+UBSan | PASS; native tests plus 10 lifecycles, 7,811,025 instructions, zero AVX-family instructions | `.so` `97933bc98789443a952c499b1db06657cf48aa54f7c79a35b2be9be99c3641b6` |
| Linux arm64 ASan+UBSan | PASS; real AArch64 native tests plus 10 lifecycles, 7,794,751 instructions | `.so` `7c5056c918d0155f899b6fd029cc8335387a457334a2ca65a2a34bffdb95823e` |
| Ubuntu 24.04 x64 compatibility | PASS; exact AVX2 and baseline bundles, 100 lifecycles each, byte identities and authenticated mode restored | artifact `9477efff1af830fb0eefc96f741d3d1928b21b6ae34066dfc6c5ae6310933585` |
| Ubuntu 24.04 arm64 compatibility | PASS; exact arm64 bundle, 100 lifecycles, byte identities and authenticated mode restored | artifact `85ec86c6f34a04ade344e4bebcddb5ee5d7c71a9fffba5f9f5fba8b8776e0eee` |

Hosted job identities: Native x64 build/sanitizers `96662888419`, Native x64
compatibility `96669081123`, Native arm64 build/sanitizers `96662888349`,
Native arm64 compatibility `96668559831`, protected PR Linux x64
`96662937357`, and corrected protected PR Windows `96662937228`.

## Security, privacy, licensing, and compatibility

```text
User content handling: unchanged; fixed test canary only, no translation logging
Network access: build/model materializers only; release ELFs use system runtime libraries only
Native boundary: unchanged ABI 1.0 opaque handles and exact 20-symbol export surface
Sanitizers: ASan+UBSan pass on x64 and real arm64; leak detection and halt-on-error active
Secrets/credentials: none introduced
Production dependencies: none added
Mozilla source: immutable snapshot unchanged at locked digest 94e42bbd…182f
Corresponding source: upstream locks, external patch metadata, ABI header, and licenses packaged
Public Kotlin/Java/Swift API: unchanged
Model schema/persisted metadata: unchanged
Minimum platform promise: unchanged; glibc 2.35 build baseline proven
```

The local Docker bind mount caused macOS conflict copies inside the immutable
snapshot. Every inspected group was exact or recoverably quarantined by strict
conflict-name/canonical-counterpart guards; the canonical digest never changed.
`snapshot.py prepare` now rejects ordinary and ignored untracked files before any
checkout and avoids rewriting a byte-identical tree when container Git reports a
false dirty state.

## Known limitations

- Local x64 execution used Docker Desktop's x86_64 environment; independent
  GitHub `ubuntu-22.04` and `ubuntu-24.04` runners repeated and passed the proof.
- WP05 packages native-profile candidates. Plain one-dependency Maven/Gradle
  consumer resolution is deliberately not claimed until WP09.
- Android, iOS, and Apple export proofs remain WP06-WP08.
- Performance baselines are not created or changed by this feasibility slice.

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
SAFE TO START NEXT WORK PACKAGE: YES, AFTER PR #12 MERGES
SAFE TO ADVANCE MILESTONE: NOT A MILESTONE BOUNDARY
```
