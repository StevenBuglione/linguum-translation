# M0 to M1 Transition Verification Report

## Result

```text
Status: PASS — final evidence commit and protected merge pending
Completed milestone: M0 — Repository and governance
Activated milestone: M1 — Platform and packaging feasibility
Branch: codex/M0-WP04-m1-transition-gates
Pull request: https://github.com/StevenBuglione/linguum-translation/pull/6
Date/time UTC: 2026-08-20
Verifier: Codex
```

## Source and remote identity

```text
Base main commit: 650c85f89395eb7359e6c3bacb36f3e9b17765c9
Transition-gate commit: 91f7aa84525ab75c2a991ec2efe998d129171d22
Dedicated milestone-marker commit: 31515e003a844be0109a63c73ceaa1c27c64b08f
Remote branch SHA: 31515e003a844be0109a63c73ceaa1c27c64b08f
Remote SHA matches local: YES
Working tree clean after verified push: YES
```

## Requirement traceability

| Requirement | Implementation | Evidence | Result |
|---|---|---|---|
| M0 completed before M1 | M0 PR 1 and correction PR 5 merged | main `650c85f89395eb7359e6c3bacb36f3e9b17765c9` | PASS |
| Dedicated milestone advance | marker-only commit changes `current-milestone.txt` | commit `31515e003a844be0109a63c73ceaa1c27c64b08f` | PASS |
| Incremental active work packages | active-milestone modules are optional until introduced | build-logic unit tests | PASS |
| Completed milestone preservation | all modules from prior milestones remain mandatory | build-logic unit tests | PASS |
| Stable CI identities | all 15 protected names route through milestone dispatcher | hosted PR runs | PASS |
| Fail-closed routing | unsupported milestones terminate with an error | dispatcher source inspection | PASS |
| M0 behavior preserved | M0 dispatcher delegates to historical scripts | M0 hosted run 32368954311 | PASS |
| M1 transition works | M1 scopes run after marker commit | M1 hosted run 32369299665 | PASS |

## Changed paths and classification

| Path | Classification | Change |
|---|---|---|
| `scripts/ci/verify-scope.*` | CI tooling | milestone-aware POSIX/Windows dispatch |
| `.github/workflows/` | CI governance | stable jobs call the milestone dispatcher |
| `build-logic` | architecture enforcement | incremental active, mandatory completed modules |
| `testing/architecture` | test harness | validate any canonical milestone marker |
| `architecture/current-milestone.txt` | milestone lock | dedicated M0 to M1 advance |

## Local verification

Both the M0 preparatory commit and the M1 marker commit passed:

- all 17 routed scopes (`architecture`, `quality`, `api`, `kotlin`, Linux, macOS,
  Android, iOS, Swift, consumers, native, models, license, artifacts, upstream,
  performance, and release);
- `./gradlew clean verificationGate --warning-mode=fail`;
- actionlint 1.7.12, JSON/YAML parsing, and shell syntax checks;
- diff whitespace and credential/private-key pattern scans;
- local/remote SHA parity.

## Hosted verification

| Commit/scope | Workflow run | Result |
|---|---:|---|
| M0 preparatory matrix | 32368954311 | PASS — all 15 protected jobs |
| M0 preparatory native safety | 32368954274 | PASS |
| M0 preparatory dependency review | 32368954293 | PASS |
| M0 preparatory CodeQL | 32368960435 | PASS |
| M1 marker matrix | 32369299665 | PASS — all 15 protected jobs |
| M1 marker native safety | 32369299617 | PASS |
| M1 marker dependency review | 32369299715 | PASS |
| M1 marker CodeQL | 32369297996 | PASS |

The evidence commit containing this report and the milestone-neutral native-safety
label must pass the same final local and hosted gates before PR 6 merges.

## Compatibility, security, and limitations

```text
Kotlin/Java/Swift/C ABI: unchanged
Model and persisted schemas: unchanged
Minimum platforms: unchanged
Dependencies and licenses: unchanged
Translation output: unchanged
Protected baselines or thresholds: unchanged
Live ruleset: 21078407; active, no bypass, 15 strict checks, zero approvals
```

M1 is active only on this branch until PR 6 merges. No Firefox snapshot, native ABI,
platform artifact, model, translation runtime, or consumer feasibility proof exists
yet; those begin with M1-WP01 and remain hard gates.

## Final decision

```text
M0 COMPLETION GATE: PASS
M1 TRANSITION GATE: PASS
SAFE TO MERGE PR 6: YES, AFTER THE FINAL EVIDENCE SHA PASSES ALL GATES
SAFE TO CLAIM M1 FEASIBILITY: NO
SAFE TO START M1-WP01 AFTER MERGE: YES
```
