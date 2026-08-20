# Milestone Roadmap and Hard Gates

## M0 — Repository and governance

### Goal

Create the GitHub repository immediately, push the constitution, establish pinned toolchains/build logic/architecture checks/CI skeleton, and prevent ungoverned implementation.

### Hard gate

- public remote exists;
- main remote SHA verified;
- protected architecture files committed;
- Gradle wrapper and pinned toolchain run from clean checkout;
- `verificationGate` exists and passes scaffold scope;
- dependency locking/verification enabled;
- branch/PR workflow configured;
- draft M1 PR/work package can be created;
- no translation production implementation yet.

## M1 — Platform and packaging feasibility

### Goal

Prove every risky native/platform/publication assumption before stable API code.

### Required proofs

- exact Firefox-pinned recursive source snapshot;
- minimal C ABI adapter;
- canary translation on every required platform/architecture;
- optimized and fallback x64 profile proof;
- ARM backend proof;
- Android AAR proof;
- iOS XCFramework proof;
- Objective-C export + Swift overlay proof;
- one-dependency desktop native variant resolution proof;
- Maven-local clean consumer fixtures.

### Hard gate

All requested targets build, package, consume, and translate, or a blocker is accepted. No M3 stable API implementation begins before this.

## M2 — Native ABI and runtime foundation

### Goal

Implement ABI major 1, opaque handle ownership, error mapping, runtime/model/translator lifecycle, CPU selection, and native-safety harnesses.

### Hard gate

- C/C++ ABI consumers pass;
- symbol allowlist exact;
- create/load/translate/destroy soak passes;
- ASan/UBSan jobs green;
- TSan/concurrency profile green where supported;
- fuzz corpus seeded and no known crash;
- ABI snapshot created and protected;
- every native artifact reports correct runtime info.

## M3 — Public API and consumer facades

### Goal

Implement canonical KMP contracts, factories/fakes, Java facade, Apple export, and Swift overlay API shape without depending on the production native runtime.

### Hard gate

- explicit API/ABI snapshots;
- Kotlin, Java, Swift consumer fixtures compile;
- testing artifact implements shared contracts;
- provider/native types absent from public signatures;
- KDoc/docs coverage gate green;
- stable/experimental boundaries established.

## M4 — Scheduler, lifecycle, and model pool

### Goal

Implement service lifecycle, translators, bounded queues, workloads, deadlines, cancellation, supersession, batch semantics, generation references, and memory-budgeted LRU using fake runtime/storage.

### Hard gate

- deterministic/property/concurrency tests green;
- no stale result delivery;
- no unbounded queue/memory behavior;
- close/drain/race tests green;
- active/pinned generation eviction impossible;
- production/testing services pass shared behavioral contracts.

## M5 — Model manifest, acquisition, and storage

### Goal

Implement approved manifest parser/generator, model sources, network policies, transactional installer, process locks, integrity verification, disk LRU/retention, quarantine, and crash recovery.

### Hard gate

- manifest schema and canonicalization green;
- es→en/en→es canaries generated from Mozilla registry snapshot;
- install failure injection at every phase leaves no visible partial model;
- offline installed model works;
- corrupt models quarantined;
- concurrent install deduplicated;
- metered/storage policy tested on mobile adapters/fakes;
- no network dependency in runtime modules.

## M6 — Platform bindings and end-to-end runtime

### Goal

Connect JVM/Android/iOS bindings to the production ABI, implement loader/extraction/linking, and run end-to-end local translation.

### Hard gate

- all platform consumer fixtures translate;
- JNI/cinterop no-op overhead measured;
- wrapper+engine latency meets profile gates;
- exact runtime binary digest/ABI verified before load;
- model load/unload/close leak tests green;
- minimum OS/API smoke tests green;
- plain dependency/AAR/XCFramework consumption green.

## M7 — Structured text, segmentation, batch, and switching

### Goal

Implement semantic span preservation, deterministic segmentation/reassembly, real native batch behavior, atomic model switching, and optional language-detection API surface.

### Hard gate

- protected/non-translatable spans survive exactly;
- all ranges valid;
- malformed/overlapping input handled deterministically;
- segmentation golden/property tests green;
- batch ordering/failure semantics green;
- generation switch never mixes models or loses previous working generation;
- language detection remains isolated from translator hot path.

## M8 — Full platform quality and security validation

### Goal

Run full model matrix, drift analysis, fuzz/sanitizer/soak, memory/thermal, CPU fallback, supported OS, reproducibility, dependency/license/security, and dedicated performance gates.

### Hard gate

- every approved pair passes full lifecycle;
- all profile absolute performance floors green;
- relative regressions within approved limits;
- native/JNI/cinterop leak/race tests green;
- minimum platforms validated;
- full SBOM/license/source compliance green;
- no unresolved critical/high vulnerability;
- reproducibility report accepted.

## M9 — Publishing, release candidate, and docs

### Goal

Complete Maven Central namespace/signing setup, docs site, GitHub release assets, SwiftPM companion repo, provenance/attestations, and publish `1.0.0-rc.1`.

### Hard gate

- `io.linguum` namespace verified;
- POM/signing checks green;
- Maven Central candidate resolves in clean consumers;
- XCFramework SwiftPM checksum resolves;
- source/SBOM/provenance/attestations available;
- legal/compliance checkpoint complete;
- release notes/drift/migration docs complete;
- RC soak period completed with no release blocker.

## M10 — 1.0 release and Linguum consumer validation

### Goal

Publish 1.0.0, consume it from the Linguum-style service fixture and optionally Linguum integration PR, and establish maintenance automation.

### Hard gate

- canonical release workflow green;
- Maven Central and GitHub release identities match;
- SwiftPM package resolves exact XCFramework checksum;
- Kotlin/Java/Swift/Android/iOS/desktop consumer verification green;
- Linguum service fixture uses only public API;
- release source/provenance verified independently;
- upstream checker/nightly/security/deprecation processes active.
