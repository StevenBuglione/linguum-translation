# M1-WP04: prove macOS arm64 and x64 native profiles

## Scope

- lock host-independent arm64 and x64 native candidate profiles;
- build the exact Firefox-pinned source plus Linguum ABI adapter;
- run the C and C++ ABI consumers and 100 es→en lifecycles per profile;
- prove thin Mach-O architectures, macOS 13.0 load-command floors, and exact exports;
- prove Accelerate linkage and record ARM/Ruy versus x64/intgemm backend selection;
- reject host-dependent `-march=native` and non-system dylib dependencies;
- create deterministic, architecture-specific JARs with source/license metadata;
- run the proof on physical Apple Silicon and physical Intel GitHub runners.

## Safety boundary

The x64 general-code floor is explicit Nehalem/SSE4.2, which does not require AVX.
Upstream intgemm retains its own runtime-selected optimized kernels. The arm64 profile
uses the existing upstream ARM/Ruy quantized path. Both use Accelerate for SGEMM.

## Verification

- 55 native profile/helper tests, Python compilation, YAML parsing, immutable source
  verification, the clean 17-task repository gate, and all local CI scopes pass;
- hosted Apple Silicon and Intel builds each pass C/C++ ABI, 100 translation
  lifecycles, exact 20 exports, architecture/minimum-OS/dependency/command audits,
  and deterministic packaging;
- all protected PR checks, Native Safety, and Dependency Review pass on the exact
  implementation head.

## Boundaries

This PR does not claim plain one-dependency Maven consumption, iOS slices, or an
XCFramework. Those remain WP09 and WP07/WP08. It does not change the Firefox pin,
public API, C ABI, model manifest, dependencies, minimum platform promise, or any
protected quality baseline.

Full evidence: `reports/work-packages/M1-WP04-VERIFICATION.md`.
