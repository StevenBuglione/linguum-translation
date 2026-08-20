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
