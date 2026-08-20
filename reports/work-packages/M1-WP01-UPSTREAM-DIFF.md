# M1-WP01 Upstream Source Diff Report

## Compared identities

```text
Firefox repository:       https://github.com/mozilla-firefox/firefox.git
Firefox pin source SHA:   48d55cf7ec80093903e2ef7f58b61a84a22ef716
Firefox pin path:         toolkit/components/translations/bergamot-translator/moz.yaml
Firefox pin file SHA-256: 42b4fcddfd421cfe4959c3a126f93aa2c5b26f5380b337a88be2fe336c2604c4
Translations repository:  https://github.com/mozilla/translations.git
Translations revision:    eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d
Bergamot release:         v0.6.0
Declared license:         MPL-2.0
```

## Clean recursive checkout comparison

The independent source checkout used:

```bash
git clone --filter=blob:none --no-checkout https://github.com/mozilla/translations.git <temporary>/translations
git -C <temporary>/translations checkout --detach eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d
git -C <temporary>/translations submodule update --init --recursive --filter=blob:none --jobs 8
python3 scripts/upstream/snapshot.py verify --checkout <temporary>/translations
```

Comparison result:

```text
Top-level HEAD mismatch:          0
Dirty/untracked checkout paths:   0
Missing recursive submodules:     0
Changed submodule revisions:      0
Changed submodule URLs:           0
Changed submodule tree hashes:    0
Source path/byte/mode/link diffs: 0
Recursive submodules locked:      31
License files inventoried:        88
Canonical source-tree SHA-256:    94e42bbd05187c94dbb8adc04074015faab65d8f648d583b7056e8e4cf59182f
Result:                           PASS — exact recursive pin
```

One license-pointer file, `inference/marian-fork/src/3rd_party/onnxjs/benchmark/LICENSE`,
contains links to three external project licenses rather than license text and is
therefore recorded as SPDX `NOASSERTION`; its bytes are still locked. The other 87
license files have explicit SPDX identities or expressions.
