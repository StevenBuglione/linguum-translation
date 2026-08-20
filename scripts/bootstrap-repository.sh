#!/usr/bin/env bash
set -euo pipefail

REPOSITORY="${1:-StevenBuglione/linguum-translation}"
DESCRIPTION="${LINGUUM_REPOSITORY_DESCRIPTION:-Firefox-compatible native translation for Kotlin Multiplatform}"
VISIBILITY="${LINGUUM_REPOSITORY_VISIBILITY:-public}"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

command -v git >/dev/null 2>&1 || fail "git is required"
command -v gh >/dev/null 2>&1 || fail "GitHub CLI (gh) is required"
gh auth status >/dev/null || fail "gh is not authenticated"

[[ -f START_HERE.md ]] || fail "Run from the extracted handoff/repository root"
[[ -f architecture/LOCKED_DECISIONS.md ]] || fail "Frozen architecture source is missing"
[[ -f MANIFEST.sha256 ]] || fail "MANIFEST.sha256 is missing"

if [[ ! -d .git ]]; then
  git init -b main
fi

current_branch="$(git branch --show-current)"
if [[ -z "$current_branch" ]]; then
  git switch -c main
elif [[ "$current_branch" != "main" ]]; then
  fail "Initial bootstrap must run on main, not $current_branch"
fi

# Stage only the known handoff roots. Never use git add . or git add -A.
git add -- \
  START_HERE.md \
  README.md \
  AGENTS.md \
  CODEX_EXECUTION_CONTRACT.md \
  LINGUUM_TRANSLATION_COMPLETE_CODEX_HANDOFF.md \
  MANIFEST.sha256 \
  architecture \
  implementation \
  research \
  schemas \
  codex \
  scripts \
  templates

git diff --cached --check

if git diff --cached --quiet; then
  printf 'No initial handoff changes to commit.\n'
else
  git commit -m "M0-WP01: add frozen Linguum Translation handoff"
fi

if gh repo view "$REPOSITORY" >/dev/null 2>&1; then
  printf 'Repository %s already exists; reusing it.\n' "$REPOSITORY"
  remote_url="https://github.com/${REPOSITORY}.git"
  if git remote get-url origin >/dev/null 2>&1; then
    existing="$(git remote get-url origin)"
    [[ "$existing" == "$remote_url" || "$existing" == "git@github.com:${REPOSITORY}.git" ]] || \
      fail "origin points to $existing instead of $REPOSITORY"
  else
    git remote add origin "$remote_url"
  fi
else
  case "$VISIBILITY" in
    public) visibility_flag="--public" ;;
    private) visibility_flag="--private" ;;
    *) fail "LINGUUM_REPOSITORY_VISIBILITY must be public or private" ;;
  esac

  gh repo create "$REPOSITORY" \
    "$visibility_flag" \
    --source=. \
    --remote=origin \
    --description "$DESCRIPTION"
fi

git push -u origin main
git fetch origin main

local_sha="$(git rev-parse HEAD)"
remote_sha="$(git rev-parse origin/main)"
[[ "$local_sha" == "$remote_sha" ]] || fail "Remote SHA $remote_sha does not match local SHA $local_sha"

printf 'Repository bootstrap verified.\n'
printf 'Repository: https://github.com/%s\n' "$REPOSITORY"
printf 'Commit: %s\n' "$local_sha"
