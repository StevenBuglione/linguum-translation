# Maven Central, SwiftPM, and Release Plan

## 1. Canonical identities

```text
Maven group:      io.linguum
Main artifact:    translation
Testing artifact: translation-testing
Git tag:          v<semver>
Swift product:    LinguumTranslation
```

## 2. Prerequisites

Before RC:

- public GitHub repository;
- Maven Central account;
- verified `io.linguum` namespace through domain/DNS control;
- PGP signing key and public key publication;
- Central Portal token;
- protected GitHub release environment;
- legal/MPL source-compliance review;
- dedicated performance gate availability;
- Apple runner able to build all required XCFramework slices;
- SwiftPM companion repository access.

Do not change Maven group if namespace verification is missing; release is blocked.

## 3. Publication tooling

Initial:

```text
com.vanniktech.maven.publish 0.36.0
Dokka 2.2.0
Maven Central Portal
```

Pin plugin and action versions/checksums. Run:

```text
checkSigningConfiguration
checkPomFileFor...Publication
publishToMavenLocal
```

against all public publications before remote staging.

## 4. Maven publications

`translation` publishes:

- KMP root metadata JAR;
- common/KLIB metadata;
- JVM/Android/iOS target publications as applicable;
- sources;
- Dokka/Javadoc artifacts required by Central;
- Gradle Module Metadata;
- POM with Apache-2.0 original license and bundled MPL notice/reference;
- dependencies on internal target/platform publications.

`translation-testing` publishes corresponding KMP/testing variants without native engines or real models.

Internal native/platform publications use the same version and are built only by canonical workflow.

## 5. POM metadata

Required:

```text
name
clear description
project URL
inception year
developer/owner
Apache-2.0 license
SCM HTTPS/connection/developerConnection
issue tracker
```

NOTICE/third-party docs identify Mozilla/MPL components and source location.

## 6. GitHub release assets

```text
Maven publication bundle/report
LinguumTranslation.xcframework.zip
Swift checksum
platform native archives
source JARs/archive
Mozilla corresponding source archive
UPSTREAM.json
UPSTREAM_LOCK.json
PATCHES.yaml
approved-models.json + digest
SBOMs
checksums
provenance/attestation instructions
benchmark/drift/release verification reports
CHANGELOG/release notes
```

## 7. SwiftPM

The primary release uploads XCFramework ZIP and checksum.

The companion `linguum-translation-swift` repository receives a commit/tag with `Package.swift` referencing the immutable GitHub release URL and checksum.

The release workflow opens/updates it through a protected token/environment and runs a clean Swift package consumer before publication completion.

## 8. Release workflow phases

### Candidate

- validate version/tag/commit cleanliness;
- full clean gate;
- full model/platform/performance/security/reproducibility;
- build unsigned reproducible artifacts;
- independent rebuild/digest comparison;
- create SBOM/provenance;
- sign Maven publication;
- stage Central deployment;
- create draft GitHub release;
- owner approval.

### Publish

- publish/release Central deployment;
- publish GitHub release and attestations;
- push SwiftPM manifest/tag;
- verify artifacts from public endpoints;
- run clean Kotlin/Java/Android/Swift consumers;
- write immutable release report.

## 9. Versioning

Semantic Versioning:

- patch: compatible bug/security/performance fixes with no behavior/model drift unless documented compatible correction;
- minor: additive stable APIs, experimental changes, approved model/runtime upgrade with drift report;
- major: breaking stable API/ABI/semantic changes.

Native ABI version is independent but a breaking native contract implies appropriate library major impact.

## 10. Release candidates

At least `1.0.0-rc.1` before 1.0.

RC must be consumed by the clean Linguum service fixture and Swift/Android/iOS/desktop examples.

No forced calendar cadence. Release when a verified change warrants it.

## 11. Reproducibility

- deterministic archives/timestamps/order;
- Gradle Module Metadata without unique build identifier;
- locked toolchains/dependencies/upstream/model manifest;
- compare independent unsigned builds where possible;
- signing envelopes may differ, but underlying executable/package content digest is recorded and compared;
- Maven/GitHub/Swift artifacts share one release identity.

## 12. Post-publication verification

Download from public Maven Central/GitHub/SwiftPM endpoints—not build workspace—and verify:

- PGP signatures/checksums;
- provenance/attestations;
- SBOM presence;
- source/license assets;
- correct native runtime per platform;
- ABI/runtime info;
- canary translation;
- no hidden model/network behavior;
- exact version alignment.
