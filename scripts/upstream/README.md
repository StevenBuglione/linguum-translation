# Firefox-pinned source snapshot

`snapshot.py` creates and verifies the immutable recursive source snapshot required
by M1-WP01. Creation accepts only a clean checkout at the locked Firefox-selected
`mozilla/translations` revision and fails if any recursive submodule is missing,
modified, or checked out at a different revision.

The `linguum-source-tree-v1` digest is a canonical byte stream over sorted relative
paths, entry types, normalized portable modes, symlink targets, and unmodified file
bytes. Git administrative files are excluded; source-controlled `.gitmodules` files
are included. This makes the digest reproducible across supported operating systems
without relying on platform-specific tar ownership or timestamps.

Create the initial snapshot from a clean recursive checkout and the exact Firefox
pin file:

```bash
python3 scripts/upstream/snapshot.py create \
  --checkout /path/to/mozilla-translations \
  --firefox-pin-file /path/to/moz.yaml \
  --generated-at 2026-08-20T00:00:00Z \
  --run-id codex-M1-WP01-initial
```

The expanded recursive tree contains upstream ignore and attribute rules. Stage it
through the snapshot tool so Git clean filters cannot normalize or omit source bytes:

```bash
python3 scripts/upstream/snapshot.py stage
```

On a clean clone, run `prepare` before using the expanded source. It installs a
managed rule in the clone-local `.git/info/attributes` and rematerializes the index
bytes. The highest-precedence rule prevents a parent submodule's attributes from
being inherited by formerly separate nested submodules after flattening. It never
changes a tracked upstream file.

```bash
python3 scripts/upstream/snapshot.py prepare
```

Normal verification is offline and performs the same preparation automatically:

```bash
python3 scripts/upstream/snapshot.py verify
```

For a source-provenance comparison, provide a newly fetched clean recursive checkout:

```bash
python3 scripts/upstream/snapshot.py verify --checkout /path/to/mozilla-translations
```

Never edit `native/upstream/mozilla-translations/**` directly. Regeneration belongs
to the dedicated upstream compatibility workflow.
