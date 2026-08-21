# M1-WP05: prove Linux x64 and arm64 native profiles

## Scope

- lock Ubuntu 22.04/glibc 2.35 release builds for `linux-x64-avx2`,
  `linux-x64-baseline`, and `linux-arm64`;
- build the exact Firefox-pinned source plus the stable Linguum ABI adapter;
- prove AVX2 FBGEMM/intgemm acceleration without AVX-512, a zero-AVX x64
  baseline, and the real arm64 Ruy/NEON path;
- run the C/C++ ABI consumers and repeated es→en translation lifecycles;
- inspect ELF architecture, SONAME, exact exports, symbol-version ceilings,
  dependencies, RPATH/RUNPATH, and complete disassembly;
- run ASan+UBSan on x64 and real arm64 with leak detection and fail-fast
  undefined-behavior handling;
- create deterministic native JARs and authenticated compatibility bundles;
- execute the exact Ubuntu 22.04 artifacts on Ubuntu 24.04 for both CPU
  architectures;
- add protected x64 PR coverage and independent x64/arm64 Native Safety jobs.

## Safety boundary

The x64 baseline rejects every AVX-family instruction in the linked ELF. The
optimized x64 profile requires executable AVX2 evidence while rejecting all
AVX-512/EVEX instructions. The arm64 profile requires real AArch64 execution,
Ruy compile evidence, and linked NEON/ASIMD instructions. Release ELFs may depend
only on the closed Linux system-library allowlist, must not contain an RPATH or
RUNPATH, and may require no GLIBC symbol newer than 2.35.

Sanitizer execution exposed two unaligned model-read paths in the pinned native
source. They are fixed only through the approved external patch queue with
`memcpy`; the immutable Mozilla snapshot remains byte-identical to its lock.

## Verification

- 72 native profile/helper tests and 9 immutable-snapshot tests pass;
- the clean 21-task repository `verificationGate`, all local CI scopes, Python
  compilation, JSON/YAML validation, and actionlint pass;
- all three release profiles pass exact ABI/export/dependency/ISA inspection,
  deterministic packaging, and 100 translation lifecycles;
- x64 baseline and real arm64 ASan+UBSan builds pass native tests and 10 repeated
  translation lifecycles with fail-fast and leak checks active;
- the exact three Ubuntu 22.04 release bundles pass 100 translation lifecycles
  again on Ubuntu 24.04 for their matching architectures;
- hosted PR, Native Safety, Dependency Review, and merge evidence will be added
  to `M1-WP05-VERIFICATION.md` from the pushed checkpoint.

## Boundaries

This PR does not claim Android AAR/JNI proof, iOS slices, Apple export, or plain
one-dependency Maven resolution; those remain WP06-WP09. It does not change the
Firefox pin, public API, C ABI, model manifest/schema, production dependencies,
minimum platform promise, or any protected quality/performance baseline.

Full evidence: `reports/work-packages/M1-WP05-VERIFICATION.md`.
