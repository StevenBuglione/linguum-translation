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
