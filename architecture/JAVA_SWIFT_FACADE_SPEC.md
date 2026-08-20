# Java and Swift Facade Specification

## 1. Principle

The canonical KMP API is the sole source of semantics. Java and Swift facades improve language ergonomics only. They may not add policy, model behavior, scheduling, network behavior, or failure semantics.

## 2. Java facade

Package:

```text
io.linguum.translation.java
```

### Required experience

```java
TranslationService service = TranslationServices
    .create("io.linguum.desktop")
    .toCompletableFuture()
    .join()
    .getOrThrow();

LanguagePair pair = LanguagePairs.of("es", "en");

Translator translator = service
    .translator(pair)
    .toCompletableFuture()
    .join()
    .getOrThrow();

CompletionStage<JavaTranslationOutcome<JavaTranslationResult>> stage =
    translator.translate("¿Dónde estás?");
```

### Java rules

- expose `CompletionStage`, not coroutine internals;
- avoid Kotlin `Unit`, mangled names, default-argument artifacts, and companion syntax in normal usage;
- expose immutable Java collections or unmodifiable views;
- map `StateFlow` to an explicit `Flow.Publisher`/listener facade only where stable and tested;
- support cancellation through returned `CompletableFuture`/stage adapter;
- Java outcome/failure wrappers preserve all canonical failure categories;
- Java facade methods contain no business logic.

### Required Java consumer fixture

A pure Java 17 Gradle project must compile and run without Kotlin source. It must:

- create a fake testing service;
- create a production service in local model mode;
- translate one sentence;
- observe model state;
- close the service;
- prove cancellation and typed failure mapping.

The exported Java API is snapshotted and compatibility-checked.

## 3. Swift facade strategy

Kotlin Swift export is Alpha and is not the stable v1 API mechanism.

Use:

```text
KMP Objective-C-compatible umbrella framework
        +
handwritten Swift overlay
        =
LinguumTranslation XCFramework/Swift Package
```

Swift module:

```text
LinguumTranslation
```

### Required Swift experience

```swift
let service = try await LinguumTranslationService.create(
    configuration: .default
)

let pair = try LanguagePair(source: "es", target: "en")
let translator = try await service.translator(pair: pair)
let result = try await translator.translate(text: "¿Dónde estás?")

print(result.text)
```

### Swift rules

- use `async throws`;
- map typed canonical failures to a documented `LinguumTranslationError` enum/struct hierarchy;
- expose `AsyncStream` or a documented observation token for model/service state;
- hide Kotlin coroutine completion handlers, Objective-C generated names, Kotlin collections, and internal wrapper types;
- map immutable Kotlin values to Swift value-like wrappers where appropriate;
- `close()` remains explicit and idempotent;
- cancellation of a Swift task propagates to the canonical coroutine operation;
- Swift overlay contains no model, scheduling, or network policy.

### Required Swift consumer fixture

An independent SwiftPM/Xcode fixture must:

- resolve the binary package;
- import `LinguumTranslation`;
- compile async factory/translate/error/state APIs;
- run on iOS arm64 simulator and device validation tiers;
- verify public symbol names against a checked-in Swift API snapshot.

## 4. XCFramework and SwiftPM publication

The primary repository builds:

```text
LinguumTranslation.xcframework
LinguumTranslation.xcframework.zip
```

The release computes:

```bash
swift package compute-checksum LinguumTranslation.xcframework.zip
```

A companion repository, created in M9, publishes `Package.swift` containing a binary target pointing to the exact GitHub release asset and checksum.

The package version must equal the primary library release tag.

## 5. Compatibility gates

Every PR affecting public API runs:

- Kotlin API validation;
- JVM bytecode/API validation;
- pure Java consumer compile;
- Objective-C header diff;
- Swift overlay API diff;
- pure Swift consumer compile.

A stable public symbol removal, rename, type change, async/error semantic change, or generated-name degradation is a compatibility failure.
