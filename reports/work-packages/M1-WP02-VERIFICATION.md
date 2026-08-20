# M1-WP02 Minimal ABI Canary Verification Report

## Result

```text
Status: LOCAL IMPLEMENTATION PASS — commit and hosted evidence pending
Milestone/work package: M1-WP02
Branch: codex/M1-WP02-minimal-abi-canary
Date/time UTC: 2026-08-20
Verifier: Codex
```

## Source and remote identity

```text
Repository: https://github.com/StevenBuglione/linguum-translation
Base main commit: a9da9261ca7a1cc593b95ab68e8bc50fbc81a945
Implementation commit: pending
Final evidence commit: pending
Remote branch SHA: pending
Pull request: pending
Working tree clean: NO — intentional implementation awaits checkpoint commit
Shallow clone: NO
```

## Requirement traceability

| Requirement | Implementation | Executable evidence | Result |
|---|---|---|---|
| Stable Linguum C ABI v1.0 | normative opaque-handle header and adapter; no C++/Mozilla types exported | C and C++ consumers; runtime ABI probe | PASS |
| Minimal runtime/model/translator/result/error/info lifecycle | same-library allocation/destruction and exception-guarded status mapping | 100 full create/load/translate/destroy cycles | PASS |
| Exact Firefox source | only staged external patch queue is built from the WP01 immutable snapshot | snapshot verifier; runtime revision probe | PASS |
| Real fixed es→en translation | Firefox-approved v2.0 model and fixed expected output | `¿Qué estás haciendo?` → `What are you doing?` on all 100 cycles | PASS |
| Input and descriptor safety | pre-dereference bounds, UTF-8/NUL/format/struct validation, privacy-safe errors | hostile probes repeated inside the lifecycle canary | PASS |
| Exact exports | one synchronized 20-symbol allowlist for header/macOS/Linux | Mach-O symbol inspection plus metadata unit test | PASS |
| Locked build inputs | official CMake 4.0.2 and Ninja 1.13.2 assets with per-host SHA-256 | bootstrap version/hash validation | PASS |
| Patch governance | external-only MPL patch, exact revision/platform/path/approval/removal metadata | schema-derived metadata test and patch-byte hash | PASS |
| Minimum macOS | deployment target remains macOS 13 | Mach-O `LC_BUILD_VERSION` inspection | PASS |
| Repeatable host gate | one clean command verifies source, tools, model, build, tests, symbols, OS target, and hashes | two independent `--clean` runs produced identical dylib SHA-256 | PASS |

## Changed modules and paths

| Path/module | Classification | Change | Dependency rule result |
|---|---|---|---|
| `native/abi` | public native ABI | normative v1.0 C header | allowed `native-abi`; PASS |
| `native/mozilla-adapter` | internal native adapter | stable ABI to pinned Bergamot translation | allowed `native-adapter`; PASS |
| `native/runtime-build` | internal native bridge | CMake build, hidden visibility, exact linker exports | allowed `native-bridge`; PASS |
| `native/patches` | MPL external patch queue | flattened-source/toolchain portability fixes and metadata | upstream tree untouched; PASS |
| `testing/native` | internal test harness | C/C++ consumers, fixed canary, model fixture, export baseline | allowed M1 harness; PASS |
| `scripts/native` | build/evidence tooling | locked tools, safe staging, model fetch, repeatable host gate | build-time only; PASS |
| `toolchains/*.lock.*` | toolchain policy | locked desktop CMake/Ninja versions and official assets | no production dependency; PASS |
| CI scope dispatchers/workflow | verification tooling | helper/metadata validation plus a clean Linux host-native build and 100-cycle canary | no module edge; PASS |

## Commands executed

| Command | Exit/result | Environment |
|---|---:|---|
| `python3 scripts/native/run_host_canary.py --clean --iterations 100` | 0; run 1, 3/3 CTest tests and 100 lifecycles passed | macOS 26.4 arm64, AppleClang 21.0.0 |
| `./gradlew clean verificationGate --warning-mode=fail` | 0; 21 tasks, 17 executed | Temurin JDK 21 / Gradle 9.5.0 |
| all 17 routed Unix M1 scopes | 0; every scope passed | local macOS arm64 |
| `python3 scripts/native/run_host_canary.py --clean --iterations 100` | 0; run 2 reproduced the exact dylib hash | clean regenerated build/source stage |
| `python3 -m unittest discover -s scripts/native/tests -v` | 0; 16 tests passed | Python standard library only |
| `python3 -m py_compile scripts/native/*.py scripts/native/tests/*.py` | 0 | local Python |
| `python3 scripts/upstream/snapshot.py verify` | 0; 31 submodules, 88 licenses | immutable source digest verified |
| `actionlint 1.7.12 -color` | 0; all workflows passed | official arm64 artifact hash and GitHub attestation verified |
| Ruby workflow YAML parse and `bash -n` over shell scripts | 0 | local macOS |
| JSON parse of model/tool/patch locks | 0 | Python `json.tool` |
| owned-path `git diff --check` | 0 | vendored byte-preserved tree excluded |

The adapter and all Linguum-owned C/C++ consumers compile with warnings as errors.
Warnings printed by the clean build originate in the immutable, legacy pinned
SentencePiece/zlib/YAML/Marian sources; they were not hidden or converted into a
weaker global warning policy. The adapter uses a system-header wrapper only around
third-party includes, leaving all Linguum implementation diagnostics at `-Werror`.

## Native and artifact results

| Target/profile | Build/link | Run/canary | Minimum version | Artifact SHA-256 |
|---|---|---|---|---|
| macOS arm64 / `apple-accelerate-arm64` | PASS; shared dylib, exact 20 exports | PASS; exact result, 100 lifecycles plus hostile probes | macOS 13.0 | `12f063e64498e83df62ea83cfccee43e07a87cc5615c0924e55840d5ac963b13` |

| Artifact/input | Bytes | SHA-256 |
|---|---:|---|
| `liblinguum_translation.dylib` | 9,932,960 | `12f063e64498e83df62ea83cfccee43e07a87cc5615c0924e55840d5ac963b13` |
| es→en model | 31,561,787 | `4aed7734152ae0045d1a69ae49c86cfda18f53c61f90e95e1d1de1c7c7c3b033` |
| es→en shortlist | 4,636,248 | `e2610211d3b9577d012638fe7e7e74ed7b4b708ce96b9e792e67c282a6492daa` |
| es→en vocabulary | 816,054 | `5ae254fa9b15aa182e70fd2a6186b1333c63a29a48043a9224c6aa4fcac058ad` |
| CMake 4.0.2 macOS archive | 80,051,064 | `4c53ba41092617d1be2205dbc10bb5873a4c5ef5e9e399fc927ffbe78668a6d3` |
| Ninja 1.13.2 macOS archive | 314,051 | `c99048673aa765960a99cf10c6ddb9f1fad506099ff0a0e137ad8960a88f321b` |
| external patch queue | 7,062 | `39fdeee61d7b327adc3b54e5d4ec1dc0e4180acb59a2420e97859f8930044b39` |

Source identity is Firefox `48d55cf7ec80093903e2ef7f58b61a84a22ef716`,
translations `eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d`, canonical
source-tree SHA-256 `94e42bbd05187c94dbb8adc04074015faab65d8f648d583b7056e8e4cf59182f`,
and Bergamot `v0.6.0`.

## Security, privacy, licensing, and compatibility

```text
User content handling: synchronous in-memory processing; no source/translation logging
Network access: build/model materializers only; runtime/adapter contains no network code
Native boundary: opaque C handles; bounded caller views; no C++ exception crosses C
Secrets/credentials: none introduced
Production dependencies: none added
Mozilla source: immutable snapshot unchanged; patches apply only in ignored build staging
Patch license: MPL-2.0 with exact metadata and corresponding-source path
Public Kotlin/Java/Swift API: unchanged (M3 remains blocked)
C ABI: initial ABI 1.0 feasibility surface; baseline protection begins in M2
Model schema/persisted metadata: unchanged; test-only exact canary manifest added
Minimum platforms: unchanged; macOS 13 encoded and inspected
Translation drift: fixed canary exact-match only; full corpus drift is later work
```

The source/model/tool fetchers reject traversal, escaping archive links, duplicate or
malformed model identities, wrong sizes/hashes, unsafe file names, and stale partial
downloads. Model runtime diagnostics never include the source or translated text.

## Known limitations

- WP02 proves the minimal ABI on the current macOS arm64 host only. Windows, macOS
  x64, Linux, Android, and iOS native build/run/package proofs belong to WP03–WP07.
- Packaging and clean one-dependency consumer resolution belong to WP08–WP10.
- Sanitizers, fuzzing, complete lifecycle-race handling, allocation failure, and the
  protected binary ABI baseline are M2 hard gates and are not claimed here.
- The pinned upstream source emits legacy compiler warnings. Linguum-owned sources
  remain warnings-as-errors; no upstream warning baseline or suppression was added.

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
WORK PACKAGE GATE: PENDING COMMIT AND HOSTED CHECKS
SAFE TO START NEXT WORK PACKAGE: NO
SAFE TO ADVANCE MILESTONE: NOT A MILESTONE BOUNDARY
```
