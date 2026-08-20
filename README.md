# Linguum Translation — Complete Codex Implementation Handoff

This package is the complete implementation contract for a standalone, public, production-grade Kotlin Multiplatform translation library.

## Product shape

```text
Kotlin / Java / Swift consumer
            │
            ▼
   io.linguum:translation
            │
   provider-neutral API
            │
   bounded scheduler + model lifecycle
            │
       stable C ABI
            │
 Firefox-pinned mozilla/translations
            │
 Bergamot AsyncService, one worker/model
```

Translation is local and offline once a model is installed. Mozilla, Bergamot, Marian, FBGEMM, RUY, Accelerate, JNI, and cinterop are implementation details and must never leak into the stable public API.

## What is already validated

The selected Windows native engine was benchmarked against Chrome's local Translator API using six paired rounds and 3,000 measured translations per engine. The current Firefox-pinned native implementation achieved approximately:

```text
p50         11.13 ms
p95         30.00 ms
p99         38.26 ms
throughput  71.74 lines/sec
```

It beat Chrome at p50, p95, and p99 in all six rounds. The complete benchmark evidence is retained under `research/evidence/`.

## What remains intentionally unproven

The implementation must still prove:

- native builds and inference on every requested non-Windows target;
- correct architecture-specific math backends;
- desktop native artifact variant resolution from one dependency;
- JNI/cinterop overhead;
- real model installation and switching;
- Android and iOS memory/thermal behavior;
- minimum OS compatibility;
- Swift facade quality;
- full release/model matrix.

Those proofs are front-loaded into M1 and later hard gates.

## Single-file edition

For tools that work best from one large context file, use:

```text
LINGUUM_TRANSLATION_COMPLETE_CODEX_HANDOFF.md
```

The structured directories remain authoritative for implementation and automated validation. The single-file edition is generated from those files for review and prompt ingestion.

## Handoff contents

- `HANDOFF_VALIDATION_REPORT.md`: package-integrity and syntax-validation evidence
- `architecture/`: frozen decisions and exact contracts
- `implementation/`: milestone, work-package, CI, release, and verification plan
- `research/`: current-source validation and known risks
- `schemas/`: machine-readable formats Codex must implement and validate
- `codex/`: initial prompt and report templates
- `scripts/`: repository bootstrap and remote checkpoint helpers
- `research/evidence/`: benchmark evidence from the validated engine-selection spike

## Repository policy

The intended primary repository is:

```text
https://github.com/StevenBuglione/linguum-translation
```

The repository is public by default because this is an Apache-2.0/MPL-2.0 library intended for Maven Central, public source compliance, and GitHub artifact attestations.

A small companion SwiftPM repository may be created in M9:

```text
https://github.com/StevenBuglione/linguum-translation-swift
```

It contains only the versioned `Package.swift`, release notes, and verification fixture for the binary XCFramework published by the primary repository.

## Non-negotiable implementation rule

No agent may redefine passing by lowering a threshold, replacing a protected baseline, changing a golden translation, removing a failing test, skipping a platform, editing vendored Mozilla files, or updating the Firefox pin outside the dedicated compatibility workflow.
