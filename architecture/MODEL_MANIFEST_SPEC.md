# Approved Model Manifest and Installation Specification

## 1. Purpose

Each library release embeds one immutable approved model manifest. The manifest determines:

- supported direct language pairs;
- exact Mozilla model/version/architecture;
- exact artifact locations;
- compressed and installed hashes/sizes;
- required runtime capabilities;
- compatibility with the Firefox-pinned engine revision.

The live Mozilla registry is never consulted by translation runtime code.

## 2. Files

```text
translation-model-manifest/src/commonMain/resources/
├── approved-models.json
└── approved-models.sha256
```

Release evidence also contains:

```text
publication/provenance/
├── approved-models.json
├── approved-models.sha256
├── source-registry-snapshot.json
├── model-drift-report.json
└── model-validation-report.md
```

The manifest is authenticated as part of the signed/attested Maven/AAR/XCFramework release artifact. Runtime verifies its embedded digest before parsing. Runtime-downloaded alternate manifests are forbidden in v1.

## 3. Schema

Canonical structure:

```json
{
  "schemaVersion": 1,
  "manifestRevision": "2026-08-20.1",
  "libraryVersion": "1.0.0",
  "firefox": {
    "repository": "mozilla-firefox/firefox",
    "translationsRepository": "mozilla/translations",
    "translationsRevision": "eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d",
    "bergamotVersion": "v0.6.0"
  },
  "sourceRegistry": {
    "url": "https://storage.googleapis.com/moz-fx-translations-data--303e-prod-translations-data/db/models.json",
    "retrievedAt": "2026-08-20T00:00:00Z",
    "sha256": "..."
  },
  "models": [
    {
      "id": "es-en@2.0",
      "pair": {
        "source": "es",
        "target": "en"
      },
      "mozillaVersion": "2.0",
      "releaseStatus": "Release",
      "architecture": "base-memory",
      "capabilities": {
        "plainText": true,
        "structuredText": true,
        "alignment": "experimental",
        "qualityEstimation": "unsupported"
      },
      "artifacts": [
        {
          "role": "model",
          "fileName": "model.esen.intgemm.alphas.bin",
          "compression": "gzip",
          "downloadSources": [
            {
              "kind": "mozilla",
              "url": "https://.../model.esen.intgemm.alphas.bin.gz"
            }
          ],
          "compressedSize": 0,
          "compressedSha256": "...",
          "installedSize": 0,
          "installedSha256": "4aed7734152ae0045d1a69ae49c86cfda18f53c61f90e95e1d1de1c7c7c3b033"
        },
        {
          "role": "vocabulary",
          "fileName": "vocab.esen.spm",
          "compression": "gzip",
          "downloadSources": [{ "kind": "mozilla", "url": "https://..." }],
          "compressedSize": 0,
          "compressedSha256": "...",
          "installedSize": 0,
          "installedSha256": "..."
        },
        {
          "role": "shortlist",
          "fileName": "lex.50.50.esen.s2t.bin",
          "compression": "gzip",
          "downloadSources": [{ "kind": "mozilla", "url": "https://..." }],
          "compressedSize": 0,
          "compressedSha256": "...",
          "installedSize": 0,
          "installedSha256": "..."
        }
      ],
      "runtimeConfiguration": {
        "configurationResource": "configs/es-en.yml",
        "configurationSha256": "..."
      }
    }
  ]
}
```

`schemas/model-manifest.schema.json` is authoritative for syntax.

## 4. Generation workflow

Only the protected model/upstream compatibility workflow may generate the manifest.

Steps:

1. fetch Firefox pin metadata;
2. fetch and hash the Mozilla model registry;
3. select candidate entries with `releaseStatus == Release`;
4. apply the approved language/model policy;
5. download all artifacts into an isolated workspace;
6. verify any upstream-published hashes;
7. compute compressed size/hash;
8. decompress safely with expansion limits;
9. compute installed size/hash for every artifact;
10. generate deterministic model config;
11. build every runtime profile;
12. install/load/translate/unload each pair;
13. run golden/drift/quality sanity suite;
14. run performance subset per architecture class;
15. sort canonical JSON by language pair and artifact role;
16. write manifest and digest;
17. create compatibility PR with reports;
18. never merge automatically.

## 5. Source abstraction

A `ModelSource` supplies bytes but is not trusted.

Supported source kinds:

- Mozilla official HTTPS;
- future Linguum mirror;
- enterprise HTTPS mirror;
- local filesystem/offline bundle;
- test source.

Every source must produce the exact artifact bytes identified by the embedded manifest.

No source may override:

- model version;
- expected size;
- hash;
- language pair;
- runtime configuration;
- capabilities.

## 6. Transactional installation

Per-model directory layout:

```text
<storage-root>/
├── installed/
│   └── es-en/
│       └── 2.0/
│           ├── model.esen.intgemm.alphas.bin
│           ├── vocab.esen.spm
│           ├── lex.50.50.esen.s2t.bin
│           ├── model.yml
│           └── installation.json
├── staging/
│   └── <transaction-id>/
├── quarantine/
├── locks/
└── store.json
```

Installation sequence:

1. acquire process-safe pair/version installation lock;
2. check current verified installation;
3. calculate required bytes plus safety margin;
4. preflight available storage;
5. create unique staging directory;
6. download with bounded retries/cancellation/resume policy;
7. verify compressed size/hash;
8. stream decompress with output limit;
9. verify installed size/hash;
10. write generated config and installation metadata;
11. run native compatibility probe;
12. fsync files/directories where platform supports it;
13. atomically rename/promote staging directory;
14. update store metadata atomically;
15. expose `Installed` state;
16. clean stale staging entries on restart.

If any step fails, the previous installation remains active and the staged files are removed or quarantined.

## 7. Resumable downloads

- resume only when the source supports safe byte ranges and entity consistency;
- retain partial files only with recorded URL, expected total size, validator/ETag where available, and manifest identity;
- revalidate range response and final complete hash;
- if safe resume cannot be proven, restart;
- never install a partial artifact;
- cancellation leaves only a recoverable staging state, never an installed state.

## 8. Activation and model generations

A verified installed model is not automatically active.

Activation:

1. load candidate generation;
2. run canary translation and runtime compatibility checks;
3. atomically mark new generation for new requests;
4. allow old generation's in-flight requests to finish;
5. destroy old generation when reference count reaches zero;
6. retain previous installed version temporarily for rollback according to policy.

A failed candidate activation leaves the old generation active.

## 9. Disk and memory policies

Disk retention and memory pinning are separate.

- memory pin lease prevents loaded-model eviction;
- disk retention lease prevents installed-model eviction;
- active, loading, installing, verifying, pinned, retained, and activating models are never evicted;
- disk eviction is byte-budgeted LRU;
- memory eviction is byte-budgeted LRU;
- inability to free enough space returns typed `InsufficientStorage`.

## 10. Runtime invariants

- runtime never resolves `latest`;
- same library release exposes same catalog;
- runtime never accepts a manifest supplied by a remote model source;
- all installed files are hash-verified before native load;
- installed model paths are never public API;
- corrupt existing installation is quarantined and reported;
- offline translation works indefinitely with a valid installed model;
- library upgrades do not silently activate a new model without their embedded manifest and installation/activation flow.
