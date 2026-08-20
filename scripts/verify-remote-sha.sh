#!/usr/bin/env bash
set -euo pipefail

branch="${1:-$(git branch --show-current)}"
[[ -n "$branch" ]] || { printf 'ERROR: no branch specified\n' >&2; exit 1; }

git fetch origin "$branch"
local_sha="$(git rev-parse HEAD)"
remote_sha="$(git rev-parse "origin/$branch")"

if [[ "$local_sha" != "$remote_sha" ]]; then
  printf 'ERROR: local %s != remote %s for %s\n' "$local_sha" "$remote_sha" "$branch" >&2
  exit 1
fi

printf '%s %s\n' "$branch" "$local_sha"
