Below is the consolidated **canonical architecture decision record** for the Linguum Translation library. This is the design we should treat as the source of truth when producing the implementation plan and handing the project to an implementation agent.

# Linguum Translation — Final Architecture Decisions

## 0. Foundation: translation engine selection is closed

The underlying translation engine is the **current Firefox-maintained native Mozilla translation implementation**, not the older archived Bergamot/browsermt mirror.

| ItemDecision            |                                                   |
| ----------------------- | ------------------------------------------------- |
| Upstream repository     | `mozilla/translations`                            |
| Firefox-pinned revision | `eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d`        |
| Bergamot version        | `v0.6.0`                                          |
| Native service          | Mozilla `AsyncService`                            |
| Workers                 | `numWorkers = 1` per model/runtime instance       |
| Bergamot cache          | Disabled for deterministic benchmarking           |
| Native optimization     | FBGEMM/native CPU path                            |
| Model source            | Mozilla Firefox released translation models       |
| Engine license          | MPL-2.0                                           |
| Engine-upgrade policy   | Track Firefox's exact pin, never arbitrary `main` |

Validated Spanish→English native performance was approximately:

| MetricCurrent Mozilla native |                 |
| ---------------------------- | --------------- |
| Median p50                   | 11.13 ms        |
| Median p95                   | 30.00 ms        |
| Median p99                   | 38.26 ms        |
| Throughput                   | 71.74 lines/sec |
| Short subtitle p95           | 14.52 ms        |
| Medium subtitle p95          | 28.75 ms        |
| Long subtitle p95            | 41.06 ms        |

Native beat Chrome's local Translator API at p50/p95/p99 in all six validated benchmark rounds.

The engine-selection question is therefore **closed**. Future work is integration and library engineering, not searching for another translation engine.

---

# I. Public API and repository

| #DecisionLocked design |                         |                                                                                                                                                                                       |
| ---------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Q1**                 | Public abstraction      | Expose both a high-level **`TranslationService`** and lower-level pair-bound **`Translator`**. Normal callers use the service; hot paths can retain a translator.                     |
| **Q2**                 | Repository              | Standalone, independently versioned repository, likely `linguum-translation`. Consumed by Linguum as a real published library rather than a monorepo module.                          |
| **Q3**                 | Platforms               | Full v1 support for Windows, macOS, Linux, Android and iOS.                                                                                                                           |
| **Q4**                 | Native interoperability | One stable **C ABI** around Mozilla/Bergamot, with thin platform bindings. No C++ types cross the boundary.                                                                           |
| **Q5**                 | Firefox tracking        | Follow the exact revision that Firefox pins. Scheduled automation may open compatibility PRs when Firefox changes its pin. Never auto-merge them.                                     |
| **Q6**                 | Provider neutrality     | Public API is completely provider-neutral. No Mozilla/Bergamot/Marian/FBGEMM types are public.                                                                                        |
| **Q7**                 | Model management        | High-level automatic model discovery/download/cache/verify/load/evict plus lower-level explicit controls such as preload, availability, unload and removal.                           |
| **Q8**                 | Model versioning        | Every library release carries an immutable approved model manifest. Model binaries are normally downloaded on demand and pinned to exact hashes/versions.                             |
| **Q9**                 | Concurrency API         | Structured `suspend` APIs, library-managed concurrency, thread-safe public objects, per-translator ordering, cancellation and bounded queues.                                         |
| **Q10**                | Error model             | Typed sealed failure hierarchy for expected failures, with a library-owned outcome/result abstraction. True library defects may throw documented exceptions.                          |
| **Q11**                | Published artifacts     | One primary consumer dependency: `io.linguum:translation:<version>`. Internal platform/native implementation artifacts remain hidden.                                                 |
| **Q12**                | Package namespace       | Primary public package: **`io.linguum.translation`**. Implementation lives under `io.linguum.translation.internal.*`.                                                                 |
| **Q13**                | Service creation        | `TranslationService.create()` plus optional immutable Kotlin DSL configuration. No global singleton.                                                                                  |
| **Q14**                | Lifecycle               | `TranslationService` owns native resources. `Translator` is a lightweight service-owned handle. `close()` is deterministic and idempotent.                                            |
| **Q15**                | Request API             | Structured request/result API plus simple convenience translation. Batch, request IDs, cancellation, capabilities and structured content are supported without exposing engine knobs. |
| **Q16**                | Languages               | Strong **BCP-47-based** **`LanguageTag`** value type, predefined common constants, and `LanguagePair`. Language validity and model support remain separate concepts.                  |
| **Q17**                | Pair discovery          | First-class immutable **`TranslationCatalog`** derived from the release's approved model manifest.                                                                                    |
| **Q18**                | Native ABI versioning   | C ABI has independent major/minor versioning. Breaking ABI requires ABI-major change. Kotlin validates ABI compatibility on startup.                                                  |
| **Q19**                | Publishing              | **Maven Central** is canonical. GitHub Releases provide changelogs, provenance and inspectable native assets.                                                                         |
| **Q20**                | API compatibility       | Strict SemVer plus machine-enforced Kotlin public API, JVM binary API, Swift surface and C ABI compatibility.                                                                         |

Public usage should feel approximately like:

```kotlin
val service = TranslationService.create()

val pair = LanguagePair(
    source = Languages.SPANISH,
    target = Languages.ENGLISH,
)

val translator = service.translator(pair)

val result = translator.translate("¿Dónde estás?")
```

---

# II. Internal repository architecture

**Q21 — Strict responsibility-based multi-module architecture.**

Canonical conceptual layout:

```text
linguum-translation/
├── build-logic/
├── translation-api/
├── translation-runtime/
├── translation-models/
├── native/
│   ├── abi/
│   ├── mozilla-adapter/
│   ├── runtime/
│   ├── upstream/
│   │   └── mozilla-translations/
│   └── patches/
├── platform/
│   ├── jvm/
│   ├── android/
│   └── apple/
├── upstream/
│   └── firefox/
├── testing/
│   ├── fixtures/
│   ├── contract-tests/
│   ├── native-harness/
│   ├── compatibility/
│   ├── fuzz/
│   └── benchmarks/
├── architecture/
├── gradle/
└── .github/
```

Dependency direction must be machine enforced.

Production directories/modules named things such as:

```text
common
helpers
utils
misc
core
```

are prohibited unless there is an explicitly approved responsibility that justifies the name.

The API module cannot depend on native/platform implementation modules.

---

# III. Native artifact strategy

| #DecisionLocked design |                     |                                                                                                                                                                                          |
| ---------------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Q22**                | Native packaging    | One public dependency with Gradle/KMP variants resolving platform-native assets internally. Native executable code ships with the library; models remain runtime data.                   |
| **Q23**                | CI model            | Three layers: local `verificationGate`, required PR CI matrix, and extended nightly/release validation.                                                                                  |
| **Q24**                | Coverage            | Risk-based thresholds: deterministic API/runtime/models around 95% line / 90% branch; platform Kotlin around 90/85; native quality relies heavily on real integration/sanitizer testing. |
| **Q25**                | Clean code          | Strict machine-enforced clean-code limits, warnings-as-errors, no Detekt baseline, formatting required, complexity/size/nesting bounds, no generic managers/helpers.                     |
| **Q26**                | Mozilla source      | Vendor an immutable source snapshot of the exact Firefox-pinned Mozilla revision. Build must be reproducible/offline-capable.                                                            |
| **Q27**                | Upstream patches    | Vendored upstream remains immutable. Necessary fixes live in an explicit external patch queue with metadata, review and removal conditions.                                              |
| **Q28**                | CPU/platform matrix | Modern production architectures plus required development simulator/emulator targets.                                                                                                    |

Official architecture matrix:

```text
DESKTOP
Windows
  x86_64

macOS
  arm64
  x86_64

Linux
  x86_64
  arm64

ANDROID
  arm64-v8a
  x86_64 emulator

iOS
  arm64 device
  arm64 simulator
  x86_64 simulator
```

No legacy 32-bit support.

A target counts as officially supported only when CI builds and validates it.

---

# IV. Model acquisition and installation

| #DecisionLocked design |                     |                                                                                                                                                             |
| ---------------------- | ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Q29**                | Model source        | Source abstraction. Mozilla is canonical default, but enterprise/local/Linguum mirrors may supply the exact approved bytes. Source is not the trust anchor. |
| **Q30**                | Installation        | Transactional, manifest-driven model installation with staging, verification and atomic promotion. Partial installations are never visible.                 |
| **Q31**                | Loaded model memory | Memory-budgeted LRU model pool with explicit preload and pin controls. Active/pinned models cannot be evicted.                                              |
| **Q32**                | Native threading    | One validated Mozilla worker per active model; global library scheduler bounds total concurrency.                                                           |
| **Q33**                | Cancellation        | Cooperative. Queued work is removed; running native inference safely finishes and its stale result is discarded.                                            |
| **Q34**                | State/progress      | Suspend commands plus strongly typed `Flow`/`StateFlow` state surfaces. Translation results remain direct suspend returns.                                  |
| **Q35**                | Observability       | Optional privacy-safe observer/metrics API. No mandatory logging backend and never log source or translated content.                                        |
| **Q36**                | Offline guarantee   | Translation/runtime code is strictly network-independent once a model is installed. Network exists only in model acquisition.                               |
| **Q37**                | Missing model       | `translator()` remains local-only. `ensureTranslator()` or explicit model installation may perform acquisition.                                             |

The security principle is:

> **A model source supplies bytes; the immutable approved manifest decides whether those bytes are trusted.**

---

# V. Language and networking behavior

| #DecisionLocked design |                    |                                                                                                                                           |
| ---------------------- | ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Q38**                | Language detection | Optional separate capability. A pair-bound `Translator` never performs source-language detection.                                         |
| **Q39**                | Licensing          | Original Linguum code: **Apache-2.0**. Mozilla-derived/upstream code remains MPL-2.0 with rigorous boundary and compliance enforcement.   |
| **Q40**                | OS minimums        | Explicit machine-enforced support floors rather than compiler defaults.                                                                   |
| **Q41**                | CPU instructions   | Runtime CPU dispatch. AVX2 is optimized primary x64 path, with a validated compatible fallback profile.                                   |
| **Q42**                | C ABI memory       | Opaque handles and explicit matching destroy functions. Memory must be freed by the same ABI implementation that allocated it.            |
| **Q43**                | Process isolation  | In-process native runtime for v1, behind a private abstraction allowing future desktop process isolation without changing the public API. |
| **Q44**                | Model trust        | Authenticated immutable release manifest + exact hashes + secure transport + provenance.                                                  |
| **Q45**                | Mobile downloads   | Policy-driven acquisition with conservative mobile defaults, explicit metered-network opt-in, resumability and storage preflight.         |

Initial minimum OS targets:

```text
Windows
  Windows 10 22H2+

macOS
  macOS 13+

Linux
  glibc >= 2.35
  primary validation on Ubuntu 22.04 / 24.04

Android
  minSdk 26 / Android 8.0+

iOS
  iOS 15+
```

These minimums are compatibility contracts. Agents cannot silently raise them.

---

# VI. Translation scheduling

| #DecisionLocked design |                   |                                                                                                                                                  |
| ---------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Q46**                | Deadlines         | Optional per-request monotonic deadline, understood by the scheduler. Expired queued work never enters inference.                                |
| **Q47**                | Backpressure      | Workload-aware bounded backpressure: freshness for real-time, bounded response for interactive, completeness/backpressure for batch.             |
| **Q48**                | Markup/text       | Plain text is canonical; presentation formatting is represented as structured semantic spans. Format parsers remain adapters outside the engine. |
| **Q49**                | Segmentation      | Explicit library-owned `Automatic`, `PreserveInput`, and `Sentence` segmentation policies.                                                       |
| **Q50**                | Translation drift | Same version/configuration must be deterministic. Engine/model upgrades may change outputs only through reviewed drift analysis.                 |
| **Q51**                | Performance gates | Dual gates: relative regression versus approved baseline plus absolute product ceilings.                                                         |
| **Q52**                | Native safety     | Layered native tests, sanitizers, fuzzing, hostile-input validation, stress/soak tests and permanent regression corpora.                         |

Realtime scheduling semantics:

```text
Cancellation
  caller no longer wants result

Deadline
  result would no longer be useful

Supersession
  newer realtime work replaces stale queued work

Backpressure
  keeps memory and latency bounded
```

Real-time subtitle workloads prioritize **freshness**.

Batch workloads prioritize **completeness**.

---

# VII. Java, Swift and API evolution

| #DecisionLocked design |                   |                                                                                                                           |
| ---------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Q53**                | Java/Swift        | Canonical KMP domain API plus intentionally designed thin Java and Swift façades.                                         |
| **Q54**                | Experimental APIs | Explicit stable vs experimental tiers. Experimental APIs require opt-in and do not receive full compatibility guarantees. |
| **Q55**                | Dependencies      | Minimal dependency policy with explicit approval for every new production dependency.                                     |
| **Q56**                | Consumer testing  | Publish separate **`io.linguum:translation-testing`** artifact containing contract-faithful fakes and fixtures.           |
| **Q57**                | Supply chain      | Reproducible-build controls, signed provenance, SBOMs and exact artifact/source/upstream/model identity enforcement.      |
| **Q58**                | Disk cache        | Byte-budgeted installed-model disk cache with safe LRU eviction and explicit retention.                                   |

`translation-testing` must not carry actual Mozilla engines/models unnecessarily. It should allow downstream code to simulate:

```text
successful translations
typed failures
model unavailable
model download state
model loaded state
deadlines
cancellation
queue overload
service closed
```

and the fake implementation must itself pass shared behavioral contract tests.

---

# VIII. Native error and lifecycle details

| #DecisionLocked design |                           |                                                                                                                                                                             |
| ---------------------- | ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Q59**                | Native errors             | Stable numeric status codes plus explicit error/result objects. No C++ exceptions, global last-error state or string-based program logic across ABI.                        |
| **Q60**                | Runtime info              | Immutable privacy-safe `RuntimeInfo`: library version, ABI version, Mozilla revision, Bergamot version, manifest revision, OS, architecture, acceleration and capabilities. |
| **Q61**                | Model switching           | Generation-based atomic activation. Existing requests finish against old model; new requests move to validated new generation.                                              |
| **Q62**                | Batch                     | Dedicated `translateBatch()` API with ordering, bounded chunking and per-item versus systemic failure distinction.                                                          |
| **Q63**                | Stable v1 scope           | Stable translation fundamentals only; advanced capabilities such as quality estimation/alignment/pivot start experimental.                                                  |
| **Q64**                | Networking implementation | Internal `ModelTransport` abstraction using mature platform HTTPS capabilities. No custom TLS stack.                                                                        |
| **Q65**                | Filesystem                | Platform-appropriate application storage, process-safe locks, staging/quarantine separation and atomic state changes.                                                       |
| **Q66**                | Serialization             | Public domain types are not wire-protocol DTOs. Only persisted formats receive explicit schemas and migrations.                                                             |

Important lifecycle rule:

```text
new model
  ↓
download
  ↓
verify
  ↓
compatibility probe
  ↓
load
  ↓
atomic generation activation
  ↓
new requests use it
  ↓
old generation drains
  ↓
old native resources destroyed
```

A failed upgrade must leave the currently working model intact.

---

# IX. Toolchains, routing and input safety

| #DecisionLocked design |                          |                                                                                                                                     |
| ---------------------- | ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Q67**                | JVM/toolchains           | Build using **JDK 21 LTS**, target **Java 17 bytecode**. Kotlin, Gradle, AGP, NDK, CMake and native build tools are pinned.         |
| **Q68**                | Pivot translation        | Never silently pivot through another language. `Translator(A,B)` means an approved direct pair.                                     |
| **Q69**                | Input safety             | Hard bounded payload/request limits, explicit-length UTF-8, malformed input validation and typed oversized-request failure.         |
| **Q70**                | Documentation            | Stable public API requires KDoc and maintained Kotlin/Java/Swift/platform examples and versioned operational documentation.         |
| **Q71**                | Security                 | `SECURITY.md`, private reporting, scanning, SAST, SBOM, sanitizer/fuzzer integration and explicit upstream security-update process. |
| **Q72**                | Governance               | Protected main, CODEOWNERS, required CI, ADRs, CONTRIBUTING and strict `AGENTS.md`.                                                 |
| **Q73**                | Model tests              | Spanish→English permanent PR canary; release/compatibility validation across full approved model manifest.                          |
| **Q74**                | Benchmark infrastructure | Blocking performance gates run on stable dedicated hardware/profiled runners. Hosted shared CI is not authoritative for latency.    |
| **Q75**                | Releases                 | Manual/promoted SemVer releases from canonical workflow, RC validation where warranted, Maven Central canonical.                    |
| **Q76**                | Deprecation              | Stable API may be deprecated compatibly in minor versions but is removed only in a major release.                                   |

---

# X. Native C ABI rules

The C ABI must obey these rules:

```text
C only
opaque handles
explicit lengths
UTF-8
explicit create/destroy ownership
numeric status codes
no C++ classes
no std::string/vector/etc.
no exceptions across boundary
no allocator crossing
no temporary-pointer returns
no undocumented thread-local state
```

Conceptually:

```c
typedef struct linguum_service linguum_service;
typedef struct linguum_translator linguum_translator;
typedef struct linguum_translation_result linguum_translation_result;

uint32_t linguum_translation_abi_version(void);

linguum_status linguum_translator_translate(
    linguum_translator* translator,
    const linguum_translation_request* request,
    linguum_translation_result** result
);

const char* linguum_translation_result_text(
    const linguum_translation_result* result
);

size_t linguum_translation_result_text_length(
    const linguum_translation_result* result
);

void linguum_translation_result_destroy(
    linguum_translation_result* result
);
```

The governing ownership rule is:

> **Anything created by the Linguum native ABI must be destroyed through the corresponding Linguum native ABI function.**

---

# XI. Model lifecycle

Models have multiple independent states:

```text
SUPPORTED
   model exists in this release's approved manifest

INSTALLED
   verified model exists on disk

LOADED
   native runtime has model in memory

PINNED
   model cannot currently be memory-evicted

RETAINED
   model cannot currently be disk-evicted
```

Pinning and retention are deliberately different.

For example:

```text
pin()
→ memory protection

retainOnDisk()
→ storage protection
```

Automatic eviction may never remove models that are:

```text
actively translating
pinned
retained
installing
verifying
being atomically activated
```

---

# XII. Network contract

These are strict architectural guarantees:

```text
translator()
translate()
translateBatch()
runtime/model loading from installed storage
```

**cannot make network calls.**

Network-capable operations are explicit:

```text
ensureTranslator()
models.install()
models.preload() when acquisition is requested
```

The translation runtime modules must not even depend upon networking libraries.

That makes the offline promise structural rather than merely documented.

---

# XIII. Privacy contract

The library itself performs **no user-content telemetry**.

Forbidden observability data includes:

```text
source translation text
translated text
auth tokens
arbitrary user file contents
secret-bearing URLs
native memory addresses
```

Permitted operational metrics include:

```text
language pair
input character count
duration
queue depth
model state transition
model download bytes
runtime profile
failure classification
```

Example:

```kotlin
TranslationCompleted(
    pair = LanguagePair(ES, EN),
    duration = 31.milliseconds,
    inputCharacters = 42,
)
```

rather than retaining the actual sentence.

---

# XIV. Performance contract

The validated native engine result becomes the initial reference profile:

```text
~30 ms p95
~38 ms p99
~72 lines/sec
```

but those numbers are **not universal requirements for every CPU**.

Each runtime profile gets its own baseline:

```text
windows-x64-avx2
windows-x64-fallback

macos-arm64
macos-x64

linux-x64-avx2
linux-x64-fallback
linux-arm64

android-arm64
ios-arm64
```

Two gates apply simultaneously:

```text
relative regression limit
+
absolute product floor
```

Current product ceilings remain:

```text
p95 <= 150 ms
p99 <= 250 ms
throughput >= 10 lines/sec
```

A series of small regressions therefore cannot slowly destroy the realtime capability.

Performance baselines cannot be casually regenerated by agents.

---

# XV. Agent-written-code governance

This is particularly important for this project.

An implementation agent is **never authorized merely to make CI green** by changing the rules.

Agents may not independently:

```text
lower coverage thresholds
increase performance thresholds
replace a benchmark baseline
update golden translations
disable tests
skip supported platforms
remove fuzz cases
add sanitizer suppressions
create Detekt baselines
globally suppress warnings
add dynamic dependency versions
add unapproved production dependencies
change the Firefox upstream pin
edit vendored Mozilla source directly
weaken API compatibility checks
raise OS minimum versions
remove license/provenance checks
disable dependency verification
change CODEOWNERS
bypass release workflow
silently alter the native ABI baseline
```

Changes to protected baselines require a dedicated workflow, explanation and maintainer authorization.

---

# XVI. Clean-code constraints

The approximate starting rules are:

```text
warnings as errors
Detekt baseline prohibited
mandatory formatting

cyclomatic complexity <= 10
cognitive complexity <= 12
function <= 40 logical lines
class <= 300 lines
file <= 400 lines
nesting <= 3
function parameters <= 5
constructor parameters <= 7

no wildcard imports
no meaningless magic numbers
no release TODO/FIXME
no println/System.out
no broad catch-and-ignore
no mutable global service locator
no public mutable collections
no runtime platform checks in commonMain
no native pointer leakage outside native bridge
```

Avoid vague names such as:

```text
Utils
Helpers
Common
Misc
Stuff
BaseManager
GenericManager
```

Prefer one precise responsibility per type/module.

---

# XVII. Licensing and upstream compliance

Original Linguum files:

```text
Apache-2.0
```

Mozilla-derived files:

```text
MPL-2.0
```

Vendored Mozilla source remains visibly isolated.

Release artifacts include appropriate:

```text
LICENSE
NOTICE
THIRD_PARTY_LICENSES
SBOM
UPSTREAM.json
source/provenance information
```

`UPSTREAM.json` should identify at least:

```json
{
  "repository": "mozilla/translations",
  "revision": "eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d",
  "bergamotVersion": "v0.6.0",
  "license": "MPL-2.0"
}
```

Mozilla source may never be silently copied into Apache-licensed Linguum files.

---

# XVIII. Upstream update workflow

Firefox changes its translation-engine pin:

```text
Firefox upstream checker
        ↓
detect new pin
        ↓
create compatibility PR
        ↓
fetch clean immutable source snapshot
        ↓
reapply necessary patch queue
        ↓
build every supported platform
        ↓
native/C ABI tests
        ↓
full model matrix
        ↓
golden/drift analysis
        ↓
performance comparison
        ↓
sanitizers/fuzz/stress
        ↓
license/security/SBOM
        ↓
maintainer review
        ↓
new Linguum library release
```

Never:

```text
Firefox changed
→ automatically update main
→ publish
```

---

# XIX. Release identity

A published version such as:

```text
io.linguum:translation:1.4.0
```

must be traceable to one exact identity:

```text
Git commit
Git tag
library SemVer
native ABI version
Firefox revision
Bergamot version
approved model manifest
upstream source digest
dependency locks
toolchain versions
native binaries
SBOM
artifact hashes
build workflow
provenance attestation
```

Maven Central artifacts and GitHub release artifacts must derive from that same release identity.

Official publishing occurs only through the protected canonical release workflow.

---

# XX. Stable v1 feature set

### Stable in 1.0

```text
TranslationService
Translator

plain-text translation
structured text spans
BCP-47 LanguageTag
LanguagePair
TranslationCatalog

direct supported-pair discovery

model download/install
model verification
model cache
model preload
model pinning
model unloading/removal
disk retention

local/offline inference

structured concurrency
cancellation
deadlines
backpressure
realtime supersession

batch translation

segmentation

runtime diagnostics
observable state/progress

Kotlin API
Java facade
Swift facade

testing artifact
```

### Separate/optional capability

```text
language detection
```

It must not affect known-pair translation latency.

### Experimental until separately validated

```text
alignment
quality estimation
pivot translation
other advanced Mozilla features
alternate runtimes/providers
```

---

# XXI. Final architecture

The complete intended architecture is:

```text
                         io.linguum:translation
                                  │
                     Canonical Kotlin/KMP API
                                  │
               ┌──────────────────┼─────────────────┐
               │                  │                 │
            Kotlin              Java              Swift
               │               facade             facade
               └──────────────────┬─────────────────┘
                                  │
                       TranslationService
                                  │
          ┌───────────────┬───────┼──────────┬──────────────┐
          │               │       │          │              │
      Translator       Catalog   Models   Detection*   Diagnostics
          │                         │
          │                  Model acquisition
          │                         │
          │               ┌─────────┴─────────┐
          │               │                   │
          │             Mozilla            Alternate
          │              source              source
          │               │                   │
          │               └─────────┬─────────┘
          │                         │
          │                 signed manifest
          │                         │
          │               integrity verification
          │                         │
          │                transactional store
          │                         │
          └───────────────┬─────────┘
                          │
                Loaded model LRU pool
                          │
                bounded scheduler
                          │
             private TranslationRuntime
                          │
              InProcessNativeRuntime
                          │
          ┌───────────────┴────────────────┐
          │                                │
        JNI                         Kotlin/Native
 Windows/macOS/Linux/Android          cinterop/iOS
          │                                │
          └───────────────┬────────────────┘
                          │
                  Stable Linguum C ABI
                          │
                   Mozilla adapter
                          │
                 external patch queue
                          │
         immutable Firefox-pinned snapshot
                          │
               mozilla/translations
                          │
                Bergamot AsyncService
                     1 worker/model
```

`*` Language detection is an optional independent capability.

---

# XXII. Core principles

All 76 decisions reduce to a few non-negotiable properties:

> **Linguum Translation is a first-party, provider-neutral Kotlin Multiplatform library built around the exact native translation technology Firefox maintains.**

> **Once a model is installed, translation is entirely local.**

> **Mozilla is an implementation detail, not part of the consumer API.**

> **The same library release and configuration produces deterministic behavior.**

> **Model binaries are trusted because they match an authenticated immutable release manifest—not because of where they were downloaded.**

> **Native performance remains close to the validated Firefox-native benchmark path.**

> **Kotlin, Java and Swift are intentional supported consumer experiences.**

> **Windows, macOS, Linux, Android and iOS are real tested release targets rather than nominal compile targets.**

> **The public API remains simple even though the internals are rigorously modular.**

> **Agent-written code is held to immutable architecture, correctness, compatibility, security and performance gates.**

> **No agent gets to redefine “passing” simply because the implementation failed.**

This is now sufficiently complete to be treated as the **frozen architecture specification for the implementation-planning phase**.