# M1-WP03: prove Windows AVX2 and baseline native profiles

## Scope

- build the exact Firefox-pinned source and Linguum ABI as two Windows x64 DLLs;
- prove the optimized AVX2/FBGEMM profile and a non-AVX baseline candidate;
- run the exact es→en translation and complete lifecycle 100 times per profile;
- inspect the complete PE export, ISA, architecture, and dependent-DLL surfaces;
- lock MSVC, Windows SDK, CMake, Ninja, and backend identities;
- create deterministic profile-specific candidate JARs with source/license metadata;
- make the two-profile proof part of the stable protected Windows CI job.

## Safety boundary

MSVC cannot isolate `intgemm` AVX kernels with per-function target attributes. The
baseline build therefore uses an external MPL build-only patch to exclude AVX2 and
AVX-512 kernels at configure time, then rejects any AVX-family instruction found in
the complete DLL disassembly. The immutable Firefox snapshot remains untouched.

## Local gate

- 31 native helper/profile tests pass;
- Python compilation, clean external patch staging, and immutable source verification pass;
- the clean macOS arm64 native ABI and 100-cycle translation regression pass;
- the clean repository gate and all 17 POSIX M1 workflow scopes pass;
- protected ABI 1.0 and exact 20-symbol allowlists are unchanged.

## Boundaries

This PR does not claim JNI loading, plain one-dependency consumer resolution, or
Windows 10/11 physical minimum-version execution. Those remain later locked gates.
It does not change the Firefox pin, public API, C ABI, model manifest, dependencies,
minimum platform promise, or any protected quality baseline.

Full evidence: `reports/work-packages/M1-WP03-VERIFICATION.md`.
