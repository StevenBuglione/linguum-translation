# Contributing

Read `START_HERE.md`, `AGENTS.md`, `CODEX_EXECUTION_CONTRACT.md`, and the contracts referenced by the active work package before changing the repository.

Contributions must stay within `architecture/current-milestone.txt`, preserve `architecture/LOCKED_DECISIONS.md`, add tests, pass `./gradlew verificationGate --warning-mode=fail`, and include a work-package verification report. Stage intentional paths explicitly; never use broad staging, force-push shared history, edit vendored Mozilla source directly, or change a protected baseline to make an implementation pass.

Open a focused pull request using the repository template. Report security issues through `SECURITY.md`, not a public issue.
