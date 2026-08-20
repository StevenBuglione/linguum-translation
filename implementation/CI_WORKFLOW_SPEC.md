# GitHub Actions and Required Check Specification

## 1. General rules

- Use only approved official actions unless a dependency approval record exists.
- Pin actions by full commit SHA, with release tag in a comment.
- Use least-privilege `permissions`.
- No untrusted pull-request code receives publishing/signing secrets.
- Release secrets live in protected GitHub environments.
- Build artifacts are checksummed and have short retention outside releases.
- Every workflow verifies Gradle wrapper and dependency metadata.

## 2. Workflows

```text
.github/workflows/pr.yml
.github/workflows/native-safety.yml
.github/workflows/nightly.yml
.github/workflows/upstream-firefox-check.yml
.github/workflows/upstream-firefox-compatibility.yml
.github/workflows/performance.yml
.github/workflows/release.yml
.github/workflows/codeql.yml
.github/workflows/dependency-review.yml
```

## 3. Required PR check names

Keep these names stable for branch protection:

```text
PR / Architecture and protected files
PR / Formatting, compiler, Detekt
PR / API and ABI compatibility
PR / Kotlin common and JVM tests
PR / Windows native and JVM integration
PR / Linux x64 native and JVM integration
PR / macOS native and JVM integration
PR / Android build and emulator integration
PR / iOS build and simulator integration
PR / Consumer fixtures Kotlin and Java
PR / Consumer fixture Swift
PR / Native safety smoke
PR / Model manifest and canary pairs
PR / License, dependency, SBOM smoke
PR / Artifact integrity and publication smoke
```

Every check always reports a result. Before a module is introduced, the check validates absence/architecture state rather than disappearing.

## 4. `pr.yml`

### Architecture/static job — Ubuntu

Runs:

```text
wrapper validation
protected-file check
architectureCheck
format check
compiler warnings as errors
Detekt no baseline
API validation
schema validation
dependency lock/verification
secret scan
```

### Common/JVM tests — Ubuntu

Runs common, runtime, model, testing artifact, Java facade, and fixture tests plus coverage thresholds.

### Windows

Runs:

- native Windows build for affected profiles;
- C ABI smoke;
- JVM/JNI integration;
- Windows consumer fixture;
- artifact loader/CPU selection tests;
- package checks.

### Linux x64

Use Ubuntu 22.04/glibc 2.35 baseline container/runner for native output. Run native ABI, JVM integration, ASan/UBSan short suite, and symbol/GLIBC checks.

### macOS

Build/run macOS arm64 on Apple Silicon runner; build/validate x64 artifact and run on Intel scheduled/release runner where available. Build Apple framework inputs.

### Android

Build Android KMP/AAR, arm64 and x86_64 native code. Run x86_64 emulator integration at configured API. Physical arm64 is nightly/release unless dedicated runner exists.

### iOS

Build iosArm64/iosSimulatorArm64/iosX64 framework slices on macOS. Run simulator arm64 tests and Swift consumer fixture. Device and Intel simulator are scheduled/release tiers.

## 5. `native-safety.yml`

PR-triggered when C/C++/ABI/build files change.

Jobs:

- Linux ASan+UBSan;
- Linux TSan separate configuration where compatible;
- Windows native abuse suite;
- macOS sanitizer smoke;
- fuzz regression corpus;
- ABI symbol/layout diff.

## 6. `nightly.yml`

Scheduled and manual:

- full all-platform build matrix;
- longer sanitizer/soak;
- bounded fuzz campaign;
- all approved model pairs where runners/storage permit;
- dependency/security scan;
- minimum OS/API compatibility tiers;
- native artifact reproducibility comparison;
- model store failure/recovery suite;
- memory growth and mobile thermal smoke;
- docs link/sample validation.

Nightly failures open/refresh an issue using the GitHub CLI; they never silently become allowed failures.

## 7. Upstream checker

`upstream-firefox-check.yml` reads current Firefox pin weekly. On change it opens a draft PR scaffold using `gh` and includes old/new metadata. It does not merge or publish.

`upstream-firefox-compatibility.yml` is manually dispatched or PR-labeled by the owner and performs the full protected update workflow.

## 8. Performance workflow

Hosted CI performs non-authoritative smoke. Dedicated self-hosted/profiled runners perform blocking baseline comparison.

The workflow:

- verifies machine profile identity;
- verifies no thermal/power/session contamination;
- uses frozen corpus/model/runtime profile;
- runs balanced repetitions;
- compares approved baseline;
- uploads raw JSON and report;
- may not write a new baseline.

Baseline update uses a separate owner-approved workflow/environment.

## 9. Release workflow

Trigger:

- `workflow_dispatch` with version and commit/tag candidate;
- optionally protected version tag after candidate validation.

Stages:

1. clean source/decision/protected-file validation;
2. full tests/coverage/API/ABI;
3. full native build matrix;
4. full approved model matrix;
5. performance/reproducibility/security/license gates;
6. build Maven/AAR/XCFramework/source/docs/SBOM artifacts;
7. independent artifact identity/hash verification;
8. sign Maven publications;
9. generate GitHub artifact attestations for executable/library artifacts and SBOM where repository plan supports it;
10. create draft GitHub release;
11. stage Maven Central deployment;
12. protected `release-production` environment approval;
13. publish Maven Central deployment and GitHub release;
14. update SwiftPM manifest repo/release;
15. post-publication clean consumer verification;
16. write immutable release verification report.

No automatic release from arbitrary main commits.

## 10. Security workflows

- CodeQL for C/C++ and Java/Kotlin where supported;
- GitHub dependency review on PRs;
- Dependabot/Renovate only opens PRs, never auto-merges;
- secret scanning and push protection enabled;
- OSV/dependency/license scans;
- CycloneDX SBOM;
- native dependency/submodule inventory.

## 11. Branch rules

Required:

- PR before merge;
- required checks listed above;
- current branch up to date where practical;
- CODEOWNERS review for protected areas;
- all conversations resolved;
- no force push/delete;
- no bypass;
- squash or linear merge policy;
- release tags protected/immutable.
