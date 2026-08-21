# M1-WP06: prove Android arm64-v8a and x86_64 native profiles

## Scope

- lock NDK `28.2.13676358`, Build Tools `36.0.0`, API 26, arm64-v8a, and
  x86_64 feasibility profiles;
- build the exact Firefox-pinned source plus the stable Linguum ABI adapter;
- prove real arm64 Ruy/NEON and an x86-64-v2 baseline with no AVX-family
  instructions;
- expose only `JNI_OnLoad`, register natives explicitly, and statically link
  all private native dependencies into one JNI library per ABI;
- create a deterministic two-ABI AAR containing corresponding-source,
  provenance, patch, and license metadata;
- compile a clean standalone consumer from one AAR dependency and the pinned
  es→en model assets;
- run the exact 100-cycle ABI/model/translation lifecycle on the API-26
  x86_64 emulator and physical arm64 hardware;
- add protected PR emulator coverage and locked nightly/release physical jobs.

## Safety boundary

The x86_64 library is fully disassembled and rejects every AVX-family
instruction. The arm64 library requires Ruy compile evidence plus linked
NEON/ASIMD evidence and must complete on a real 64-bit arm64 device. Each JNI
ELF has the exact SONAME, only Android system dependencies, no RPATH/RUNPATH,
and exactly one export. Device success is accepted only from a marker correlated
to the current ADB run token or from an authoritative Test Lab game loop that
finishes after the native lifecycle completes.

## Verification

- 91 native profile/helper tests and 9 immutable-snapshot tests pass;
- the clean 21-task repository `verificationGate`, Python compilation, JSON
  validation, and architecture checks pass;
- three clean two-ABI builds pass compile-database, ELF, export, dependency,
  ISA, packaging, and consumer audits;
- independent clean arm64, x86_64, and AAR outputs compare byte-for-byte;
- physical Test Lab matrix `matrix-3p9hhd7brxn1d` passes on F-01L/API 27 and
  logs `primaryAbi=arm64-v8a`, `osArch=aarch64`, `is64Bit=true`, followed by
  `100 iterations, ABI 1.0`;
- the physical-test APK downloaded from Test Lab is byte-identical to the
  submitted APK;
- exact checkpoint `5dd9bc71f6161461f17ae49b9b2cb8e99950d6ae` passed all 22
  hosted PR, Native Safety, and Dependency Review checks, including the API-26
  token-correlated x86_64 emulator canary and both Linux sanitizer profiles;
- final hosted run, job, artifact, and log identities are recorded in
  `M1-WP06-VERIFICATION.md`; the report-only successor will repeat the complete
  matrix before readiness and merge.

## Boundaries

This PR does not create the production Android module, publish to Maven, or
change the Firefox pin, public API, C ABI, model manifest/schema, production
dependencies, minimum API promise, or any protected quality/performance
baseline. Production Android remains M6 and publication remains WP09.

Full evidence: `reports/work-packages/M1-WP06-VERIFICATION.md`.
