# Repository Layout

## Root

```text
linguum-translation/
├── README.md
├── START_HERE.md
├── AGENTS.md
├── CODEX_EXECUTION_CONTRACT.md
├── LICENSE
├── NOTICE
├── THIRD_PARTY_LICENSES.md
├── SECURITY.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── settings.gradle.kts
├── build.gradle.kts
├── gradle.properties
├── gradlew
├── gradlew.bat
├── gradle/
│   ├── libs.versions.toml
│   ├── verification-metadata.xml
│   ├── dependency-locks/
│   └── wrapper/
├── build-logic/
├── architecture/
├── translation/
├── translation-api/
├── translation-runtime/
├── translation-model-contracts/
├── translation-model-management/
├── translation-structured-text/
├── translation-diagnostics/
├── translation-detection-api/
├── translation-testing/
├── platform/
├── facades/
├── native/
├── publication/
├── testing/
├── docs/
├── scripts/
├── reports/
└── .github/
```

## Build logic

```text
build-logic/
└── src/main/kotlin/
    ├── linguum.translation.kotlin-base.gradle.kts
    ├── linguum.translation.kmp-api.gradle.kts
    ├── linguum.translation.kmp-internal.gradle.kts
    ├── linguum.translation.jvm-platform.gradle.kts
    ├── linguum.translation.android-platform.gradle.kts
    ├── linguum.translation.apple-platform.gradle.kts
    ├── linguum.translation.native-build.gradle.kts
    ├── linguum.translation.testing.gradle.kts
    ├── linguum.translation.publication.gradle.kts
    ├── linguum.translation.architecture.gradle.kts
    └── linguum.translation.quality.gradle.kts
```

Each Gradle project applies exactly one primary architecture convention. Shared quality conventions may be applied transitively by the primary convention.

## Public API modules

```text
translation-api/
└── src/
    ├── commonMain/kotlin/io/linguum/translation/
    ├── commonTest/kotlin/io/linguum/translation/
    ├── jvmMain/
    ├── androidMain/
    └── iosMain/

translation/
└── public umbrella publication

translation-testing/
└── public test-only artifact
```

Only `io.linguum.translation` and explicitly documented subpackages are stable public Kotlin packages.

## Internal KMP modules

```text
translation-runtime/
translation-model-contracts/
translation-model-management/
translation-structured-text/
translation-diagnostics/
translation-detection-api/
```

Internal implementation packages use:

```text
io.linguum.translation.internal.*
```

No internal type may appear in a public signature.

## Platform adapters

```text
platform/
├── jvm/
│   ├── src/main/kotlin/io/linguum/translation/internal/jvm/
│   ├── src/main/resources/
│   └── native-loader tests
├── android/
│   ├── src/androidMain/kotlin/io/linguum/translation/internal/android/
│   ├── src/androidMain/jniLibs/ (generated into build, never hand-edited)
│   └── Android instrumented tests
└── apple/
    ├── src/iosMain/kotlin/io/linguum/translation/internal/apple/
    ├── src/nativeInterop/cinterop/linguum_translation.def
    └── XCTest/Swift fixture integration
```

Platform adapters implement storage, HTTPS transport, clock, filesystem locks, native binding, and platform memory-pressure hooks. They contain no model-selection or translation policy.

## Java and Swift facades

```text
facades/
├── java/
│   └── src/main/java/io/linguum/translation/java/
└── apple-export/
    ├── KMP umbrella framework configuration
    └── Objective-C export annotations/adapters

swift-overlay/
├── Sources/LinguumTranslation/
├── Tests/LinguumTranslationTests/
└── generated into release XCFramework package
```

Swift source lives in the primary repo, while the release `Package.swift` may be mirrored into `linguum-translation-swift` during M9.

## Native source boundary

```text
native/
├── abi/
│   ├── include/linguum_translation.h
│   ├── src/abi_validation.c
│   └── baseline/abi-v1.txt
├── mozilla-adapter/
│   ├── include/
│   └── src/
├── runtime-build/
│   ├── CMakeLists.txt
│   ├── CMakePresets.json
│   ├── toolchains/
│   ├── cmake/
│   └── scripts/
├── upstream/
│   └── mozilla-translations/
├── patches/
│   ├── PATCHES.yaml
│   ├── windows/
│   ├── macos/
│   ├── linux/
│   ├── android/
│   └── ios/
├── UPSTREAM.json
├── UPSTREAM_LOCK.json
└── SOURCE_TREE.sha256
```

`native/upstream/mozilla-translations/**` is immutable and must match `UPSTREAM_LOCK.json`.

## Publication assets

```text
publication/
├── desktop-natives/
│   ├── windows-x64-avx2/
│   ├── windows-x64-baseline/
│   ├── macos-arm64/
│   ├── macos-x64/
│   ├── linux-x64-avx2/
│   ├── linux-x64-baseline/
│   └── linux-arm64/
├── android-aar/
├── apple-xcframework/
├── maven/
├── sbom/
└── provenance/
```

Publication directories contain build definitions and generated outputs only under `build/`; generated artifacts are never committed unless a specific baseline/evidence policy requires them.

## Testing

```text
testing/
├── architecture/
├── contracts/
├── native/
├── consumer-kotlin/
├── consumer-java/
├── consumer-swift/
├── consumer-linguum/
├── benchmarks/
├── fuzz/
├── model-fixtures/
├── failure-injection/
├── platform-smoke/
└── release-verification/
```

## Documentation

```text
docs/
├── quickstart/
├── kotlin/
├── java/
├── swift/
├── android/
├── ios/
├── desktop/
├── models/
├── offline-and-privacy/
├── troubleshooting/
├── migration/
├── native-abi/
├── security/
└── licensing/
```

## Prohibited production names

Do not create vague production modules or packages named:

```text
common
shared-utils
utils
helpers
misc
stuff
core
base-manager
generic-manager
```

Source-set names generated by Kotlin such as `commonMain` are normal and exempt; the prohibition applies to architecture/module/package responsibility names.
