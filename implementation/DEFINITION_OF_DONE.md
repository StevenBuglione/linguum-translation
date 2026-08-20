# Definition of Done

## Work package

A work package is done only when:

- requirement/decision references are recorded;
- affected modules are classified;
- implementation and tests are complete;
- narrow gate is green;
- architecture/API/ABI/privacy/security impact is assessed;
- artifacts/hashes are recorded where applicable;
- verification report is committed;
- commit is pushed;
- remote SHA matches report;
- draft PR is updated;
- no protected gate/baseline was weakened.

## Milestone

A milestone is done only when:

- every work package is done;
- clean full milestone gate passes from a clean non-shallow checkout;
- all required platforms/artifacts exist;
- verification report contains actual command output summaries;
- no unresolved blocker contradicts the milestone promise;
- every required PR check is green and every existing review thread is resolved;
- local and hosted evidence belongs to the exact merged head SHA;
- milestone PR is merged;
- remote main contains verification report;
- current milestone advances in a dedicated verified commit.

## Library 1.0

1.0 is done only when:

### Architecture/API

- all 76 locked decisions implemented or explicitly represented as stable/experimental/optional exactly as specified;
- public API package/provider neutrality green;
- Kotlin, Java, Swift facades green;
- API/ABI/schema baselines protected;
- no internal/native/provider leakage.

### Platforms

- Windows x64, macOS arm64/x64, Linux x64/arm64, Android arm64-v8a/x86_64, iOS arm64/simulator arm64/x64 artifacts built and validated;
- minimum OS/API/glibc gates green;
- correct native backend/profile recorded;
- one-dependency/AAR/SwiftPM consumption green.

### Native

- exact Firefox-pinned source and recursive lock;
- stable C ABI major 1;
- ownership/error/thread rules green;
- sanitizers/fuzz/soak green;
- no direct upstream modifications;
- patch queue audited.

### Models

- immutable approved manifest;
- full approved pair matrix;
- transactional install/recovery;
- integrity/source abstraction;
- offline behavior;
- memory/disk LRU/pins/retention;
- atomic model switching/rollback;
- drift report.

### Runtime

- bounded scheduler;
- cancellation/deadline/supersession/backpressure;
- batch ordering/failures;
- structured spans/segmentation;
- deterministic close/resource release;
- no hidden networking/telemetry.

### Performance

- all profile absolute floors;
- relative regressions within approved limits;
- wrapper overhead measured;
- dedicated benchmark evidence;
- mobile memory/thermal evidence;
- baselines protected.

### Quality/security

- coverage/mutation thresholds;
- full CI/nightly/release gates;
- dependency locks/verification;
- no critical/high blocker;
- SBOM/provenance/attestations;
- reproducibility report;
- privacy/log redaction tests;
- source/license compliance and legal checkpoint.

### Publication

- `io.linguum` namespace verified;
- `io.linguum:translation:1.0.0` and `translation-testing` available from Maven Central;
- GitHub release/source/native/SBOM/provenance assets available;
- `LinguumTranslation` Swift package resolves exact XCFramework;
- clean public consumer tests pass;
- release identity report immutable;
- Linguum service-style fixture consumes only public API.
