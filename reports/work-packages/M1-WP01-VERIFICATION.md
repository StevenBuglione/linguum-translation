# M1-WP01 Firefox Source Snapshot Verification Report

## Result

```text
Status: HOSTED IMPLEMENTATION PASS — final evidence commit pending
Milestone/work package: M1-WP01
Branch: codex/M1-WP01-firefox-source-snapshot
Date/time UTC: 2026-08-20
Verifier: Codex
```

## Source and remote identity

```text
Base main commit: 48d2718b1d894aea9cd50d7f08401de286261a73
Initial implementation commit: b1c8345aaecefb5781ec1d57a1132717c2d926d1
Final implementation commit: 63f070d750c6032faa39486463e5435067e55fc4
Final evidence commit: pending
Remote branch SHA: 63f070d750c6032faa39486463e5435067e55fc4
Pull request: https://github.com/StevenBuglione/linguum-translation/pull/7
```

## Requirement traceability

| Requirement | Implementation | Evidence | Result |
|---|---|---|---|
| Exact Firefox pin | pin file from Firefox commit `48d55cf7…` is parsed and matched | `native/UPSTREAM.json`; source diff report | PASS |
| Clean recursive checkout | dirty, missing, changed, or conflicted submodules fail | `validate_checkout`; integration comparison | PASS |
| Immutable expanded snapshot | Git metadata stripped; direct mutation changes the canonical digest | `native/upstream/mozilla-translations`; unit tests | PASS |
| Recursive source lock | path, HTTPS URL, revision, and tree digest for every nested submodule | 31 records in `native/UPSTREAM_LOCK.json` | PASS |
| Source hash | canonical archive covers paths, bytes, executable modes, and symlink targets | `native/SOURCE_TREE.sha256` | PASS |
| License inventory | all discovered license/copying/notice files have hash and SPDX identity | 88 lock records; one justified `NOASSERTION` pointer | PASS |
| Flattened Git boundary | byte-exact no-filter staging plus clone-local highest-precedence attributes | `snapshot.py stage/prepare`; index-mode unit test | PASS |
| Offline normal verification | committed source and metadata verify without network access | `snapshot.py verify` | PASS |
| Upstream diff report | clean source and committed lock compare with zero differences | `M1-WP01-UPSTREAM-DIFF.md` | PASS |
| CI enforcement | native/upstream and Windows M1 scopes run snapshot tests and verification | milestone dispatchers and workflows | PASS |

## Changed paths and classification

| Path | Classification | Change |
|---|---|---|
| `native/upstream/mozilla-translations/**` | immutable MPL/upstream boundary | exact recursive Firefox-pinned source |
| `native/UPSTREAM*.json`, `native/SOURCE_TREE.sha256` | provenance/identity | source, submodule, license, and generation lock |
| `scripts/upstream/**` | Apache-2.0 build tooling/tests | create, byte-exact stage, prepare, and verify |
| `scripts/ci/verify-scope.*` | CI tooling | M1 cross-platform snapshot gate |
| `.github/workflows/upstream-firefox-*.yml` | upstream CI | M1 snapshot and candidate identity gates |
| `.gitattributes` | repository policy | request byte preservation for vendored paths |
| `architecture/UPSTREAM_FIREFOX_POLICY.md` | upstream policy | record exact pin source and canonical archive rules |

No Gradle module or dependency edge is introduced. The upstream tree remains outside
the Apache-licensed Linguum implementation boundary and is not a public API module.

## Local verification

| Command/gate | Exit/result |
|---|---|
| `python3 -m unittest discover -s scripts/upstream/tests -v` | 0; 8 tests passed |
| `python3 -m py_compile scripts/upstream/snapshot.py scripts/upstream/tests/test_snapshot.py` | 0 |
| `python3 scripts/upstream/snapshot.py verify` | 0; offline lock and source pass |
| `python3 scripts/upstream/snapshot.py verify --checkout <clean-recursive-checkout>` | 0; 31 recursive submodules and source bytes match |
| all 17 routed Unix M1 scopes | 0; every scope passed |
| `./gradlew clean verificationGate --warning-mode=fail` | 0; 17 actionable tasks, architecture/policy/coverage/tests pass |
| actionlint 1.7.12 over all workflows | 0; official release SHA-256 `aba9ced2…6953f` verified |
| Ruby workflow YAML parse; Python owned JSON parse; Bash syntax | 0 |
| Draft 2020-12 `jsonschema` 4.25.1 validation of `UPSTREAM_LOCK.json` | 0 |
| owned-path staged/unstaged `git diff --check` | 0 |
| owned-path secret/private-key and merge-marker scans | 0 findings |
| snapshot structural checks | 9,669 index/filesystem entries; 0 Git admin entries; 7 symlinks |
| GitHub file-size preflight | 0 files above 90 MiB |

Immutable upstream paths are excluded only from owned-source whitespace and
merge-marker scans because rewriting those bytes is prohibited; their complete
contents are covered by the canonical source digest. PowerShell is unavailable on
the local macOS verifier, so Windows script execution and cross-platform index
verification remain mandatory hosted checks before merge.

The first hosted run (`32373365366`) correctly exposed two platform assumptions in
the test harness: POSIX executable-bit mutation and POSIX-only absolute-path parsing.
The implementation itself had prepared the Windows snapshot successfully. The tests
now keep byte sensitivity platform-neutral, exercise mode sensitivity where chmod is
supported, and reject both POSIX and drive-qualified Windows absolute paths.

The second hosted run (`32373734090`) passed those tests and reached full snapshot
verification. It then exposed one remaining working-tree dependency: a license-file
hash read normalized Windows bytes instead of the locked Git blob. License hashes now
read the byte-exact index blobs, matching the canonical tree verifier and preserving
the same cross-platform source identity.

The manually dispatched CodeQL run (`32374452938`) then proved the workflow was
cache-sensitive: restored Gradle compilation outputs left CodeQL with no observed
Java/Kotlin build. The CodeQL build step now disables build/configuration caches and
reruns every task under instrumentation; the full clean verification task remains
the build target.

## Hosted implementation verification

All hosted checks below ran against final implementation commit
`63f070d750c6032faa39486463e5435067e55fc4`. The report-only evidence commit must
pass the same required and specialized gates before merge.

| Workflow/run | Hosted result |
|---|---|
| Protected PR matrix `32374785356` | PASS; all 15 required checks |
| Native safety `32374785362` | PASS |
| Dependency review `32374785369` | PASS |
| CodeQL `32374789830` | PASS; uncached instrumented Gradle build observed |
| Firefox snapshot integrity `32374791423` | PASS |
| Firefox compatibility `32374793304` | PASS; snapshot verification and candidate identity |

The protected Windows job passed in 3m00s, including the unit suite, Python compile,
snapshot preparation, Git-index source and license verification, and architecture
checks. This supplies the mandatory Windows execution evidence unavailable on the
local macOS verifier.

## Compatibility, security, and limitations

```text
Public API/ABI: unchanged
Runtime behavior: unchanged; no engine is built or loaded in WP01
Network behavior: generation only; normal verification is offline
Privacy: no user/model/translation content introduced
Dependencies: no production or test dependency added
Minimum platforms: unchanged
Protected baselines/thresholds: unchanged
Direct upstream edits: none
```

M1-WP01 proves source identity and reproducibility only. Platform compilation,
translation canaries, native ABI behavior, performance, sanitizers, and packaging are
subsequent M1 work-package gates and are not claimed here.
