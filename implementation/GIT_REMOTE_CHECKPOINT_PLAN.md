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
- no rebasing or rewriting pushed branch history;
- corrections are new commits;
- squash merge may be used by the protected merge workflow while original branch commits remain in GitHub history until branch deletion.

## 10. Main protection

After required PR checks have run at least once, apply a main-branch ruleset requiring:

- pull request;
- required status checks;
- conversation resolution;
- linear history/squash merge policy;
- no force pushes;
- no deletion;
- no bypass, including administrators where supported;
- signed release tags;
- zero mandatory human approvals or CODEOWNERS approvals; CODEOWNERS is routing metadata.

The owner grants standing delivery authorization to merge when the exact remote head
SHA has passed every required status check. Manual review remains welcome but is not
a progression or merge gate. Protected architecture, upstream, ABI, baseline, and
release changes still require their dedicated evidence-producing workflows.

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
