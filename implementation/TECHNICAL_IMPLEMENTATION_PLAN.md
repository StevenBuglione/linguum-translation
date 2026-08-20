# Technical Implementation Plan

## 1. Outcome

Produce a public Kotlin Multiplatform library with:

```text
io.linguum:translation:<version>
io.linguum:translation-testing:<version>
```

and a Swift Package product:

```text
LinguumTranslation
```

The library translates locally using the native Mozilla inference source revision pinned by Firefox, behind a stable C ABI and platform-specific bindings.

## 2. Build strategy

### Canonical toolchain

```text
Kotlin                  2.4.10
Gradle                   9.5.0
JDK                      21 LTS
JVM target               17
Coroutines               1.11.0
AGP                      9.1.1 after M0 proof
Android NDK              28.2.13676358
Android Build Tools      36.0.0
Dokka                    2.2.0
Vanniktech Maven Publish 0.36.0
Detekt                   2.0.0-alpha.6, tooling only
Kover                    0.9.9
```

No RC/EAP runtime/compiler version in a stable release.

### Gradle principles

- version catalog only;
- convention plugins in `build-logic`;
- configuration cache where supported;
- build cache enabled;
- dependency locking for every resolvable configuration;
- dependency verification with SHA-256;
- repository allowlist limited to Maven Central, Google, Gradle Plugin Portal, and explicit local test repos;
- explicit API mode;
- all Kotlin warnings as errors;
- deterministic archives and Gradle Module Metadata without random build identity;
- no project may apply conflicting primary architecture conventions.

## 3. Public artifact architecture

`translation` is the public umbrella KMP publication.

Conceptual dependencies:

```text
translation
├── api(translation-api)
├── implementation(translation-runtime)
├── target JVM → platform:jvm + Java facade
├── target Android → platform:android
└── target iOS → platform:apple + apple-export
```

Internal modules may be published as transitive implementation details when required by KMP publication, but:

- they are not documented as consumer coordinates;
- they use internal artifact names;
- they follow the same version;
- public compatibility promises apply only to `translation`, `translation-testing`, and the Swift Package product unless explicitly documented.

## 4. Desktop native runtime selection proof

Before committing to final publication layout, M1 publishes dummy platform runtime variants to an isolated Maven repository.

Clean consumer fixture:

```kotlin
dependencies {
    implementation("io.linguum:translation:0.0.0-feasibility")
}
```

It must resolve and package the correct native binary on each desktop OS/architecture without:

- a second dependency;
- a classifier;
- an extra Gradle plugin;
- runtime executable download;
- all-platform native bundle fallback.

Implement the intended Gradle Module Metadata variant model using OS/architecture attributes and verify actual consumer resolution.

If the plain consumer configuration cannot disambiguate variants, stop and report the conflict with Q11/Q22. Do not continue with a hidden compromise.

## 5. Native source and build

### Source preparation

- vendor exact Firefox-pinned `mozilla/translations` revision;
- include recursive submodule source at exact SHAs;
- record `UPSTREAM.json`, `UPSTREAM_LOCK.json`, and source tree hash;
- preserve MPL notices;
- apply optional approved patches only in temporary build workspaces.

### Linguum adapter

The adapter owns:

- C ABI implementation;
- exception containment;
- UTF-8 validation;
- runtime/model/translator/result/error handles;
- model descriptor conversion;
- `AsyncService` creation with one worker and zero cache;
- synchronous promise/future translation wrapper;
- runtime build metadata;
- native error mapping;
- no network/storage/model policy.

### Native build outputs

Build profiles are separate artifacts with one ABI:

```text
windows-x64-avx2
windows-x64-baseline
macos-arm64
macos-x64
linux-x64-avx2
linux-x64-baseline
linux-arm64
android-arm64-v8a
android-x86_64
ios-arm64
ios-simulator-arm64
ios-simulator-x64
```

Every build emits:

```text
native binary/static library
symbol export report
runtime-info manifest
compiler/linker command manifest
recursive upstream lock
license manifest
SHA-256
```

## 6. Platform bindings

### JVM desktop

- minimal JNI layer with `JNI_OnLoad`;
- explicit native registration preferred over exported Java-name symbols;
- native loader selects verified embedded/resolved artifact by OS/arch/CPU;
- extract to versioned application-specific cache with file lock and digest verification when the artifact is in a JAR;
- never load from arbitrary `java.library.path` before the verified packaged runtime unless an explicit testing-only hook is used;
- dedicated library dispatcher invokes synchronous ABI calls off UI/event-loop threads;
- Java facade wraps canonical API.

### Android

- KMP Android library module using AGP 9 Android-KMP plugin;
- AAR packages `arm64-v8a` and `x86_64` JNI library;
- one exported JNI bridge library per ABI, static-linking private native dependencies where allowed;
- app-specific storage from `Context`;
- connectivity/metered policy from Android APIs;
- memory-pressure integration;
- instrumented tests on minimum/current emulator plus physical arm64 release smoke.

### iOS

- cinterop consumes `linguum_translation.h`;
- native runtime linked into umbrella framework/XCFramework;
- KMP implementation invokes synchronous ABI on background coroutine context;
- Foundation storage/network/locking adapters;
- memory-warning integration;
- Objective-C-compatible export;
- handwritten Swift overlay provides async/throws/state ergonomics;
- release XCFramework contains device and required simulator slices.

## 7. Service/runtime composition

Internal composition root builds:

```text
TranslationServiceImpl
├── TranslationCatalogImpl
├── TranslationModelsImpl
├── ModelInstaller
├── InstalledModelStore
├── LoadedModelPool
├── TranslationScheduler
├── TranslationRuntime
├── StructuredTextProcessor
├── SegmentationEngine
├── MonotonicClock
├── PlatformStorage
├── ModelTransport
├── IntegrityVerifier
└── TranslationObserver (optional)
```

No reflection or DI container. Construct explicitly from immutable configuration.

## 8. Scheduler

### Queues

Maintain:

- global active-model concurrency budget;
- per-translator ordered queue;
- global queued request count and byte budget;
- workload-specific policy;
- monotonic deadlines;
- cancellation state;
- supersession index.

### Realtime

- preserve latest useful request by supersession key;
- remove stale queued requests;
- active call finishes safely;
- stale result discarded;
- deadline failures are typed;
- no queue growth beyond configured bounds.

### Interactive

- bounded wait;
- explicit overload/deadline outcome;
- no silent dropping.

### Batch

- preserve all accepted items;
- suspend producer/backpressure;
- bounded chunking;
- ordered results;
- cancellation stops remaining work;
- systemic failures differentiated from per-item failures.

## 9. Model lifecycle

### Catalog

Generated from embedded immutable approved manifest.

### Installation

Transactional staging, compressed/installed hash verification, safe decompression, config generation, compatibility probe, atomic promotion, stale staging recovery.

### Loading

- one model generation creates one native model/translator handle set;
- one native `AsyncService` worker/model;
- loading occurs off hot path;
- first canary translation required before activation;
- failed load leaves previous generation active.

### Memory pool

- memory-budgeted LRU;
- active/pinned generations not evictable;
- explicit pin leases;
- platform memory pressure may request eviction of unpinned idle models;
- model size measured from real resident memory where possible.

### Disk store

- byte-budgeted LRU;
- explicit retention leases;
- no eviction during install/verify/load/activation;
- app-specific root;
- process-safe locks;
- storage snapshot API.

## 10. Structured text

- validate semantic spans in common code;
- transform to a controlled internal representation only after M7 engine compatibility tests;
- protect non-translatable spans;
- translate;
- deterministically restore/map allowed formatting;
- validate all result ranges;
- return typed failure when preservation is impossible;
- format adapters (WebVTT/SRT/limited HTML) remain outside core runtime.

## 11. Segmentation

Library-owned deterministic segmenter supports:

```text
PreserveInput
Sentence
Automatic
```

Automatic preserves realtime/short input and segments longer prose according to versioned thresholds.

Segmentation must:

- be Unicode-aware;
- preserve newline/whitespace intent;
- not split protected spans;
- bound native input size;
- propagate cancellation/deadline;
- reassemble all-or-explicit-partial result deterministically;
- be golden/property tested.

## 12. Manifest and model update

The release manifest generator is a build/release tool, not runtime code.

It snapshots Mozilla registry data, downloads and hashes every artifact, validates every selected pair across the platform matrix, generates drift/performance reports, and writes canonical JSON.

Normal PRs cannot update the manifest.

## 13. API compatibility

Use Kotlin 2.4 built-in ABI validation as primary KMP API snapshot mechanism, supplemented by:

- JVM bytecode/API diff;
- pure Java consumer fixture;
- Objective-C header diff;
- Swift API/consumer fixture;
- C ABI symbol/header snapshot;
- persisted schema compatibility tests.

Do not rely solely on the older maintenance-mode binary compatibility validator when AGP/KMP support is uncertain.

## 14. Security and privacy

- no source/translated text logs;
- no hidden telemetry;
- no network in runtime modules;
- manifest/artifact digest verification;
- decompression bomb/path traversal protection;
- TLS system trust, no custom TLS;
- model URLs never logged with sensitive query data;
- C ABI fuzz/sanitizer coverage;
- trusted model manifest only;
- signed/attested release artifacts;
- secrets only in GitHub release environments.

## 15. Documentation

Generate Dokka API docs and handwritten guides:

- quickstart;
- Kotlin/Java/Swift;
- desktop/Android/iOS;
- model storage/network/offline;
- privacy/security;
- failures/troubleshooting;
- migration/deprecation;
- native ABI;
- licensing/corresponding source.

Every stable public symbol requires KDoc and a consumer example where nontrivial.

## 16. Downstream Linguum validation

Before 1.0 release, a fixture mirrors the existing service package style:

```kotlin
package io.linguum.services.api

import io.linguum.translation.TranslationService
```

It consumes only:

```kotlin
implementation("io.linguum:translation:<candidate>")
```

and proves the library does not leak native/platform/Mozilla configuration into the service composition root.
