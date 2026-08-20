# Testing, CI, and Zero-Regression Quality Gates

## 1. Testing layers

1. Architecture and Gradle graph tests.
2. Public API and compatibility tests.
3. Pure Kotlin example/property/invariant tests.
4. Scheduler/concurrency/deadline/cancellation tests.
5. Model manifest/parser/generator tests.
6. Transactional installer/storage/failure-injection tests.
7. C ABI unit/contract/abuse tests.
8. Native adapter integration tests.
9. JNI and Kotlin/Native cinterop tests.
10. Java and Swift facade consumer tests.
11. Platform packaging and clean consumer tests.
12. Native sanitizers and fuzzing.
13. Model compatibility and translation-drift tests.
14. Performance/memory/thermal tests.
15. Reproducible build, SBOM, license, provenance, and release tests.

## 2. Kotlin test technology

- `kotlin.test` in common tests;
- JUnit Platform for JVM;
- pinned property-testing library for generators/shrinking;
- `kotlinx-coroutines-test` for scheduler tests;
- handwritten fakes over mocking frameworks;
- Android instrumented tests for AAR/JNI/platform behavior;
- XCTest/SwiftPM tests for Apple facade/framework behavior.

## 3. Coverage policy

### High-risk deterministic modules

```text
translation-api
translation-runtime
translation-model-contracts
translation-model-management
translation-structured-text
```

Minimum:

```text
line   95%
branch 90%
```

### Platform Kotlin adapters

```text
line   90%
branch 85%
```

### Java/Swift facades

Scenario/API coverage and consumer compilation are mandatory; measured Kotlin/Java line coverage target 90% where tooling is meaningful.

### Native code

Line coverage is secondary to:

- C/C++ unit and ABI tests;
- sanitizer coverage;
- fuzzing;
- lifecycle/soak;
- platform integration;
- symbol and ownership checks.

Generated code, immutable vendored upstream, and platform boilerplate exclusions must be explicit and protected.

Repository-wide aggregate coverage may not hide a weak critical module.

## 4. Mandatory invariants

Property/invariant tests must prove:

- `LanguageTag` canonicalization is deterministic and idempotent;
- invalid BCP-47 syntax is rejected consistently;
- a syntactically valid tag does not imply catalog support;
- manifest resolution never selects an unapproved model;
- downloaded bytes never become installed before full verification;
- an observable model state is either fully usable or unavailable, never partial;
- atomic activation never mixes model generations;
- failed activation leaves prior generation active;
- active or pinned models cannot be memory-evicted;
- retained models cannot be disk-evicted;
- queue count and byte bounds are never exceeded;
- expired queued work never enters native inference;
- stale/cancelled/superseded results are never delivered;
- batch result order matches input order;
- service close eventually releases every handle/thread/lease;
- close is idempotent;
- calls after close return `ServiceClosed`;
- runtime translation modules cannot perform network access;
- observability types cannot carry translation text;
- same release/config/profile/input is deterministic;
- API and test fake satisfy the same contract suite.

## 5. Static and clean-code rules

Required:

```text
formatting
warnings as errors
Detekt no baseline
explicit API
no wildcard imports
no release TODO/FIXME
no println/System.out
no broad catch-and-ignore
no public mutable collections
no global mutable state/service locator
no reflection-based wiring
no platform checks in commonMain
no native pointer outside binding modules
no networking outside model acquisition adapters
no Mozilla types outside native adapter/upstream
```

Initial ceilings:

```text
cyclomatic complexity <= 10
cognitive complexity <= 12
function length <= 40 logical lines
class length <= 300 logical lines
file length <= 400 logical lines
nesting <= 3
function parameters <= 5
constructor parameters <= 7
```

Specific justified exceptions for generated/native glue/test fixtures are allowlisted by symbol/file/rule, never globally.

## 6. API compatibility

PR gate extracts and compares:

- Kotlin common/KLIB API;
- JVM public bytecode API;
- Java facade API;
- Objective-C generated header;
- Swift overlay public API;
- C ABI symbols/header/layout;
- persisted model/install/release schema versions.

Agents may not update baselines during normal work.

## 7. Native safety

### PR

- native unit/contract tests;
- invalid/null/destroyed handle tests;
- ASan+UBSan short suite on Linux;
- Windows native abuse/stress suite;
- cinterop/JNI smoke;
- fuzz regression corpus.

### Nightly/release

- longer ASan/UBSan;
- separate TSan profile where supported;
- coverage-guided fuzz budget;
- repeated runtime/model/translator create/destroy;
- concurrent shutdown/model switch;
- malformed/truncated config/model metadata;
- allocation failure/large input;
- memory growth/leak monitoring.

No sanitizer suppressions or fuzz corpus deletions without owner-reviewed evidence.

## 8. Model tests

### Every PR

- permanent es→en canary;
- en→es reverse canary;
- affected pair(s);
- manifest parser/hash/config tests;
- deterministic golden subset.

### Compatibility/release

- every approved direct pair;
- install→verify→load→translate→unload→remove;
- current/previous generation switch;
- full drift corpus;
- empty/truncation/language mismatch checks;
- performance subset per model architecture.

## 9. Failure injection

At minimum:

- network disconnect at every download stage;
- unsafe/unsupported range response;
- wrong content length/hash;
- decompression bomb/path traversal;
- disk full before/during install;
- process death after every transaction step;
- stale staging recovery;
- concurrent same-pair install;
- model removed externally;
- corrupt existing installation;
- load failure and rollback;
- memory pressure during active/pinned translation;
- service close during download/load/translate/batch;
- ABI mismatch/wrong native binary;
- unsupported CPU/OS/architecture;
- queue saturation/deadline/supersession races.

## 10. Performance gates

Absolute product floors:

```text
p95 <= 150 ms
p99 <= 250 ms
throughput >= 10 subtitle lines/sec
```

Relative controlled-profile gate:

```text
p50 regression <= 10%
p95 regression <= 10%
p99 regression <= 15%
throughput regression <= 10%
```

Wrapper overhead target:

```text
no-op binding p95 <= 2 ms desktop
no-op binding p99 <= 5 ms
end-to-end wrapper overhead p95 <= 3 ms where measured against same raw engine
```

A profile may have a documented target-specific threshold, but it cannot exceed the absolute product floor without owner approval.

Shared hosted runners run smoke tests only; authoritative gates use dedicated documented hardware.

## 11. Mutation testing

Nightly/release mutation testing covers:

- manifest resolution;
- hash/integrity state machine;
- installer transaction states;
- scheduler cancellation/deadline/supersession;
- LRU/pin/retention;
- failure mapping;
- LanguageTag parsing.

Surviving mutations in critical logic are blockers or require a real test/justification.

## 12. Architecture gate

`architectureCheck` verifies:

- every module declared/classified;
- allowed dependency graph;
- no cycles;
- public package allowlist;
- internal/native type leakage;
- no runtime network dependency;
- no platform API in common modules;
- no direct upstream edits;
- patch metadata/paths valid;
- protected files changed only in authorized workflow;
- minimum platform declarations unchanged;
- no unapproved target/dependency/repository.

## 13. Local gate

```bash
./gradlew verificationGate --warning-mode=fail
./scripts/verification/local-merge-gate.sh
```

The local merge gate runs from a clean, non-shallow commit and records tool versions, source SHA, locks, and artifact checksums.

## 14. Gate immutability

Agents may not:

- lower coverage;
- add a baseline;
- suppress a warning globally;
- exclude a critical source set;
- disable or ignore a test;
- relax a performance comparison;
- regenerate a golden/API/ABI baseline;
- reduce fuzz/sanitizer budgets;
- skip a platform;
- bypass dependency verification;
- change expected translations outside compatibility workflow.
