# M1-WP03 Windows Native Profiles Verification Report

## Result

```text
Status: PASS — hosted Windows build/run/ABI/ISA/package evidence verified
Milestone/work package: M1-WP03
Branch: codex/M1-WP03-windows-native-canary
Date/time UTC: 2026-08-20
Verifier: Codex
```

## Source and remote identity

```text
Repository: https://github.com/StevenBuglione/linguum-translation
Base main commit: 0bcb8479f98e4a973f04dd2c676c0e12f3ff6dae
Implementation commit: 6d694e3af4dee2572109212c4a1508c4bd474139
Hosted evidence commit: 98666c1f098b296e0e737af550774c70d54bf5e1
Remote branch SHA at hosted proof: 98666c1f098b296e0e737af550774c70d54bf5e1
Pull request: https://github.com/StevenBuglione/linguum-translation/pull/10
Working tree clean: YES after verified checkpoint commit
Shallow clone: NO
```

## Requirement traceability

| ID | Requirement | Implementation | Executable evidence | Result |
|---|---|---|---|---|
| WP03-WIN-01 | Build exact Firefox-pinned source and Linguum ABI as Windows x64 DLL | locked staged source and shared CMake target | hosted MSVC build | PASS |
| WP03-WIN-02 | Prove optimized x64 AVX2 profile | `/arch:AVX2`, FBGEMM, intgemm, ONNX SGEMM | compiler-command and PE-disassembly audit | PASS |
| WP03-WIN-03 | Prove a non-AVX2 fallback candidate | `/arch:SSE2`, no FBGEMM, SSSE3/SSE2-only intgemm, ONNX SGEMM | reject all AVX-family instructions in complete DLL disassembly | PASS |
| WP03-WIN-04 | Keep one exact C ABI and export surface | existing ABI 1.0 header and 20-symbol allowlist | C/C++ consumers plus `dumpbin /exports` | PASS |
| WP03-WIN-05 | Translate Firefox-approved es→en canary | same v2.0 model/config and exact expected text | 100 lifecycle/translation iterations per profile | PASS |
| WP03-WIN-06 | Record backend/toolchain/runtime identity | immutable profile lock and generated runtime metadata | exact MSVC/SDK/CMake/Ninja checks | PASS |
| WP03-WIN-07 | Package both DLL profiles | deterministic profile-specific candidate JARs | entry/notice/provenance inspection and SHA-256 | PASS |
| WP03-WIN-08 | Avoid build-host-only DLL dependencies | statically linked non-system libraries | `dumpbin /dependents` system allowlist | PASS |
| WP03-WIN-09 | Preserve corresponding-source obligations | MPL license, upstream lock, patch metadata in each package | package entry inspection | PASS |
| WP03-WIN-10 | Preserve all prior milestone gates | Windows proof is added to the stable Windows PR scope | clean local and hosted repository gates | PASS |

## Changed modules and paths

| Path/module | Classification | Change | Dependency rule result |
|---|---|---|---|
| `native/runtime-build` | internal native bridge | locked Windows profile switches | allowed `native-bridge`; gate PASS |
| `native/patches` | MPL external patch queue | constrain profile-specific intgemm dispatch, transport async worker failures, and enable the native ONNX SGEMM product path without leaking Marian's ARM `SSE` macro into Eigen | upstream tree untouched; gate PASS |
| `scripts/native` | build/evidence tooling | MSVC activation, two-profile build, PE/ISA/dependency audit, deterministic packages | build-time only; gate PASS |
| `scripts/native/tests` | internal test harness | offline profile, ISA, dependency, and package invariants | build-time only; local PASS |
| `toolchains` | toolchain policy | exact Windows profile/MSVC/SDK/backend lock | no production dependency; hosted identity PASS |
| Windows CI dispatcher/workflow | verification tooling | make two-profile proof part of the stable protected Windows job | no module edge; hosted gate PASS |

## Commands executed

| Command | Exit/result | Environment |
|---|---:|---|
| `python3 -m unittest discover -s scripts/native/tests -v` | 0; 45 tests passed | local macOS arm64 |
| `python3 -m py_compile scripts/native/*.py scripts/native/tests/*.py` | 0 | local Python |
| `python3 scripts/native/stage_source.py --clean` | 0; external patch applied in ignored staging only | local macOS arm64 |
| `python3 scripts/upstream/snapshot.py verify` | 0; 31 submodules and 88 licenses | immutable source unchanged |
| `python3 scripts/native/run_host_canary.py --clean --iterations 100` | 0; ABI C/C++ and 100-cycle es→en canary passed; clean-build dylib SHA-256 `60a8221cc45f8ded7c5b59084d113cafc57ffd3794c16b673379132df28946b6` | macOS 13 arm64 regression profile, CMake 4.0.2, Ninja 1.13.2 |
| two independent `python3 scripts/native/run_host_canary.py --clean --iterations 100` runs after the baseline external-search patch | 0; each clean 293-object build passed ABI C/C++, exact 20 exports, macOS 13 minimum, and 100 es→en lifecycles; both produced dylib SHA-256 `e212b97c73f51c95081b984bc3717814d4194b158cc84e7b19711b8a08dfb383` | macOS 13 arm64 regression profile, CMake 4.0.2, Ninja 1.13.2; deterministic after staged patch-byte change |
| two independent `python3 scripts/native/run_host_canary.py --clean --iterations 100` runs after the baseline scalar-search patch | 0; each clean 293-object build passed ABI C/C++, exact 20 exports, macOS 13 minimum, and 100 es→en lifecycles; both produced dylib SHA-256 `03485a6fefb29d95f62f4a9a0d146d59fe080b7c62d5520dc7a91dfa278b5cd5` | macOS 13 arm64 regression profile, CMake 4.0.2, Ninja 1.13.2; deterministic optimized/non-MSVC path |
| clean locked CMake configure/build/CTest with `-DUSE_ONNX_SGEMM=ON` | 0; native ONNX `gemm.cpp` compiled without the conflicting `SSE` macro, Marian `prod.cpp` compiled with `USE_ONNX_SGEMM=1`, exactly the three intended ABI/canary tests passed, and the real es→en canary completed 100 cycles; 20-export dylib SHA-256 `e4fd3e05f83985df6e093688d4db9f3d169411db308abdd990e53e9f7795d09c` | clean macOS arm64 forced-ONNX diagnostic, CMake 4.0.2, Ninja 1.13.2 |
| `./gradlew --no-daemon clean verificationGate --warning-mode=fail` | 0; 17 tasks, architecture/policy/API/format/coverage/quality passed | local Temurin JDK 21 / Gradle 9.5.0 |
| all 17 `scripts/ci/verify-scope.sh` M1 scopes | 0 each | architecture, quality, API, Kotlin, native, upstream, platform, consumer, model, license, artifact, release, performance |
| workflow YAML parse | 0 | all GitHub workflow YAML loaded with aliases enabled |
| hosted PR run `32392262528`, Windows job `96500930701` | 1 before compilation; mutable `windows-2025` selected the new VS 2026 image while the initial lock named VS 2022 | fail-closed runner discovery; removed ambiguous `-latest` selection |
| hosted PR run `32392539956`, Windows job `96501807295` | 1 before compilation; exact VS 17 selection proved absent on image `windows-2025-vs2026` `20260818.207.1` | official image manifest verified; exact VS 2026 install identity added while retaining legacy MSVC 14.44 |
| hosted PR run `32392944640`, Windows job `96503094811` | 1 before compilation; exact VS 2026 path resolved, but inline `cmd /s /c` quoting treated the quoted batch path literally | temporary activation batch script added with exact-content regression test |
| hosted PR run `32393175982`, Windows job `96503848960` | 1 before compilation; activation completed but the case-sensitive toolset lookup returned no value and exposed no related-key diagnostics | case-insensitive Windows environment lookup added with fail-closed related-variable diagnostics |
| hosted PR run `32393470949`, Windows job `96504800219` | 1 before compilation; case-insensitive inspection proved `VCToolsVersion` was genuinely absent after vcvars returned, with only unrelated `VCPKG_INSTALLATION_ROOT` present | activation batch now reports the vcvars exit code and installed MSVC toolset directories before failing closed |
| hosted PR run `32393848450`, Windows job `96505999675` | 1 before compilation; a second runner region served official rolling image `20260810.198.2` with VS `18.8.12023.21` instead of image `20260818.207.1` with VS `18.9.12112.369` | both finite official rollout identities locked; exact compiler, MSVC toolset, SDK, CMake, and Ninja locks remain singular |
| hosted PR run `32394104132`, Windows job `96506822256` | 1 before compilation; diagnostics proved VS 2026 rejects the named `-winsdk` form and listed exact installed legacy toolset directory `14.44.35207` | SDK changed to the supported positional argument; exact full legacy toolset requested and locked |
| hosted PR run `32394364835`, Windows job `96507654648` | 1 before compilation; exact SDK and legacy toolset activation succeeded, then the compiler banner differed from the provisional compiler lock | compiler-banner parser and fail-closed expected/actual diagnostic added before changing the lock |
| hosted PR run `32394570521`, Windows job `96508383645` | 1 before compilation; exact activation proved the legacy toolset compiler banner is `19.44.35228` | observed compiler identity locked exactly |
| hosted PR run `32394796302`, Windows job `96509086153` | 1 during optimized-profile CMake configuration; installed Doxygen activated an optional upstream docs branch whose input is absent from the pinned snapshot | upstream documentation forced off so host tool presence cannot change the native build graph |
| hosted PR run `32395376300`, Windows job `96510842275` | 1 at optimized-profile object 318/319; `/WX` promoted warnings emitted from pinned upstream headers while compiling the Linguum adapter | external target/include boundary marked `SYSTEM`; first-party adapter remains `/W4 /WX` |
| hosted PR run `32396191855`, Windows job `96513462526` | 1 at optimized-profile DLL link after all objects compiled; pinned PCRE2 installs `pcre2-8-static.lib` on MSVC while the upstream integration assumed `pcre2-8.lib` | staged external patch selects PCRE2's exact MSVC static-library filename without changing non-Windows names |
| hosted PR run `32397117391`, Windows job `96516421868` | 1 at optimized-profile DLL link; the correct static PCRE2 archive was linked, but `ssplit` compiled PCRE2 calls as DLL imports and produced ten unresolved `__imp_pcre2_*` symbols | staged external patch defines `PCRE2_STATIC` privately for the `ssplit` target on MSVC |
| hosted PR run `32398081608`, Windows job `96519499238` | 1 after the optimized DLL and both ABI consumers linked and the ABI tests passed; the first real translation lifecycle terminated with Windows fast-fail `0xc0000409` before producing application diagnostics | first-iteration Windows canary breadcrumbs added to localize the exact model/translation/cleanup boundary without weakening the 100-cycle gate |
| hosted PR run `32399217334`, Windows job `96523135772` | 1 after runtime creation, runtime-info validation, descriptor bounds, model load, translator creation, and invalid-input rejection probes; fast-fail `0xc0000409` occurs inside the first valid translation call before cleanup | first AVX2-cap attempt added with independent profile execution so the baseline proof still runs after an optimized-profile failure |
| hosted PR run `32400843977`, Windows job `96528411259` | 1 during both profile builds; removing AVX-512 implementations made the pinned intgemm header's six-way function-pointer dispatch ill-formed in the optimized build, while the independently executed baseline exposed unused CPUID register warning C4189 under `/WX` | retain the complete optimized implementation set but cap runtime CPUID at AVX2; add the pinned unsupported-backend integer aliases and explicit unused-register expression required by an SSSE3-only MSVC build; hosted result pending |
| hosted PR run `32402074501`, Windows job `96532383070` | 1 after both profiles built and linked completely and both C/C++ ABI consumers passed; optimized and independently executed SSSE3-only baseline both fast-failed with `0xc0000409` inside the first valid asynchronous translation call | matching failures rule out optimized acceleration and AVX-512 dispatch as the cause; hold Marian's process-global throw-on-abort mode for the async operation and propagate worker exceptions through the C ABI promise instead of terminating the host; hosted result pending |
| hosted PR run `32404301933`, Windows job `96539620777` | 1 after both profiles again built and linked completely and both C/C++ ABI consumers passed; the exception bridge replaced the process fast-fail with a clean status-300 error and full cleanup: `Marian must be compiled with a BLAS library` | the pinned dependent option silently forced requested native ONNX SGEMM off; preserve the wasm default while allowing an explicit native ONNX backend, include it in the CPU product dispatch, and require both its compile definition and implementation source in generated-command evidence; hosted result pending |
| hosted PR run `32407748816`, Windows job `96550745234` | 1 after both profiles built and linked completely and both passed C ABI, C++ ABI, and the real 100-cycle es→en canary; optimized DLL SHA-256 `dcfa89b99bd1b730f227e4ca0a4ee6d9fc8c7ef3703a81695bbaa7410d8c5072` passed its AVX2 audit but dependency policy omitted Windows system library `DBGHELP.DLL`; baseline completed the same tests but its complete-DLL audit found AVX-family instructions | add the Windows Debug Help OS library to the closed system dependency allowlist and retain the zero-AVX baseline rejection while emitting exact symbol/instruction evidence for the remaining binary provenance diagnosis; hosted result pending |
| hosted PR run `32409261621`, Windows job `96555601899` | 1 only at the baseline complete-DLL ISA gate after both profiles again passed C ABI, C++ ABI, and the real 100-cycle es→en canary; optimized DLL SHA-256 `fff40a9b98c14c651f20f12147d0bc3bef2fea7eb86dc00417035b32a98eeece` passed AVX2/export/dependency audits; baseline DLL SHA-256 `ec1165c4679d3a55f4471e31e22798d205932e87aa38ab08d9ff24a78ea4c976` contained exactly 975 AVX-family instructions, beginning with a contiguous `vmovdqu`/`vpmovzxbd`/`vpsrld`/`vpermd`/`vpandn`/`vpsllvd`/`vmovmskps`/`vzeroupper` block | source-level comparison with the pinned static MSVC STL identified its runtime-dispatched vector-algorithm object; disable vectorized STL call sites across every baseline C++ command, prove the profile-wide definition in `compile_commands.json`, and keep the zero-AVX final-DLL rejection unchanged; hosted result pending |
| hosted PR run `32411217246`, Windows job `96561828613` | 1 only at the baseline complete-DLL ISA gate; all other 14 PR jobs, Native Safety run `32411217268`, and Dependency Review run `32411217218` passed; both profiles passed C ABI, C++ ABI, and the real 100-cycle es→en canary; optimized DLL SHA-256 `8b9756641c3ef78454bb45777b18ef3b4419ec099215cef04a1d91c88fdbdad5`; baseline DLL SHA-256 `cbe356212570a9dc960f4014ccbf75bd9ac7714cbdef99d25164cb30dfb774bf` contained 819 AVX-family instructions, down by 156, with first blocks matching MSVC trivial-find vector routines (`vpbroadcastw`/`vpcmpeqw`/`vpmovmskb` and byte-compare/masked-load AVX2) | emit actual compile-database coverage before disassembly and enable baseline linker library tracing to identify the exact unresolved symbol and archive member that still retain the shared static-STL vector object; zero-AVX rejection remains unchanged; hosted result pending |
| hosted PR run `32412791637`, Windows job `96566895037` | 1 only at the unchanged baseline complete-DLL ISA gate; all other 14 PR jobs, Native Safety run `32412791666`, and Dependency Review run `32412791660` passed; both profiles passed C ABI, C++ ABI, and the real 100-cycle es→en canary; optimized DLL SHA-256 `68e6781ae3d72c8732c82698e7e66181ccab636a876df0888175fb41d4cdeb1e`; baseline DLL SHA-256 `35ae11022e2e20b9c8b4e652aa7669bf1d99eac3684da70e237c451342776f8c` still contained exactly 819 AVX-family instructions; compile evidence proved `_USE_STD_VECTOR_ALGORITHMS=0` on all 227/227 baseline C++ commands and on 0/302 optimized commands | profile-wide propagation is proven and library verbosity emitted no archive-resolution lines; replace that unsuccessful trace with a baseline MSVC map-file audit that resolves each rejected instruction to the closest public/static function and its defining `Lib:Object`; zero-AVX rejection remains unchanged; hosted result pending |
| hosted PR run `32414682911`, Windows job `96573018765` | 1 only at the unchanged baseline complete-DLL ISA gate; all other 14 PR jobs, Native Safety run `32414682953`, and Dependency Review run `32414682898` passed; both profiles passed C ABI, C++ ABI, and the real 100-cycle es→en canary; optimized DLL SHA-256 `feb384067206e5cb04884b306c012e6d1c79af4ffb1cc564c19f9dad36e6fb81`; baseline DLL SHA-256 `63f3ff9ffe035e592e34b379e5a2861d7614a57a20e5e4964d512fa3dc97aac0` still contained exactly 819 AVX-family instructions; the 35,697-function map resolved the first block to synthesized `wmemchr` in `marian:factored_vocab.cpp.obj` and the second to a trivial-find implementation in `libcpmt:vector_algorithms.obj`, where five functions remain live | remaining AVX is not confined to one static-STL archive member; summarize all 819 rejected instructions by mapped symbol and defining object, including the exact five live vector-algorithm functions, before choosing compiler-intrinsic, CRT-linkage, or scalar-shim boundaries; zero-AVX rejection remains unchanged; hosted result pending |
| hosted PR run `32416133464`, Windows job `96577582628` | 1 only at the unchanged baseline complete-DLL ISA gate after both profiles again passed C ABI, C++ ABI, and the real 100-cycle es→en canary; all other 14 PR jobs, Native Safety run `32416133504`, and Dependency Review run `32416133554` passed; optimized DLL SHA-256 `73c6895fc17e55d98c1878e6b752b52aa9b55a12121d3eb6f5302170d86cfb81`; baseline DLL SHA-256 `49c7bf6ed586977fd5e2dad17c7eeff516b9e7f739200ec108a2bc78ab77e89c`; all 819 rejected instructions mapped with no omissions: 680 in static UCRT math/string objects, 105 in static VC runtime `memmove`/`memset`, 34 in exactly three public static-STL vector entry points (plus their two internal implementations), and 8 in compiler-synthesized `wmemchr` | use the documented Windows 10+ system UCRT linkage for the baseline only, disable intrinsic substitution across every baseline compiler command, provide an unoptimized scalar object for the six exact memory/STL ABI symbols, and place a scalar/non-LTCG boundary on the one `wmemchr`-emitting source; add direct scalar edge/overlap tests plus linker-map proof that the static vector object is absent; optimized profile remains unchanged; hosted result pending |
| hosted PR run `32418174525`, Windows job `96584026814` | 1 at the final baseline DLL link after the optimized profile built, tested, audited, and packaged; all other 14 PR jobs, Native Safety run `32418174524`, and Dependency Review run `32418174534` passed; all 232 baseline objects compiled, including the new scalar object, before LNK2005 reported that `wmemchr` is already defined in `marian:factored_vocab.cpp.obj` | remove the redundant `wmemchr` shim and apply `/Od /Oi- /GL-` to the single proven `factored_vocab.cpp` source so its emitted implementation cannot be auto-vectorized or regenerated by LTCG; explicitly suppress the conflicting combined dynamic CRT default library while retaining the documented system-UCRT import; hosted result pending |
| hosted PR run `32419732952`, Windows job `96588939110` | 1 only at the baseline complete-DLL ISA gate; all other 14 PR jobs, Native Safety run `32419732924`, and Dependency Review run `32419732940` passed; optimized profile passed ABI, 100-cycle es-en canary, export, dependency, and AVX2 gates with DLL SHA-256 `03cede365311b0aba937f28bc8a791283fc8241faa5d3d920c5a8f95d42a0c02`; baseline linked, passed its direct scalar runtime test, both ABI tests, and 100-cycle canary with DLL SHA-256 `f0531a84b14a993ed45881df232f10b1d84fe72352c1ab0950b5edf34b05815e`; static UCRT/VC/STL AVX was eliminated and all 15 residual instructions mapped without omission to MSVC's compiler-expanded `wmemchr` in `marian:factored_vocab.cpp.obj` | add a baseline-only `#pragma function(wmemchr)` before the staged source's headers so MSVC emits the system-UCRT call; retain `/Oi-` and `/GL-` on that source while restoring normal optimization; zero-AVX rejection remains unchanged; hosted result pending |
| hosted PR run `32421630891`, Windows job `96594710937` | 1 during the baseline build after the optimized profile completed; all other 14 PR jobs, Native Safety run `32421630878`, and Dependency Review run `32421630868` passed; locked MSVC rejected `#pragma function(wmemchr)` with C4163 because its generated `wmemchr` is not an available `/Oi` intrinsic | replace the unsupported pragma with a baseline-only scalar UTF-16 code-unit loop in the staged source while retaining the optimized profile's standard-library search; compile evidence continues to require the baseline definition plus `/Oi-` and `/GL-`; hosted result pending |
| hosted PR run `32422987502`, Windows job `96598847206` | 1 only at the baseline complete-DLL ISA gate; all other 14 PR jobs, Native Safety run `32422987625`, and Dependency Review run `32422987564` passed; optimized profile passed ABI, 100-cycle canary, export, dependency, and AVX2 gates with DLL SHA-256 `a9df98d039669016397df4fcace17994c81738a13e59cf5ffbac379c90eac29c`; baseline linked, passed its direct scalar test, both ABI tests, and 100-cycle canary with DLL SHA-256 `3c69c1245423006772c549cb2be14619fd1f6bb18f4fdfed14b04acc8b2ddce9`; the scalar UTF-16 boundary eliminated all 15 `wmemchr` instructions, leaving one fully mapped VEX store (`vmovlpd`) in inline `Dense::apply` emitted by `marian:expression_operators.cpp.obj` | compile only the proven graph-construction translation unit with `/Od /Oi- /GL-`; it is not a tensor compute kernel, all other source optimization remains unchanged, and the zero-AVX rejection remains unchanged; hosted result pending |
| hosted PR run `32424273792`, Windows job `96602807970` | 0; exact optimized and baseline MSVC profiles built, linked, tested, audited, and packaged; optimized passed C/C++ ABI plus 100-cycle es→en canary in 12.73 seconds, with DLL SHA-256 `ab10fecddbc728e583017345553e098ad591658b7a8827bc9fcf7221c57778c1` and 63,798 AVX-family instructions across 1,216,732 disassembled instructions; baseline passed its direct scalar test, C/C++ ABI, and 100-cycle canary in 49.59 seconds, with DLL SHA-256 `7938a778c7daa433d8f6648370c7842f7515ff5d3b6ef35bc19b128110b737e5` and exactly zero AVX-family instructions across 1,219,391 disassembled instructions; compile evidence proved both scalar source boundaries, `/Oi-` on all commands, and vectorized STL disabled on all 227 C++ commands; all 20 exports, system-only dependencies, deterministic packages, the other 14 PR jobs, Native Safety run `32424273773`, and Dependency Review run `32424273694` passed | PASS; WP03 requirements are complete without weakening the zero-AVX rejection or optimizing away any tensor compute kernel |

## Local test and policy results

The offline suite proves the profile lock is exact, Windows profile configuration is
not host-ambiguous, the baseline patch disables all high intgemm kernels, malformed
tool metadata fails closed, AVX evidence parsing distinguishes optimized and baseline
artifacts, non-system DLL dependencies fail, compiler flags are profile-specific,
compiler command evidence is emitted, and package generation is byte-reproducible
with sorted fixed-metadata entries. The complete pre-WP03 macOS native profile was
also rebuilt from clean staging and passed its exact ABI/export/minimum-OS and
100-cycle translation regression. An independent clean forced-ONNX build compiled
the same SGEMM implementation requested by both Windows profiles and passed the
same ABI and 100-cycle translation lifecycle without registering Eigen's upstream
test suite into the product CTest tree.

## Platform and artifact results

| Target/profile | Build/link | Run/canary | ISA evidence | Package/artifact SHA-256 |
|---|---|---|---|---|
| Windows x64 AVX2 / `fbgemm-intgemm-avx2` | PASS; locked MSVC, 324 build actions | PASS; C and C++ ABI plus 100-cycle es→en canary | PASS; 63,798 AVX-family instructions including required AVX2 evidence across 1,216,732 decoded instructions | DLL `ab10fecddbc728e583017345553e098ad591658b7a8827bc9fcf7221c57778c1`; JAR `ce94cec4179ccf140cd4d94e727a1af94565326069d5a38ee9db23e495eab149` |
| Windows x64 baseline / `intgemm-ssse3-onnx-sgemm-baseline` | PASS; locked MSVC, 234 build actions including scalar runtime test | PASS; scalar runtime, C and C++ ABI, plus 100-cycle es→en canary | PASS; zero AVX-family instructions across 1,219,391 decoded instructions | DLL `7938a778c7daa433d8f6648370c7842f7515ff5d3b6ef35bc19b128110b737e5`; JAR `84289f130960b9d6d34a3e9f2c18c2eedfdb918c7a63ec82723ee20aa611f371` |

## Security, privacy, licensing, and compatibility

```text
User content handling: unchanged; fixed test canary only, no translation logging
Network access: build/model materializers only; packaged DLL has no network module
Native boundary: unchanged ABI 1.0 opaque C handles and same-library destruction
Secrets/credentials: none introduced
Production dependencies: none added
Mozilla source: immutable snapshot unchanged; patch applies only in ignored staging
Patch license: MPL-2.0 with exact affected path, SHA-256, approval, and removal rule
Public Kotlin/Java/Swift API: unchanged
Model schema/persisted metadata: unchanged
Minimum platform promise: unchanged; Windows 10 22H2 remains the floor
```

## Known limitations

- WP03 packages native-profile candidates; plain one-dependency Maven/Gradle consumer
  resolution is deliberately not claimed until WP09.
- Hosted Windows Server proves the compiler, DLL, ABI, ISA, package, and translation
  behavior. Windows 10 22H2 and Windows 11 physical/VM minimum-version smoke remain
  required release-tier evidence and are not claimed by this hosted runner alone.
- JVM/JNI loading belongs to later feasibility/binding packages; WP03 exercises the C
  ABI consumers directly.

## Gate immutability declaration

```text
[x] No coverage threshold was lowered.
[x] No performance threshold/baseline was weakened or regenerated.
[x] No API/ABI baseline was changed to hide incompatibility.
[x] No test, sanitizer, fuzz case, platform, or check was disabled/ignored.
[x] No Detekt baseline or broad suppression was added.
[x] No unapproved dependency or repository was added.
[x] Firefox pin and vendored source were not changed.
[x] Mozilla source was not directly edited.
[x] OS minimums and platform support were not raised.
[x] License, provenance, and dependency-verification gates were preserved.
```

## Final decision

```text
WORK PACKAGE GATE: PASS
SAFE TO START NEXT WORK PACKAGE: YES
SAFE TO ADVANCE MILESTONE: NOT A MILESTONE BOUNDARY
```
