#!/usr/bin/env bash
set -euo pipefail

repository="${1:-StevenBuglione/linguum-translation}"
[[ "$repository" == "StevenBuglione/linguum-translation" ]] || {
  printf 'Refusing to apply the canonical ruleset to %s.\n' "$repository" >&2
  exit 1
}

gh auth status >/dev/null
ruleset_id="$(gh api "repos/$repository/rulesets" --jq '.[] | select(.name == "protect-main") | .id' | head -n 1)"
if [[ -n "$ruleset_id" ]]; then
  gh api --method PUT "repos/$repository/rulesets/$ruleset_id" --input .github/rulesets/main.json >/dev/null
  printf 'Updated protect-main ruleset %s.\n' "$ruleset_id"
else
  gh api --method POST "repos/$repository/rulesets" --input .github/rulesets/main.json >/dev/null
  printf 'Created protect-main ruleset.\n'
fi
