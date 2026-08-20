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
