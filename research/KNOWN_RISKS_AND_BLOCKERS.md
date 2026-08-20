# Known Risks, Hard Gates, and Blocker Decisions

## How to use this file

These are not reasons to weaken the architecture. They are the items the implementation sequence must prove early.

## R1 — Mobile native source compatibility

**Risk:** the exact Firefox-pinned C++ inference source may require platform-specific build fixes or may not meet memory/thermal requirements on Android/iOS.

**Gate:** M1 canary build and one real translation on Android arm64/x86_64 and iOS arm64/simulators.

**Forbidden shortcut:** substituting WASM, cloud translation, an old BrowserMT fork, or arbitrary `main`.

**Blocker outcome:** report exact compiler/runtime evidence and the smallest owner decision required.

## R2 — One-dependency desktop native artifact selection

**Risk:** Gradle Module Metadata can describe OS/architecture variants, but a plain JVM dependency may not request the attributes needed to disambiguate them.

**Gate:** publish to an isolated Maven repository and consume `implementation("io.linguum:translation:<version>")` from clean Windows/macOS/Linux fixture projects with no plugin or classifier.

**Pass:** the correct single runtime is resolved and loaded.

**Fail:** stop. Do not silently bundle all runtimes, download executable code at runtime, or require an undisclosed plugin.

## R3 — x64 fallback

**Risk:** the validated Windows path used AVX2; the fallback backend and its performance are not yet proven.

**Gate:** build on a baseline x86-64 profile, verify no unsupported instructions, run correctness and performance gates on controlled hardware/virtual CPU masking.

**Fail:** document AVX2 as a required v1 CPU only after owner authorization; do not claim a fallback.

## R4 — ARM math backend

**Risk:** FBGEMM is not the universal backend for ARM. Android/Linux ARM and Apple ARM must use the backend resolved by the pinned upstream source.

**Gate:** build manifests record resolved flags/backends; tests execute on real ARM hardware or required target runners.

## R5 — Structured span preservation

**Risk:** stable semantic span preservation is more difficult than plain text and must not depend on arbitrary HTML or fragile sentinel substitution.

**Gate:** deterministic adapter, range invariants, protected-span tests, cross-engine golden corpus, and failure/degradation semantics.

**Fail:** stable 1.0 is blocked because structured spans are a locked stable feature; do not silently downgrade to plain text.

## R6 — iOS x86_64 simulator

**Risk:** `iosX64` is a low support tier and Intel Apple hosts are disappearing.

**Gate:** compile on the supported macOS toolchain and run scheduled real simulator validation on an Intel host when available.

**Fail:** report toolchain evidence. Do not remove the target without architecture authorization.

## R7 — Maven namespace

**Risk:** `io.linguum` cannot publish until the Maven Central namespace is verified through domain control.

**Gate:** Central Portal namespace verification before first release candidate.

**Fail:** release blocked; implementation may continue. Do not change group ID silently.

## R8 — Dedicated performance hardware

**Risk:** shared CI runners are too noisy for authoritative latency gates.

**Gate:** provision and document stable benchmark profiles before performance becomes a merge/release blocker.

**Interim:** shared CI runs smoke thresholds only; the validated Windows baseline remains evidence but not a universal runner baseline.

## R9 — Language detection implementation

**Risk:** the architecture includes an optional language-detection capability but does not select a built-in detector.

**Locked interpretation:** implement the stable capability interface, Java/Swift facade, fakes, and contract tests. Do not bundle a detector in 1.0 unless separately researched, licensed, benchmarked, and owner-approved.

## R10 — Manifest authentication

**Risk:** adding a cross-platform runtime cryptography dependency merely to verify an embedded manifest would increase complexity.

**Locked implementation:** the immutable model manifest is embedded in the Maven/XCFramework/AAR release artifact; artifact signing, PGP, provenance, and checked-in generated digest authenticate it. Runtime verifies its generated digest and all downloaded model hashes. Runtime-downloaded alternate manifests are not supported in v1.

## R11 — Upstream source size and provenance

**Risk:** `mozilla/translations` uses recursive submodules. A simple top-level commit pin is insufficient.

**Gate:** `UPSTREAM_LOCK.json` records every recursive repository URL/path/SHA and a deterministic source-tree archive digest. Vendored source must reproduce that lock exactly.

## R12 — Native crashes in-process

**Risk:** native memory corruption terminates the host process.

**Mitigation:** strict C ABI, trusted models, sanitizers, fuzzing, hostile-input tests, soak tests, and private `TranslationRuntime` abstraction allowing future desktop process isolation.

**Forbidden shortcut:** declaring process isolation implemented when v1 is in-process.

## R13 — Model registry volatility

**Risk:** the live Mozilla registry changes over time and some artifact roles may not contain published hashes.

**Mitigation:** compatibility workflow snapshots the registry, downloads artifacts, computes all hashes/sizes, and generates an immutable release manifest. Runtime never resolves `latest`.

## R14 — Repository visibility and attestations

**Risk:** private repos on non-Enterprise GitHub plans cannot use GitHub artifact attestations.

**Default:** create the library repository public. If private is explicitly required, release is blocked until a public/provenance-compatible strategy is established.
