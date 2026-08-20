# Licensing and Source-Compliance Boundary

## 1. License split

Original Linguum Translation source:

```text
Apache License 2.0
```

Mozilla-derived source and covered modifications:

```text
Mozilla Public License 2.0
```

The MPL is file-level copyleft. It permits combining MPL-covered files with Apache-2.0 files in a larger work, including static linking, while requiring recipients of distributed executable/library forms to be informed where the MPL-covered source can be obtained.

## 2. Directory classification

### Apache-2.0

```text
translation*/
platform/
facades/
native/abi/
native/mozilla-adapter/  (only independently written adapter code)
native/runtime-build/
testing/
build-logic/
scripts/
docs/
```

Every original source file carries an SPDX header where appropriate:

```text
SPDX-License-Identifier: Apache-2.0
```

### MPL-2.0

```text
native/upstream/mozilla-translations/**
```

Files retain their original notices and SPDX/license headers.

Patches that modify MPL-covered files are treated as MPL-covered source and distributed with corresponding source.

## 3. Prohibited contamination

- Do not paste Mozilla implementation code into Apache-licensed files.
- Do not remove or rewrite Mozilla notices.
- Do not label a modified Mozilla file Apache-2.0.
- Do not place Linguum application code inside the vendored tree.
- Do not ship an executable native artifact without corresponding-source information.

## 4. Required root files

```text
LICENSE                   Apache-2.0 full text
NOTICE                    Linguum notices and attribution summary
THIRD_PARTY_LICENSES.md   dependency/upstream licenses
SECURITY.md
```

## 5. Required release assets

Each release includes:

```text
linguum-translation-<version>-sources.zip
mozilla-translations-source-<revision>.tar.zst
UPSTREAM.json
UPSTREAM_LOCK.json
PATCHES.yaml
THIRD_PARTY_LICENSES.md
CycloneDX SBOM(s)
artifact checksums
provenance attestations
```

The Maven POM names Apache-2.0 as the license of the original library artifact and its descriptions/NOTICE clearly identify bundled MPL-covered components.

## 6. Corresponding source

The release notes and native artifact metadata must state:

- exact Mozilla repository and revision;
- where the exact vendored source archive can be downloaded;
- where applied patch source can be downloaded;
- the MPL-2.0 license link/text;
- the source archive SHA-256.

The corresponding-source location must remain durable for the lifetime of the distributed release.

## 7. Dependency license policy

Allowed by default:

- Apache-2.0
- MIT
- BSD-2-Clause
- BSD-3-Clause
- MPL-2.0 when isolated/compliant
- other permissive licenses after explicit approval

Review/block by default:

- GPL/AGPL/SSPL and strong copyleft dependencies;
- non-commercial/custom terms;
- unlicensed source;
- dependencies with unclear native redistribution rights;
- runtime model/data licenses not explicitly documented.

## 8. Legal checkpoint

Before `1.0.0-rc.1`, obtain a real legal/compliance review covering:

- Apache/MPL boundary;
- static native linking and third-party submodules;
- model distribution/download terms;
- Maven/AAR/XCFramework notices;
- corresponding source process;
- trademark naming/attribution;
- dependency license report.

Codex records completion evidence but must not claim to provide legal advice.
