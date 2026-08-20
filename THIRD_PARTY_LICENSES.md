# Third-party licenses

M0 contains build tooling dependencies only; it publishes no runtime library or native artifact.

Future native distributions will include the exact Firefox-pinned
[`mozilla/translations`](https://github.com/mozilla/translations) source and its recursive dependencies under their original licenses. Mozilla-covered files remain MPL-2.0 and isolated under `native/upstream/mozilla-translations/`.

Every release must regenerate this inventory from locked dependencies, the recursive upstream source lock, SBOMs, and model/source compliance evidence. This file may not be used to claim that a future release inventory is complete.
