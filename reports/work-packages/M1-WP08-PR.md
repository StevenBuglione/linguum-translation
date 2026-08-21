# M1-WP08: prove Apple XCFramework and Swift export

## Scope

- lock iOS 15, Kotlin `2.4.10`, CMake `4.0.2`, Ninja `1.13.2`, and
  runner-selected Xcode;
- export static `iosArm64`, `iosSimulatorArm64`, and `iosX64` Kotlin/Native
  frameworks over the exact WP07 native profiles;
- merge the simulator frameworks after exact header/module-map comparison and
  create one two-library `LinguumTranslation.xcframework`;
- inspect every archive object, framework, export header, module map, and
  XCFramework plist for exact architecture, platform, iOS 15, and API identity;
- expose a minimum pointer-free handwritten Swift overlay with typed errors,
  async translation, and idempotent close;
- stage an isolated SwiftPM binary-target consumer and run the exact 100-cycle
  translation/lifecycle canary;
- compile the unexecuted device-arm64 and simulator-x64 consumers;
- package a deterministic ZIP and require the SwiftPM checksum to equal its
  SHA-256;
- add protected Apple Silicon, Intel, and signed physical-device CI tiers.

## Safety boundary

The export driver rejects an unselected execution slice, mismatched headers or
module maps, wrong Mach-O platform/architecture/minimum OS, dynamic or partial
native content, malformed XCFramework metadata, native pointer leakage,
unexpected Swift declarations, mismatched checksum, malformed canary output,
or incomplete signing/provisioning identity. Xcode DerivedData is ephemeral and
outside FileProvider-managed workspace paths.

The Kotlin and Swift code is an isolated M1 feasibility fixture. It is not the
production `platform/apple` module, the canonical M3 API, or the M9 SwiftPM
companion publication surface.

## Verification

- 124 native profile/helper/export tests and 9 immutable-snapshot tests pass;
- the clean 21-task repository verification, policy, quality, architecture,
  Python compilation, JSON validation, and scope-diff gates pass;
- two independent clean three-slice local exports produce the byte-identical
  XCFramework ZIP and Swift checksum
  `66487011e242fadbd25c4a47c9f969b306a8efe6c41cff6b02b7f0276f3b0af0`;
- local Xcode 26.6 and hosted Xcode 16.4 compile the device-arm64 and
  simulator-x64 consumers and execute the arm64 Simulator async canary for 100
  translations;
- the hosted Intel safety job builds and executes the `iosX64` export for 100
  translations on a real x86_64 macOS runner;
- implementation checkpoint `86fe51828221d6ea174a17b6fc0c7ee03048611a`
  passes all 23 hosted PR, Native Safety, compatibility, and Dependency Review
  checks;
- final local/hosted slice identities, hashes, toolchains, job/run identities,
  and the fail-closed Windows path-portability regression are recorded in
  `M1-WP08-VERIFICATION.md`; the report-only successor will repeat the complete
  matrix before readiness and merge.

## Physical-device status

The signed physical-arm64 path is implemented as a fail-closed nightly/release
tier. `devicectl` reports no attached device and the repository reports zero
registered self-hosted runners, so this work package does not claim a physical
device execution result. Exact device, signing, provisioning, team, entitlement,
bundle, 100-iteration, and cleanup contracts remain mandatory when a signed
runner is configured.

## Boundaries

This PR does not create `platform/apple`, the production canonical Apple API,
or a companion SwiftPM repository. Those remain M3/M6 and M9 work. It does not
change the Firefox pin, stable C ABI, public production API, model
manifest/schema, production dependencies, minimum iOS promise, or any protected
quality/performance baseline.

Full evidence: `reports/work-packages/M1-WP08-VERIFICATION.md`.
