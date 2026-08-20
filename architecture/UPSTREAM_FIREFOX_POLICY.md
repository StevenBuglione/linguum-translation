# Firefox Upstream Compatibility and Vendoring Policy

## 1. Canonical source

The production engine source is the exact `mozilla/translations` revision selected by Firefox's own pin metadata.

Initial pin:

```text
Firefox repository:         mozilla-firefox/firefox
pin file:                   toolkit/components/translations/bergamot-translator/moz.yaml
translations repository:    mozilla/translations
revision:                   eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d
Bergamot release:           v0.6.0
```

Do not use:

- `mozilla/translations/main`;
- `browsermt/bergamot-translator`;
- archived `mozilla/bergamot-translator`;
- a permanent Linguum fork;
- a newer release not yet pinned and validated by Firefox.

## 2. Immutable snapshot

Vendored path:

```text
native/upstream/mozilla-translations/
```

The update tool creates a clean recursive checkout, strips Git administrative data, normalizes only archive metadata—not source bytes—and records:

```text
native/UPSTREAM.json
native/UPSTREAM_LOCK.json
native/SOURCE_TREE.sha256
```

`UPSTREAM_LOCK.json` records:

- top-level repository URL and SHA;
- every recursive submodule path, URL, and SHA;
- source archive SHA-256;
- license identities;
- pin metadata source SHA;
- generated timestamp and workflow run identity.

Normal PRs fail if files under the upstream path differ from the lock.

## 3. Linguum-owned code boundary

Original code lives only outside the upstream tree:

```text
native/abi/
native/mozilla-adapter/
native/runtime-build/
native/patches/
```

The adapter translates stable C ABI calls into current Mozilla C++ APIs.

No Mozilla source is copied into Apache-licensed files without an explicit license/provenance review.

## 4. Patch queue

Patches are exceptions, not normal development.

```text
native/patches/
├── PATCHES.yaml
├── windows/
├── macos/
├── linux/
├── android/
└── ios/
```

Each patch has metadata matching `schemas/patch-metadata.schema.json`:

- unique ID;
- title/reason;
- exact upstream revision;
- affected platforms and paths;
- upstream issue/PR URL where available;
- owner approval reference;
- introduction version;
- removal condition;
- license classification;
- tests proving necessity and behavior.

Builds apply patches only in a temporary worktree/build workspace. The immutable snapshot remains unchanged.

Upstream update PRs must attempt to remove every patch and fail review if an already-upstreamed patch remains without justification.

## 5. Scheduled checker

Workflow:

```text
.github/workflows/upstream-firefox-check.yml
```

Schedule: weekly and manual.

Steps:

1. fetch current Firefox default branch;
2. read/parse `moz.yaml`;
3. compare revision/release/license with `native/UPSTREAM.json`;
4. if unchanged, record success and exit;
5. if changed, create branch `automation/firefox-pin-<short-sha>`;
6. generate a compatibility work-package scaffold and source diff report;
7. open a draft PR;
8. do not update vendored source or merge automatically until compatibility workflow is explicitly dispatched/approved.

## 6. Compatibility PR requirements

A Firefox pin update PR must contain:

- old/new Firefox pin and metadata diff;
- old/new recursive source lock;
- license diff;
- patch reapplication/removal report;
- all-platform native builds;
- C ABI compatibility;
- public API compatibility;
- all approved model pairs install/load/translate/unload;
- deterministic output comparison;
- translation drift report;
- performance report by runtime profile;
- sanitizers/fuzz/stress results;
- SBOM and dependency/submodule changes;
- release notes and migration impact.

It must never auto-merge.

## 7. Security updates

A Mozilla security advisory or urgent Firefox pin update may use an expedited compatibility PR, but it cannot skip:

- source identity;
- license checks;
- required native builds;
- ABI tests;
- model load/canary translation;
- sanitizer smoke;
- provenance;
- maintainer approval.

Performance/full-model extended work may continue after an emergency patch release only when the owner explicitly accepts a documented temporary exception and the absolute product floor remains green.
