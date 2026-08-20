# Security, Privacy, and Supply-Chain Plan

## 1. Threat model

Protect against:

- malicious/corrupt model bytes;
- compromised mirror/CDN;
- decompression bombs/path traversal;
- native memory corruption;
- ABI mismatch/wrong runtime artifact;
- dependency/submodule compromise;
- release artifact substitution;
- secrets in repository/build logs;
- user translation text leakage;
- untrusted platform paths/permissions;
- concurrent process store corruption;
- unsupported CPU illegal instructions.

## 2. Runtime privacy

`translate`, `translator`, and loaded model use are offline and have no network dependency.

The library never logs/emits:

- source text;
- translated text;
- auth tokens;
- arbitrary user files;
- sensitive query strings;
- native addresses.

Privacy-safe events use lengths, language pairs, durations, state and categories only.

No telemetry endpoint exists by default.

## 3. Model trust

Trust chain:

```text
signed/attested library release
  → embedded immutable manifest + digest
  → exact artifact sizes/hashes
  → source supplies bytes
  → staged verification
  → safe decompression
  → native compatibility probe
  → atomic install/activation
```

HTTPS is transport protection, not the trust anchor.

Never accept a manifest from the download source in v1.

## 4. Native runtime trust

Every packaged runtime is bound to:

- library version;
- C ABI version;
- Firefox/Mozilla revision;
- recursive source lock;
- platform/architecture/backend;
- compiler/toolchain;
- SHA-256;
- release provenance.

The loader verifies the artifact digest and ABI before use.

## 5. Safe model extraction

- fixed expected filenames/roles from manifest;
- no archive-controlled paths;
- no `..`, absolute path, symlink, device file, or alternate stream;
- compressed and installed size limits;
- bounded streaming decompression;
- temporary files with restrictive permissions;
- atomic promotion only after complete verification;
- quarantine invalid existing installations;
- no executable permissions on model data.

## 6. Native safety

- stable C ABI;
- opaque handles;
- explicit lengths;
- UTF-8 validation;
- bounded inputs;
- exception containment;
- no cross-allocator free;
- sanitizers;
- fuzzing;
- hostile-input and lifecycle tests;
- trusted models;
- no dynamic native plugin loading.

## 7. Dependency security

- version catalog and lock files;
- Gradle verification metadata;
- recursive submodule lock;
- no dynamic versions/snapshots;
- repository allowlist;
- Dependabot/update PRs only;
- OSV/dependency review;
- CodeQL/SAST;
- license policy;
- SBOM for each release artifact family.

## 8. GitHub security settings

Enable:

- branch/ruleset protection;
- secret scanning and push protection;
- Dependabot alerts;
- dependency graph;
- private vulnerability reporting/security policy;
- required CODEOWNERS review;
- protected release environment;
- least-privilege workflow permissions;
- OIDC/provenance where supported.

## 9. Secrets

Never store:

- Maven Central tokens;
- PGP private key;
- signing passwords;
- Apple credentials;
- release environment tokens;
- model mirror credentials.

Use GitHub encrypted environment secrets with approval gates. Fork PRs never receive them.

## 10. SBOM and provenance

Generate CycloneDX SBOMs for:

- KMP/JVM artifacts;
- Android AAR/native libs;
- Apple XCFramework;
- each desktop native runtime;
- vendored/source dependency set.

Generate artifact attestations for executable/library artifacts and SBOMs in the public repository release workflow.

Provenance includes:

- source commit/tag;
- workflow identity;
- toolchain lock;
- upstream lock;
- model manifest digest;
- artifact digest.

Attestations must be verified in release validation; creation alone is insufficient.

## 11. Vulnerability response

`SECURITY.md` defines private reporting and supported versions.

Critical flow:

1. triage privately;
2. reproduce and add protected regression where safe;
3. assess upstream impact;
4. patch outside vendored tree or adopt Firefox pin update;
5. run non-skippable safety/compatibility gates;
6. publish signed advisory/release;
7. update source/provenance/SBOM;
8. do not disclose exploit details before coordinated release when inappropriate.

## 12. Security blockers

Release blocks on:

- known critical/high exploitable vulnerability;
- missing source/license compliance;
- unsigned/unattested canonical artifacts where required;
- model hash mismatch;
- sanitizer/fuzzer crash;
- unverified native runtime;
- secret in history;
- dependency verification bypass;
- direct upstream edits;
- missing security review for new native/crypto/network dependency.
