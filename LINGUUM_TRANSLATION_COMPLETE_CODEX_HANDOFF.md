# Linguum Translation — Complete Codex Implementation Handoff
**Generated:** 2026-08-20T05:21:10.711856+00:00  
**Purpose:** single-file, reviewable rendering of the structured handoff package. The individual files named below remain the implementation source files.  
**Execution rule:** begin with `codex/INITIAL_CODEX_PROMPT.md` and execute M0 only.

## Included source files
1. `START_HERE.md`
2. `README.md`
3. `AGENTS.md`
4. `CODEX_EXECUTION_CONTRACT.md`
5. `HANDOFF_VALIDATION_REPORT.md`
6. `architecture/LOCKED_DECISIONS.md`
7. `research/VALIDATION_REPORT.md`
8. `research/KNOWN_RISKS_AND_BLOCKERS.md`
9. `research/SOURCE_REGISTER.md`
10. `research/evidence/FINAL_BENCHMARK_REPORT.md`
11. `research/evidence/current-mozilla-native-build.json`
12. `research/evidence/current-mozilla-source-manifest.txt`
13. `architecture/ARCHITECTURE_CONSTITUTION.yaml`
14. `architecture/MODULE_CATALOG.yaml`
15. `architecture/REPOSITORY_LAYOUT.md`
16. `architecture/MODULE_DEPENDENCY_GRAPH.md`
17. `architecture/PUBLIC_API_SPEC.md`
18. `architecture/JAVA_SWIFT_FACADE_SPEC.md`
19. `architecture/NATIVE_ABI_SPEC.md`
20. `architecture/MODEL_MANIFEST_SPEC.md`
21. `architecture/UPSTREAM_FIREFOX_POLICY.md`
22. `architecture/PLATFORM_SUPPORT_MATRIX.md`
23. `architecture/LICENSING_BOUNDARY.md`
24. `implementation/TECHNICAL_IMPLEMENTATION_PLAN.md`
25. `implementation/MILESTONE_ROADMAP.md`
26. `implementation/WORK_PACKAGES.md`
27. `implementation/GIT_REMOTE_CHECKPOINT_PLAN.md`
28. `implementation/TEST_CI_AND_QUALITY_GATES.md`
29. `implementation/CI_WORKFLOW_SPEC.md`
30. `implementation/PERFORMANCE_VALIDATION.md`
31. `implementation/SECURITY_SUPPLY_CHAIN.md`
32. `implementation/PUBLISHING_RELEASE.md`
33. `implementation/DEFINITION_OF_DONE.md`
34. `schemas/model-manifest.schema.json`
35. `schemas/upstream-lock.schema.json`
36. `schemas/patch-metadata.schema.json`
37. `schemas/release-identity.schema.json`
38. `codex/INITIAL_CODEX_PROMPT.md`
39. `codex/WORK_PACKAGE_TEMPLATE.md`
40. `codex/VERIFICATION_REPORT_TEMPLATE.md`
41. `templates/PULL_REQUEST_TEMPLATE.md`
42. `templates/ADR_TEMPLATE.md`
43. `templates/BLOCKER_REPORT_TEMPLATE.md`
44. `scripts/bootstrap-repository.sh`
45. `scripts/bootstrap-repository.ps1`
46. `scripts/checkpoint-push.sh`
47. `scripts/checkpoint-push.ps1`
48. `scripts/verify-remote-sha.sh`
49. `scripts/verify-remote-sha.ps1`

---

<!-- BEGIN FILE: START_HERE.md -->

# Source file: `START_HERE.md`

# START HERE — Linguum Translation Codex Handoff

## Mission

Build and publish a production-grade Kotlin Multiplatform library named **Linguum Translation** that exposes a provider-neutral translation API while using the exact native Mozilla translation implementation pinned by Firefox behind a stable Linguum-owned C ABI.

The library must support:

- Windows x64
- macOS arm64 and x64
- Linux x64 and arm64
- Android arm64-v8a and x86_64 emulator
- iOS arm64, arm64 simulator, and x86_64 simulator

Canonical consumer coordinates:

```text
io.linguum:translation:<version>
io.linguum:translation-testing:<version>
```

Canonical Kotlin package:

```text
io.linguum.translation
```

## Authority

The file `architecture/LOCKED_DECISIONS.md` is the product and architecture source of truth. It contains 76 owner-approved decisions. Codex is an implementer and verifier, not an architect. Codex may not replace, reinterpret away, or weaken those decisions.

This handoff adds researched implementation detail, milestone order, executable gates, and known-risk handling. Where a current external toolchain conflicts with a locked decision, Codex must use the blocker protocol rather than silently changing the architecture.

## Mandatory reading order

1. `START_HERE.md`
2. `AGENTS.md`
3. `CODEX_EXECUTION_CONTRACT.md`
4. `architecture/LOCKED_DECISIONS.md`
5. `research/VALIDATION_REPORT.md`
6. `research/KNOWN_RISKS_AND_BLOCKERS.md`
7. `architecture/ARCHITECTURE_CONSTITUTION.yaml`
8. `architecture/MODULE_CATALOG.yaml`
9. `architecture/REPOSITORY_LAYOUT.md`
10. `architecture/MODULE_DEPENDENCY_GRAPH.md`
11. `architecture/PUBLIC_API_SPEC.md`
12. `architecture/JAVA_SWIFT_FACADE_SPEC.md`
13. `architecture/NATIVE_ABI_SPEC.md`
14. `architecture/MODEL_MANIFEST_SPEC.md`
15. `architecture/UPSTREAM_FIREFOX_POLICY.md`
16. `architecture/PLATFORM_SUPPORT_MATRIX.md`
17. `architecture/LICENSING_BOUNDARY.md`
18. `implementation/TECHNICAL_IMPLEMENTATION_PLAN.md`
19. `implementation/MILESTONE_ROADMAP.md`
20. `implementation/WORK_PACKAGES.md`
21. `implementation/GIT_REMOTE_CHECKPOINT_PLAN.md`
22. `implementation/TEST_CI_AND_QUALITY_GATES.md`
23. `implementation/CI_WORKFLOW_SPEC.md`
24. `implementation/PERFORMANCE_VALIDATION.md`
25. `implementation/SECURITY_SUPPLY_CHAIN.md`
26. `implementation/PUBLISHING_RELEASE.md`
27. `implementation/DEFINITION_OF_DONE.md`
28. `HANDOFF_VALIDATION_REPORT.md`
29. `codex/INITIAL_CODEX_PROMPT.md`

## First action

Execute **M0 only**. M0 creates the public GitHub repository, pushes the handoff and repository constitution immediately, establishes the Gradle/toolchain skeleton, and installs the protected remote workflow.

Do not start public API implementation in M0.

The exact initial repository command is:

```bash
gh auth status
gh repo create StevenBuglione/linguum-translation \
  --public \
  --source=. \
  --remote=origin \
  --push \
  --description "Firefox-compatible native translation for Kotlin Multiplatform"
```

If the owner explicitly requires a private implementation phase, replace `--public` with `--private`, but record that artifact attestations on GitHub Free/Pro/Team are available only for public repositories and that the repository must become public before the first release candidate unless GitHub Enterprise Cloud is available.

## Remote-save invariant

No completed vertical slice may exist only on a local machine.

After every verified work-package checkpoint:

1. inspect `git status --short`;
2. run the work package's required narrow gate;
3. stage only intentional paths with `git add -- <paths>`;
4. commit with the work-package ID;
5. push the branch;
6. verify the remote SHA;
7. update the draft pull request and verification report.

Codex must never work more than one clean, committed checkpoint ahead of the remote branch.

## Hard sequencing rule

The first technical milestone after repository foundation is **M1 — platform and packaging feasibility**.

M1 must prove all of the following before stable API work begins:

- the exact Firefox-pinned native source builds and translates a canary sentence on every required target;
- the stable C ABI can be linked and invoked on every target;
- Android AAR and Apple XCFramework packaging work;
- a plain Gradle consumer can resolve the correct desktop native runtime from the one public dependency, or the work stops with a documented architecture blocker;
- the Objective-C framework plus handwritten Swift overlay produces an idiomatic Swift API without relying on Kotlin Swift export, which is Alpha;
- x64 fallback and ARM math backends are real, tested implementations rather than assumptions.

A failed M1 proof is a good outcome if it exposes an invalid assumption early. Codex must not build around an unproven platform promise.

## Definition of truthful progress

A claim is complete only when its command output, tests, hashes, artifacts, and remote commit SHA are recorded in a work-package verification report.

Do not use confidence language in place of evidence.

<!-- END FILE: START_HERE.md -->

---

<!-- BEGIN FILE: README.md -->

# Source file: `README.md`

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

<!-- END FILE: README.md -->

---

<!-- BEGIN FILE: AGENTS.md -->

# Source file: `AGENTS.md`

# AGENTS.md — Linguum Translation Agent Constitution

This file governs every coding-agent task in the Linguum Translation repository.

## 1. Role and authority

Codex and other coding agents are implementers, verifiers, and evidence producers. They are not product owners and may not redesign the library.

The architecture is already chosen in `architecture/LOCKED_DECISIONS.md`.

Agents must:

- work only in the current milestone and work package;
- read the relevant contracts before editing code;
- preserve package/module boundaries;
- implement the smallest complete vertical slice;
- add tests before claiming completion;
- run the documented narrow and clean gates;
- create real artifacts where the work package requires them;
- write a verification report with commands and outputs;
- push every verified checkpoint to GitHub;
- stop and report blockers rather than inventing exceptions.

## 2. Protected files and baselines

Normal implementation work may not modify:

- `architecture/LOCKED_DECISIONS.md`
- `architecture/ARCHITECTURE_CONSTITUTION.yaml`
- `architecture/MODULE_CATALOG.yaml`
- accepted ADRs
- API compatibility baselines
- native ABI baselines
- serialized schema baselines
- approved model manifests outside the upstream/model update workflow
- performance baselines outside the performance-baseline workflow
- golden translation corpora outside the compatibility-drift workflow
- coverage thresholds
- sanitizer/fuzzer budgets
- minimum OS support declarations
- dependency verification policy
- CODEOWNERS
- release provenance rules
- completed milestone acceptance tests

The owner must explicitly authorize an architecture change before those items are changed.

## 3. Prohibited shortcuts

Agents must not:

- edit `native/upstream/mozilla-translations/**` directly;
- use arbitrary `mozilla/translations/main` instead of the Firefox pin;
- silently replace native inference with WASM or a cloud service;
- leak Mozilla/Bergamot/Marian/FBGEMM types into public APIs;
- expose native pointers, JNI handles, C++ types, or platform context types in common public contracts;
- add a new runtime provider or alternate engine without authorization;
- add a production dependency merely for convenience;
- use dynamic dependency versions, snapshots, or unapproved repositories;
- introduce global mutable state or a service locator;
- perform network access from translation/runtime modules;
- log or emit source/translated user text;
- catch and ignore native/runtime failures;
- use `@Suppress("ALL")`, a Detekt baseline, global warning suppressions, ignored tests, or weaker assertions;
- delete a failing regression or fuzz corpus input;
- regenerate a performance/API/ABI/golden baseline to make CI pass;
- skip a required platform because a runner is inconvenient;
- raise an OS minimum silently;
- force-push or rewrite pushed history;
- use `git add .`, `git add -A`, or `git add --all`;
- claim completion from unit tests alone;
- proceed past a hard gate that is not green.

## 4. Work-package procedure

For every work package:

1. Read the requirement and decision references.
2. Create/update the traceability row.
3. List affected modules and allowed dependency edges.
4. Create or update tests first where practical.
5. Implement one vertical slice.
6. Run the narrow gate.
7. Inspect the diff and generated artifacts.
8. Stage only intentional paths.
9. Commit using `<MILESTONE>-<WP>: <imperative summary>`.
10. Push immediately to the remote branch.
11. Verify local and remote SHAs match.
12. Update the draft PR and work-package verification report.
13. At milestone end, run the full clean milestone gate.
14. Merge only through a protected pull request after every required check is green.

## 5. Remote checkpoint rule

No completed slice may remain local.

A branch may contain multiple pushed commits, but each pushed commit must:

- contain no secrets;
- be internally coherent;
- compile or pass the narrow gate for the affected scope;
- state incomplete work honestly when it is a scaffold checkpoint;
- never weaken main-branch rules.

After each push:

```bash
LOCAL_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git ls-remote origin "refs/heads/$(git branch --show-current)" | awk '{print $1}')"
test "$LOCAL_SHA" = "$REMOTE_SHA"
```

## 6. Blocker protocol

Stop when:

- a locked decision conflicts with a current toolchain;
- a target cannot build or execute the exact Firefox-pinned native source;
- plain one-dependency native runtime selection cannot be proven;
- a supported platform requires a forbidden fork or incompatible license;
- a test passes only after weakening its requirement;
- the `io.linguum` Maven namespace cannot be verified;
- a platform runner or signing/release prerequisite is missing;
- an upstream patch would be required without maintainer authorization;
- an invariant cannot be implemented safely in-process.

Report exactly:

```text
BLOCKER TYPE:
WORK PACKAGE:
LOCKED DECISION:
OBSERVED CONFLICT:
REPRODUCTION COMMANDS:
EVIDENCE:
SAFE WORK THAT CAN CONTINUE:
SMALLEST OWNER DECISION REQUIRED:
```

## 7. Dependency policy

- Add dependencies only through `gradle/libs.versions.toml`.
- Pin versions and checksums.
- Update locks and verification metadata intentionally.
- Prefer official, actively maintained, permissively licensed dependencies.
- Keep networking dependencies only in model-acquisition platform adapters.
- Keep logging backends out of production library artifacts.
- Do not add DI, reflection, utility, retry, result-wrapper, or service-locator libraries.
- Test-only dependencies remain pinned and scanned.
- A new production dependency requires an ADR or dependency-approval record.

## 8. Native safety policy

- C ABI only; no C++ ABI exposure.
- Every allocation has a matching same-library destroy function.
- No exceptions cross the C boundary.
- Every public ABI struct has a `struct_size` field and reserved space.
- Invalid handles and malformed UTF-8 must fail safely.
- Sanitizer/fuzzer findings are blockers.
- Platform-specific source fixes belong in the external patch queue, never the vendored tree.

## 9. Evidence standard

Every completion report must identify:

- source commit and remote SHA;
- affected modules;
- architecture result;
- commands executed and exit codes;
- test and coverage results;
- native build/runtime profile;
- model and upstream hashes where relevant;
- artifacts and checksums;
- compatibility impact;
- privacy/security impact;
- known limitations and blockers.

Do not use screenshots in place of executable evidence.

<!-- END FILE: AGENTS.md -->

---

<!-- BEGIN FILE: CODEX_EXECUTION_CONTRACT.md -->

# Source file: `CODEX_EXECUTION_CONTRACT.md`

# Codex Execution Contract — Linguum Translation

## Objective

Implement the frozen Linguum Translation architecture incrementally, prove each risky assumption before building on it, and preserve all verified work on GitHub through frequent clean checkpoint pushes.

## Milestone lock

`architecture/current-milestone.txt` records the active milestone. Codex may work only in that milestone plus completed earlier milestones.

Advancing the milestone requires:

- all milestone work packages complete;
- the clean milestone gate green;
- all artifacts reproducible from a clean checkout;
- a milestone verification report committed and pushed;
- a protected PR merged;
- `architecture/current-milestone.txt` advanced in a dedicated commit.

## Repository creation contract

M0-WP01 must:

1. create the local repository from this handoff;
2. make an initial constitution-only commit;
3. create `StevenBuglione/linguum-translation` on GitHub;
4. push `main` immediately;
5. verify the remote SHA;
6. configure branch protection/rulesets after the first CI check names exist;
7. create the first milestone branch and draft PR.

Default visibility is public. If private visibility is explicitly selected, the release gate records that public artifact attestations are unavailable on GitHub Free/Pro/Team for private repositories and blocks RC publication until the provenance strategy is satisfied.

## Commit and push contract

- Never commit generated secrets, credentials, signing keys, model payloads, build directories, or local tool caches.
- Never force-push.
- Never rebase already reviewed/pushed milestone history unless the maintainer explicitly authorizes it.
- Prefer small commits aligned to one traceability slice.
- Push after every verified slice.
- A local branch must never be more than one verified commit ahead of origin.
- Create a draft PR immediately after the first branch push.
- Keep the PR body current with work-package checkboxes and evidence links.

## Branch and commit naming

Branches:

```text
codex/M0-WP01-repository-foundation
codex/M1-WP03-windows-native-canary
codex/M6-WP02-jvm-jni-runtime
```

Commits:

```text
M0-WP01: establish repository constitution
M1-WP03: prove Windows AVX2 native canary
M5-WP04: implement transactional model promotion
```

## Change classes

### Normal implementation

May change code, tests, fixtures, generated outputs, docs, and verification reports inside the active work package.

### Architecture change

Requires an ADR, owner authorization, architecture/schema/test updates, migration impact, and full clean verification. It may not be hidden in feature work.

### Upstream compatibility update

May change the Firefox pin, immutable snapshot, recursive source lock, patch queue, approved model manifest, drift report, and performance baseline only through the dedicated upstream workflow.

### Release-baseline update

May update API, ABI, schema, model, or performance baselines only through a release/compatibility work package with before/after evidence and maintainer approval.

## Pull request requirements

Every PR must contain:

- milestone and work-package IDs;
- linked decisions/requirements;
- affected module classifications;
- dependency-edge proof;
- API/ABI/schema impact;
- model/upstream impact;
- privacy/security impact;
- platform impact;
- exact commands and results;
- coverage/performance impact where applicable;
- artifacts and checksums;
- rollback notes;
- explicit statement that no protected gate or baseline was weakened;
- local and remote head SHA.

## Self-check before completion

```text
[ ] I worked only in the active work package.
[ ] Every changed module is classified.
[ ] Every new dependency is approved and pinned.
[ ] No provider/native/platform detail leaked into the public API.
[ ] No translation content enters logs or telemetry.
[ ] Runtime translation remains network-independent.
[ ] I did not edit vendored Mozilla source directly.
[ ] I did not change a protected baseline to fit the implementation.
[ ] I ran the documented narrow and clean gates.
[ ] I pushed every verified checkpoint.
[ ] The remote branch SHA matches the verification report.
[ ] I recorded blockers and limitations factually.
```

<!-- END FILE: CODEX_EXECUTION_CONTRACT.md -->

---

<!-- BEGIN FILE: HANDOFF_VALIDATION_REPORT.md -->

# Source file: `HANDOFF_VALIDATION_REPORT.md`

# Handoff Validation Report

**Validated:** 2026-08-20  
**Artifact:** Linguum Translation Complete Codex Implementation Handoff

## Source preservation

The frozen architecture source copied to:

```text
architecture/LOCKED_DECISIONS.md
```

is byte-for-byte identical to the user-provided source file.

```text
SHA-256:
ad38429d30cdbdee2d432235f322d40ce97b52b80c2501dcc4f253edbac4e4f1
```

## Structural validation

Validated presence of the required root documents, frozen architecture, researched validation, machine-readable architecture/module catalog, public API specification, native ABI specification, model-manifest specification, milestone/work-package plan, Git checkpoint policy, CI/security/release plans, Codex prompt/templates, repository scripts, schemas, and retained benchmark evidence.

The package includes:

- structured source files for implementation and automation;
- a generated single-file rendering: `LINGUUM_TRANSLATION_COMPLETE_CODEX_HANDOFF.md`;
- retained benchmark evidence under `research/evidence/`;
- bootstrap/checkpoint scripts for Bash and PowerShell;
- a SHA-256 manifest generated after this validation.

## Parsing and syntax validation

Passed:

```text
JSON parsing:
  schemas/model-manifest.schema.json
  schemas/upstream-lock.schema.json
  schemas/patch-metadata.schema.json
  schemas/release-identity.schema.json
  research/evidence/current-mozilla-native-build.json

YAML parsing:
  architecture/ARCHITECTURE_CONSTITUTION.yaml
  architecture/MODULE_CATALOG.yaml

Bash syntax:
  scripts/bootstrap-repository.sh
  scripts/checkpoint-push.sh
  scripts/verify-remote-sha.sh
```

The execution container did not contain PowerShell, so the `.ps1` files received textual and delimiter-balance validation rather than execution by the PowerShell parser. M0 requires running the PowerShell scripts on Windows before they are treated as validated automation.

## Research/implementation boundary

The handoff deliberately distinguishes:

- frozen owner-approved decisions;
- current externally validated facts;
- implementation interpretations required to make the decisions executable;
- still-unproven platform/package assumptions.

The first technical hard gate is M1 platform and packaging feasibility. Failure to prove a target or the one-dependency native-resolution contract must produce a blocker rather than a hidden compromise.

## Remote repository status

No GitHub repository was created during handoff generation. The package contains the exact Codex instructions and scripts to create:

```text
https://github.com/StevenBuglione/linguum-translation
```

as the first M0 action and to push every verified checkpoint thereafter.

## Validation decision

```text
Frozen source preserved:                PASS
Structured handoff completeness:        PASS
JSON schemas parse:                      PASS
YAML architecture documents parse:      PASS
Bash helper scripts parse:               PASS
PowerShell execution validation:         DEFERRED TO WINDOWS M0
Benchmark evidence retained:             PASS
Single-file handoff generated:           PASS
Ready to give to Codex for M0:            YES
Ready to claim library implementation:    NO — implementation has not started
```

<!-- END FILE: HANDOFF_VALIDATION_REPORT.md -->

---

<!-- BEGIN FILE: architecture/LOCKED_DECISIONS.md -->

# Source file: `architecture/LOCKED_DECISIONS.md`

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

<!-- END FILE: architecture/LOCKED_DECISIONS.md -->

---

<!-- BEGIN FILE: research/VALIDATION_REPORT.md -->

# Source file: `research/VALIDATION_REPORT.md`

# Research and Validation Report

**Validated:** 2026-08-20  
**Purpose:** distinguish owner-locked design from current external facts, implementation interpretations, and still-unproven assumptions.

## 1. Source-of-truth decisions

`architecture/LOCKED_DECISIONS.md` contains the 76 owner-approved decisions. This report does not replace them.

The implementation is provider-neutral, local/offline after model installation, cross-platform, and built around a Linguum-owned stable C ABI in front of Firefox-maintained Mozilla inference.

## 2. Firefox/Mozilla engine validation

Current Firefox source metadata pins its translation inference dependency to:

```text
repository: mozilla/translations
revision:   eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d
release:    v0.6.0
license:    MPL-2.0
```

The pinned Mozilla source includes native inference code and the current `AsyncService` API. Its native build script enables CPU inference and FBGEMM and disables CUDA for the CPU build. The selected Windows benchmark used `AsyncService`, `numWorkers=1`, and `cacheSize=0`.

Validated primary sources:

- Firefox pin metadata: `toolkit/components/translations/bergamot-translator/moz.yaml`
- Mozilla inference source: `mozilla/translations/inference/`
- service API: `inference/src/translator/service.h`
- native CLI example: `inference/src/app/translator_cli.cpp`
- native build script: `inference/scripts/build.py`
- engine version: `inference/BERGAMOT_VERSION`

The implementation must never use the archived `mozilla/bergamot-translator` repository or arbitrary `mozilla/translations/main` as its production source.

## 3. Translation performance validation

The retained benchmark evidence demonstrates that the current Firefox-pinned native implementation is viable and faster than Chrome's local Translator API on the validated Windows machine.

Reference result:

```text
current Mozilla native p50:        11.13 ms
current Mozilla native p95:        30.00 ms
current Mozilla native p99:        38.26 ms
current Mozilla native throughput: 71.74 lines/sec
```

It beat Chrome at p50, p95, and p99 in all six paired rounds.

Evidence:

- `research/evidence/FINAL_BENCHMARK_REPORT.md`
- `research/evidence/current-mozilla-native-build.json`
- `research/evidence/current-mozilla-source-manifest.txt`
- `research/evidence/translation-benchmark-validation.zip`

This validates engine selection on the measured Windows profile. It does not validate wrapper overhead, other architectures, thermal behavior, model switching, or concurrent video playback.

## 4. Toolchain validation

Pin the initial implementation toolchain to the highest stable combination fully supported by Kotlin 2.4.10 rather than copying the Linguum monorepo's current JDK 25/Kotlin RC stack.

Initial lock:

```text
Kotlin                  2.4.10
Gradle wrapper           9.5.0
Gradle runtime JDK       21 LTS
JVM bytecode target      17
kotlinx.coroutines       1.11.0
Android Gradle Plugin    9.1.x, initially 9.1.1 with M0 compatibility proof
Android NDK              28.2.13676358
Android Build Tools      36.0.0
Dokka                    2.2.0
Vanniktech publish       0.36.0
Detekt                   2.0.0-alpha.6, tooling-only and explicitly pinned
Kover                    0.9.9
```

Kotlin 2.4.0–2.4.10 documents full Gradle compatibility through 9.5.0 and AGP compatibility through the 9.1 line. AGP 9.1.1 documents NDK 28.2.13676358 and JDK 17. The build itself runs on JDK 21 and emits Java 17 bytecode.

M0 must run a toolchain compatibility proof and fail on warnings indicating unsupported combinations. A patch downgrade within the AGP 9.1 line is permitted only if the compatibility report demonstrates the need; it is a toolchain lock correction, not an architecture change.

## 5. Kotlin/Apple integration validation

Kotlin Swift export is currently Alpha. Therefore it is not the stable v1 Swift surface.

The stable Apple strategy is:

```text
KMP common API
  → Objective-C-compatible Kotlin/Native framework
  → umbrella XCFramework
  → handwritten thin Swift overlay
  → Swift Package Manager binary package
```

The Swift overlay provides idiomatic `async throws`, names, errors, and state observation while delegating all semantics to the canonical KMP API.

A separate small SwiftPM manifest repository is recommended for scaling and versioning:

```text
StevenBuglione/linguum-translation-swift
```

The primary library repository remains the source and release authority.

## 6. Desktop target interpretation

Windows, macOS, and Linux support is delivered through the KMP/JVM target plus JNI and platform C++ runtimes.

Do not create Kotlin/Native desktop public targets merely to claim desktop support. This avoids tying desktop consumers to deprecated or lower-tier Kotlin/Native targets and matches the intended Linguum desktop service usage.

Desktop matrix:

```text
JVM target, Java 17 bytecode
  Windows x64  → JNI → DLL
  macOS arm64  → JNI → dylib
  macOS x64    → JNI → dylib
  Linux x64    → JNI → .so
  Linux arm64  → JNI → .so
```

Android uses the Android KMP library target and NDK/JNI. iOS uses Kotlin/Native cinterop and an XCFramework.

## 7. Kotlin target-support caveats

Current Kotlin/Native target tiers matter:

- `iosArm64` and `iosSimulatorArm64` are strongly supported.
- `linuxArm64` is a lower support tier and requires our own runtime validation.
- `iosX64` is Tier 3 and must be treated as a compatibility target with scheduled real-run validation where an Intel simulator host is available.
- `macosX64` Kotlin/Native is deprecated, but desktop macOS x64 is delivered by JVM/JNI, so that deprecation does not remove the library's macOS Intel desktop support.

Codex must not promise stronger Kotlin/Native guarantees than the toolchain provides without independent evidence.

## 8. Architecture-specific native backends

The Windows benchmark proved the x64 optimized path. It did not prove one universal backend for every architecture.

Required implementation matrix:

```text
x86_64 optimized
  FBGEMM + AVX2 where supported and validated

x86_64 fallback
  upstream-supported compatible path selected by executable proof;
  no illegal-instruction recovery strategy

Apple arm64
  upstream ARM path + Apple Accelerate/NEON as resolved by the pinned source

Android/Linux arm64
  upstream ARM path, typically RUY/NEON as resolved by the pinned source
```

The exact resolved backend, compiler flags, submodule revisions, and CPU requirements must be stored in each native build manifest.

Do not force FBGEMM on ARM merely because it is used by the validated Windows build.

## 9. Model registry validation

Mozilla publishes a current model registry containing language pairs, release status, architecture, artifact paths, model sizes, hashes, and metrics.

The library must not use the live registry directly at runtime.

The upstream compatibility workflow must:

1. fetch the registry at a recorded instant;
2. select only approved `Release` entries;
3. download every artifact required by each selected pair;
4. compute compressed and uncompressed size and SHA-256 for every artifact, including vocabularies and shortlists even if the registry does not provide them;
5. run compatibility, quality-drift, loading, and performance tests;
6. generate deterministic `approved-models.json`;
7. commit the manifest only through the protected compatibility workflow.

The initial permanent canary is Spanish→English. English→Spanish is the required reverse-direction canary.

## 10. Licensing validation

Original Linguum files are Apache-2.0. Mozilla-derived and vendored files remain MPL-2.0.

MPL-2.0 is file-level copyleft. It allows a larger work to contain differently licensed files, including statically linked code, but recipients of executable/library distributions must be told where to obtain the corresponding MPL-covered source.

The release must include:

- Apache-2.0 `LICENSE` for original Linguum code;
- Mozilla/MPL notices;
- `THIRD_PARTY_LICENSES`;
- exact `UPSTREAM.json` and recursive source lock;
- corresponding MPL source archive or durable source URL;
- patch source for MPL-covered modifications;
- SBOM and provenance.

A legal-review checkpoint is required before the first public release. The implementation may not state that the review is legal advice.

## 11. Maven Central validation

Maven Central requires a verified namespace. Publishing under:

```text
io.linguum
```

requires control of the reverse-DNS domain namespace, normally `linguum.io`, and DNS verification in the Central Portal.

Implementation may proceed without that credential, but `1.0.0-rc.1` publication is blocked until the namespace is verified. Codex must not silently switch the group to `io.github.stevenbuglione` because the group is a locked decision.

Maven Central publishing requires signing credentials and compliant POM metadata. Apple publications must be built on macOS.

## 12. Native runtime artifact selection risk

The locked design requires one public dependency while resolving platform-specific desktop native artifacts internally.

Gradle Module Metadata supports OS/architecture variants, but JVM consumer configurations do not inherently request native OS/architecture attributes in every build. Therefore M1 must prove the exact one-dependency consumer experience using clean Maven-local fixture projects on Windows, macOS, and Linux.

The proof must show:

- only the intended native runtime is resolved or packaged;
- no consumer plugin or manual classifier declaration is needed;
- Gradle and Maven consumers behave as documented;
- unsupported or ambiguous platforms fail clearly.

If a plain dependency cannot satisfy the locked experience, Codex stops with a blocker. It may not silently bundle every desktop runtime or require an extra Gradle plugin.

## 13. Mobile native feasibility risk

Firefox proves the model/runtime architecture and uses Bergamot WASM in the browser, but this handoff requires native C++ execution on Android and iOS.

The pinned source contains native and ARM-oriented code paths, but a production-quality Android/iOS build is not already validated by the Windows benchmark or Firefox's web integration.

M1 therefore requires real canary builds and execution before stable API implementation. No WASM fallback may be introduced without owner authorization.

## 14. Repository and artifact provenance validation

GitHub CLI supports creating a remote repository from an existing local source and pushing the initial commit in one operation.

GitHub artifact attestations link release artifacts to source and workflow provenance. On GitHub Free/Pro/Team they are available for public repositories; private/internal repositories require Enterprise Cloud.

The canonical plan creates the implementation repository as public. Release workflows attest executable/library artifacts and SBOMs and publish only from protected tags/environments.

## 15. Conclusions

Validated and closed:

- selected Firefox-maintained engine revision;
- native Windows performance and determinism;
- provider-neutral architecture direction;
- current stable Kotlin/Gradle publication stack;
- license boundary model;
- Maven Central and SwiftPM publication paths.

Must be proven before stable API work:

- all non-Windows native targets;
- architecture-specific math backends;
- x64 fallback;
- one-dependency desktop native variant resolution;
- Objective-C/XCFramework/Swift overlay consumer experience.

<!-- END FILE: research/VALIDATION_REPORT.md -->

---

<!-- BEGIN FILE: research/KNOWN_RISKS_AND_BLOCKERS.md -->

# Source file: `research/KNOWN_RISKS_AND_BLOCKERS.md`

# Known Risks, Hard Gates, and Blocker Decisions

## How to use this file

These are not reasons to weaken the architecture. They are the items the implementation sequence must prove early.

## R1 — Mobile native source compatibility

**Risk:** the exact Firefox-pinned C++ inference source may require platform-specific build fixes or may not meet memory/thermal requirements on Android/iOS.

**Gate:** M1 canary build and one real translation on Android arm64/x86_64 and iOS arm64/simulators.

**Forbidden shortcut:** substituting WASM, cloud translation, an old BrowserMT fork, or arbitrary `main`.

**Blocker outcome:** report exact compiler/runtime evidence and the smallest owner decision required.

## R2 — One-dependency desktop native artifact selection

**Risk:** Gradle Module Metadata can describe OS/architecture variants, but a plain JVM dependency may not request the attributes needed to disambiguate them.

**Gate:** publish to an isolated Maven repository and consume `implementation("io.linguum:translation:<version>")` from clean Windows/macOS/Linux fixture projects with no plugin or classifier.

**Pass:** the correct single runtime is resolved and loaded.

**Fail:** stop. Do not silently bundle all runtimes, download executable code at runtime, or require an undisclosed plugin.

## R3 — x64 fallback

**Risk:** the validated Windows path used AVX2; the fallback backend and its performance are not yet proven.

**Gate:** build on a baseline x86-64 profile, verify no unsupported instructions, run correctness and performance gates on controlled hardware/virtual CPU masking.

**Fail:** document AVX2 as a required v1 CPU only after owner authorization; do not claim a fallback.

## R4 — ARM math backend

**Risk:** FBGEMM is not the universal backend for ARM. Android/Linux ARM and Apple ARM must use the backend resolved by the pinned upstream source.

**Gate:** build manifests record resolved flags/backends; tests execute on real ARM hardware or required target runners.

## R5 — Structured span preservation

**Risk:** stable semantic span preservation is more difficult than plain text and must not depend on arbitrary HTML or fragile sentinel substitution.

**Gate:** deterministic adapter, range invariants, protected-span tests, cross-engine golden corpus, and failure/degradation semantics.

**Fail:** stable 1.0 is blocked because structured spans are a locked stable feature; do not silently downgrade to plain text.

## R6 — iOS x86_64 simulator

**Risk:** `iosX64` is a low support tier and Intel Apple hosts are disappearing.

**Gate:** compile on the supported macOS toolchain and run scheduled real simulator validation on an Intel host when available.

**Fail:** report toolchain evidence. Do not remove the target without architecture authorization.

## R7 — Maven namespace

**Risk:** `io.linguum` cannot publish until the Maven Central namespace is verified through domain control.

**Gate:** Central Portal namespace verification before first release candidate.

**Fail:** release blocked; implementation may continue. Do not change group ID silently.

## R8 — Dedicated performance hardware

**Risk:** shared CI runners are too noisy for authoritative latency gates.

**Gate:** provision and document stable benchmark profiles before performance becomes a merge/release blocker.

**Interim:** shared CI runs smoke thresholds only; the validated Windows baseline remains evidence but not a universal runner baseline.

## R9 — Language detection implementation

**Risk:** the architecture includes an optional language-detection capability but does not select a built-in detector.

**Locked interpretation:** implement the stable capability interface, Java/Swift facade, fakes, and contract tests. Do not bundle a detector in 1.0 unless separately researched, licensed, benchmarked, and owner-approved.

## R10 — Manifest authentication

**Risk:** adding a cross-platform runtime cryptography dependency merely to verify an embedded manifest would increase complexity.

**Locked implementation:** the immutable model manifest is embedded in the Maven/XCFramework/AAR release artifact; artifact signing, PGP, provenance, and checked-in generated digest authenticate it. Runtime verifies its generated digest and all downloaded model hashes. Runtime-downloaded alternate manifests are not supported in v1.

## R11 — Upstream source size and provenance

**Risk:** `mozilla/translations` uses recursive submodules. A simple top-level commit pin is insufficient.

**Gate:** `UPSTREAM_LOCK.json` records every recursive repository URL/path/SHA and a deterministic source-tree archive digest. Vendored source must reproduce that lock exactly.

## R12 — Native crashes in-process

**Risk:** native memory corruption terminates the host process.

**Mitigation:** strict C ABI, trusted models, sanitizers, fuzzing, hostile-input tests, soak tests, and private `TranslationRuntime` abstraction allowing future desktop process isolation.

**Forbidden shortcut:** declaring process isolation implemented when v1 is in-process.

## R13 — Model registry volatility

**Risk:** the live Mozilla registry changes over time and some artifact roles may not contain published hashes.

**Mitigation:** compatibility workflow snapshots the registry, downloads artifacts, computes all hashes/sizes, and generates an immutable release manifest. Runtime never resolves `latest`.

## R14 — Repository visibility and attestations

**Risk:** private repos on non-Enterprise GitHub plans cannot use GitHub artifact attestations.

**Default:** create the library repository public. If private is explicitly required, release is blocked until a public/provenance-compatible strategy is established.

<!-- END FILE: research/KNOWN_RISKS_AND_BLOCKERS.md -->

---

<!-- BEGIN FILE: research/SOURCE_REGISTER.md -->

# Source file: `research/SOURCE_REGISTER.md`

# Primary Source Register

Validated on 2026-08-20. External facts must be rechecked through the dedicated update workflow before a future toolchain or upstream upgrade.

## Frozen architecture and benchmark evidence

- `architecture/LOCKED_DECISIONS.md` — owner-approved 76-decision source of truth.
- `research/evidence/translation-benchmark-validation.zip` — complete corrected benchmark harness/results.
- `research/evidence/FINAL_BENCHMARK_REPORT.md` — summarized validated result.

## Linguum architectural conventions

- `https://github.com/StevenBuglione/Linguum/blob/codex/m4-daily-review-1-0/AGENTS.md`
- `https://github.com/StevenBuglione/Linguum/blob/codex/m4-daily-review-1-0/CODEX_EXECUTION_CONTRACT.md`
- `https://github.com/StevenBuglione/Linguum/blob/codex/m4-daily-review-1-0/architecture/REPOSITORY_LAYOUT.md`
- `https://github.com/StevenBuglione/Linguum/blob/codex/m4-daily-review-1-0/architecture/ARCHITECTURE_CONSTITUTION.yaml`
- `https://github.com/StevenBuglione/Linguum/blob/codex/m4-daily-review-1-0/implementation/TEST_CI_AND_QUALITY_GATES.md`

## Firefox and Mozilla translation source

- Firefox repository: `https://github.com/mozilla-firefox/firefox`
- Firefox pin metadata: `toolkit/components/translations/bergamot-translator/moz.yaml`
- Mozilla translations repository: `https://github.com/mozilla/translations`
- pinned revision: `eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d`
- native inference root: `inference/`
- service API: `inference/src/translator/service.h`
- native CLI example: `inference/src/app/translator_cli.cpp`
- native build script: `inference/scripts/build.py`
- model registry JSON: `https://storage.googleapis.com/moz-fx-translations-data--303e-prod-translations-data/db/models.json`
- Firefox translations docs: `https://firefox-source-docs.mozilla.org/toolkit/components/translations/`

## Kotlin and Gradle

- Kotlin releases: `https://kotlinlang.org/docs/releases.html`
- KGP/Gradle/AGP compatibility: `https://kotlinlang.org/docs/gradle-configure-project.html`
- Kotlin/Native target support: `https://kotlinlang.org/docs/native-target-support.html`
- C interop: `https://kotlinlang.org/docs/native-c-interop.html`
- Apple framework export: `https://kotlinlang.org/docs/apple-framework.html`
- Swift export status: `https://kotlinlang.org/docs/native-swift-export.html`
- SwiftPM/XCFramework export: `https://kotlinlang.org/docs/multiplatform/multiplatform-spm-export.html`
- Maven Central publishing: `https://kotlinlang.org/docs/multiplatform/multiplatform-publish-libraries-to-maven.html`
- KMP publication structure: `https://kotlinlang.org/docs/multiplatform-publish-lib-setup.html`
- ABI validation: Kotlin 2.4 documentation and built-in `abiValidation` DSL.
- Gradle Module Metadata: `https://docs.gradle.org/current/userguide/publishing_gradle_module_metadata.html`
- Gradle variants/attributes: `https://docs.gradle.org/current/userguide/variant_attributes.html`

## Android

- AGP 9.1 release notes: `https://developer.android.com/build/releases/agp-9-1-0-release-notes`
- NDK configuration: `https://developer.android.com/studio/projects/configure-agp-ndk`
- Android ABIs: `https://developer.android.com/ndk/guides/abis.html`
- AGP 9 KMP migration: `https://kotlinlang.org/docs/multiplatform/multiplatform-project-agp-9-migration.html`

## Publishing and GitHub

- GitHub repository creation: `https://cli.github.com/manual/gh_repo_create`
- GitHub branch protection: `https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches`
- GitHub artifact attestations: `https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations`
- Maven Central tutorial and namespace requirements: Kotlin Maven Central publishing documentation.

## Licensing

- MPL 2.0: `https://www.mozilla.org/en-US/MPL/2.0/`
- MPL 2.0 FAQ: `https://www.mozilla.org/en-US/MPL/2.0/FAQ/`
- Apache License 2.0: `https://www.apache.org/licenses/LICENSE-2.0`

<!-- END FILE: research/SOURCE_REGISTER.md -->

---

<!-- BEGIN FILE: research/evidence/FINAL_BENCHMARK_REPORT.md -->

# Source file: `research/evidence/FINAL_BENCHMARK_REPORT.md`

TRANSLATION PERFORMANCE VALIDATION

Rounds completed: 6 / 6
Samples per engine per round: 500
Total measured samples per engine: 3000
Warmup per engine per run: 20
Warmup overlap with corpus: 0
Corpus order: deterministic and paired per round
Chrome model pre-downloaded: YES
Caches:
  WASM Bergamot: 0
  Native Bergamot: 0

NATIVE ENGINE SOURCE

Repository:
mozilla/translations

Firefox-pinned revision:
eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d

Bergamot:
v0.6.0

Service:
AsyncService

Workers:
1

Cache:
0

CPU backend:
FBGEMM

Build:
Release x64

Architecture:
AVX2

Machine
──────────────────────────
CPU: AMD Ryzen 9 5900X 12-Core Processor
RAM: 127.93 GB
Windows: Windows 11 Pro (10.0.26100)
GPU: NVIDIA GeForce RTX 3070
Chrome version: Google Chrome 151

                         Chrome       WASM       Native

Median run p50              15.80      21.65      11.13
Median run p95              44.31      64.73      30.00
Median run p99              48.05      69.05      38.26

Mean run p50                15.78      21.57      11.01
Mean run p95                44.40      64.82      30.05
Mean run p99                48.00      69.24      38.39

p95 stddev                   0.77       0.58       1.48

Pooled p50                  15.80      21.60      11.00
Pooled p95                  44.60      65.30      30.26
Pooled p99                  48.20      69.20      40.20

Median TPS                  49.35      34.83      71.74
Median words/sec           566.59     399.82     823.56

CURRENT FIREFOX NATIVE

Round 1
p50: 10.62
p95: 28.78
p99: 33.74
TPS: 75.00

Round 2
p50: 11.64
p95: 31.57
p99: 41.18
TPS: 67.55

Round 3
p50: 10.14
p95: 28.25
p99: 36.78
TPS: 77.33

Round 4
p50: 11.35
p95: 30.74
p99: 39.74
TPS: 70.04

Round 5
p50: 11.42
p95: 31.69
p99: 43.75
TPS: 68.32

Round 6
p50: 10.91
p95: 29.25
p99: 35.19
TPS: 73.44

CURRENT FIREFOX NATIVE AGGREGATE

Median p50: 11.13
Median p95: 30.00
Median p99: 38.26
Median TPS: 71.74

Mean p50: 11.01
Mean p95: 30.05
Mean p99: 38.39

p95 stddev: 1.48

| Metric              | Chrome | Firefox WASM | Old Native | Current Firefox Native |
| ------------------- | -----: | -----------: | ---------: | ---------------------: |
| Median p50          | 15.80 | 21.65 | 10.13 | 11.13 |
| Median p95          | 44.31 | 64.73 | 28.07 | 30.00 |
| Median p99          | 48.05 | 69.05 | 30.35 | 38.26 |
| TPS                 | 49.35 | 34.83 | 79.91 | 71.74 |
| Short subtitle p95  | 17.51 | 23.75 | 11.12 | 14.52 |
| Medium subtitle p95 | 34.69 | 45.75 | 19.75 | 28.75 |
| Long subtitle p95   | 48.83 | 70.17 | 30.81 | 41.06 |

CURRENT FIREFOX NATIVE VS CHROME

p50 wins: 6 / 6
p95 wins: 6 / 6
p99 wins: 6 / 6

median p50 ratio:
native / chrome = 0.707

median p95 ratio:
native / chrome = 0.682

median p99 ratio:
native / chrome = 0.806

CURRENT FIREFOX NATIVE VS OLD NATIVE

p50 delta: 1.00 ms (ratio 1.099)
p95 delta: 1.93 ms (ratio 1.069)
p99 delta: 7.90 ms (ratio 1.260)
throughput delta: -8.18 TPS (ratio 0.898)

STARTUP — INFORMATIONAL

Median engineSetupMs Chrome/WASM/Native: 81.95 / 364.80 / 60.35
Median firstTranslationMs Chrome/WASM/Native: 32.70 / 170.60 / 48.85

CURRENT FIREFOX NATIVE BERGAMOT

Source verification:
PASS

Firefox-pinned revision:
PASS

Six rounds completed:
PASS

Same frozen corpora:
PASS

Chrome/WASM baselines unchanged:
PASS

Absolute subtitle p95:
PASS

Absolute subtitle p99:
PASS

Throughput:
PASS

Native vs Chrome:
FASTER THAN CHROME

Output agreement with Firefox WASM:
480 / 500
96%

FINAL DECISION:

CURRENT MOZILLA NATIVE TRANSLATION
IS VALIDATED.

KOTLIN INTEGRATION: DO NOT START automatically. Return these results for architectural review first.

<!-- END FILE: research/evidence/FINAL_BENCHMARK_REPORT.md -->

---

<!-- BEGIN FILE: research/evidence/current-mozilla-native-build.json -->

# Source file: `research/evidence/current-mozilla-native-build.json`

````json
{
  "repository": "mozilla/translations",
  "revision": "eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d",
  "bergamotVersion": "v0.6.0",
  "buildType": "Release",
  "compiler": "MSVC",
  "architecture": "x64",
  "buildArch": "native",
  "expectedIsa": "AVX2",
  "service": "AsyncService",
  "workers": 1,
  "cacheSize": 0,
  "useFbgemm": true,
  "useStaticLibs": true,
  "compileCpu": true,
  "compileCuda": false,
  "compileWasm": false,
  "useMkl": "OFF",
  "useIntgemm": "ON",
  "useOnnxSgemm": "ON",
  "modelSha256": "4aed7734152ae0045d1a69ae49c86cfda18f53c61f90e95e1d1de1c7c7c3b033",
  "executable": "native/mozilla-translations-firefox/inference/build-harness/src/app/Release/harness-native-bench.exe"
}
````

<!-- END FILE: research/evidence/current-mozilla-native-build.json -->

---

<!-- BEGIN FILE: research/evidence/current-mozilla-source-manifest.txt -->

# Source file: `research/evidence/current-mozilla-source-manifest.txt`

````text
CURRENT MOZILLA SOURCE MANIFEST
repository: mozilla/translations
HEAD: eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d
BERGAMOT_VERSION: v0.6.0

submodule status --recursive
-42fa605b53f32eaf6c6e0b5677255c21c91b3d49 3rd_party/extract-lex
-cab1e9aac8d3bb02ff5ae58218d8d225a039fa11 3rd_party/fast_align
-bbf4fc511266c5d4515047055d7bdec659a6e158 3rd_party/kenlm
-e8a1a2530fb84cbff7383302ebca393e5875c441 3rd_party/marian-dev
-64307314b4d5a9a0bd529b5c1036b0710d995eec 3rd_party/preprocess
-2346baa7bb44a4a0571cc75f1986ab9aaa35aa03 inference/3rd_party/emsdk
 a311f9865ade34db1e8e080e6cc146f55dafb067 inference/3rd_party/ssplit-cpp (heads/master)
 0e33146d3e7f070c7de9494efef49147a9d20558 inference/marian-fork/src/3rd_party/fbgemm (0e33146)
 4da474ac9aa2689e88d5e40a2f37628f302d7e3c inference/marian-fork/src/3rd_party/fbgemm/third_party/asmjit (4da474a)
 d5e37adf1406cf899d7d9ec1d317c47506ccb970 inference/marian-fork/src/3rd_party/fbgemm/third_party/cpuinfo (d5e37ad)
 0fc5466dbb9e623029b1ada539717d10bd45e99e inference/marian-fork/src/3rd_party/fbgemm/third_party/googletest (0fc5466)
 f7401513da71758dacce52fed1c7855549abee59 inference/marian-fork/src/3rd_party/intgemm (v1.0)
-7d3486128ebc865b9f2cad63a5cfd3a8f6abcb5a inference/marian-fork/src/3rd_party/nccl
 924924b08e9596b41aeebada4a172f026be95f5a inference/marian-fork/src/3rd_party/onnxjs (heads/master)
 fff37f4ca0397af9ed7e04f3bd6b893a1ea2b08e inference/marian-fork/src/3rd_party/onnxjs/deps/eigen (fff37f4)
 2d950b3bfa7ebfbe7a97ecb44b1cc4da5ac1d6f0 inference/marian-fork/src/3rd_party/ruy (2d950b3)
 5916273f79a21551890fd3d56fc5375a78d1598d inference/marian-fork/src/3rd_party/ruy/third_party/cpuinfo (5916273)
 6c58c11d5497b6ee1df3cb400ce30deb72fc28c0 inference/marian-fork/src/3rd_party/ruy/third_party/googletest (6c58c11)
 ae41b7740d7006596bb9257e83340b2620db9d00 inference/marian-fork/src/3rd_party/sentencepiece (heads/master)
 d0793d86aea9036a5bc77b9ca7791dff024168ca inference/marian-fork/src/3rd_party/simd_utils (d0793d8)
 417a2a9e9dbd720b8d2dfa1dafe57cf1b37ca0d7 inference/marian-fork/src/3rd_party/simple-websocket-server (417a2a9)
````

<!-- END FILE: research/evidence/current-mozilla-source-manifest.txt -->

---

<!-- BEGIN FILE: architecture/ARCHITECTURE_CONSTITUTION.yaml -->

# Source file: `architecture/ARCHITECTURE_CONSTITUTION.yaml`

````yaml
version: 1
library:
  name: Linguum Translation
  repository: StevenBuglione/linguum-translation
  package_root: io.linguum.translation
  maven_group: io.linguum
  primary_artifact: translation
  testing_artifact: translation-testing
  license_original_code: Apache-2.0
  license_upstream_code: MPL-2.0
source_of_truth:
  decisions: architecture/LOCKED_DECISIONS.md
  constitution: architecture/ARCHITECTURE_CONSTITUTION.yaml
  modules: architecture/MODULE_CATALOG.yaml
  public_api: architecture/PUBLIC_API_SPEC.md
  native_abi: architecture/NATIVE_ABI_SPEC.md
  model_manifest: architecture/MODEL_MANIFEST_SPEC.md
  upstream_policy: architecture/UPSTREAM_FIREFOX_POLICY.md
upstream:
  firefox_repository: mozilla-firefox/firefox
  translations_repository: mozilla/translations
  firefox_pinned_revision: eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d
  bergamot_version: v0.6.0
  source_path: native/upstream/mozilla-translations
  immutable: true
  direct_edits_forbidden: true
  update_requires_workflow: upstream-firefox-compatibility
runtime:
  provider_neutral_public_api: true
  native_execution_v1: in_process
  private_runtime_abstraction_required: true
  c_abi_required: true
  cxx_abi_public: false
  network_on_translate: forbidden
  telemetry_user_text: forbidden
  native_workers_per_model: 1
  native_cache_entries: 0
platforms:
  desktop_jvm:
    java_bytecode: 17
    build_jdk: 21
    targets:
      - windows-x64
      - macos-arm64
      - macos-x64
      - linux-x64
      - linux-arm64
  android:
    min_sdk: 26
    targets:
      - arm64-v8a
      - x86_64
  ios:
    minimum_version: "15.0"
    targets:
      - ios-arm64
      - ios-simulator-arm64
      - ios-simulator-x64
public_api:
  stable_package: io.linguum.translation
  internal_package_prefix: io.linguum.translation.internal
  primary_types:
    - TranslationService
    - Translator
    - TranslationRequest
    - TranslationResult
    - TranslationOutcome
    - TranslationFailure
    - LanguageTag
    - LanguagePair
    - TranslationCatalog
  implementation_types_in_public_signatures: forbidden
  explicit_api_mode: required
  java_facade: required
  swift_facade: required
  experimental_opt_in: required
model_rules:
  direct_pairs_only: true
  silent_pivot: forbidden
  release_manifest_immutable: true
  runtime_live_registry_resolution: forbidden
  integrity_algorithm: SHA-256
  installation_transactional: true
  partial_install_visible: false
  network_source_trusted: false
  manifest_is_trust_anchor: true
  loaded_pool: memory_budgeted_lru
  disk_store: byte_budgeted_lru
  active_model_eviction: forbidden
  pinned_model_eviction: forbidden
  retained_model_disk_eviction: forbidden
module_types:
  public-api:
    may_depend_on:
      - public-api
    prohibited:
      - platform-api
      - native-api
      - network-api
      - mozilla-api
  orchestration:
    may_depend_on:
      - public-api
      - orchestration
      - internal-contract
    prohibited:
      - direct-platform-api
      - direct-native-api
      - direct-network-api
  internal-contract:
    may_depend_on:
      - public-api
      - internal-contract
  platform-adapter:
    may_depend_on:
      - public-api
      - orchestration
      - internal-contract
      - native-bridge
      - approved-platform-api
  native-bridge:
    may_depend_on:
      - native-abi
      - native-adapter
  native-abi:
    public_c_only: true
    cxx_public: false
  native-adapter:
    may_depend_on:
      - native-abi
      - immutable-upstream
      - approved_patch_queue
  immutable-upstream:
    hand_editing_allowed: false
  test-harness:
    production_dependency_target: false
  publication:
    business_logic_allowed: false
codex_rules:
  protected_files_mutable_by_normal_task: false
  accepted_adr_mutable_by_normal_task: false
  weaken_test_or_gate: false
  update_baseline_to_fit_code: false
  add_global_suppression: false
  create_detekt_baseline: false
  edit_upstream_tree: false
  change_firefox_pin_outside_workflow: false
  add_unapproved_dependency: false
  use_dynamic_dependency_version: false
  skip_supported_platform: false
  change_minimum_os_silently: false
  force_push: false
  work_beyond_current_milestone: false
  verified_checkpoint_push_required: true
  clean_milestone_gate_required: true
quality_gates:
  - formatting
  - compiler_warnings_as_errors
  - detekt_no_baseline
  - custom_architecture_rules
  - dependency_locking
  - dependency_verification
  - api_compatibility
  - jvm_binary_compatibility
  - swift_surface_compatibility
  - c_abi_compatibility
  - unit_tests
  - property_tests
  - contract_tests
  - platform_integration_tests
  - native_sanitizers
  - fuzz_regressions
  - model_manifest_validation
  - model_drift_validation
  - performance_smoke
  - dedicated_performance_gate
  - license_policy
  - sbom
  - provenance
  - artifact_reproducibility
milestones:
  M0: repository_and_governance
  M1: platform_and_packaging_feasibility
  M2: native_abi_and_runtime_foundation
  M3: public_api_and_consumer_facades
  M4: scheduler_lifecycle_and_model_pool
  M5: model_manifest_acquisition_and_storage
  M6: platform_bindings_and_end_to_end_runtime
  M7: structured_text_segmentation_batch_and_switching
  M8: full_platform_quality_and_security_validation
  M9: publishing_release_candidate_and_docs
  M10: release_1_0_and_linguum_consumer_validation
````

<!-- END FILE: architecture/ARCHITECTURE_CONSTITUTION.yaml -->

---

<!-- BEGIN FILE: architecture/MODULE_CATALOG.yaml -->

# Source file: `architecture/MODULE_CATALOG.yaml`

````yaml
version: 1
modules:
  - path: :translation
    directory: translation
    type: publication
    visibility: public
    artifact: io.linguum:translation
    introduced: M3
    responsibility: public KMP umbrella and target publication

  - path: :translation-api
    directory: translation-api
    type: public-api
    visibility: public
    introduced: M3
    responsibility: canonical provider-neutral KMP contracts

  - path: :translation-runtime
    directory: translation-runtime
    type: orchestration
    visibility: internal
    introduced: M4
    responsibility: service composition, scheduler, lifecycle, model generations

  - path: :translation-model-contracts
    directory: translation-model-contracts
    type: internal-contract
    visibility: internal
    introduced: M3
    responsibility: manifest, installation, catalog, and storage contracts

  - path: :translation-model-management
    directory: translation-model-management
    type: orchestration
    visibility: internal
    introduced: M5
    responsibility: acquisition, transactional installation, cache and activation policies

  - path: :translation-structured-text
    directory: translation-structured-text
    type: orchestration
    visibility: internal
    introduced: M7
    responsibility: semantic spans, segmentation and deterministic reassembly

  - path: :translation-diagnostics
    directory: translation-diagnostics
    type: internal-contract
    visibility: internal
    introduced: M3
    responsibility: privacy-safe diagnostics, runtime info and metrics contracts

  - path: :translation-detection-api
    directory: translation-detection-api
    type: public-api
    visibility: public-experimental
    introduced: M7
    responsibility: optional language-detection capability contract only

  - path: :translation-testing
    directory: translation-testing
    type: test-harness
    visibility: public
    artifact: io.linguum:translation-testing
    introduced: M3
    responsibility: contract-faithful fakes, fixtures and consumer test support

  - path: :platform:jvm
    directory: platform/jvm
    type: platform-adapter
    visibility: internal
    introduced: M6
    responsibility: desktop JVM factory, storage, transport, JNI loader and native runtime binding

  - path: :platform:android
    directory: platform/android
    type: platform-adapter
    visibility: internal
    introduced: M6
    responsibility: Android factory, Context-backed storage/network and AAR JNI binding

  - path: :platform:apple
    directory: platform/apple
    type: platform-adapter
    visibility: internal
    introduced: M6
    responsibility: iOS Foundation storage/network and Kotlin/Native cinterop binding

  - path: :facades:java
    directory: facades/java
    type: publication
    visibility: public-through-main
    introduced: M3
    responsibility: idiomatic Java facade and CompletionStage mapping

  - path: :facades:apple-export
    directory: facades/apple-export
    type: publication
    visibility: public-through-xcframework
    introduced: M3
    responsibility: Objective-C-compatible umbrella framework export

  - path: :native:abi
    directory: native/abi
    type: native-abi
    visibility: public-native
    introduced: M1
    responsibility: stable C header, ABI versioning and C contract tests

  - path: :native:mozilla-adapter
    directory: native/mozilla-adapter
    type: native-adapter
    visibility: internal
    introduced: M1
    responsibility: C++ adapter from stable C ABI to Firefox-pinned Mozilla inference

  - path: :native:runtime-build
    directory: native/runtime-build
    type: native-bridge
    visibility: internal
    introduced: M1
    responsibility: CMake presets, toolchains, CPU dispatch and native artifact assembly

  - path: :native:upstream
    directory: native/upstream/mozilla-translations
    type: immutable-upstream
    visibility: vendored
    introduced: M1
    responsibility: byte-preserved Firefox-pinned Mozilla source snapshot

  - path: :testing:architecture
    directory: testing/architecture
    type: test-harness
    visibility: internal
    introduced: M0
    responsibility: module graph, package boundary, dependency and protected-file checks

  - path: :testing:contracts
    directory: testing/contracts
    type: test-harness
    visibility: internal
    introduced: M3
    responsibility: shared production/fake behavioral contract suite

  - path: :testing:native
    directory: testing/native
    type: test-harness
    visibility: internal
    introduced: M1
    responsibility: C ABI canary, hostile input, sanitizer and lifecycle harnesses

  - path: :testing:consumer-kotlin
    directory: testing/consumer-kotlin
    type: test-harness
    visibility: internal
    introduced: M3
    responsibility: clean Kotlin consumer compilation and runtime fixture

  - path: :testing:consumer-java
    directory: testing/consumer-java
    type: test-harness
    visibility: internal
    introduced: M3
    responsibility: clean Java consumer compilation and runtime fixture

  - path: :testing:consumer-swift
    directory: testing/consumer-swift
    type: test-harness
    visibility: internal
    introduced: M3
    responsibility: clean SwiftPM/Xcode consumer compilation and runtime fixture

  - path: :testing:consumer-linguum
    directory: testing/consumer-linguum
    type: test-harness
    visibility: internal
    introduced: M10
    responsibility: fixture matching io.linguum.services.api consumption style

  - path: :testing:benchmarks
    directory: testing/benchmarks
    type: test-harness
    visibility: internal
    introduced: M1
    responsibility: raw native, wrapper, end-to-end and platform performance suites

  - path: :testing:fuzz
    directory: testing/fuzz
    type: test-harness
    visibility: internal
    introduced: M2
    responsibility: coverage-guided C ABI/parser fuzzing and permanent corpus
````

<!-- END FILE: architecture/MODULE_CATALOG.yaml -->

---

<!-- BEGIN FILE: architecture/REPOSITORY_LAYOUT.md -->

# Source file: `architecture/REPOSITORY_LAYOUT.md`

# Repository Layout

## Root

```text
linguum-translation/
├── README.md
├── START_HERE.md
├── AGENTS.md
├── CODEX_EXECUTION_CONTRACT.md
├── LICENSE
├── NOTICE
├── THIRD_PARTY_LICENSES.md
├── SECURITY.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── settings.gradle.kts
├── build.gradle.kts
├── gradle.properties
├── gradlew
├── gradlew.bat
├── gradle/
│   ├── libs.versions.toml
│   ├── verification-metadata.xml
│   ├── dependency-locks/
│   └── wrapper/
├── build-logic/
├── architecture/
├── translation/
├── translation-api/
├── translation-runtime/
├── translation-model-contracts/
├── translation-model-management/
├── translation-structured-text/
├── translation-diagnostics/
├── translation-detection-api/
├── translation-testing/
├── platform/
├── facades/
├── native/
├── publication/
├── testing/
├── docs/
├── scripts/
├── reports/
└── .github/
```

## Build logic

```text
build-logic/
└── src/main/kotlin/
    ├── linguum.translation.kotlin-base.gradle.kts
    ├── linguum.translation.kmp-api.gradle.kts
    ├── linguum.translation.kmp-internal.gradle.kts
    ├── linguum.translation.jvm-platform.gradle.kts
    ├── linguum.translation.android-platform.gradle.kts
    ├── linguum.translation.apple-platform.gradle.kts
    ├── linguum.translation.native-build.gradle.kts
    ├── linguum.translation.testing.gradle.kts
    ├── linguum.translation.publication.gradle.kts
    ├── linguum.translation.architecture.gradle.kts
    └── linguum.translation.quality.gradle.kts
```

Each Gradle project applies exactly one primary architecture convention. Shared quality conventions may be applied transitively by the primary convention.

## Public API modules

```text
translation-api/
└── src/
    ├── commonMain/kotlin/io/linguum/translation/
    ├── commonTest/kotlin/io/linguum/translation/
    ├── jvmMain/
    ├── androidMain/
    └── iosMain/

translation/
└── public umbrella publication

translation-testing/
└── public test-only artifact
```

Only `io.linguum.translation` and explicitly documented subpackages are stable public Kotlin packages.

## Internal KMP modules

```text
translation-runtime/
translation-model-contracts/
translation-model-management/
translation-structured-text/
translation-diagnostics/
translation-detection-api/
```

Internal implementation packages use:

```text
io.linguum.translation.internal.*
```

No internal type may appear in a public signature.

## Platform adapters

```text
platform/
├── jvm/
│   ├── src/main/kotlin/io/linguum/translation/internal/jvm/
│   ├── src/main/resources/
│   └── native-loader tests
├── android/
│   ├── src/androidMain/kotlin/io/linguum/translation/internal/android/
│   ├── src/androidMain/jniLibs/ (generated into build, never hand-edited)
│   └── Android instrumented tests
└── apple/
    ├── src/iosMain/kotlin/io/linguum/translation/internal/apple/
    ├── src/nativeInterop/cinterop/linguum_translation.def
    └── XCTest/Swift fixture integration
```

Platform adapters implement storage, HTTPS transport, clock, filesystem locks, native binding, and platform memory-pressure hooks. They contain no model-selection or translation policy.

## Java and Swift facades

```text
facades/
├── java/
│   └── src/main/java/io/linguum/translation/java/
└── apple-export/
    ├── KMP umbrella framework configuration
    └── Objective-C export annotations/adapters

swift-overlay/
├── Sources/LinguumTranslation/
├── Tests/LinguumTranslationTests/
└── generated into release XCFramework package
```

Swift source lives in the primary repo, while the release `Package.swift` may be mirrored into `linguum-translation-swift` during M9.

## Native source boundary

```text
native/
├── abi/
│   ├── include/linguum_translation.h
│   ├── src/abi_validation.c
│   └── baseline/abi-v1.txt
├── mozilla-adapter/
│   ├── include/
│   └── src/
├── runtime-build/
│   ├── CMakeLists.txt
│   ├── CMakePresets.json
│   ├── toolchains/
│   ├── cmake/
│   └── scripts/
├── upstream/
│   └── mozilla-translations/
├── patches/
│   ├── PATCHES.yaml
│   ├── windows/
│   ├── macos/
│   ├── linux/
│   ├── android/
│   └── ios/
├── UPSTREAM.json
├── UPSTREAM_LOCK.json
└── SOURCE_TREE.sha256
```

`native/upstream/mozilla-translations/**` is immutable and must match `UPSTREAM_LOCK.json`.

## Publication assets

```text
publication/
├── desktop-natives/
│   ├── windows-x64-avx2/
│   ├── windows-x64-baseline/
│   ├── macos-arm64/
│   ├── macos-x64/
│   ├── linux-x64-avx2/
│   ├── linux-x64-baseline/
│   └── linux-arm64/
├── android-aar/
├── apple-xcframework/
├── maven/
├── sbom/
└── provenance/
```

Publication directories contain build definitions and generated outputs only under `build/`; generated artifacts are never committed unless a specific baseline/evidence policy requires them.

## Testing

```text
testing/
├── architecture/
├── contracts/
├── native/
├── consumer-kotlin/
├── consumer-java/
├── consumer-swift/
├── consumer-linguum/
├── benchmarks/
├── fuzz/
├── model-fixtures/
├── failure-injection/
├── platform-smoke/
└── release-verification/
```

## Documentation

```text
docs/
├── quickstart/
├── kotlin/
├── java/
├── swift/
├── android/
├── ios/
├── desktop/
├── models/
├── offline-and-privacy/
├── troubleshooting/
├── migration/
├── native-abi/
├── security/
└── licensing/
```

## Prohibited production names

Do not create vague production modules or packages named:

```text
common
shared-utils
utils
helpers
misc
stuff
core
base-manager
generic-manager
```

Source-set names generated by Kotlin such as `commonMain` are normal and exempt; the prohibition applies to architecture/module/package responsibility names.

<!-- END FILE: architecture/REPOSITORY_LAYOUT.md -->

---

<!-- BEGIN FILE: architecture/MODULE_DEPENDENCY_GRAPH.md -->

# Source file: `architecture/MODULE_DEPENDENCY_GRAPH.md`

# Module Dependency Graph and Enforcement Rules

## Canonical graph

```text
translation-api
     ▲
     │
translation-model-contracts ◄──── translation-diagnostics
     ▲                                  ▲
     │                                  │
translation-model-management      translation-runtime
     ▲                                  ▲
     └──────────────┬───────────────────┘
                    │
        translation-structured-text
                    ▲
                    │
        platform adapters / facades
                    ▲
                    │
              translation umbrella

native/abi ◄── native/mozilla-adapter ◄── immutable Mozilla source
    ▲
    ├── JVM JNI binding
    ├── Android JNI binding
    └── Apple cinterop binding
```

## Allowed dependencies

### `translation-api`

May depend only on:

- Kotlin standard library;
- `kotlinx-coroutines-core` for `Flow`, `StateFlow`, and suspend semantics;
- explicitly approved annotations needed for API stability.

It may not depend on:

- any platform module;
- JNI/cinterop;
- HTTP/network libraries;
- filesystem libraries;
- Mozilla/Bergamot/Marian;
- serialization libraries in public type signatures;
- a logging backend.

### `translation-model-contracts`

May depend on `translation-api` and standard/coroutines APIs. It contains immutable internal manifest/catalog/storage contracts.

### `translation-runtime`

May depend on:

- `translation-api`;
- model contracts;
- diagnostics contracts;
- structured-text orchestration;
- internal runtime ports.

It may not import JNI, Android, Foundation, filesystem, HTTP, or Mozilla APIs.

### `translation-model-management`

May depend on:

- API/model contracts;
- runtime ports;
- platform-neutral state machines.

All actual filesystem/network behavior is injected through internal ports implemented by platform adapters.

### `platform:jvm`

May depend on runtime/model modules, JDK APIs, JNI loader code, and an approved HTTP implementation isolated here.

It may not own model-selection policy, scheduling semantics, or public failure definitions.

### `platform:android`

May depend on runtime/model modules, Android Context/storage/network APIs, and JNI. It may not expose `Context` through common public contracts.

### `platform:apple`

May depend on runtime/model modules, Foundation/Security/network APIs, and the generated C interop bindings. It may not expose C pointers through stable Kotlin/Swift APIs.

### Native adapter

May depend on the C ABI, immutable Mozilla source, and approved patch queue. It contains no Kotlin/public API knowledge.

### Testing modules

May depend on production modules. Production modules may never depend on testing modules.

## Custom architecture checks

`architectureCheck` must fail for:

- forbidden Gradle project edges;
- imports from `io.linguum.translation.internal` in public API modules;
- public declarations containing internal/native/platform types;
- networking imports outside platform acquisition adapters;
- native calls outside platform binding modules;
- Mozilla includes outside `native/mozilla-adapter` and vendored source;
- edits inside the upstream tree not produced by the update workflow;
- public mutable collections;
- global mutable state;
- runtime OS checks in `commonMain`;
- unclassified modules;
- cycles;
- production dependencies on tests/fixtures;
- generic/vague module names;
- unsupported target declarations.

## Package rule

Stable public packages are allowlisted in `architecture/public-packages.txt`.

All other Kotlin implementation code must be `internal` and use:

```text
io.linguum.translation.internal...
```

The Java facade is allowlisted under:

```text
io.linguum.translation.java
```

The Swift overlay module name is:

```text
LinguumTranslation
```

<!-- END FILE: architecture/MODULE_DEPENDENCY_GRAPH.md -->

---

<!-- BEGIN FILE: architecture/PUBLIC_API_SPEC.md -->

# Source file: `architecture/PUBLIC_API_SPEC.md`

# Canonical Public API Specification

## 1. Governing principles

The public API is provider-neutral, Kotlin-first, immutable, coroutine-native, and compatible with thin Java/Swift facades.

The stable public package root is:

```text
io.linguum.translation
```

No public type or signature may mention:

```text
Mozilla
Bergamot
Marian
FBGEMM
RUY
JNI
cinterop
native pointer/handle
Android Context
Foundation types
filesystem path implementation
HTTP client implementation
```

Public API source below is normative pseudocode. Codex may make syntax-level adjustments required by Kotlin 2.4.10 only when semantics and names remain identical and API compatibility baselines are generated before 1.0.

## 2. Language types

```kotlin
package io.linguum.translation

@JvmInline
public value class LanguageTag private constructor(
    public val value: String,
) {
    public companion object {
        public fun parse(value: String): LanguageTagOutcome
        public fun require(value: String): LanguageTag
    }

    override public fun toString(): String = value
}

public sealed interface LanguageTagOutcome {
    public data class Valid(public val tag: LanguageTag) : LanguageTagOutcome
    public data class Invalid(public val reason: LanguageTagFailure) : LanguageTagOutcome
}

public sealed interface LanguageTagFailure {
    public data object Empty : LanguageTagFailure
    public data class InvalidSyntax(public val inputLength: Int) : LanguageTagFailure
    public data class TooLong(public val inputLength: Int) : LanguageTagFailure
}

public object Languages {
    public val ENGLISH: LanguageTag
    public val SPANISH: LanguageTag
    public val FRENCH: LanguageTag
    public val GERMAN: LanguageTag
    public val ITALIAN: LanguageTag
    public val PORTUGUESE: LanguageTag
}

public data class LanguagePair(
    public val source: LanguageTag,
    public val target: LanguageTag,
) {
    init {
        require(source != target)
    }
}
```

Rules:

- parse and canonicalize BCP-47 syntax deterministically in common code;
- reject underscores and malformed subtags;
- canonical casing: language lower-case, script title-case, region upper-case, remaining subtags normalized per the parser contract;
- syntactic validity does not imply model support;
- `LanguagePair` is directional;
- no implicit pivot route.

## 3. Outcome and failures

```kotlin
public sealed interface TranslationOutcome<out T> {
    public data class Success<T>(public val value: T) : TranslationOutcome<T>
    public data class Failure(public val reason: TranslationFailure) : TranslationOutcome<Nothing>
}

public sealed interface TranslationFailure {
    public data class UnsupportedLanguagePair(public val pair: LanguagePair) : TranslationFailure
    public data class ModelNotInstalled(public val pair: LanguagePair) : TranslationFailure
    public data class ModelUnavailable(public val pair: LanguagePair) : TranslationFailure
    public data class ModelDownloadFailed(
        public val pair: LanguagePair,
        public val category: ModelDownloadFailureCategory,
    ) : TranslationFailure
    public data class ModelIntegrityViolation(public val pair: LanguagePair) : TranslationFailure
    public data class ModelIncompatible(public val pair: LanguagePair) : TranslationFailure
    public data class InsufficientStorage(
        public val requiredBytes: ULong,
        public val availableBytes: ULong?,
    ) : TranslationFailure
    public data class DownloadDisallowedByPolicy(public val pair: LanguagePair) : TranslationFailure
    public data class MeteredNetworkDisallowed(public val pair: LanguagePair) : TranslationFailure
    public data object NetworkUnavailable : TranslationFailure
    public data class RequestTooLarge(
        public val actualBytes: ULong,
        public val maximumBytes: ULong,
    ) : TranslationFailure
    public data object InvalidText : TranslationFailure
    public data object DeadlineExceeded : TranslationFailure
    public data object Superseded : TranslationFailure
    public data object Overloaded : TranslationFailure
    public data object ServiceClosed : TranslationFailure
    public data class NativeRuntimeUnavailable(public val code: RuntimeFailureCode) : TranslationFailure
    public data class PlatformUnsupported(public val platform: String) : TranslationFailure
    public data class AbiIncompatible(
        public val expectedMajor: UInt,
        public val actualMajor: UInt,
    ) : TranslationFailure
}

public enum class ModelDownloadFailureCategory {
    Transport,
    Interrupted,
    RemoteUnavailable,
    InvalidResponse,
    Storage,
}

public enum class RuntimeFailureCode {
    NativeLibraryMissing,
    NativeLibraryCorrupt,
    NativeInitializationFailed,
    ModelLoadFailed,
    TranslationFailed,
    InternalFailure,
}
```

Rules:

- expected operational failures use typed outcomes;
- coroutine cancellation propagates `CancellationException` in Kotlin and is not converted into a normal success/failure value;
- Java and Swift facades map cancellation to their native async cancellation semantics;
- `TranslationFailure.Cancelled` is not needed in the canonical Kotlin API because structured coroutine cancellation propagates; explicit supersession/deadline remain typed failures;
- catastrophic invariant violations may throw a documented `TranslationRuntimeException` and must never contain user text.

## 4. Service lifecycle

```kotlin
public interface TranslationService {
    public val state: StateFlow<TranslationServiceState>
    public val catalog: TranslationCatalog
    public val models: TranslationModels
    public val runtimeInfo: TranslationRuntimeInfo
    public val languageDetection: LanguageDetection?

    public suspend fun translator(
        pair: LanguagePair,
    ): TranslationOutcome<Translator>

    public suspend fun ensureTranslator(
        pair: LanguagePair,
        acquisition: ModelAcquisitionOptions = ModelAcquisitionOptions.Default,
    ): TranslationOutcome<Translator>

    public fun close()
}

public sealed interface TranslationServiceState {
    public data object Initializing : TranslationServiceState
    public data object Ready : TranslationServiceState
    public data class Degraded(public val reason: TranslationFailure) : TranslationServiceState
    public data object Closing : TranslationServiceState
    public data object Closed : TranslationServiceState
}
```

`close()` is deterministic and idempotent. It:

1. rejects new work;
2. removes/cancels queued work;
3. safely drains currently running native calls;
4. releases translator logical handles;
5. unloads model generations;
6. stops scheduler/native workers;
7. releases native runtime handles;
8. moves state to `Closed`.

`Translator` objects do not own native resources independently and become unusable when the parent service closes.

## 5. Platform factories

The canonical service interface remains platform-neutral. Factories are platform-specific overloads/facades.

### Desktop JVM/Kotlin

```kotlin
package io.linguum.translation

public object TranslationServices {
    public suspend fun create(
        applicationId: String,
        configure: TranslationConfiguration.Builder.() -> Unit = {},
    ): TranslationOutcome<TranslationService>
}
```

### Android Kotlin

```kotlin
package io.linguum.translation.android

public object AndroidTranslationServices {
    public suspend fun create(
        context: android.content.Context,
        configure: TranslationConfiguration.Builder.() -> Unit = {},
    ): TranslationOutcome<TranslationService>
}
```

The Android-specific `Context` appears only in the Android facade package, never the common API.

### Apple Kotlin

The Kotlin/Native API accepts an Apple platform environment created by the Apple adapter; the handwritten Swift facade hides it and exposes a normal Swift factory.

## 6. Configuration DSL

```kotlin
public class TranslationConfiguration private constructor(
    public val runtime: RuntimeConfiguration,
    public val models: ModelConfiguration,
    public val observability: ObservabilityConfiguration,
) {
    public class Builder internal constructor() {
        public fun runtime(block: RuntimeConfiguration.Builder.() -> Unit)
        public fun models(block: ModelConfiguration.Builder.() -> Unit)
        public fun observability(block: ObservabilityConfiguration.Builder.() -> Unit)
    }
}

public data class RuntimeConfiguration(
    public val concurrency: RuntimeConcurrency,
    public val maximumQueuedRequests: UInt,
    public val maximumQueuedBytes: ULong,
    public val maximumInputBytes: ULong,
    public val defaultDeadline: TranslationDeadline,
    public val modelMemoryBudget: ModelMemoryBudget,
)

public sealed interface RuntimeConcurrency {
    public data object Automatic : RuntimeConcurrency
    public data object Conservative : RuntimeConcurrency
    public data class MaximumConcurrentModels(public val count: UInt) : RuntimeConcurrency
}

public sealed interface ModelMemoryBudget {
    public data object Automatic : ModelMemoryBudget
    public data class Bytes(public val value: ULong) : ModelMemoryBudget
}

public data class ModelConfiguration(
    public val acquisitionPolicy: ModelAcquisitionPolicy,
    public val diskBudget: ModelDiskBudget,
    public val defaultSource: ModelSourceSelection,
)

public sealed interface ModelDiskBudget {
    public data object Automatic : ModelDiskBudget
    public data class Bytes(public val value: ULong) : ModelDiskBudget
}

public sealed interface ModelAcquisitionPolicy {
    public data object Automatic : ModelAcquisitionPolicy
    public data object WifiOnly : ModelAcquisitionPolicy
    public data object AllowMetered : ModelAcquisitionPolicy
    public data object OfflineOnly : ModelAcquisitionPolicy
}
```

Configuration is immutable after service creation.

No public configuration property exposes Bergamot worker count, beam size, FBGEMM, model YAML, native paths, or C ABI handles.

## 7. Translator

```kotlin
public interface Translator {
    public val pair: LanguagePair
    public val capabilities: TranslationCapabilities

    public suspend fun translate(
        text: String,
    ): TranslationOutcome<TranslationResult>

    public suspend fun translate(
        request: TranslationRequest,
    ): TranslationOutcome<TranslationResult>

    public suspend fun translateBatch(
        request: TranslationBatchRequest,
    ): TranslationBatchOutcome
}
```

A translator is bound to one direct language pair. It never auto-detects the source and never silently pivots.

## 8. Requests and scheduling

```kotlin
@JvmInline
public value class TranslationRequestId(public val value: String)

@JvmInline
public value class SupersessionKey(public val value: String)

public data class TranslationRequest(
    public val id: TranslationRequestId = TranslationRequestIds.random(),
    public val content: TranslationContent,
    public val workload: TranslationWorkload = TranslationWorkload.Interactive,
    public val deadline: TranslationDeadline = TranslationDeadline.None,
    public val supersessionKey: SupersessionKey? = null,
    public val segmentation: SegmentationPolicy = SegmentationPolicy.Automatic,
)

public enum class TranslationWorkload {
    Realtime,
    Interactive,
    Batch,
}

public sealed interface TranslationDeadline {
    public data object None : TranslationDeadline
    public data class After(public val duration: Duration) : TranslationDeadline
}

public enum class SegmentationPolicy {
    Automatic,
    PreserveInput,
    Sentence,
}
```

Semantics:

- deadlines are converted to monotonic internal deadlines at submission;
- expired queued work never enters native inference;
- a result is never delivered after its deadline;
- queued requests sharing a realtime supersession key may replace stale queued work;
- already-running native inference is not forcibly interrupted;
- stale/cancelled completed native results are discarded;
- queues are bounded by request count and total payload bytes;
- batch workload backpressures rather than silently dropping items.

## 9. Content and spans

```kotlin
public sealed interface TranslationContent {
    public data class PlainText(public val text: String) : TranslationContent
    public data class StructuredText(
        public val text: String,
        public val spans: List<TextSpan>,
    ) : TranslationContent
}

public data class TextRange(
    public val startInclusive: UInt,
    public val endExclusive: UInt,
)

public data class TextSpan(
    public val range: TextRange,
    public val kind: TextSpanKind,
)

public enum class TextSpanKind {
    Emphasis,
    Italic,
    Bold,
    NonTranslatable,
}
```

Rules:

- ranges are over Unicode scalar/code-point indexing as defined and tested by the library, never raw platform UTF-16 indices;
- ranges must be ordered, in bounds, and valid;
- overlapping spans are accepted only for combinations explicitly allowed by the span validator;
- `NonTranslatable` content must survive exactly;
- arbitrary HTML is not accepted as public input;
- WebVTT/SRT/HTML adapters live outside the core runtime;
- unsupported preservation returns a typed failure or documented degradation result, never malformed spans.

## 10. Results

```kotlin
public data class TranslationResult(
    public val requestId: TranslationRequestId,
    public val pair: LanguagePair,
    public val content: TranslatedContent,
    public val segments: List<TranslatedSegment>,
)

public sealed interface TranslatedContent {
    public data class PlainText(public val text: String) : TranslatedContent
    public data class StructuredText(
        public val text: String,
        public val spans: List<TextSpan>,
    ) : TranslatedContent
}

public data class TranslatedSegment(
    public val sourceRange: TextRange,
    public val translatedRange: TextRange,
)
```

The stable result does not expose quality score, alignment matrices, model path, backend name, or native timing internals. Privacy-safe timing belongs to diagnostics/metrics.

## 11. Batch API

```kotlin
public data class TranslationBatchRequest(
    public val requests: List<TranslationRequest>,
    public val maximumChunkItems: UInt? = null,
)

public data class TranslationBatchOutcome(
    public val items: List<TranslationBatchItemOutcome>,
    public val systemicFailure: TranslationFailure? = null,
)

public sealed interface TranslationBatchItemOutcome {
    public data class Success(public val result: TranslationResult) : TranslationBatchItemOutcome
    public data class Failure(
        public val requestId: TranslationRequestId,
        public val reason: TranslationFailure,
    ) : TranslationBatchItemOutcome
}
```

Ordering must match input ordering. A systemic runtime/service failure may fail remaining items. Per-item validation failures do not erase successful items.

## 12. Catalog and capabilities

```kotlin
public interface TranslationCatalog {
    public val supportedPairs: Set<LanguagePair>
    public fun supports(pair: LanguagePair): Boolean
    public fun targetsFor(source: LanguageTag): Set<LanguageTag>
    public fun sourcesFor(target: LanguageTag): Set<LanguageTag>
    public fun info(pair: LanguagePair): TranslationPairInfo?
}

public data class TranslationPairInfo(
    public val pair: LanguagePair,
    public val modelVersion: String,
    public val installation: ModelInstallationState,
    public val runtime: ModelRuntimeState,
    public val capabilities: TranslationCapabilities,
)

public data class TranslationCapabilities(
    public val batchTranslation: Boolean,
    public val structuredText: Boolean,
    public val alignment: CapabilityState,
    public val qualityEstimation: CapabilityState,
    public val pivotTranslation: CapabilityState,
)

public enum class CapabilityState {
    Unsupported,
    Experimental,
    Supported,
}
```

The catalog is derived from the immutable approved model manifest, not the live Mozilla registry.

## 13. Model management

```kotlin
public interface TranslationModels {
    public val installedModels: StateFlow<Set<LanguagePair>>
    public val loadedModels: StateFlow<Set<LanguagePair>>

    public fun state(pair: LanguagePair): StateFlow<ModelState>
    public suspend fun downloadRequirement(pair: LanguagePair): TranslationOutcome<ModelDownloadRequirement>
    public suspend fun install(
        pair: LanguagePair,
        options: ModelAcquisitionOptions = ModelAcquisitionOptions.Default,
    ): TranslationOutcome<ModelInstallation>
    public suspend fun preload(
        pair: LanguagePair,
        options: ModelAcquisitionOptions = ModelAcquisitionOptions.Default,
    ): TranslationOutcome<Unit>
    public suspend fun unload(pair: LanguagePair): TranslationOutcome<Unit>
    public suspend fun removeFromDisk(pair: LanguagePair): TranslationOutcome<Unit>
    public suspend fun pin(pair: LanguagePair): TranslationOutcome<ModelPinLease>
    public suspend fun retainOnDisk(pair: LanguagePair): TranslationOutcome<ModelRetentionLease>
    public suspend fun storageSnapshot(): TranslationOutcome<ModelStorageSnapshot>
}

public interface ModelPinLease {
    public val pair: LanguagePair
    public fun close()
}

public interface ModelRetentionLease {
    public val pair: LanguagePair
    public fun close()
}
```

Leases are idempotent and reference-counted internally. A model with active work or active leases cannot be evicted.

`translator()` is local-only and fails with `ModelNotInstalled` when necessary. `ensureTranslator()` and explicit model install/preload operations may acquire model bytes according to policy.

## 14. Model states

```kotlin
public sealed interface ModelState {
    public data object Unsupported : ModelState
    public data object NotInstalled : ModelState
    public data class Downloading(
        public val downloadedBytes: ULong,
        public val totalBytes: ULong,
    ) : ModelState
    public data object Verifying : ModelState
    public data object Installing : ModelState
    public data object Installed : ModelState
    public data object Loading : ModelState
    public data object Loaded : ModelState
    public data class Failed(public val reason: TranslationFailure) : ModelState
}

public enum class ModelInstallationState {
    NotInstalled,
    Installed,
}

public enum class ModelRuntimeState {
    Unloaded,
    Loaded,
}
```

## 15. Model acquisition options

```kotlin
public data class ModelAcquisitionOptions(
    public val networkPolicy: ModelNetworkPolicy,
    public val allowResume: Boolean,
) {
    public companion object {
        public val Default: ModelAcquisitionOptions
    }
}

public enum class ModelNetworkPolicy {
    UseServiceDefault,
    WifiOnly,
    AllowMetered,
    OfflineOnly,
}

public data class ModelDownloadRequirement(
    public val totalBytes: ULong,
    public val downloadedBytes: ULong,
    public val remainingBytes: ULong,
)
```

## 16. Runtime information and observability

```kotlin
public data class TranslationRuntimeInfo(
    public val libraryVersion: String,
    public val nativeAbiMajor: UInt,
    public val nativeAbiMinor: UInt,
    public val firefoxRevision: String,
    public val bergamotVersion: String,
    public val modelManifestRevision: String,
    public val platform: String,
    public val architecture: String,
    public val accelerationProfile: String,
)

public fun interface TranslationObserver {
    public fun onEvent(event: TranslationDiagnosticEvent)
}

public sealed interface TranslationDiagnosticEvent {
    public data class RuntimeInitialized(public val info: TranslationRuntimeInfo) : TranslationDiagnosticEvent
    public data class ModelStateChanged(public val pair: LanguagePair, public val state: ModelState) : TranslationDiagnosticEvent
    public data class TranslationCompleted(
        public val pair: LanguagePair,
        public val inputCharacters: UInt,
        public val duration: Duration,
    ) : TranslationDiagnosticEvent
    public data class QueueDepthChanged(public val requests: UInt, public val bytes: ULong) : TranslationDiagnosticEvent
    public data class FailureObserved(public val category: String) : TranslationDiagnosticEvent
}
```

No diagnostic type may contain source text, translated text, auth data, full sensitive URLs, native pointers, or arbitrary file contents.

## 17. Optional language detection

```kotlin
@ExperimentalTranslationApi
public interface LanguageDetection {
    public suspend fun detect(text: String): LanguageDetectionOutcome
}

public sealed interface LanguageDetectionOutcome {
    public data class Detected(
        public val language: LanguageTag,
        public val confidence: Double,
    ) : LanguageDetectionOutcome
    public data class Failure(public val reason: LanguageDetectionFailure) : LanguageDetectionOutcome
}
```

The 1.0 core publishes the capability contract and fakes. It does not bundle a detector unless a separate approved work package selects and validates one.

## 18. Experimental marker

```kotlin
@RequiresOptIn(
    message = "This API is experimental and may change before stabilization.",
    level = RequiresOptIn.Level.ERROR,
)
@Retention(AnnotationRetention.BINARY)
@Target(
    AnnotationTarget.CLASS,
    AnnotationTarget.FUNCTION,
    AnnotationTarget.PROPERTY,
    AnnotationTarget.TYPEALIAS,
)
public annotation class ExperimentalTranslationApi
```

Stable APIs may never be relabeled experimental to bypass compatibility rules.

## 19. API invariants

- public values are immutable;
- no public mutable collection;
- no global singleton service;
- no hidden network call from `translator`, `translate`, or `translateBatch`;
- no direct model pair silently pivots;
- no stale/cancelled/deadline-expired result is delivered;
- no native resource survives a closed service;
- no active/pinned model is evicted;
- same release/config/profile/request is deterministic;
- public behavior is identical across Kotlin, Java, and Swift facades.

<!-- END FILE: architecture/PUBLIC_API_SPEC.md -->

---

<!-- BEGIN FILE: architecture/JAVA_SWIFT_FACADE_SPEC.md -->

# Source file: `architecture/JAVA_SWIFT_FACADE_SPEC.md`

# Java and Swift Facade Specification

## 1. Principle

The canonical KMP API is the sole source of semantics. Java and Swift facades improve language ergonomics only. They may not add policy, model behavior, scheduling, network behavior, or failure semantics.

## 2. Java facade

Package:

```text
io.linguum.translation.java
```

### Required experience

```java
TranslationService service = TranslationServices
    .create("io.linguum.desktop")
    .toCompletableFuture()
    .join()
    .getOrThrow();

LanguagePair pair = LanguagePairs.of("es", "en");

Translator translator = service
    .translator(pair)
    .toCompletableFuture()
    .join()
    .getOrThrow();

CompletionStage<JavaTranslationOutcome<JavaTranslationResult>> stage =
    translator.translate("¿Dónde estás?");
```

### Java rules

- expose `CompletionStage`, not coroutine internals;
- avoid Kotlin `Unit`, mangled names, default-argument artifacts, and companion syntax in normal usage;
- expose immutable Java collections or unmodifiable views;
- map `StateFlow` to an explicit `Flow.Publisher`/listener facade only where stable and tested;
- support cancellation through returned `CompletableFuture`/stage adapter;
- Java outcome/failure wrappers preserve all canonical failure categories;
- Java facade methods contain no business logic.

### Required Java consumer fixture

A pure Java 17 Gradle project must compile and run without Kotlin source. It must:

- create a fake testing service;
- create a production service in local model mode;
- translate one sentence;
- observe model state;
- close the service;
- prove cancellation and typed failure mapping.

The exported Java API is snapshotted and compatibility-checked.

## 3. Swift facade strategy

Kotlin Swift export is Alpha and is not the stable v1 API mechanism.

Use:

```text
KMP Objective-C-compatible umbrella framework
        +
handwritten Swift overlay
        =
LinguumTranslation XCFramework/Swift Package
```

Swift module:

```text
LinguumTranslation
```

### Required Swift experience

```swift
let service = try await LinguumTranslationService.create(
    configuration: .default
)

let pair = try LanguagePair(source: "es", target: "en")
let translator = try await service.translator(pair: pair)
let result = try await translator.translate(text: "¿Dónde estás?")

print(result.text)
```

### Swift rules

- use `async throws`;
- map typed canonical failures to a documented `LinguumTranslationError` enum/struct hierarchy;
- expose `AsyncStream` or a documented observation token for model/service state;
- hide Kotlin coroutine completion handlers, Objective-C generated names, Kotlin collections, and internal wrapper types;
- map immutable Kotlin values to Swift value-like wrappers where appropriate;
- `close()` remains explicit and idempotent;
- cancellation of a Swift task propagates to the canonical coroutine operation;
- Swift overlay contains no model, scheduling, or network policy.

### Required Swift consumer fixture

An independent SwiftPM/Xcode fixture must:

- resolve the binary package;
- import `LinguumTranslation`;
- compile async factory/translate/error/state APIs;
- run on iOS arm64 simulator and device validation tiers;
- verify public symbol names against a checked-in Swift API snapshot.

## 4. XCFramework and SwiftPM publication

The primary repository builds:

```text
LinguumTranslation.xcframework
LinguumTranslation.xcframework.zip
```

The release computes:

```bash
swift package compute-checksum LinguumTranslation.xcframework.zip
```

A companion repository, created in M9, publishes `Package.swift` containing a binary target pointing to the exact GitHub release asset and checksum.

The package version must equal the primary library release tag.

## 5. Compatibility gates

Every PR affecting public API runs:

- Kotlin API validation;
- JVM bytecode/API validation;
- pure Java consumer compile;
- Objective-C header diff;
- Swift overlay API diff;
- pure Swift consumer compile.

A stable public symbol removal, rename, type change, async/error semantic change, or generated-name degradation is a compatibility failure.

<!-- END FILE: architecture/JAVA_SWIFT_FACADE_SPEC.md -->

---

<!-- BEGIN FILE: architecture/NATIVE_ABI_SPEC.md -->

# Source file: `architecture/NATIVE_ABI_SPEC.md`

# Stable Native C ABI Specification

## 1. Purpose

The Linguum C ABI is the only contract between platform bindings and Mozilla/Bergamot C++ internals.

It must remain stable even when Firefox changes its pinned source or Mozilla changes C++ classes.

Header path:

```text
native/abi/include/linguum_translation.h
```

Symbol prefix:

```text
linguum_translation_
```

## 2. ABI version

Initial ABI:

```text
major = 1
minor = 0
```

Rules:

- major change: incompatible struct, ownership, symbol, or semantic change;
- minor change: backward-compatible additive function/field capability;
- patch behavior is represented by library SemVer, not ABI version;
- Kotlin/JNI/cinterop checks ABI before creating a runtime;
- incompatible runtime is rejected before any non-version ABI call.

Required functions:

```c
uint32_t linguum_translation_abi_major(void);
uint32_t linguum_translation_abi_minor(void);
```

## 3. Header shape

Normative starting header:

```c
#ifndef LINGUUM_TRANSLATION_H
#define LINGUUM_TRANSLATION_H

#include <stddef.h>
#include <stdint.h>

#if defined(_WIN32)
  #if defined(LINGUUM_TRANSLATION_BUILD)
    #define LINGUUM_TRANSLATION_API __declspec(dllexport)
  #else
    #define LINGUUM_TRANSLATION_API __declspec(dllimport)
  #endif
#else
  #define LINGUUM_TRANSLATION_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

#define LINGUUM_TRANSLATION_ABI_MAJOR 1u
#define LINGUUM_TRANSLATION_ABI_MINOR 0u

typedef struct linguum_translation_runtime linguum_translation_runtime;
typedef struct linguum_translation_model linguum_translation_model;
typedef struct linguum_translation_translator linguum_translation_translator;
typedef struct linguum_translation_result linguum_translation_result;
typedef struct linguum_translation_error linguum_translation_error;
typedef struct linguum_translation_runtime_info linguum_translation_runtime_info;

typedef struct linguum_translation_string_view {
    const uint8_t* data;
    size_t length;
} linguum_translation_string_view;

typedef enum linguum_translation_status {
    LINGUUM_TRANSLATION_STATUS_OK = 0,

    LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT = 100,
    LINGUUM_TRANSLATION_STATUS_INVALID_UTF8 = 101,
    LINGUUM_TRANSLATION_STATUS_INVALID_HANDLE = 102,
    LINGUUM_TRANSLATION_STATUS_ABI_INCOMPATIBLE = 103,
    LINGUUM_TRANSLATION_STATUS_RUNTIME_CLOSED = 104,
    LINGUUM_TRANSLATION_STATUS_REQUEST_TOO_LARGE = 105,

    LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID = 200,
    LINGUUM_TRANSLATION_STATUS_MODEL_LOAD_FAILED = 201,
    LINGUUM_TRANSLATION_STATUS_MODEL_INCOMPATIBLE = 202,
    LINGUUM_TRANSLATION_STATUS_MODEL_CORRUPT = 203,

    LINGUUM_TRANSLATION_STATUS_TRANSLATION_FAILED = 300,

    LINGUUM_TRANSLATION_STATUS_UNSUPPORTED_CPU = 400,
    LINGUUM_TRANSLATION_STATUS_PLATFORM_UNSUPPORTED = 401,

    LINGUUM_TRANSLATION_STATUS_OUT_OF_MEMORY = 500,
    LINGUUM_TRANSLATION_STATUS_INTERNAL_ERROR = 900
} linguum_translation_status;

typedef enum linguum_translation_input_format {
    LINGUUM_TRANSLATION_INPUT_PLAIN_TEXT = 0,
    LINGUUM_TRANSLATION_INPUT_INTERNAL_STRUCTURED = 1
} linguum_translation_input_format;

typedef struct linguum_translation_runtime_config {
    uint32_t struct_size;
    uint32_t expected_abi_major;
    uint32_t expected_abi_minor;
    uint32_t worker_count;
    uint64_t maximum_input_bytes;
    uint64_t reserved_u64[8];
    const void* reserved_ptr[8];
} linguum_translation_runtime_config;

typedef struct linguum_translation_model_descriptor {
    uint32_t struct_size;
    linguum_translation_string_view language_pair;
    linguum_translation_string_view model_path;
    linguum_translation_string_view shortlist_path;
    const linguum_translation_string_view* vocabulary_paths;
    size_t vocabulary_path_count;
    linguum_translation_string_view configuration_yaml;
    uint64_t reserved_u64[8];
    const void* reserved_ptr[8];
} linguum_translation_model_descriptor;

typedef struct linguum_translation_request {
    uint32_t struct_size;
    linguum_translation_string_view input;
    linguum_translation_input_format input_format;
    uint32_t reserved_u32[8];
    uint64_t reserved_u64[8];
    const void* reserved_ptr[8];
} linguum_translation_request;

LINGUUM_TRANSLATION_API uint32_t linguum_translation_abi_major(void);
LINGUUM_TRANSLATION_API uint32_t linguum_translation_abi_minor(void);

LINGUUM_TRANSLATION_API linguum_translation_status
linguum_translation_runtime_create(
    const linguum_translation_runtime_config* config,
    linguum_translation_runtime** runtime_out,
    linguum_translation_error** error_out
);

LINGUUM_TRANSLATION_API linguum_translation_status
linguum_translation_runtime_info_create(
    const linguum_translation_runtime* runtime,
    linguum_translation_runtime_info** info_out,
    linguum_translation_error** error_out
);

LINGUUM_TRANSLATION_API void
linguum_translation_runtime_destroy(linguum_translation_runtime* runtime);

LINGUUM_TRANSLATION_API linguum_translation_status
linguum_translation_model_load(
    linguum_translation_runtime* runtime,
    const linguum_translation_model_descriptor* descriptor,
    linguum_translation_model** model_out,
    linguum_translation_error** error_out
);

LINGUUM_TRANSLATION_API void
linguum_translation_model_destroy(linguum_translation_model* model);

LINGUUM_TRANSLATION_API linguum_translation_status
linguum_translation_translator_create(
    linguum_translation_runtime* runtime,
    linguum_translation_model* model,
    linguum_translation_translator** translator_out,
    linguum_translation_error** error_out
);

LINGUUM_TRANSLATION_API void
linguum_translation_translator_destroy(
    linguum_translation_translator* translator
);

LINGUUM_TRANSLATION_API linguum_translation_status
linguum_translation_translator_translate(
    linguum_translation_translator* translator,
    const linguum_translation_request* request,
    linguum_translation_result** result_out,
    linguum_translation_error** error_out
);

LINGUUM_TRANSLATION_API linguum_translation_string_view
linguum_translation_result_text(
    const linguum_translation_result* result
);

LINGUUM_TRANSLATION_API void
linguum_translation_result_destroy(linguum_translation_result* result);

LINGUUM_TRANSLATION_API int32_t
linguum_translation_error_code(const linguum_translation_error* error);

LINGUUM_TRANSLATION_API linguum_translation_string_view
linguum_translation_error_message(const linguum_translation_error* error);

LINGUUM_TRANSLATION_API void
linguum_translation_error_destroy(linguum_translation_error* error);

LINGUUM_TRANSLATION_API linguum_translation_string_view
linguum_translation_runtime_info_library_version(
    const linguum_translation_runtime_info* info
);

LINGUUM_TRANSLATION_API linguum_translation_string_view
linguum_translation_runtime_info_firefox_revision(
    const linguum_translation_runtime_info* info
);

LINGUUM_TRANSLATION_API linguum_translation_string_view
linguum_translation_runtime_info_bergamot_version(
    const linguum_translation_runtime_info* info
);

LINGUUM_TRANSLATION_API linguum_translation_string_view
linguum_translation_runtime_info_acceleration_profile(
    const linguum_translation_runtime_info* info
);

LINGUUM_TRANSLATION_API void
linguum_translation_runtime_info_destroy(
    linguum_translation_runtime_info* info
);

#ifdef __cplusplus
}
#endif

#endif
```

The implementation may add backward-compatible minor-version functions, but may not remove or reinterpret these contracts within ABI major 1.

## 4. Ownership

- The caller owns input buffers for the duration of the call only.
- The ABI copies or consumes input synchronously before returning.
- Native-owned runtime/model/translator/result/error/info handles are destroyed only by their matching Linguum destroy functions.
- Bindings must never call `free`, `delete`, `LocalFree`, `CoTaskMemFree`, or platform allocators on ABI-owned memory.
- Returned string views are borrowed from their owning result/error/info object and remain valid only until that object is destroyed.
- Destroy functions are idempotent only for null pointers; destroying the same non-null handle twice is invalid and must be caught in debug/abuse tests.

## 5. Error contract

- no C++ exception crosses the ABI;
- every exported implementation function is exception-guarded;
- status code is the programmatic contract;
- error message is diagnostic, privacy-safe, and not used for branching;
- error messages contain no source or translated text;
- `error_out` may be null;
- when provided, successful calls set `*error_out = NULL`;
- failed calls either create an error object or return a status whose allocation failure makes that impossible;
- there is no global or thread-local `last_error`.

## 6. Thread safety

- ABI version functions are thread-safe.
- runtime creation/destruction is externally serialized.
- model load/destroy is externally serialized against destruction but may occur while other model generations translate when the runtime supports it.
- translator calls may originate from multiple platform threads, but the Kotlin scheduler normally serializes a pair-bound translator; the native adapter must still reject invalid lifecycle races safely.
- result/error/info objects are immutable after creation.
- no callback from C++ into Kotlin/Java/Swift is part of ABI v1.

## 7. Synchronous boundary rationale

ABI v1 uses a synchronous `translate` call even though Mozilla internally uses `AsyncService`.

The adapter:

1. submits to `AsyncService`;
2. waits on its private promise/future;
3. returns the completed result through C ABI.

Platform bindings invoke this from library-owned background execution contexts. This avoids cross-language callback lifetime complexity and preserves cooperative cancellation semantics: queued work can be removed before the call, while an already-running ~30 ms call safely completes and may have its result discarded.

## 8. Model descriptor

The C ABI accepts only already-installed, fully verified model paths/configuration.

It never:

- downloads models;
- trusts the live Mozilla registry;
- chooses model versions;
- verifies network policy;
- manages disk eviction.

Those are Kotlin model-management responsibilities.

The native adapter validates that files exist/read, config is bounded, vocab count is valid, and model creation succeeds. Cryptographic integrity must already have been established by the model installer; a native compatibility probe remains required before activation.

## 9. Structured input

`LINGUUM_TRANSLATION_INPUT_INTERNAL_STRUCTURED` is a private internal serialization between the Kotlin structured-text module and the native adapter. It is not arbitrary HTML and is not exposed as public user input.

Its exact grammar must be versioned and tested before M7. ABI major 1 reserves the enum but production support remains capability-gated until M7 passes.

## 10. CPU dispatch

The loader selects a compatible native artifact before calling the ABI.

- no unsupported instruction may be executed to detect support;
- no SIGILL/illegal-instruction recovery strategy;
- selected acceleration profile is exposed through runtime info;
- incompatible CPU returns `UNSUPPORTED_CPU` before model load;
- optimized and fallback artifacts share ABI major/minor and behavior.

## 11. ABI testing

Required:

- C compiler consumer test;
- C++ consumer test using only the C header;
- JNI and cinterop tests;
- struct-size forward/backward compatibility tests;
- symbol export allowlist;
- binary ABI snapshot/diff;
- null/invalid/destroyed handle abuse tests;
- invalid UTF-8 and embedded NUL tests;
- oversized input tests;
- allocation-failure tests where feasible;
- ASan/UBSan/TSan matrix;
- coverage-guided fuzzing of ABI argument validation;
- repeated create/load/translate/destroy soak tests.

A breaking ABI change requires a major ABI bump, migration documentation, compatibility fixture updates, and a library major release if it affects stable consumers.

<!-- END FILE: architecture/NATIVE_ABI_SPEC.md -->

---

<!-- BEGIN FILE: architecture/MODEL_MANIFEST_SPEC.md -->

# Source file: `architecture/MODEL_MANIFEST_SPEC.md`

# Approved Model Manifest and Installation Specification

## 1. Purpose

Each library release embeds one immutable approved model manifest. The manifest determines:

- supported direct language pairs;
- exact Mozilla model/version/architecture;
- exact artifact locations;
- compressed and installed hashes/sizes;
- required runtime capabilities;
- compatibility with the Firefox-pinned engine revision.

The live Mozilla registry is never consulted by translation runtime code.

## 2. Files

```text
translation-model-manifest/src/commonMain/resources/
├── approved-models.json
└── approved-models.sha256
```

Release evidence also contains:

```text
publication/provenance/
├── approved-models.json
├── approved-models.sha256
├── source-registry-snapshot.json
├── model-drift-report.json
└── model-validation-report.md
```

The manifest is authenticated as part of the signed/attested Maven/AAR/XCFramework release artifact. Runtime verifies its embedded digest before parsing. Runtime-downloaded alternate manifests are forbidden in v1.

## 3. Schema

Canonical structure:

```json
{
  "schemaVersion": 1,
  "manifestRevision": "2026-08-20.1",
  "libraryVersion": "1.0.0",
  "firefox": {
    "repository": "mozilla-firefox/firefox",
    "translationsRepository": "mozilla/translations",
    "translationsRevision": "eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d",
    "bergamotVersion": "v0.6.0"
  },
  "sourceRegistry": {
    "url": "https://storage.googleapis.com/moz-fx-translations-data--303e-prod-translations-data/db/models.json",
    "retrievedAt": "2026-08-20T00:00:00Z",
    "sha256": "..."
  },
  "models": [
    {
      "id": "es-en@2.0",
      "pair": {
        "source": "es",
        "target": "en"
      },
      "mozillaVersion": "2.0",
      "releaseStatus": "Release",
      "architecture": "base-memory",
      "capabilities": {
        "plainText": true,
        "structuredText": true,
        "alignment": "experimental",
        "qualityEstimation": "unsupported"
      },
      "artifacts": [
        {
          "role": "model",
          "fileName": "model.esen.intgemm.alphas.bin",
          "compression": "gzip",
          "downloadSources": [
            {
              "kind": "mozilla",
              "url": "https://.../model.esen.intgemm.alphas.bin.gz"
            }
          ],
          "compressedSize": 0,
          "compressedSha256": "...",
          "installedSize": 0,
          "installedSha256": "4aed7734152ae0045d1a69ae49c86cfda18f53c61f90e95e1d1de1c7c7c3b033"
        },
        {
          "role": "vocabulary",
          "fileName": "vocab.esen.spm",
          "compression": "gzip",
          "downloadSources": [{ "kind": "mozilla", "url": "https://..." }],
          "compressedSize": 0,
          "compressedSha256": "...",
          "installedSize": 0,
          "installedSha256": "..."
        },
        {
          "role": "shortlist",
          "fileName": "lex.50.50.esen.s2t.bin",
          "compression": "gzip",
          "downloadSources": [{ "kind": "mozilla", "url": "https://..." }],
          "compressedSize": 0,
          "compressedSha256": "...",
          "installedSize": 0,
          "installedSha256": "..."
        }
      ],
      "runtimeConfiguration": {
        "configurationResource": "configs/es-en.yml",
        "configurationSha256": "..."
      }
    }
  ]
}
```

`schemas/model-manifest.schema.json` is authoritative for syntax.

## 4. Generation workflow

Only the protected model/upstream compatibility workflow may generate the manifest.

Steps:

1. fetch Firefox pin metadata;
2. fetch and hash the Mozilla model registry;
3. select candidate entries with `releaseStatus == Release`;
4. apply the approved language/model policy;
5. download all artifacts into an isolated workspace;
6. verify any upstream-published hashes;
7. compute compressed size/hash;
8. decompress safely with expansion limits;
9. compute installed size/hash for every artifact;
10. generate deterministic model config;
11. build every runtime profile;
12. install/load/translate/unload each pair;
13. run golden/drift/quality sanity suite;
14. run performance subset per architecture class;
15. sort canonical JSON by language pair and artifact role;
16. write manifest and digest;
17. create compatibility PR with reports;
18. never merge automatically.

## 5. Source abstraction

A `ModelSource` supplies bytes but is not trusted.

Supported source kinds:

- Mozilla official HTTPS;
- future Linguum mirror;
- enterprise HTTPS mirror;
- local filesystem/offline bundle;
- test source.

Every source must produce the exact artifact bytes identified by the embedded manifest.

No source may override:

- model version;
- expected size;
- hash;
- language pair;
- runtime configuration;
- capabilities.

## 6. Transactional installation

Per-model directory layout:

```text
<storage-root>/
├── installed/
│   └── es-en/
│       └── 2.0/
│           ├── model.esen.intgemm.alphas.bin
│           ├── vocab.esen.spm
│           ├── lex.50.50.esen.s2t.bin
│           ├── model.yml
│           └── installation.json
├── staging/
│   └── <transaction-id>/
├── quarantine/
├── locks/
└── store.json
```

Installation sequence:

1. acquire process-safe pair/version installation lock;
2. check current verified installation;
3. calculate required bytes plus safety margin;
4. preflight available storage;
5. create unique staging directory;
6. download with bounded retries/cancellation/resume policy;
7. verify compressed size/hash;
8. stream decompress with output limit;
9. verify installed size/hash;
10. write generated config and installation metadata;
11. run native compatibility probe;
12. fsync files/directories where platform supports it;
13. atomically rename/promote staging directory;
14. update store metadata atomically;
15. expose `Installed` state;
16. clean stale staging entries on restart.

If any step fails, the previous installation remains active and the staged files are removed or quarantined.

## 7. Resumable downloads

- resume only when the source supports safe byte ranges and entity consistency;
- retain partial files only with recorded URL, expected total size, validator/ETag where available, and manifest identity;
- revalidate range response and final complete hash;
- if safe resume cannot be proven, restart;
- never install a partial artifact;
- cancellation leaves only a recoverable staging state, never an installed state.

## 8. Activation and model generations

A verified installed model is not automatically active.

Activation:

1. load candidate generation;
2. run canary translation and runtime compatibility checks;
3. atomically mark new generation for new requests;
4. allow old generation's in-flight requests to finish;
5. destroy old generation when reference count reaches zero;
6. retain previous installed version temporarily for rollback according to policy.

A failed candidate activation leaves the old generation active.

## 9. Disk and memory policies

Disk retention and memory pinning are separate.

- memory pin lease prevents loaded-model eviction;
- disk retention lease prevents installed-model eviction;
- active, loading, installing, verifying, pinned, retained, and activating models are never evicted;
- disk eviction is byte-budgeted LRU;
- memory eviction is byte-budgeted LRU;
- inability to free enough space returns typed `InsufficientStorage`.

## 10. Runtime invariants

- runtime never resolves `latest`;
- same library release exposes same catalog;
- runtime never accepts a manifest supplied by a remote model source;
- all installed files are hash-verified before native load;
- installed model paths are never public API;
- corrupt existing installation is quarantined and reported;
- offline translation works indefinitely with a valid installed model;
- library upgrades do not silently activate a new model without their embedded manifest and installation/activation flow.

<!-- END FILE: architecture/MODEL_MANIFEST_SPEC.md -->

---

<!-- BEGIN FILE: architecture/UPSTREAM_FIREFOX_POLICY.md -->

# Source file: `architecture/UPSTREAM_FIREFOX_POLICY.md`

# Firefox Upstream Compatibility and Vendoring Policy

## 1. Canonical source

The production engine source is the exact `mozilla/translations` revision selected by Firefox's own pin metadata.

Initial pin:

```text
Firefox repository:         mozilla-firefox/firefox
pin file:                   toolkit/components/translations/bergamot-translator/moz.yaml
translations repository:    mozilla/translations
revision:                   eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d
Bergamot release:           v0.6.0
```

Do not use:

- `mozilla/translations/main`;
- `browsermt/bergamot-translator`;
- archived `mozilla/bergamot-translator`;
- a permanent Linguum fork;
- a newer release not yet pinned and validated by Firefox.

## 2. Immutable snapshot

Vendored path:

```text
native/upstream/mozilla-translations/
```

The update tool creates a clean recursive checkout, strips Git administrative data, normalizes only archive metadata—not source bytes—and records:

```text
native/UPSTREAM.json
native/UPSTREAM_LOCK.json
native/SOURCE_TREE.sha256
```

`UPSTREAM_LOCK.json` records:

- top-level repository URL and SHA;
- every recursive submodule path, URL, and SHA;
- source archive SHA-256;
- license identities;
- pin metadata source SHA;
- generated timestamp and workflow run identity.

Normal PRs fail if files under the upstream path differ from the lock.

## 3. Linguum-owned code boundary

Original code lives only outside the upstream tree:

```text
native/abi/
native/mozilla-adapter/
native/runtime-build/
native/patches/
```

The adapter translates stable C ABI calls into current Mozilla C++ APIs.

No Mozilla source is copied into Apache-licensed files without an explicit license/provenance review.

## 4. Patch queue

Patches are exceptions, not normal development.

```text
native/patches/
├── PATCHES.yaml
├── windows/
├── macos/
├── linux/
├── android/
└── ios/
```

Each patch has metadata matching `schemas/patch-metadata.schema.json`:

- unique ID;
- title/reason;
- exact upstream revision;
- affected platforms and paths;
- upstream issue/PR URL where available;
- owner approval reference;
- introduction version;
- removal condition;
- license classification;
- tests proving necessity and behavior.

Builds apply patches only in a temporary worktree/build workspace. The immutable snapshot remains unchanged.

Upstream update PRs must attempt to remove every patch and fail review if an already-upstreamed patch remains without justification.

## 5. Scheduled checker

Workflow:

```text
.github/workflows/upstream-firefox-check.yml
```

Schedule: weekly and manual.

Steps:

1. fetch current Firefox default branch;
2. read/parse `moz.yaml`;
3. compare revision/release/license with `native/UPSTREAM.json`;
4. if unchanged, record success and exit;
5. if changed, create branch `automation/firefox-pin-<short-sha>`;
6. generate a compatibility work-package scaffold and source diff report;
7. open a draft PR;
8. do not update vendored source or merge automatically until compatibility workflow is explicitly dispatched/approved.

## 6. Compatibility PR requirements

A Firefox pin update PR must contain:

- old/new Firefox pin and metadata diff;
- old/new recursive source lock;
- license diff;
- patch reapplication/removal report;
- all-platform native builds;
- C ABI compatibility;
- public API compatibility;
- all approved model pairs install/load/translate/unload;
- deterministic output comparison;
- translation drift report;
- performance report by runtime profile;
- sanitizers/fuzz/stress results;
- SBOM and dependency/submodule changes;
- release notes and migration impact.

It must never auto-merge.

## 7. Security updates

A Mozilla security advisory or urgent Firefox pin update may use an expedited compatibility PR, but it cannot skip:

- source identity;
- license checks;
- required native builds;
- ABI tests;
- model load/canary translation;
- sanitizer smoke;
- provenance;
- maintainer approval.

Performance/full-model extended work may continue after an emergency patch release only when the owner explicitly accepts a documented temporary exception and the absolute product floor remains green.

<!-- END FILE: architecture/UPSTREAM_FIREFOX_POLICY.md -->

---

<!-- BEGIN FILE: architecture/PLATFORM_SUPPORT_MATRIX.md -->

# Source file: `architecture/PLATFORM_SUPPORT_MATRIX.md`

# Platform and Native Backend Support Matrix

## 1. Public platform promise

A platform is supported only when its production artifact is built, packaged, consumed, executed, and verified in CI/release evidence.

## 2. Desktop delivery model

Desktop uses one Kotlin/JVM target with Java 17 bytecode and JNI-loaded native runtimes.

| Platform | Public runtime | Native artifact | Minimum OS | Primary validation |
|---|---|---|---|---|
| Windows x64 | JVM | DLL | Windows 10 22H2 | Windows 10/11 physical/VM integration |
| macOS arm64 | JVM | dylib | macOS 13 | Apple Silicon runner + real smoke |
| macOS x64 | JVM | dylib | macOS 13 where supported | Intel build/run tier |
| Linux x64 | JVM | `.so` | glibc 2.35 | Ubuntu 22.04/24.04 |
| Linux arm64 | JVM | `.so` | glibc 2.35 | real arm64 scheduled/release runner |

Do not publish Kotlin/Native desktop targets merely to claim desktop support.

## 3. Android

| ABI | Purpose | Minimum |
|---|---|---|
| `arm64-v8a` | production devices | API 26 |
| `x86_64` | emulator/development | API 26 |

Use the AGP 9 Android-KMP library plugin in an isolated Android platform module. Package JNI runtime through an AAR. Native dependencies should be statically linked into one exported JNI library per ABI where licensing permits, limiting exported symbols to `JNI_OnLoad` and the approved JNI bridge.

Do not support `armeabi-v7a` or `x86` in v1.

## 4. iOS

| Target | Purpose | Minimum |
|---|---|---|
| `iosArm64` | physical devices | iOS 15 |
| `iosSimulatorArm64` | Apple Silicon simulator | iOS 15 |
| `iosX64` | Intel simulator compatibility | iOS 15 |

Build the KMP umbrella framework and the native C++ runtime into a release XCFramework. The Swift facade is handwritten and distributed through SwiftPM.

`iosX64` is a lower-support Kotlin target and requires scheduled/release validation on an appropriate host. Failure must be reported, not hidden.

## 5. Toolchain lock

Initial lock:

```text
Kotlin                  2.4.10
Gradle                   9.5.0
JDK build runtime        21 LTS
JVM target               17
AGP                      9.1.1, with M0 compatibility proof
Android NDK              28.2.13676358
Android Build Tools      36.0.0
Xcode                    Kotlin 2.4.10-supported Xcode, initially 26.4
MSVC                     Visual Studio 2022 / toolset locked in toolchains file
CMake desktop            4.0.2 initially, because benchmark validated it
Ninja                    locked in toolchains file
```

All exact versions and container/runner images belong in:

```text
gradle/libs.versions.toml
toolchains/toolchains.lock.yaml
toolchains/ci-runners.lock.yaml
```

Toolchain upgrades require compatibility PRs.

## 6. Native backend profiles

Exact backend selection is an implementation result, not a public API.

### x86_64 optimized

Expected profile:

```text
FBGEMM
AVX2
Release optimization
one AsyncService worker/model
```

Initial authoritative benchmark profile:

```text
windows-x64-avx2
```

### x86_64 fallback

Must be proven in M1.

Requirements:

- no AVX2 instruction;
- no illegal-instruction-based detection;
- exact backend recorded;
- same C ABI/public behavior;
- correctness and product absolute latency gate;
- platform-specific artifact selected before load.

Do not claim fallback support until executable evidence exists.

### Apple arm64

Resolve and record the pinned source's ARM/Accelerate path. Validate on physical Apple Silicon and iOS device/simulator.

### Linux/Android arm64

Resolve and record the pinned source's ARM/NEON/RUY path. Validate on real ARM64, not compile-only evidence.

### Android x86_64

Use a compatible x86_64 profile that does not assume host AVX2. This is a development/emulator target and still must meet correctness and a documented performance floor.

## 7. CPU detection

The JVM loader detects:

- OS;
- normalized architecture;
- CPU capability needed for optimized profile;
- expected artifact digest and ABI.

Selection happens before loading native code.

The library may not:

- load an AVX2 binary and catch illegal instruction;
- choose based only on OS name;
- accept an unknown architecture as x64;
- use a downloaded executable runtime;
- fall back silently to a different translation engine.

## 8. Minimum-version validation

### Windows

- compile against supported SDK/toolset;
- run smoke on Windows 10 22H2 and Windows 11;
- avoid APIs newer than the floor unless dynamically guarded internally.

### macOS/iOS

- explicit deployment targets;
- inspect Mach-O minimum versions in release validation;
- run minimum-supported simulator/device tier where feasible.

### Linux

- build against Ubuntu 22.04/glibc 2.35 baseline container;
- inspect required GLIBC symbol versions;
- run on 22.04 and 24.04;
- no accidental dependency on build-host-only shared libraries.

### Android

- `minSdk = 26` enforced;
- native API level configured consistently;
- run emulator at minimum API and current API;
- physical arm64 release smoke.

## 9. Artifact naming

```text
linguum-translation-native-windows-x64-avx2-<version>.jar
linguum-translation-native-windows-x64-baseline-<version>.jar
linguum-translation-native-macos-arm64-<version>.jar
linguum-translation-native-macos-x64-<version>.jar
linguum-translation-native-linux-x64-avx2-<version>.jar
linguum-translation-native-linux-x64-baseline-<version>.jar
linguum-translation-native-linux-arm64-<version>.jar
translation-android-<version>.aar
LinguumTranslation.xcframework.zip
```

Artifact coordinates/variant names are implementation details and are not documented as consumer dependencies.

## 10. M1 hard gate

For every target/profile:

1. build exact pinned source plus Linguum adapter;
2. verify symbol allowlist and ABI version;
3. load Firefox-approved es→en model;
4. translate a fixed canary sentence;
5. compare non-empty expected-language result;
6. create/destroy 100 times;
7. record backend/toolchain/runtime info;
8. package artifact;
9. consume from a clean fixture;
10. push report and artifact hashes.

Stable API work cannot start until M1 is green or a blocker is accepted by the owner.

<!-- END FILE: architecture/PLATFORM_SUPPORT_MATRIX.md -->

---

<!-- BEGIN FILE: architecture/LICENSING_BOUNDARY.md -->

# Source file: `architecture/LICENSING_BOUNDARY.md`

# Licensing and Source-Compliance Boundary

## 1. License split

Original Linguum Translation source:

```text
Apache License 2.0
```

Mozilla-derived source and covered modifications:

```text
Mozilla Public License 2.0
```

The MPL is file-level copyleft. It permits combining MPL-covered files with Apache-2.0 files in a larger work, including static linking, while requiring recipients of distributed executable/library forms to be informed where the MPL-covered source can be obtained.

## 2. Directory classification

### Apache-2.0

```text
translation*/
platform/
facades/
native/abi/
native/mozilla-adapter/  (only independently written adapter code)
native/runtime-build/
testing/
build-logic/
scripts/
docs/
```

Every original source file carries an SPDX header where appropriate:

```text
SPDX-License-Identifier: Apache-2.0
```

### MPL-2.0

```text
native/upstream/mozilla-translations/**
```

Files retain their original notices and SPDX/license headers.

Patches that modify MPL-covered files are treated as MPL-covered source and distributed with corresponding source.

## 3. Prohibited contamination

- Do not paste Mozilla implementation code into Apache-licensed files.
- Do not remove or rewrite Mozilla notices.
- Do not label a modified Mozilla file Apache-2.0.
- Do not place Linguum application code inside the vendored tree.
- Do not ship an executable native artifact without corresponding-source information.

## 4. Required root files

```text
LICENSE                   Apache-2.0 full text
NOTICE                    Linguum notices and attribution summary
THIRD_PARTY_LICENSES.md   dependency/upstream licenses
SECURITY.md
```

## 5. Required release assets

Each release includes:

```text
linguum-translation-<version>-sources.zip
mozilla-translations-source-<revision>.tar.zst
UPSTREAM.json
UPSTREAM_LOCK.json
PATCHES.yaml
THIRD_PARTY_LICENSES.md
CycloneDX SBOM(s)
artifact checksums
provenance attestations
```

The Maven POM names Apache-2.0 as the license of the original library artifact and its descriptions/NOTICE clearly identify bundled MPL-covered components.

## 6. Corresponding source

The release notes and native artifact metadata must state:

- exact Mozilla repository and revision;
- where the exact vendored source archive can be downloaded;
- where applied patch source can be downloaded;
- the MPL-2.0 license link/text;
- the source archive SHA-256.

The corresponding-source location must remain durable for the lifetime of the distributed release.

## 7. Dependency license policy

Allowed by default:

- Apache-2.0
- MIT
- BSD-2-Clause
- BSD-3-Clause
- MPL-2.0 when isolated/compliant
- other permissive licenses after explicit approval

Review/block by default:

- GPL/AGPL/SSPL and strong copyleft dependencies;
- non-commercial/custom terms;
- unlicensed source;
- dependencies with unclear native redistribution rights;
- runtime model/data licenses not explicitly documented.

## 8. Legal checkpoint

Before `1.0.0-rc.1`, obtain a real legal/compliance review covering:

- Apache/MPL boundary;
- static native linking and third-party submodules;
- model distribution/download terms;
- Maven/AAR/XCFramework notices;
- corresponding source process;
- trademark naming/attribution;
- dependency license report.

Codex records completion evidence but must not claim to provide legal advice.

<!-- END FILE: architecture/LICENSING_BOUNDARY.md -->

---

<!-- BEGIN FILE: implementation/TECHNICAL_IMPLEMENTATION_PLAN.md -->

# Source file: `implementation/TECHNICAL_IMPLEMENTATION_PLAN.md`

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

<!-- END FILE: implementation/TECHNICAL_IMPLEMENTATION_PLAN.md -->

---

<!-- BEGIN FILE: implementation/MILESTONE_ROADMAP.md -->

# Source file: `implementation/MILESTONE_ROADMAP.md`

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

<!-- END FILE: implementation/MILESTONE_ROADMAP.md -->

---

<!-- BEGIN FILE: implementation/WORK_PACKAGES.md -->

# Source file: `implementation/WORK_PACKAGES.md`

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

<!-- END FILE: implementation/WORK_PACKAGES.md -->

---

<!-- BEGIN FILE: implementation/GIT_REMOTE_CHECKPOINT_PLAN.md -->

# Source file: `implementation/GIT_REMOTE_CHECKPOINT_PLAN.md`

# GitHub Repository Creation and Incremental Push Plan

## 1. Repository identity

Primary:

```text
owner:       StevenBuglione
repository:  linguum-translation
visibility:  public
url:         https://github.com/StevenBuglione/linguum-translation
```

Companion SwiftPM manifest repository created only in M9:

```text
StevenBuglione/linguum-translation-swift
```

## 2. Initial local creation

From the directory containing this handoff:

```bash
mkdir linguum-translation
cd linguum-translation
git init -b main
```

Copy the handoff files into the new repository unchanged. Do not copy benchmark model payloads or build output; retain only the provided compact evidence archive.

Inspect:

```bash
git status --short
```

Stage explicitly:

```bash
git add -- \
  START_HERE.md \
  README.md \
  AGENTS.md \
  CODEX_EXECUTION_CONTRACT.md \
  architecture \
  implementation \
  research \
  schemas \
  codex \
  scripts \
  templates
```

Commit:

```bash
git commit -m "M0-WP01: establish library implementation constitution"
```

## 3. Create remote and push immediately

```bash
gh auth status || gh auth login
gh repo create StevenBuglione/linguum-translation \
  --public \
  --source=. \
  --remote=origin \
  --push \
  --description "Firefox-compatible native translation for Kotlin Multiplatform"
gh repo set-default origin
```

Verify:

```bash
git remote -v
gh repo view StevenBuglione/linguum-translation --json nameWithOwner,isPrivate,url,defaultBranchRef
LOCAL_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
test "$LOCAL_SHA" = "$REMOTE_SHA"
```

Record both SHAs in `reports/work-packages/M0-WP01-VERIFICATION.md` and push that report in the next checkpoint.

## 4. Working branches

Never implement directly on `main` after the initial constitution push.

```bash
git switch -c codex/M0-WP02-gradle-toolchain
```

Push after the first clean checkpoint:

```bash
git push -u origin codex/M0-WP02-gradle-toolchain
```

Create draft PR immediately:

```bash
gh pr create \
  --draft \
  --base main \
  --head codex/M0-WP02-gradle-toolchain \
  --title "M0-WP02: establish pinned Gradle and Kotlin toolchain" \
  --body-file reports/work-packages/M0-WP02-PR.md
```

## 5. Incremental checkpoint rule

Push after each of these events:

- a module scaffold compiles under its narrow gate;
- one public contract slice plus tests is complete;
- one platform canary builds and runs;
- one native ABI ownership/error slice plus tests is complete;
- one model installation phase plus failure tests is complete;
- a generated manifest/source lock is verified;
- a consumer fixture becomes green;
- a bug fix has a permanent regression test;
- a work-package verification report is updated.

Do not wait until an entire milestone to push.

## 6. Checkpoint commands

### Bash/macOS/Linux

```bash
BRANCH="$(git branch --show-current)"
git status --short
./gradlew <narrow-work-package-gate> --warning-mode=fail
git diff --check
git add -- <intentional-paths>
git diff --cached --stat
git diff --cached --check
git commit -m "<MILESTONE>-<WP>: <imperative summary>"
git push origin "$BRANCH"
LOCAL_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git ls-remote origin "refs/heads/$BRANCH" | awk '{print $1}')"
test "$LOCAL_SHA" = "$REMOTE_SHA"
```

### PowerShell/Windows

```powershell
$Branch = git branch --show-current
git status --short
.\gradlew.bat <narrow-work-package-gate> --warning-mode=fail
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git diff --check
git add -- <intentional-paths>
git diff --cached --stat
git diff --cached --check
git commit -m "<MILESTONE>-<WP>: <imperative summary>"
git push origin $Branch
$LocalSha = (git rev-parse HEAD).Trim()
$RemoteSha = ((git ls-remote origin "refs/heads/$Branch") -split "`t")[0]
if ($LocalSha -ne $RemoteSha) { throw "Remote SHA mismatch" }
```

## 7. Staging restrictions

Never use:

```text
git add .
git add -A
git add --all
```

Before each commit inspect:

```bash
git diff --cached --name-status
git diff --cached
```

Large vendored/generated changes additionally require:

- expected file list;
- source/provenance manifest;
- no secrets scan;
- exact generated-command report.

## 8. Push quality

A checkpoint branch commit may be incomplete relative to the milestone, but it must not be broken relative to its declared scope.

Allowed scaffold checkpoint:

```text
module registered
empty interfaces compile
architecture tests updated
narrow gate green
report says implementation not started
```

Not allowed:

```text
code does not compile
failing tests committed without a blocker fixture
secrets present
checks disabled
TODO pretending to be implemented
```

## 9. No history rewriting

- no force push;
- no `git reset --hard` to discard other agent work;
- no rebasing a reviewed branch without approval;
- corrections are new commits;
- squash merge may be used by the protected merge workflow while original branch commits remain in GitHub history until branch deletion.

## 10. Main protection

After required PR checks have run at least once, apply a main-branch ruleset requiring:

- pull request;
- one approving owner review for protected architecture/upstream/ABI/release paths;
- required status checks;
- conversation resolution;
- linear history/squash merge policy;
- no force pushes;
- no deletion;
- no bypass, including administrators where supported;
- signed release tags;
- CODEOWNERS review.

The ruleset JSON and `scripts/admin/apply-main-ruleset.*` are committed and versioned. Applying the ruleset is an administrative work-package step with evidence.

## 11. Work-package remote evidence

Every verification report includes:

```text
branch:
local SHA:
remote SHA:
draft PR URL:
commits pushed:
last push command:
remote verification command/result:
```

## 12. Recovery

If local work is lost, the remote branch is the source of recovery.

If an unpushed change exists after a tool crash:

1. do not create a second divergent branch blindly;
2. inspect local status and remote SHA;
3. preserve the diff as a patch if necessary;
4. reset only after confirming remote state;
5. reapply and rerun gates;
6. push a new normal commit.

## 13. Release tags

Agents never create or move official version tags during implementation.

Only protected release workflow creates:

```text
v1.0.0-rc.1
v1.0.0
```

Tags are immutable and must point to the exact source commit recorded in release provenance.

<!-- END FILE: implementation/GIT_REMOTE_CHECKPOINT_PLAN.md -->

---

<!-- BEGIN FILE: implementation/TEST_CI_AND_QUALITY_GATES.md -->

# Source file: `implementation/TEST_CI_AND_QUALITY_GATES.md`

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

<!-- END FILE: implementation/TEST_CI_AND_QUALITY_GATES.md -->

---

<!-- BEGIN FILE: implementation/CI_WORKFLOW_SPEC.md -->

# Source file: `implementation/CI_WORKFLOW_SPEC.md`

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

<!-- END FILE: implementation/CI_WORKFLOW_SPEC.md -->

---

<!-- BEGIN FILE: implementation/PERFORMANCE_VALIDATION.md -->

# Source file: `implementation/PERFORMANCE_VALIDATION.md`

# Performance Validation Plan

## 1. Existing baseline

Retained evidence establishes current Firefox-pinned native Windows performance around:

```text
p50         11.13 ms
p95         30.00 ms
p99         38.26 ms
throughput  71.74 lines/sec
```

This is the initial `windows-x64-avx2` raw-engine reference, not a universal target.

## 2. Benchmark layers

### L0 Raw native

C++ harness invokes the adapter/C ABI or directly comparable native path with loaded model.

### L1 C ABI

C harness measures full stable C ABI overhead and result ownership.

### L2 Platform binding

- JVM → JNI → C ABI;
- Android → JNI → C ABI;
- iOS → cinterop → C ABI.

### L3 Kotlin service

Includes scheduler, request validation, model lookup, and result conversion.

### L4 End-to-end application boundary

Optional ECS/IPC integration benchmark after library completion; not part of the core Maven library gate but required by Linguum desktop integration.

## 3. Fixed benchmark corpus

Retain the validated 500 unique Spanish→English corpus and six deterministic shuffled rounds. Add versioned corpora for:

- short subtitles;
- medium/long prose;
- Unicode/structured spans;
- batch;
- model switching;
- other approved architecture classes.

No warmup overlap. Cache disabled for raw comparison unless a production cache behavior is separately benchmarked.

## 4. Profile baselines

```text
windows-x64-avx2
windows-x64-baseline
macos-arm64
macos-x64
linux-x64-avx2
linux-x64-baseline
linux-arm64
android-arm64
android-x86_64
ios-arm64
ios-simulator-arm64
ios-simulator-x64
```

Each baseline records:

- hardware model/CPU features;
- OS/build;
- power mode/session state;
- compiler/toolchain;
- native backend/flags;
- model hashes;
- library/ABI/Firefox revisions;
- raw runs and summary.

## 5. Absolute gates

For warm subtitle-sized translation:

```text
p95 <= 150 ms
p99 <= 250 ms
throughput >= 10 lines/sec
```

All production profiles must satisfy these unless an owner-approved platform-specific architecture amendment exists.

## 6. Relative gates

Against the approved baseline on the same controlled profile:

```text
p50 regression <= 10%
p95 regression <= 10%
p99 regression <= 15%
throughput regression <= 10%
```

A candidate may improve one metric while regressing another; all limits are independent.

## 7. Wrapper overhead gates

No-op boundary benchmark, 10,000+ operations:

```text
desktop JNI/cinterop p50 < 1 ms target
p95 <= 2 ms
p99 <= 5 ms
```

Translation wrapper overhead:

```text
integrated p95 - raw native p95 <= 3 ms target
```

If a profile cannot meet 3 ms but remains under absolute/relative gates, report exact cause; do not hide it.

## 8. Model load/switch

Measure separately:

```text
cold runtime initialization
cold model read/load
first translation after load
warm cached translator acquisition
A→B load/activation
A→B→A with both models warm
unload time
memory before/after unload
```

Model load is cold path and must not be included in warm translation latency.

## 9. Concurrency/scheduler

Measure:

- one realtime translator;
- two independent pairs concurrently;
- queue saturation;
- realtime supersession;
- interactive bounded wait;
- batch 2/4/8;
- deadlines/cancellation;
- model switching under load.

Throughput uses actual wall-clock duration, never sum of overlapping per-item durations.

## 10. Playback coexistence

For Linguum desktop integration after library end-to-end:

- play DRM video in accepted browser runtime;
- run simulated subtitle arrival workload;
- measure translation p95/p99;
- inspect dropped frames/audio/DRM stability;
- compare video baseline vs translation active;
- translation under playback p95 target <= 200 ms;
- dropped-frame impact target <= 1 percentage point.

## 11. Mobile validation

Use representative physical devices.

Measure:

- cold/warm latency;
- memory per loaded model;
- sustained 10-minute subtitle workload;
- thermal throttling;
- battery/power sample where practical;
- app background/foreground lifecycle;
- memory warning eviction;
- model install storage/network behavior.

Simulator/emulator numbers are diagnostic only, not mobile release performance authority.

## 12. Baseline governance

Performance baseline files are protected.

A baseline update requires:

- dedicated workflow;
- old/new raw results;
- reason;
- hardware/profile identity;
- trend report;
- maintainer approval;
- no absolute gate violation.

Agents cannot regenerate baselines in normal PRs.

<!-- END FILE: implementation/PERFORMANCE_VALIDATION.md -->

---

<!-- BEGIN FILE: implementation/SECURITY_SUPPLY_CHAIN.md -->

# Source file: `implementation/SECURITY_SUPPLY_CHAIN.md`

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

<!-- END FILE: implementation/SECURITY_SUPPLY_CHAIN.md -->

---

<!-- BEGIN FILE: implementation/PUBLISHING_RELEASE.md -->

# Source file: `implementation/PUBLISHING_RELEASE.md`

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

<!-- END FILE: implementation/PUBLISHING_RELEASE.md -->

---

<!-- BEGIN FILE: implementation/DEFINITION_OF_DONE.md -->

# Source file: `implementation/DEFINITION_OF_DONE.md`

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
- PR required checks and reviews are green;
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

<!-- END FILE: implementation/DEFINITION_OF_DONE.md -->

---

<!-- BEGIN FILE: schemas/model-manifest.schema.json -->

# Source file: `schemas/model-manifest.schema.json`

````json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://schemas.linguum.io/translation/model-manifest.schema.json",
  "title": "Linguum Translation Approved Model Manifest",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schemaVersion",
    "manifestRevision",
    "libraryVersion",
    "firefoxCompatibility",
    "sourceRegistry",
    "generatedAt",
    "models"
  ],
  "properties": {
    "schemaVersion": { "const": 1 },
    "manifestRevision": { "type": "integer", "minimum": 1 },
    "libraryVersion": {
      "type": "string",
      "pattern": "^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?(?:\\+[0-9A-Za-z.-]+)?$"
    },
    "firefoxCompatibility": {
      "type": "object",
      "additionalProperties": false,
      "required": ["repository", "revision", "bergamotVersion", "sourceTreeSha256"],
      "properties": {
        "repository": { "const": "mozilla/translations" },
        "revision": { "$ref": "#/$defs/gitSha" },
        "bergamotVersion": { "type": "string", "minLength": 1 },
        "sourceTreeSha256": { "$ref": "#/$defs/sha256" },
        "firefoxSourceRevision": { "$ref": "#/$defs/gitSha" },
        "firefoxReleaseRange": { "type": "string", "minLength": 1 }
      }
    },
    "sourceRegistry": {
      "type": "object",
      "additionalProperties": false,
      "required": ["url", "retrievedAt", "sha256"],
      "properties": {
        "url": { "type": "string", "format": "uri", "pattern": "^https://" },
        "retrievedAt": { "type": "string", "format": "date-time" },
        "sha256": { "$ref": "#/$defs/sha256" }
      }
    },
    "generatedAt": { "type": "string", "format": "date-time" },
    "generator": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "repository": { "type": "string", "minLength": 1 },
        "revision": { "$ref": "#/$defs/gitSha" },
        "workflowRun": { "type": "string", "minLength": 1 }
      }
    },
    "models": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "#/$defs/model" }
    }
  },
  "$defs": {
    "sha256": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$"
    },
    "gitSha": {
      "type": "string",
      "pattern": "^[0-9a-f]{40}$"
    },
    "languageTag": {
      "type": "string",
      "pattern": "^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$"
    },
    "source": {
      "type": "object",
      "additionalProperties": false,
      "required": ["type", "url"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["mozilla", "linguum-mirror", "enterprise-mirror", "local"]
        },
        "url": {
          "type": "string",
          "format": "uri",
          "pattern": "^(https|file)://"
        }
      }
    },
    "artifact": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "role", "fileName", "compressedBytes", "installedBytes", "sha256", "sources"],
      "properties": {
        "id": { "type": "string", "pattern": "^[a-z0-9][a-z0-9._-]*$" },
        "role": {
          "type": "string",
          "enum": ["model", "vocabulary", "shortlist", "quality-model", "configuration", "sentence-splitter"]
        },
        "fileName": { "type": "string", "pattern": "^[^/\\\\]+$" },
        "archiveFormat": {
          "type": "string",
          "enum": ["none", "gzip", "tar-gzip", "zip", "zstd", "tar-zstd"]
        },
        "compressedBytes": { "type": "integer", "minimum": 0 },
        "installedBytes": { "type": "integer", "minimum": 1 },
        "sha256": { "$ref": "#/$defs/sha256" },
        "installedSha256": { "$ref": "#/$defs/sha256" },
        "sources": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/$defs/source" }
        }
      }
    },
    "capabilities": {
      "type": "object",
      "additionalProperties": false,
      "required": ["plainText", "batch", "structuredText"],
      "properties": {
        "plainText": { "type": "boolean" },
        "batch": { "type": "boolean" },
        "structuredText": { "type": "boolean" },
        "alignment": { "type": "boolean" },
        "qualityEstimation": { "type": "boolean" },
        "pivot": { "type": "boolean" }
      }
    },
    "model": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "id",
        "sourceLanguage",
        "targetLanguage",
        "mozillaVersion",
        "architecture",
        "status",
        "capabilities",
        "artifacts",
        "expectedConfiguration"
      ],
      "properties": {
        "id": { "type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$" },
        "sourceLanguage": { "$ref": "#/$defs/languageTag" },
        "targetLanguage": { "$ref": "#/$defs/languageTag" },
        "mozillaVersion": { "type": "string", "minLength": 1 },
        "architecture": { "type": "string", "minLength": 1 },
        "status": { "const": "approved" },
        "capabilities": { "$ref": "#/$defs/capabilities" },
        "artifacts": {
          "type": "array",
          "minItems": 2,
          "items": { "$ref": "#/$defs/artifact" }
        },
        "expectedConfiguration": {
          "type": "object",
          "additionalProperties": { "type": ["string", "number", "integer", "boolean"] }
        },
        "qualityEvidence": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "driftReport": { "type": "string" },
            "benchmarkReport": { "type": "string" },
            "approvedBy": { "type": "string" }
          }
        }
      }
    }
  }
}
````

<!-- END FILE: schemas/model-manifest.schema.json -->

---

<!-- BEGIN FILE: schemas/upstream-lock.schema.json -->

# Source file: `schemas/upstream-lock.schema.json`

````json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://schemas.linguum.io/translation/upstream-lock.schema.json",
  "title": "Linguum Translation Recursive Upstream Source Lock",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schemaVersion",
    "repository",
    "revision",
    "bergamotVersion",
    "sourceTreeSha256",
    "generatedAt",
    "submodules",
    "licenses"
  ],
  "properties": {
    "schemaVersion": { "const": 1 },
    "repository": { "const": "https://github.com/mozilla/translations.git" },
    "revision": { "$ref": "#/$defs/gitSha" },
    "bergamotVersion": { "type": "string", "minLength": 1 },
    "sourceTreeSha256": { "$ref": "#/$defs/sha256" },
    "generatedAt": { "type": "string", "format": "date-time" },
    "generatorRevision": { "$ref": "#/$defs/gitSha" },
    "submodules": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["path", "url", "revision", "treeSha256"],
        "properties": {
          "path": { "type": "string", "minLength": 1, "not": { "pattern": "(^|/)\\.\\.(/|$)" } },
          "url": { "type": "string", "format": "uri", "pattern": "^https://" },
          "revision": { "$ref": "#/$defs/gitSha" },
          "treeSha256": { "$ref": "#/$defs/sha256" }
        }
      }
    },
    "licenses": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["path", "spdx"],
        "properties": {
          "path": { "type": "string", "minLength": 1 },
          "spdx": { "type": "string", "minLength": 1 },
          "sha256": { "$ref": "#/$defs/sha256" }
        }
      }
    }
  },
  "$defs": {
    "sha256": { "type": "string", "pattern": "^[0-9a-f]{64}$" },
    "gitSha": { "type": "string", "pattern": "^[0-9a-f]{40}$" }
  }
}
````

<!-- END FILE: schemas/upstream-lock.schema.json -->

---

<!-- BEGIN FILE: schemas/patch-metadata.schema.json -->

# Source file: `schemas/patch-metadata.schema.json`

````json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://schemas.linguum.io/translation/patch-metadata.schema.json",
  "title": "Linguum Translation Upstream Patch Metadata",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schemaVersion",
    "id",
    "title",
    "reason",
    "upstreamRevision",
    "platforms",
    "affectedPaths",
    "introducedIn",
    "removeWhen",
    "license",
    "approvalReference",
    "patchSha256"
  ],
  "properties": {
    "schemaVersion": { "const": 1 },
    "id": { "type": "string", "pattern": "^LT-UPSTREAM-[0-9]{4}$" },
    "title": { "type": "string", "minLength": 1, "maxLength": 160 },
    "reason": { "type": "string", "minLength": 20 },
    "upstreamRevision": { "$ref": "#/$defs/gitSha" },
    "platforms": {
      "type": "array",
      "minItems": 1,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "windows-x64-avx2",
          "windows-x64-baseline",
          "macos-arm64",
          "macos-x64",
          "linux-x64-avx2",
          "linux-x64-baseline",
          "linux-arm64",
          "android-arm64-v8a",
          "android-x86_64",
          "ios-arm64",
          "ios-simulator-arm64",
          "ios-simulator-x64"
        ]
      }
    },
    "affectedPaths": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string", "minLength": 1 }
    },
    "upstreamIssue": { "type": ["string", "null"], "format": "uri" },
    "introducedIn": {
      "type": "string",
      "pattern": "^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?$"
    },
    "removeWhen": { "type": "string", "minLength": 10 },
    "license": { "type": "string", "enum": ["MPL-2.0", "Apache-2.0"] },
    "approvedBy": { "type": "string", "minLength": 1 },
    "approvalReference": { "type": "string", "minLength": 1 },
    "patchSha256": { "$ref": "#/$defs/sha256" }
  },
  "$defs": {
    "sha256": { "type": "string", "pattern": "^[0-9a-f]{64}$" },
    "gitSha": { "type": "string", "pattern": "^[0-9a-f]{40}$" }
  }
}
````

<!-- END FILE: schemas/patch-metadata.schema.json -->

---

<!-- BEGIN FILE: schemas/release-identity.schema.json -->

# Source file: `schemas/release-identity.schema.json`

````json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://schemas.linguum.io/translation/release-identity.schema.json",
  "title": "Linguum Translation Release Identity",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schemaVersion",
    "libraryVersion",
    "gitTag",
    "gitCommit",
    "nativeAbi",
    "firefox",
    "modelManifest",
    "toolchains",
    "artifacts",
    "sbom",
    "provenance"
  ],
  "properties": {
    "schemaVersion": { "const": 1 },
    "libraryVersion": { "$ref": "#/$defs/semver" },
    "gitTag": { "type": "string", "pattern": "^v[0-9]+\\.[0-9]+\\.[0-9]+(?:-[0-9A-Za-z.-]+)?$" },
    "gitCommit": { "$ref": "#/$defs/gitSha" },
    "nativeAbi": {
      "type": "object",
      "additionalProperties": false,
      "required": ["major", "minor", "headerSha256", "symbolSnapshotSha256"],
      "properties": {
        "major": { "type": "integer", "minimum": 1 },
        "minor": { "type": "integer", "minimum": 0 },
        "headerSha256": { "$ref": "#/$defs/sha256" },
        "symbolSnapshotSha256": { "$ref": "#/$defs/sha256" }
      }
    },
    "firefox": {
      "type": "object",
      "additionalProperties": false,
      "required": ["repository", "revision", "bergamotVersion", "sourceTreeSha256"],
      "properties": {
        "repository": { "const": "mozilla/translations" },
        "revision": { "$ref": "#/$defs/gitSha" },
        "bergamotVersion": { "type": "string", "minLength": 1 },
        "sourceTreeSha256": { "$ref": "#/$defs/sha256" }
      }
    },
    "modelManifest": {
      "type": "object",
      "additionalProperties": false,
      "required": ["revision", "sha256", "signatureSha256"],
      "properties": {
        "revision": { "type": "integer", "minimum": 1 },
        "sha256": { "$ref": "#/$defs/sha256" },
        "signatureSha256": { "$ref": "#/$defs/sha256" }
      }
    },
    "toolchains": {
      "type": "object",
      "minProperties": 1,
      "additionalProperties": { "type": "string", "minLength": 1 }
    },
    "artifacts": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["name", "kind", "target", "sha256", "sizeBytes"],
        "properties": {
          "name": { "type": "string", "minLength": 1 },
          "kind": {
            "type": "string",
            "enum": ["maven", "native-runtime", "aar", "xcframework", "sources", "documentation", "swiftpm", "license-source"]
          },
          "target": { "type": "string", "minLength": 1 },
          "sha256": { "$ref": "#/$defs/sha256" },
          "sizeBytes": { "type": "integer", "minimum": 1 },
          "unsignedPayloadSha256": { "$ref": "#/$defs/sha256" }
        }
      }
    },
    "sbom": {
      "type": "object",
      "additionalProperties": false,
      "required": ["format", "sha256"],
      "properties": {
        "format": { "type": "string", "enum": ["CycloneDX", "SPDX"] },
        "sha256": { "$ref": "#/$defs/sha256" }
      }
    },
    "provenance": {
      "type": "object",
      "additionalProperties": false,
      "required": ["workflow", "runId", "attestationSha256"],
      "properties": {
        "workflow": { "type": "string", "minLength": 1 },
        "runId": { "type": "string", "minLength": 1 },
        "attestationSha256": { "$ref": "#/$defs/sha256" },
        "builderIdentity": { "type": "string", "minLength": 1 }
      }
    }
  },
  "$defs": {
    "sha256": { "type": "string", "pattern": "^[0-9a-f]{64}$" },
    "gitSha": { "type": "string", "pattern": "^[0-9a-f]{40}$" },
    "semver": {
      "type": "string",
      "pattern": "^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?(?:\\+[0-9A-Za-z.-]+)?$"
    }
  }
}
````

<!-- END FILE: schemas/release-identity.schema.json -->

---

<!-- BEGIN FILE: codex/INITIAL_CODEX_PROMPT.md -->

# Source file: `codex/INITIAL_CODEX_PROMPT.md`

# Initial Codex Prompt — Linguum Translation

You are implementing **Linguum Translation**, a public, production-grade Kotlin Multiplatform library. The product and architecture have already been decided. You are an implementer and verifier, not the product owner or architect.

## Mandatory source package

This repository must begin from the complete handoff package containing:

```text
START_HERE.md
AGENTS.md
CODEX_EXECUTION_CONTRACT.md
architecture/
implementation/
research/
schemas/
codex/
scripts/
templates/
MANIFEST.sha256
```

Read the files in the exact order stated in `START_HERE.md` before making any change.

## Non-negotiable architecture

The frozen source of truth is `architecture/LOCKED_DECISIONS.md`.

The library must:

- publish as `io.linguum:translation` and `io.linguum:translation-testing`;
- expose public Kotlin packages rooted at `io.linguum.translation`;
- support Windows x64, macOS arm64/x64, Linux x64/arm64, Android arm64-v8a/x86_64 emulator, and iOS device/simulator targets;
- use a stable Linguum-owned C ABI;
- use the exact `mozilla/translations` revision pinned by Firefox;
- hide Mozilla/Bergamot/Marian/FBGEMM from the public API;
- perform translation fully offline after model installation;
- use immutable approved model manifests and exact artifact hashes;
- preserve the documented API, native ABI, security, privacy, performance, licensing, and agent-governance gates.

Do not substitute another engine, repository, group ID, public API shape, packaging strategy, target matrix, or release strategy.

## Execute M0 only

Your first task is **M0 — Repository and Governance**. Do not implement translation production code or public stable APIs in M0.

### M0 sequence

1. Verify prerequisites:

   ```bash
   git --version
   gh --version
   gh auth status
   java -version
   ```

2. Create a new working directory named `linguum-translation` and copy this handoff into it unchanged.

3. Initialize Git using branch `main`.

4. Create the public remote immediately:

   ```bash
   gh repo create StevenBuglione/linguum-translation \
     --public \
     --source=. \
     --remote=origin \
     --push \
     --description "Firefox-compatible native translation for Kotlin Multiplatform"
   ```

   If the repository already exists, inspect it and attach `origin` rather than creating a duplicate. Never retry repository creation blindly.

5. Verify the remote after the first push:

   ```bash
   git fetch origin main
   test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
   gh repo view StevenBuglione/linguum-translation
   ```

6. Create M0 work-package branch:

   ```bash
   git switch -c codex/M0-WP01-repository-governance
   git push -u origin HEAD
   ```

7. Open one draft PR after the first branch checkpoint. Do not open duplicate PRs.

8. Implement only the M0 work packages from `implementation/WORK_PACKAGES.md` in order.

9. After each verified work package:

   - inspect status/diff;
   - stage only intentional paths with `git add -- <paths>`;
   - commit using the work-package ID;
   - push immediately;
   - fetch and verify the remote SHA;
   - update the verification report and draft PR.

10. Never work more than one clean committed checkpoint ahead of the remote branch.

## Protected behavior

You may not:

- weaken a test, coverage threshold, performance gate, API/ABI baseline, sanitizer, fuzzer, architecture rule, dependency verification, license check, or release check;
- edit vendored Mozilla source directly;
- change the Firefox pin outside the protected compatibility workflow;
- update golden translations merely to make tests pass;
- add an unapproved production dependency;
- add a Detekt baseline or broad suppression;
- skip a requested platform;
- raise minimum OS versions;
- force-push or rewrite shared history;
- keep completed work only locally;
- create or publish an official release outside the canonical release workflow;
- silently reinterpret an unproven feasibility requirement as complete.

## M1 hard-stop rule

M1 is a feasibility milestone. It must prove the native source, C ABI, build, packaging, linking, consumer resolution, Java/Swift export, and canary translation on every required target **before** stable API implementation begins.

If any locked platform or one-dependency packaging promise cannot be proven, stop using the blocker protocol. Do not conceal the result behind a fallback that violates the frozen decisions.

## Evidence standard

Every completion claim requires a verification report containing:

- work-package and requirement IDs;
- source commit and remote commit SHA;
- changed paths/modules;
- exact commands and exit statuses;
- tests and coverage;
- artifact names and SHA-256 values;
- security/license/dependency results;
- known limitations and blockers;
- explicit statement that no protected gate was weakened.

Use `codex/VERIFICATION_REPORT_TEMPLATE.md`.

## Blocker format

When blocked, stop and report:

```text
BLOCKER TYPE:
WORK PACKAGE / REQUIREMENT:
LOCKED DECISION:
OBSERVED CONFLICT:
REPRODUCTION COMMANDS:
EVIDENCE:
WHY A SILENT WORKAROUND IS FORBIDDEN:
SMALLEST OWNER DECISION NEEDED:
SAFE WORK THAT CAN CONTINUE:
LOCAL COMMIT SHA:
REMOTE COMMIT SHA:
```

## Completion condition for this invocation

Complete M0 only. Push every M0 checkpoint. Run the complete M0 gate from a clean checkout. Produce the M0 verification report and update the draft PR. Stop before M1 implementation and return the remote repository/PR URLs, local and remote SHAs, exact verification results, and any blocker.

<!-- END FILE: codex/INITIAL_CODEX_PROMPT.md -->

---

<!-- BEGIN FILE: codex/WORK_PACKAGE_TEMPLATE.md -->

# Source file: `codex/WORK_PACKAGE_TEMPLATE.md`

# Work Package Template

## Identity

```text
Work package: M?-WP??
Title:
Milestone:
Owner-approved architecture references:
Depends on:
Blocks:
Branch:
Draft PR:
```

## Objective

State one independently verifiable vertical outcome. The objective must not contain multiple unrelated architectural changes.

## In scope

- exact behavior/module/artifact to implement;
- public API additions already authorized by the frozen specification;
- native targets affected;
- documentation and tests required for this slice.

## Out of scope

List explicitly. A work package does not authorize adjacent cleanup, framework replacement, toolchain upgrade, upstream-pin change, public API redesign, or gate relaxation.

## Requirements and traceability

| Requirement ID | Source | Implementation path | Verification |
|---|---|---|---|
| | | | |

## Affected modules

| Gradle/native module | Classification | Allowed dependencies | Reason changed |
|---|---|---|---|
| | | | |

## Public compatibility impact

```text
Kotlin API:
Java facade:
Swift facade:
C ABI:
Model manifest/schema:
Persisted metadata:
Minimum platform version:
```

Any breaking impact is a blocker unless explicitly authorized as a major-release work package.

## Security, privacy, and licensing impact

```text
User content handling:
Network access:
Native memory/unsafe boundary:
Secrets/credentials:
Dependency changes:
License/SPDX changes:
Mozilla/MPL source impact:
SBOM/provenance impact:
```

## Implementation steps

1. Write/extend failing executable tests or feasibility probe.
2. Implement the smallest complete change.
3. Run narrow validation repeatedly.
4. Run architecture/API/ABI checks affected by the change.
5. Produce artifacts and hashes.
6. Run the work-package clean gate.
7. Write verification report.
8. Stage only intentional paths, commit, push, and verify remote SHA.

## Required tests

### Pure/common

- unit examples;
- property/invariant tests;
- cancellation/deadline/backpressure semantics where relevant;
- exact failure mapping.

### Native/platform

- ABI ownership/error tests;
- platform build/link/run test;
- minimum supported platform proof where relevant;
- sanitizer/fuzz/stress scenario where relevant.

### Consumers

- Kotlin fixture;
- Java fixture;
- Swift fixture;
- clean Maven-local/SwiftPM consumption where relevant.

## Required commands

```text
Narrow development commands:

Clean work-package gate:

Artifact inspection commands:

Remote SHA verification:
```

## Checkpoints

| Checkpoint | Required gate | Commit message | Paths | Remote verified |
|---|---|---|---|---|
| 1 | | `M?-WP??: ...` | | |

No completed checkpoint may remain only local.

## Acceptance criteria

- [ ] all requirements have executable evidence;
- [ ] architecture graph remains valid;
- [ ] no public/internal type leakage;
- [ ] no protected baseline/gate changed without authorization;
- [ ] tests/coverage/safety checks pass;
- [ ] artifacts are reproducible/inspectable as required;
- [ ] verification report is complete;
- [ ] branch was pushed and local/remote SHAs match.

## Blocker rule

Stop rather than redesign if the implementation requires changing a locked decision. Use the blocker format from `AGENTS.md` and `CODEX_EXECUTION_CONTRACT.md`.

<!-- END FILE: codex/WORK_PACKAGE_TEMPLATE.md -->

---

<!-- BEGIN FILE: codex/VERIFICATION_REPORT_TEMPLATE.md -->

# Source file: `codex/VERIFICATION_REPORT_TEMPLATE.md`

# <WORK-PACKAGE-ID> Verification Report

## Result

```text
Status: PASS / PARTIAL / BLOCKED / FAIL
Milestone:
Work package:
Branch:
Draft PR:
Date/time UTC:
Verifier:
```

## Source and remote identity

```text
Repository:
Base commit:
Verified commit:
Local HEAD:
Remote branch SHA:
Remote SHA matches local: YES / NO
Working tree clean: YES / NO
Shallow clone: YES / NO
```

## Requirement traceability

| Requirement | Implementation | Test/evidence | Result |
|---|---|---|---|
| | | | |

## Changed modules and paths

| Path/module | Classification | Change | Dependency rule result |
|---|---|---|---|
| | | | |

## Commands executed

Record commands verbatim. Never summarize an unexecuted command as successful.

| Command | Exit | Environment/runner | Evidence/log |
|---|---:|---|---|
| | | | |

## Tests and quality

```text
Formatting:
Compiler warnings-as-errors:
Detekt/custom rules:
Architecture checks:
Unit tests:
Property tests:
Coverage by module:
API compatibility:
JVM binary compatibility:
Swift API snapshot:
Native ABI snapshot:
Native unit/integration:
Sanitizers:
Fuzzing:
Performance:
Consumer fixtures:
```

## Platform results

| Target/profile | Build | Link/package | Run/canary | Minimum-version evidence | Artifact SHA-256 |
|---|---|---|---|---|---|
| | | | | | |

## Artifacts

| Artifact | Size | SHA-256 | Source identity/provenance |
|---|---:|---|---|
| | | | |

## Security, privacy, licensing, supply chain

```text
Sensitive text absent from logs/events:
Dependency verification:
Dependency vulnerability scan:
Secret scan:
License/SPDX scan:
Mozilla snapshot integrity:
Patch queue validation:
SBOM:
Provenance/attestation:
Model/manifest signature/hash validation:
```

## Compatibility impact

```text
Kotlin API:
Java facade:
Swift facade:
C ABI:
Model manifest/schema:
Persisted metadata:
Minimum OS/API versions:
Translation output drift:
```

## Performance evidence

```text
Profile:
Baseline identity:
Corpus/model identity:
p50:
p95:
p99:
Throughput:
Relative regression:
Absolute product gate:
Wrapper overhead:
```

## Failure injection and recovery

List every required failure scenario, observed state, and proof that no partial/corrupt state became visible.

## Known limitations

Separate verified limitations from speculation.

## Blockers

Use the prescribed blocker format. Do not propose an unauthorized workaround as completion.

## Gate immutability declaration

```text
[ ] No coverage threshold was lowered.
[ ] No performance threshold/baseline was weakened or casually regenerated.
[ ] No API/ABI baseline was changed to hide incompatibility.
[ ] No test, sanitizer, fuzz case, platform, or check was disabled/ignored.
[ ] No Detekt baseline or broad suppression was added.
[ ] No unapproved dependency or repository was added.
[ ] Firefox pin and vendored source were not changed outside the protected workflow.
[ ] Mozilla source was not directly edited.
[ ] OS minimums and platform support were not silently changed.
[ ] License, SBOM, provenance, and dependency-verification gates were preserved.
```

## Final decision

```text
WORK PACKAGE GATE: PASS / FAIL / BLOCKED
SAFE TO START NEXT WORK PACKAGE: YES / NO
SAFE TO ADVANCE MILESTONE: YES / NO / NOT A MILESTONE BOUNDARY
```

<!-- END FILE: codex/VERIFICATION_REPORT_TEMPLATE.md -->

---

<!-- BEGIN FILE: templates/PULL_REQUEST_TEMPLATE.md -->

# Source file: `templates/PULL_REQUEST_TEMPLATE.md`

# Work package

```text
Milestone / WP:
Requirement IDs:
Architecture classifications:
```

## Summary

Describe the smallest complete behavior delivered.

## Compatibility impact

```text
Kotlin API:
JVM binary API:
Java facade:
Swift facade:
C ABI:
Manifest/persisted schema:
Minimum platform versions:
Translation output:
```

## Security, privacy, licensing

```text
Network behavior:
Sensitive text handling:
Native/unsafe changes:
Dependencies/licenses:
Mozilla snapshot/patches:
Supply-chain artifacts:
```

## Verification

Link the work-package verification report and list the clean gate commit/SHA.

```text
Local HEAD:
Remote branch SHA:
Clean gate command:
Clean gate result:
```

## Gate declaration

- [ ] I did not change protected architecture/product decisions.
- [ ] I did not weaken tests, coverage, performance, API/ABI, sanitizer, fuzzing, dependency, license, or release gates.
- [ ] I staged only intentional paths.
- [ ] The branch was pushed and the remote SHA matches the verified local commit.
- [ ] Required documentation and artifacts were updated.
- [ ] The PR contains no unrelated cleanup or speculative modules.

<!-- END FILE: templates/PULL_REQUEST_TEMPLATE.md -->

---

<!-- BEGIN FILE: templates/ADR_TEMPLATE.md -->

# Source file: `templates/ADR_TEMPLATE.md`

# ADR-XXXX — <Title>

```text
Status: Proposed / Accepted / Rejected / Superseded
Date:
Owner authorization reference:
Supersedes:
```

## Context

State the verified conflict or new requirement. Architecture changes are not authorized by implementation convenience.

## Locked decision affected

Identify exact Q-number/file/rule.

## Evidence

Include reproduction commands, platform/toolchain evidence, benchmark/artifact results, and alternatives tested.

## Options

Describe each viable option and its compatibility, security, licensing, maintenance, and migration impact.

## Decision

Record only after explicit owner authorization.

## Consequences

Include source/API/ABI/model/schema/platform/release impacts.

## Migration and rollback

Specify consumer migration, artifact compatibility, rollback behavior, and release versioning.

## Required gate changes

Any test/baseline/architecture update must be explicit and justified. Never hide it in implementation commits.

<!-- END FILE: templates/ADR_TEMPLATE.md -->

---

<!-- BEGIN FILE: templates/BLOCKER_REPORT_TEMPLATE.md -->

# Source file: `templates/BLOCKER_REPORT_TEMPLATE.md`

# Blocker Report

```text
BLOCKER TYPE:
WORK PACKAGE / REQUIREMENT:
LOCKED DECISION:
OBSERVED CONFLICT:
REPRODUCTION COMMANDS:
EVIDENCE:
WHY A SILENT WORKAROUND IS FORBIDDEN:
SMALLEST OWNER DECISION NEEDED:
SAFE WORK THAT CAN CONTINUE:
LOCAL COMMIT SHA:
REMOTE COMMIT SHA:
REMOTE URL / PR:
```

<!-- END FILE: templates/BLOCKER_REPORT_TEMPLATE.md -->

---

<!-- BEGIN FILE: scripts/bootstrap-repository.sh -->

# Source file: `scripts/bootstrap-repository.sh`

````bash
#!/usr/bin/env bash
set -euo pipefail

REPOSITORY="${1:-StevenBuglione/linguum-translation}"
DESCRIPTION="${LINGUUM_REPOSITORY_DESCRIPTION:-Firefox-compatible native translation for Kotlin Multiplatform}"
VISIBILITY="${LINGUUM_REPOSITORY_VISIBILITY:-public}"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

command -v git >/dev/null 2>&1 || fail "git is required"
command -v gh >/dev/null 2>&1 || fail "GitHub CLI (gh) is required"
gh auth status >/dev/null || fail "gh is not authenticated"

[[ -f START_HERE.md ]] || fail "Run from the extracted handoff/repository root"
[[ -f architecture/LOCKED_DECISIONS.md ]] || fail "Frozen architecture source is missing"
[[ -f MANIFEST.sha256 ]] || fail "MANIFEST.sha256 is missing"

if [[ ! -d .git ]]; then
  git init -b main
fi

current_branch="$(git branch --show-current)"
if [[ -z "$current_branch" ]]; then
  git switch -c main
elif [[ "$current_branch" != "main" ]]; then
  fail "Initial bootstrap must run on main, not $current_branch"
fi

# Stage only the known handoff roots. Never use git add . or git add -A.
git add -- \
  START_HERE.md \
  README.md \
  AGENTS.md \
  CODEX_EXECUTION_CONTRACT.md \
  LINGUUM_TRANSLATION_COMPLETE_CODEX_HANDOFF.md \
  MANIFEST.sha256 \
  architecture \
  implementation \
  research \
  schemas \
  codex \
  scripts \
  templates

git diff --cached --check

if git diff --cached --quiet; then
  printf 'No initial handoff changes to commit.\n'
else
  git commit -m "M0-WP01: add frozen Linguum Translation handoff"
fi

if gh repo view "$REPOSITORY" >/dev/null 2>&1; then
  printf 'Repository %s already exists; reusing it.\n' "$REPOSITORY"
  remote_url="https://github.com/${REPOSITORY}.git"
  if git remote get-url origin >/dev/null 2>&1; then
    existing="$(git remote get-url origin)"
    [[ "$existing" == "$remote_url" || "$existing" == "git@github.com:${REPOSITORY}.git" ]] || \
      fail "origin points to $existing instead of $REPOSITORY"
  else
    git remote add origin "$remote_url"
  fi
else
  case "$VISIBILITY" in
    public) visibility_flag="--public" ;;
    private) visibility_flag="--private" ;;
    *) fail "LINGUUM_REPOSITORY_VISIBILITY must be public or private" ;;
  esac

  gh repo create "$REPOSITORY" \
    "$visibility_flag" \
    --source=. \
    --remote=origin \
    --description "$DESCRIPTION"
fi

git push -u origin main
git fetch origin main

local_sha="$(git rev-parse HEAD)"
remote_sha="$(git rev-parse origin/main)"
[[ "$local_sha" == "$remote_sha" ]] || fail "Remote SHA $remote_sha does not match local SHA $local_sha"

printf 'Repository bootstrap verified.\n'
printf 'Repository: https://github.com/%s\n' "$REPOSITORY"
printf 'Commit: %s\n' "$local_sha"
````

<!-- END FILE: scripts/bootstrap-repository.sh -->

---

<!-- BEGIN FILE: scripts/bootstrap-repository.ps1 -->

# Source file: `scripts/bootstrap-repository.ps1`

````powershell
[CmdletBinding()]
param(
    [string]$Repository = "StevenBuglione/linguum-translation",
    [ValidateSet("public", "private")]
    [string]$Visibility = "public",
    [string]$Description = "Firefox-compatible native translation for Kotlin Multiplatform"
)

$ErrorActionPreference = "Stop"

function Assert-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is required"
    }
}

Assert-Command git
Assert-Command gh
& gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) { throw "gh is not authenticated" }

if (-not (Test-Path "START_HERE.md")) { throw "Run from the extracted handoff/repository root" }
if (-not (Test-Path "architecture/LOCKED_DECISIONS.md")) { throw "Frozen architecture source is missing" }
if (-not (Test-Path "MANIFEST.sha256")) { throw "MANIFEST.sha256 is missing" }

if (-not (Test-Path ".git")) {
    & git init -b main
    if ($LASTEXITCODE -ne 0) { throw "git init failed" }
}

$branch = (& git branch --show-current).Trim()
if ([string]::IsNullOrWhiteSpace($branch)) {
    & git switch -c main
} elseif ($branch -ne "main") {
    throw "Initial bootstrap must run on main, not $branch"
}

$paths = @(
    "START_HERE.md",
    "README.md",
    "AGENTS.md",
    "CODEX_EXECUTION_CONTRACT.md",
    "LINGUUM_TRANSLATION_COMPLETE_CODEX_HANDOFF.md",
    "MANIFEST.sha256",
    "architecture",
    "implementation",
    "research",
    "schemas",
    "codex",
    "scripts",
    "templates"
)

& git add -- $paths
if ($LASTEXITCODE -ne 0) { throw "git add failed" }
& git diff --cached --check
if ($LASTEXITCODE -ne 0) { throw "staged diff check failed" }

& git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    & git commit -m "M0-WP01: add frozen Linguum Translation handoff"
    if ($LASTEXITCODE -ne 0) { throw "initial commit failed" }
} else {
    Write-Host "No initial handoff changes to commit."
}

& gh repo view $Repository 2>$null | Out-Null
$exists = $LASTEXITCODE -eq 0
$remoteUrl = "https://github.com/$Repository.git"

if ($exists) {
    Write-Host "Repository $Repository already exists; reusing it."
    & git remote get-url origin 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $existing = (& git remote get-url origin).Trim()
        if ($existing -ne $remoteUrl -and $existing -ne "git@github.com:$Repository.git") {
            throw "origin points to $existing instead of $Repository"
        }
    } else {
        & git remote add origin $remoteUrl
    }
} else {
    $visibilityFlag = if ($Visibility -eq "public") { "--public" } else { "--private" }
    & gh repo create $Repository $visibilityFlag --source=. --remote=origin --description $Description
    if ($LASTEXITCODE -ne 0) { throw "repository creation failed" }
}

& git push -u origin main
if ($LASTEXITCODE -ne 0) { throw "initial push failed" }
& git fetch origin main
if ($LASTEXITCODE -ne 0) { throw "fetch verification failed" }

$localSha = (& git rev-parse HEAD).Trim()
$remoteSha = (& git rev-parse origin/main).Trim()
if ($localSha -ne $remoteSha) {
    throw "Remote SHA $remoteSha does not match local SHA $localSha"
}

Write-Host "Repository bootstrap verified."
Write-Host "Repository: https://github.com/$Repository"
Write-Host "Commit: $localSha"
````

<!-- END FILE: scripts/bootstrap-repository.ps1 -->

---

<!-- BEGIN FILE: scripts/checkpoint-push.sh -->

# Source file: `scripts/checkpoint-push.sh`

````bash
#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage:
  CHECKPOINT_GATE='./gradlew <required-gate>' \
    scripts/checkpoint-push.sh M1-WP01 "prove Windows native canary" path [path ...]

The script runs the supplied gate, stages only the listed paths, commits, pushes,
and verifies that the remote branch SHA equals local HEAD.
USAGE
  exit 2
}

[[ $# -ge 3 ]] || usage
WORK_PACKAGE="$1"
shift
MESSAGE="$1"
shift
PATHS=("$@")

[[ -n "${CHECKPOINT_GATE:-}" ]] || {
  printf 'ERROR: CHECKPOINT_GATE is required\n' >&2
  exit 1
}

git rev-parse --is-inside-work-tree >/dev/null
branch="$(git branch --show-current)"
[[ -n "$branch" && "$branch" != "main" ]] || {
  printf 'ERROR: checkpoint pushes must use a work-package branch, not main\n' >&2
  exit 1
}

printf 'Running checkpoint gate: %s\n' "$CHECKPOINT_GATE"
bash -lc "$CHECKPOINT_GATE"

git diff --check
git status --short

git add -- "${PATHS[@]}"
git diff --cached --check

if git diff --cached --quiet; then
  printf 'ERROR: no staged changes for %s\n' "$WORK_PACKAGE" >&2
  exit 1
fi

git commit -m "${WORK_PACKAGE}: ${MESSAGE}"
git push -u origin "$branch"
git fetch origin "$branch"

local_sha="$(git rev-parse HEAD)"
remote_sha="$(git rev-parse "origin/$branch")"
[[ "$local_sha" == "$remote_sha" ]] || {
  printf 'ERROR: local SHA %s differs from remote SHA %s\n' "$local_sha" "$remote_sha" >&2
  exit 1
}

printf 'Checkpoint saved remotely.\n'
printf 'Branch: %s\nCommit: %s\n' "$branch" "$local_sha"
````

<!-- END FILE: scripts/checkpoint-push.sh -->

---

<!-- BEGIN FILE: scripts/checkpoint-push.ps1 -->

# Source file: `scripts/checkpoint-push.ps1`

````powershell
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkPackage,

    [Parameter(Mandatory = $true)]
    [string]$Message,

    [Parameter(Mandatory = $true)]
    [string]$GateCommand,

    [Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)]
    [string[]]$Paths
)

$ErrorActionPreference = "Stop"

& git rev-parse --is-inside-work-tree | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Not inside a Git worktree" }

$branch = (& git branch --show-current).Trim()
if ([string]::IsNullOrWhiteSpace($branch) -or $branch -eq "main") {
    throw "Checkpoint pushes must use a work-package branch, not main"
}

Write-Host "Running checkpoint gate: $GateCommand"
& powershell -NoProfile -Command $GateCommand
if ($LASTEXITCODE -ne 0) { throw "Checkpoint gate failed" }

& git diff --check
if ($LASTEXITCODE -ne 0) { throw "Working-tree diff check failed" }
& git status --short

& git add -- $Paths
if ($LASTEXITCODE -ne 0) { throw "git add failed" }
& git diff --cached --check
if ($LASTEXITCODE -ne 0) { throw "Staged diff check failed" }

& git diff --cached --quiet
if ($LASTEXITCODE -eq 0) { throw "No staged changes for $WorkPackage" }

& git commit -m "${WorkPackage}: ${Message}"
if ($LASTEXITCODE -ne 0) { throw "commit failed" }
& git push -u origin $branch
if ($LASTEXITCODE -ne 0) { throw "push failed" }
& git fetch origin $branch
if ($LASTEXITCODE -ne 0) { throw "fetch failed" }

$localSha = (& git rev-parse HEAD).Trim()
$remoteSha = (& git rev-parse "origin/$branch").Trim()
if ($localSha -ne $remoteSha) {
    throw "Local SHA $localSha differs from remote SHA $remoteSha"
}

Write-Host "Checkpoint saved remotely."
Write-Host "Branch: $branch"
Write-Host "Commit: $localSha"
````

<!-- END FILE: scripts/checkpoint-push.ps1 -->

---

<!-- BEGIN FILE: scripts/verify-remote-sha.sh -->

# Source file: `scripts/verify-remote-sha.sh`

````bash
#!/usr/bin/env bash
set -euo pipefail

branch="${1:-$(git branch --show-current)}"
[[ -n "$branch" ]] || { printf 'ERROR: no branch specified\n' >&2; exit 1; }

git fetch origin "$branch"
local_sha="$(git rev-parse HEAD)"
remote_sha="$(git rev-parse "origin/$branch")"

if [[ "$local_sha" != "$remote_sha" ]]; then
  printf 'ERROR: local %s != remote %s for %s\n' "$local_sha" "$remote_sha" "$branch" >&2
  exit 1
fi

printf '%s %s\n' "$branch" "$local_sha"
````

<!-- END FILE: scripts/verify-remote-sha.sh -->

---

<!-- BEGIN FILE: scripts/verify-remote-sha.ps1 -->

# Source file: `scripts/verify-remote-sha.ps1`

````powershell
[CmdletBinding()]
param([string]$Branch = "")

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($Branch)) {
    $Branch = (& git branch --show-current).Trim()
}
if ([string]::IsNullOrWhiteSpace($Branch)) { throw "No branch specified" }

& git fetch origin $Branch
if ($LASTEXITCODE -ne 0) { throw "fetch failed" }
$localSha = (& git rev-parse HEAD).Trim()
$remoteSha = (& git rev-parse "origin/$Branch").Trim()
if ($localSha -ne $remoteSha) {
    throw "Local $localSha differs from remote $remoteSha for $Branch"
}
Write-Host "$Branch $localSha"
````

<!-- END FILE: scripts/verify-remote-sha.ps1 -->

---
