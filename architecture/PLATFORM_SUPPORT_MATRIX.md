# Platform and Native Backend Support Matrix

## 1. Public platform promise

A platform is supported only when its production artifact is built, packaged, consumed, executed, and verified in CI/release evidence.

## 2. Desktop delivery model

Desktop uses one Kotlin/JVM target with Java 17 bytecode and JNI-loaded native runtimes.

| Platform | Public runtime | Native artifact | Minimum OS | Primary validation |
|---|---|---|---|---|
| Windows x64 | JVM | DLL | Windows 10 22H2 | Windows 10/11 physical/VM integration |
| macOS arm64 | JVM | dylib | macOS 13 | Apple Silicon runner + real smoke |
| macOS x64 | JVM | dylib | macOS 13 where supported | Intel build/run tier |
| Linux x64 | JVM | `.so` | glibc 2.35 | Ubuntu 22.04/24.04 |
| Linux arm64 | JVM | `.so` | glibc 2.35 | real arm64 scheduled/release runner |

Do not publish Kotlin/Native desktop targets merely to claim desktop support.

## 3. Android

| ABI | Purpose | Minimum |
|---|---|---|
| `arm64-v8a` | production devices | API 26 |
| `x86_64` | emulator/development | API 26 |

Use the AGP 9 Android-KMP library plugin in an isolated Android platform module. Package JNI runtime through an AAR. Native dependencies should be statically linked into one exported JNI library per ABI where licensing permits, limiting exported symbols to `JNI_OnLoad` and the approved JNI bridge.

Do not support `armeabi-v7a` or `x86` in v1.

## 4. iOS

| Target | Purpose | Minimum |
|---|---|---|
| `iosArm64` | physical devices | iOS 15 |
| `iosSimulatorArm64` | Apple Silicon simulator | iOS 15 |
| `iosX64` | Intel simulator compatibility | iOS 15 |

Build the KMP umbrella framework and the native C++ runtime into a release XCFramework. The Swift facade is handwritten and distributed through SwiftPM.

`iosX64` is a lower-support Kotlin target and requires scheduled/release validation on an appropriate host. Failure must be reported, not hidden.

## 5. Toolchain lock

Initial lock:

```text
Kotlin                  2.4.10
Gradle                   9.5.0
JDK build runtime        21 LTS
JVM target               17
AGP                      9.1.1, with M0 compatibility proof
Android NDK              28.2.13676358
Android Build Tools      36.0.0
Xcode                    Kotlin 2.4.10-supported Xcode, initially 26.4
MSVC                     Visual Studio 2022 / toolset locked in toolchains file
CMake desktop            4.0.2 initially, because benchmark validated it
Ninja                    locked in toolchains file
```

All exact versions and container/runner images belong in:

```text
gradle/libs.versions.toml
toolchains/toolchains.lock.yaml
toolchains/ci-runners.lock.yaml
```

Toolchain upgrades require compatibility PRs.

## 6. Native backend profiles

Exact backend selection is an implementation result, not a public API.

### x86_64 optimized

Expected profile:

```text
FBGEMM
AVX2
Release optimization
one AsyncService worker/model
```

Initial authoritative benchmark profile:

```text
windows-x64-avx2
```

### x86_64 fallback

Must be proven in M1.

Requirements:

- no AVX2 instruction;
- no illegal-instruction-based detection;
- exact backend recorded;
- same C ABI/public behavior;
- correctness and product absolute latency gate;
- platform-specific artifact selected before load.

Do not claim fallback support until executable evidence exists.

### Apple arm64

Resolve and record the pinned source's ARM/Accelerate path. Validate on physical Apple Silicon and iOS device/simulator.

### Linux/Android arm64

Resolve and record the pinned source's ARM/NEON/RUY path. Validate on real ARM64, not compile-only evidence.

### Android x86_64

Use a compatible x86_64 profile that does not assume host AVX2. This is a development/emulator target and still must meet correctness and a documented performance floor.

## 7. CPU detection

The JVM loader detects:

- OS;
- normalized architecture;
- CPU capability needed for optimized profile;
- expected artifact digest and ABI.

Selection happens before loading native code.

The library may not:

- load an AVX2 binary and catch illegal instruction;
- choose based only on OS name;
- accept an unknown architecture as x64;
- use a downloaded executable runtime;
- fall back silently to a different translation engine.

## 8. Minimum-version validation

### Windows

- compile against supported SDK/toolset;
- run smoke on Windows 10 22H2 and Windows 11;
- avoid APIs newer than the floor unless dynamically guarded internally.

### macOS/iOS

- explicit deployment targets;
- inspect Mach-O minimum versions in release validation;
- run minimum-supported simulator/device tier where feasible.

### Linux

- build against Ubuntu 22.04/glibc 2.35 baseline container;
- inspect required GLIBC symbol versions;
- run on 22.04 and 24.04;
- no accidental dependency on build-host-only shared libraries.

### Android

- `minSdk = 26` enforced;
- native API level configured consistently;
- run emulator at minimum API and current API;
- physical arm64 release smoke.

## 9. Artifact naming

```text
linguum-translation-native-windows-x64-avx2-<version>.jar
linguum-translation-native-windows-x64-baseline-<version>.jar
linguum-translation-native-macos-arm64-<version>.jar
linguum-translation-native-macos-x64-<version>.jar
linguum-translation-native-linux-x64-avx2-<version>.jar
linguum-translation-native-linux-x64-baseline-<version>.jar
linguum-translation-native-linux-arm64-<version>.jar
translation-android-<version>.aar
LinguumTranslation.xcframework.zip
```

Artifact coordinates/variant names are implementation details and are not documented as consumer dependencies.

## 10. M1 hard gate

For every target/profile:

1. build exact pinned source plus Linguum adapter;
2. verify symbol allowlist and ABI version;
3. load Firefox-approved es→en model;
4. translate a fixed canary sentence;
5. compare non-empty expected-language result;
6. create/destroy 100 times;
7. record backend/toolchain/runtime info;
8. package artifact;
9. consume from a clean fixture;
10. push report and artifact hashes.

Stable API work cannot start until M1 is green or a blocker is accepted by the owner.
