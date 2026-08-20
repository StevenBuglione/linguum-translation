# Work Packages

Every work package ends with a verification report, intentional commit, immediate push, remote SHA verification, and draft PR update.

## M0 — Repository and governance

### M0-WP01 Repository bootstrap and first remote checkpoint

**Deliver:** root constitution files, Apache license, `.gitignore`, GitHub repository, first push.

**Commands:** use `scripts/bootstrap-repository.*`.

**Acceptance:** `origin/main` exists and matches local SHA; no secrets/build output; public repository metadata correct.

### M0-WP02 Gradle/toolchain skeleton

**Deliver:** wrapper 9.5.0, JDK 21 toolchain, Java 17 target policy, Kotlin 2.4.10, version catalog, empty build-logic, dependency verification/locks.

**Acceptance:** `./gradlew help --warning-mode=fail` and Windows equivalent pass on clean checkout.

### M0-WP03 Architecture catalog and checks

**Deliver:** module catalog parser, current milestone, architecture graph/check task, protected-file checks, package allowlist.

**Acceptance:** intentionally forbidden dependency fixture fails; clean graph passes.

### M0-WP04 Quality and CI skeleton

**Deliver:** format, Detekt no-baseline, Kover scaffolding, API validation setup, required workflow job names, CODEOWNERS, templates, security config.

**Acceptance:** local `verificationGate` green; first PR CI green; branch rules applied after checks exist.

## M1 — Feasibility

### M1-WP01 Firefox source snapshot tool

Generate immutable source snapshot, recursive lock, licenses, source hash, and diff report from exact pin.

### M1-WP02 Minimal ABI canary

Implement ABI version/runtime/model/translate/result/destroy minimum and fixed es→en canary harness.

### M1-WP03 Windows native profiles

Prove x64 AVX2 and baseline candidate, package DLLs, run lifecycle/translation.

### M1-WP04 macOS native profiles

Prove arm64 and x64 dylib builds/translation; record Accelerate/backend.

### M1-WP05 Linux native profiles

Prove x64 optimized/baseline and arm64; build against glibc 2.35 baseline.

### M1-WP06 Android native profiles

Build arm64-v8a/x86_64, package canary AAR/JNI, run emulator and physical arm64 smoke.

### M1-WP07 iOS native profiles

Build iosArm64/iosSimulatorArm64/iosX64 static/native linkage, invoke via minimal cinterop.

### M1-WP08 Apple export proof

Build umbrella XCFramework, handwritten Swift overlay minimum, SwiftPM fixture, async translation canary.

### M1-WP09 Desktop one-dependency variant proof

Publish feasibility artifacts to isolated Maven repository and consume one dependency from clean Windows/macOS/Linux projects. Stop on ambiguity/manual configuration requirement.

### M1-WP10 Feasibility consolidation

Generate all-platform report, artifact hashes, backend matrix, unresolved patch list, and hard gate decision.

## M2 — Native ABI

### M2-WP01 Complete ABI header and compatibility rules
### M2-WP02 Runtime/model/translator/result/error implementation
### M2-WP03 CPU dispatch and verified loader metadata
### M2-WP04 Native unit/abuse/lifecycle tests
### M2-WP05 ASan/UBSan/TSan configurations
### M2-WP06 Fuzz targets and permanent corpus
### M2-WP07 ABI baseline and symbol allowlist
### M2-WP08 Native artifact manifests/reproducibility

## M3 — Public API

### M3-WP01 LanguageTag/LanguagePair
### M3-WP02 Outcome/failure hierarchy
### M3-WP03 requests/results/content/spans/capabilities
### M3-WP04 service/translator/catalog/models interfaces
### M3-WP05 configuration DSL and diagnostics contracts
### M3-WP06 testing artifact and shared contract harness
### M3-WP07 Java facade
### M3-WP08 Objective-C export and Swift overlay API
### M3-WP09 API/JVM/Swift compatibility baselines
### M3-WP10 docs and consumer fixtures

## M4 — Runtime orchestration

### M4-WP01 service state/lifecycle
### M4-WP02 per-translator queues and global scheduler
### M4-WP03 cancellation/deadline/supersession
### M4-WP04 interactive/realtime/batch backpressure
### M4-WP05 loaded-model generation references and LRU
### M4-WP06 pin leases and memory-pressure port
### M4-WP07 deterministic/property/concurrency suite
### M4-WP08 fake production/testing contract parity

## M5 — Models

### M5-WP01 manifest schema/parser/canonicalizer
### M5-WP02 Mozilla registry snapshot/generator
### M5-WP03 model source/transport contracts
### M5-WP04 platform transport implementations
### M5-WP05 transactional installer/staging/quarantine
### M5-WP06 safe decompression and integrity verification
### M5-WP07 process locks/crash recovery
### M5-WP08 disk LRU/retention leases
### M5-WP09 network/metered/storage policies
### M5-WP10 failure injection and offline tests

## M6 — Bindings

### M6-WP01 JVM loader and JNI registration
### M6-WP02 JVM end-to-end service
### M6-WP03 Android factory/storage/network/JNI
### M6-WP04 Apple storage/network/cinterop
### M6-WP05 wrapper-overhead benchmarks
### M6-WP06 model lifecycle leak/soak
### M6-WP07 minimum-platform consumer tests
### M6-WP08 publication variant/AAR/XCFramework finalization

## M7 — Rich behavior

### M7-WP01 span validator/indexing
### M7-WP02 internal structured representation/native adapter support
### M7-WP03 span restoration and degradation semantics
### M7-WP04 segmentation policies and reassembly
### M7-WP05 batch implementation
### M7-WP06 atomic model generation switch/rollback
### M7-WP07 language-detection optional API/fakes only
### M7-WP08 golden/property/full behavior tests

## M8 — Full validation

### M8-WP01 all approved model pairs
### M8-WP02 output drift and determinism
### M8-WP03 dedicated performance profiles
### M8-WP04 memory/thermal/mobile validation
### M8-WP05 fuzz/sanitizer/soak expansion
### M8-WP06 minimum OS/API/glibc validation
### M8-WP07 dependency/license/SBOM/security
### M8-WP08 reproducible native/package builds
### M8-WP09 release-readiness report

## M9 — RC publication

### M9-WP01 Maven Central namespace and credentials prerequisite
### M9-WP02 POM/signing/publication tasks
### M9-WP03 GitHub release/SBOM/provenance/attestations
### M9-WP04 Dokka and guide publication
### M9-WP05 SwiftPM companion repository
### M9-WP06 clean external consumer matrix
### M9-WP07 legal/source-compliance checkpoint
### M9-WP08 publish and validate `1.0.0-rc.1`

## M10 — 1.0

### M10-WP01 resolve RC findings
### M10-WP02 final full gate
### M10-WP03 publish `1.0.0`
### M10-WP04 verify Maven Central/GitHub/SwiftPM identity
### M10-WP05 Linguum service-style consumption
### M10-WP06 activate upstream/nightly/security maintenance workflows
