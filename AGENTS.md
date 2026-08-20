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

### Standing delivery authorization

The repository owner has granted standing authorization for Codex to complete the
locked project roadmap without waiting for interactive review. Within the active
milestone and work-package contracts, agents may:

- edit implementation, tests, fixtures, workflows, documentation, and evidence;
- create commits and branches, push verified checkpoints, and maintain pull requests;
- mark pull requests ready, apply the versioned repository ruleset, and squash-merge;
- delete merged remote work branches when GitHub does not delete them automatically;
- continue to the next work package only after the progression gate below is green.

Manual user approval, an approving pull-request review, and CODEOWNERS approval are
not delivery gates. CODEOWNERS remains ownership and routing metadata. This standing
authorization does not permit a silent architecture exception, a weakened test or
baseline, credential invention, release signing without the configured identity, or
an irreversible external publication outside the documented release workflow.

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
13. Run the full clean repository gate before starting the next work package.
14. Confirm every applicable hosted pull-request check for the checkpoint is green.
15. At milestone end, rerun the full clean milestone and platform gates from a clean,
    non-shallow checkout.
16. Merge only through a protected pull request after every required check is green.
17. Record the merge SHA and advance only as the milestone contract permits.

### Progression gate

"Tested" means more than a narrow unit-test pass. Before work advances, agents must:

- run the affected module's narrow tests;
- run `./gradlew clean verificationGate --warning-mode=fail` (or the documented
  platform-equivalent clean gate) from the committed checkpoint;
- run workflow, policy, manifest, formatting, architecture, dependency, license,
  security, and secret checks applicable to the changed paths;
- push the exact verified SHA and confirm local/remote parity;
- wait for every applicable required GitHub check to finish successfully;
- treat failed, cancelled, timed-out, skipped-required, or pending checks as not green;
- fix failures and rerun the complete affected gate set before proceeding.

The verification report must name every command, exit code, hosted run, artifact, and
known platform limitation. A cached or earlier run cannot prove a later commit.

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
