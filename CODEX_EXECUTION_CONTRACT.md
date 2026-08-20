# Codex Execution Contract — Linguum Translation

## Objective

Implement the frozen Linguum Translation architecture incrementally, prove each risky assumption before building on it, and preserve all verified work on GitHub through frequent clean checkpoint pushes.

## Standing execution authorization

The repository owner authorizes Codex to implement the full locked roadmap, create
and push branches and commits, create and maintain pull requests, apply the versioned
ruleset, and squash-merge verified pull requests without waiting for human approval.
Human review is optional and is not a completion gate. This authorization is bounded
by the locked architecture, protected baselines, documented release workflows, and
the requirement that all applicable local and hosted technical gates are green.

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
- Never rebase or rewrite pushed milestone history.
- Prefer small commits aligned to one traceability slice.
- Push after every verified slice.
- A local branch must never be more than one verified commit ahead of origin.
- Create a draft PR immediately after the first branch push.
- Keep the PR body current with work-package checkboxes and evidence links.
- Mark the PR ready and merge it autonomously only after the exact remote head SHA
  has passed every applicable required check.

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

May update API, ABI, schema, model, or performance baselines only when the locked
roadmap requires it and only through a dedicated release/compatibility work package
with before/after evidence. Standing execution authorization replaces interactive
approval; it does not permit relaxing a threshold to make a failure pass.

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

An approving human or CODEOWNERS review is not required. Unresolved review threads,
when present, still block merge, and every required status check must be successful.

## Progression requirements

Before beginning the next work package, Codex must verify the committed checkpoint
with the affected narrow gate, the full clean repository gate, applicable policy and
security checks, local/remote SHA parity, and every applicable required hosted check.
Failed, cancelled, timed-out, skipped-required, or pending results are not green.
After any correction, the complete affected gate set must run again on the new SHA.

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
