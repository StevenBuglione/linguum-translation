# Research and Validation Report

**Validated:** 2026-08-20  
**Purpose:** distinguish owner-locked design from current external facts, implementation interpretations, and still-unproven assumptions.

## 1. Source-of-truth decisions

`architecture/LOCKED_DECISIONS.md` contains the 76 owner-approved decisions. This report does not replace them.

The implementation is provider-neutral, local/offline after model installation, cross-platform, and built around a Linguum-owned stable C ABI in front of Firefox-maintained Mozilla inference.

## 2. Firefox/Mozilla engine validation

Current Firefox source metadata pins its translation inference dependency to:

```text
repository: mozilla/translations
revision:   eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d
release:    v0.6.0
license:    MPL-2.0
```

The pinned Mozilla source includes native inference code and the current `AsyncService` API. Its native build script enables CPU inference and FBGEMM and disables CUDA for the CPU build. The selected Windows benchmark used `AsyncService`, `numWorkers=1`, and `cacheSize=0`.

Validated primary sources:

- Firefox pin metadata: `toolkit/components/translations/bergamot-translator/moz.yaml`
- Mozilla inference source: `mozilla/translations/inference/`
- service API: `inference/src/translator/service.h`
- native CLI example: `inference/src/app/translator_cli.cpp`
- native build script: `inference/scripts/build.py`
- engine version: `inference/BERGAMOT_VERSION`

The implementation must never use the archived `mozilla/bergamot-translator` repository or arbitrary `mozilla/translations/main` as its production source.

## 3. Translation performance validation

The retained benchmark evidence demonstrates that the current Firefox-pinned native implementation is viable and faster than Chrome's local Translator API on the validated Windows machine.

Reference result:

```text
current Mozilla native p50:        11.13 ms
current Mozilla native p95:        30.00 ms
current Mozilla native p99:        38.26 ms
current Mozilla native throughput: 71.74 lines/sec
```

It beat Chrome at p50, p95, and p99 in all six paired rounds.

Evidence:

- `research/evidence/FINAL_BENCHMARK_REPORT.md`
- `research/evidence/current-mozilla-native-build.json`
- `research/evidence/current-mozilla-source-manifest.txt`
- `research/evidence/translation-benchmark-validation.zip`

This validates engine selection on the measured Windows profile. It does not validate wrapper overhead, other architectures, thermal behavior, model switching, or concurrent video playback.

## 4. Toolchain validation

Pin the initial implementation toolchain to the highest stable combination fully supported by Kotlin 2.4.10 rather than copying the Linguum monorepo's current JDK 25/Kotlin RC stack.

Initial lock:

```text
Kotlin                  2.4.10
Gradle wrapper           9.5.0
Gradle runtime JDK       21 LTS
JVM bytecode target      17
kotlinx.coroutines       1.11.0
Android Gradle Plugin    9.1.x, initially 9.1.1 with M0 compatibility proof
Android NDK              28.2.13676358
Android Build Tools      36.0.0
Dokka                    2.2.0
Vanniktech publish       0.36.0
Detekt                   2.0.0-alpha.6, tooling-only and explicitly pinned
Kover                    0.9.9
```

Kotlin 2.4.0–2.4.10 documents full Gradle compatibility through 9.5.0 and AGP compatibility through the 9.1 line. AGP 9.1.1 documents NDK 28.2.13676358 and JDK 17. The build itself runs on JDK 21 and emits Java 17 bytecode.

M0 must run a toolchain compatibility proof and fail on warnings indicating unsupported combinations. A patch downgrade within the AGP 9.1 line is permitted only if the compatibility report demonstrates the need; it is a toolchain lock correction, not an architecture change.

## 5. Kotlin/Apple integration validation

Kotlin Swift export is currently Alpha. Therefore it is not the stable v1 Swift surface.

The stable Apple strategy is:

```text
KMP common API
  → Objective-C-compatible Kotlin/Native framework
  → umbrella XCFramework
  → handwritten thin Swift overlay
  → Swift Package Manager binary package
```

The Swift overlay provides idiomatic `async throws`, names, errors, and state observation while delegating all semantics to the canonical KMP API.

A separate small SwiftPM manifest repository is recommended for scaling and versioning:

```text
StevenBuglione/linguum-translation-swift
```

The primary library repository remains the source and release authority.

## 6. Desktop target interpretation

Windows, macOS, and Linux support is delivered through the KMP/JVM target plus JNI and platform C++ runtimes.

Do not create Kotlin/Native desktop public targets merely to claim desktop support. This avoids tying desktop consumers to deprecated or lower-tier Kotlin/Native targets and matches the intended Linguum desktop service usage.

Desktop matrix:

```text
JVM target, Java 17 bytecode
  Windows x64  → JNI → DLL
  macOS arm64  → JNI → dylib
  macOS x64    → JNI → dylib
  Linux x64    → JNI → .so
  Linux arm64  → JNI → .so
```

Android uses the Android KMP library target and NDK/JNI. iOS uses Kotlin/Native cinterop and an XCFramework.

## 7. Kotlin target-support caveats

Current Kotlin/Native target tiers matter:

- `iosArm64` and `iosSimulatorArm64` are strongly supported.
- `linuxArm64` is a lower support tier and requires our own runtime validation.
- `iosX64` is Tier 3 and must be treated as a compatibility target with scheduled real-run validation where an Intel simulator host is available.
- `macosX64` Kotlin/Native is deprecated, but desktop macOS x64 is delivered by JVM/JNI, so that deprecation does not remove the library's macOS Intel desktop support.

Codex must not promise stronger Kotlin/Native guarantees than the toolchain provides without independent evidence.

## 8. Architecture-specific native backends

The Windows benchmark proved the x64 optimized path. It did not prove one universal backend for every architecture.

Required implementation matrix:

```text
x86_64 optimized
  FBGEMM + AVX2 where supported and validated

x86_64 fallback
  upstream-supported compatible path selected by executable proof;
  no illegal-instruction recovery strategy

Apple arm64
  upstream ARM path + Apple Accelerate/NEON as resolved by the pinned source

Android/Linux arm64
  upstream ARM path, typically RUY/NEON as resolved by the pinned source
```

The exact resolved backend, compiler flags, submodule revisions, and CPU requirements must be stored in each native build manifest.

Do not force FBGEMM on ARM merely because it is used by the validated Windows build.

## 9. Model registry validation

Mozilla publishes a current model registry containing language pairs, release status, architecture, artifact paths, model sizes, hashes, and metrics.

The library must not use the live registry directly at runtime.

The upstream compatibility workflow must:

1. fetch the registry at a recorded instant;
2. select only approved `Release` entries;
3. download every artifact required by each selected pair;
4. compute compressed and uncompressed size and SHA-256 for every artifact, including vocabularies and shortlists even if the registry does not provide them;
5. run compatibility, quality-drift, loading, and performance tests;
6. generate deterministic `approved-models.json`;
7. commit the manifest only through the protected compatibility workflow.

The initial permanent canary is Spanish→English. English→Spanish is the required reverse-direction canary.

## 10. Licensing validation

Original Linguum files are Apache-2.0. Mozilla-derived and vendored files remain MPL-2.0.

MPL-2.0 is file-level copyleft. It allows a larger work to contain differently licensed files, including statically linked code, but recipients of executable/library distributions must be told where to obtain the corresponding MPL-covered source.

The release must include:

- Apache-2.0 `LICENSE` for original Linguum code;
- Mozilla/MPL notices;
- `THIRD_PARTY_LICENSES`;
- exact `UPSTREAM.json` and recursive source lock;
- corresponding MPL source archive or durable source URL;
- patch source for MPL-covered modifications;
- SBOM and provenance.

A legal-review checkpoint is required before the first public release. The implementation may not state that the review is legal advice.

## 11. Maven Central validation

Maven Central requires a verified namespace. Publishing under:

```text
io.linguum
```

requires control of the reverse-DNS domain namespace, normally `linguum.io`, and DNS verification in the Central Portal.

Implementation may proceed without that credential, but `1.0.0-rc.1` publication is blocked until the namespace is verified. Codex must not silently switch the group to `io.github.stevenbuglione` because the group is a locked decision.

Maven Central publishing requires signing credentials and compliant POM metadata. Apple publications must be built on macOS.

## 12. Native runtime artifact selection risk

The locked design requires one public dependency while resolving platform-specific desktop native artifacts internally.

Gradle Module Metadata supports OS/architecture variants, but JVM consumer configurations do not inherently request native OS/architecture attributes in every build. Therefore M1 must prove the exact one-dependency consumer experience using clean Maven-local fixture projects on Windows, macOS, and Linux.

The proof must show:

- only the intended native runtime is resolved or packaged;
- no consumer plugin or manual classifier declaration is needed;
- Gradle and Maven consumers behave as documented;
- unsupported or ambiguous platforms fail clearly.

If a plain dependency cannot satisfy the locked experience, Codex stops with a blocker. It may not silently bundle every desktop runtime or require an extra Gradle plugin.

## 13. Mobile native feasibility risk

Firefox proves the model/runtime architecture and uses Bergamot WASM in the browser, but this handoff requires native C++ execution on Android and iOS.

The pinned source contains native and ARM-oriented code paths, but a production-quality Android/iOS build is not already validated by the Windows benchmark or Firefox's web integration.

M1 therefore requires real canary builds and execution before stable API implementation. No WASM fallback may be introduced without owner authorization.

## 14. Repository and artifact provenance validation

GitHub CLI supports creating a remote repository from an existing local source and pushing the initial commit in one operation.

GitHub artifact attestations link release artifacts to source and workflow provenance. On GitHub Free/Pro/Team they are available for public repositories; private/internal repositories require Enterprise Cloud.

The canonical plan creates the implementation repository as public. Release workflows attest executable/library artifacts and SBOMs and publish only from protected tags/environments.

## 15. Conclusions

Validated and closed:

- selected Firefox-maintained engine revision;
- native Windows performance and determinism;
- provider-neutral architecture direction;
- current stable Kotlin/Gradle publication stack;
- license boundary model;
- Maven Central and SwiftPM publication paths.

Must be proven before stable API work:

- all non-Windows native targets;
- architecture-specific math backends;
- x64 fallback;
- one-dependency desktop native variant resolution;
- Objective-C/XCFramework/Swift overlay consumer experience.
