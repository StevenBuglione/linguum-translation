# M1-WP07: prove iOS native profiles through minimal cinterop

## Scope

- lock iOS 15, Kotlin `2.4.10`, CMake `4.0.2`, Ninja `1.13.2`, and
  runner-selected Xcode;
- build static `iosArm64`, `iosSimulatorArm64`, and `iosX64` native profiles
  from the exact Firefox-pinned source and stable Linguum C ABI adapter;
- use Accelerate plus Ruy/NEON for arm64 and Accelerate plus runtime-dispatched
  intgemm for x64;
- merge each profile's private native closure into one deterministic static
  archive and package it with corresponding-source, patch, provenance, and
  license metadata;
- compile a standalone Kotlin/Native consumer that reaches the stable C ABI
  only through minimal cinterop;
- run the exact 100-cycle model/translation lifecycle on installed arm64 and
  Intel simulator applications;
- add protected PR simulator coverage and fail-closed signed physical-device
  nightly/release jobs.

## Safety boundary

Every merged archive must contain the complete stable C ABI, only Mach-O
objects for its locked architecture/platform/minimum iOS version, the selected
backend evidence, and normalized archive member metadata. Build commands reject
host SDK leakage, host-dependent `-march=native`, the wrong backend, the wrong
target triple, and a partial or duplicate private-library closure. The isolated
cinterop fixture is not a production Apple module or distribution surface.

## Verification

- 106 native profile/helper tests and 9 immutable-snapshot tests pass;
- the clean 21-task repository `verificationGate`, Python compilation, JSON
  validation, scope-diff, and architecture checks pass;
- two independent post-fix clean three-profile builds produce byte-identical
  shipping archives and ZIP packages;
- the local installed `iosSimulatorArm64` app completes 100 lifecycles with ABI
  1.0, and the hosted Xcode 16.4 PR job repeats that exact execution;
- the hosted Intel safety job builds and runs `iosX64` for 100 lifecycles on a
  real x86_64 macOS runner;
- implementation checkpoint `8233ee40633e1c9979d2551fc572e88e3305c74b`
  passes all 23 hosted PR, Native Safety, compatibility, and Dependency Review
  checks;
- final hosted run/job identities, local and hosted artifact hashes, and the
  fail-closed Xcode 16.4 archive-normalization regression are recorded in
  `M1-WP07-VERIFICATION.md`; the report-only successor will repeat the complete
  matrix before readiness and merge.

## Physical-device status

The signed physical arm64 path is implemented as a fail-closed nightly/release
tier. `devicectl` reports no attached device and the repository reports zero
registered self-hosted runners, so this work package does not claim a physical
device execution result. The required runner labels, provisioning inputs,
codesigning, install/launch/uninstall flow, and exact 100-cycle marker contract
remain mandatory when a signed runner is configured.

## Boundaries

This PR does not create `platform/apple`, an XCFramework, a Swift overlay,
`Package.swift`, the production Apple API, or an Apple publication surface;
those are M1-WP08 and later work. It does not change the Firefox pin, public
API, C ABI, model manifest/schema, production dependencies, minimum iOS
promise, or any protected quality/performance baseline.

Full evidence: `reports/work-packages/M1-WP07-VERIFICATION.md`.
