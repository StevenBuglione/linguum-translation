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
