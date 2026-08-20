# Canonical Public API Specification

## 1. Governing principles

The public API is provider-neutral, Kotlin-first, immutable, coroutine-native, and compatible with thin Java/Swift facades.

The stable public package root is:

```text
io.linguum.translation
```

No public type or signature may mention:

```text
Mozilla
Bergamot
Marian
FBGEMM
RUY
JNI
cinterop
native pointer/handle
Android Context
Foundation types
filesystem path implementation
HTTP client implementation
```

Public API source below is normative pseudocode. Codex may make syntax-level adjustments required by Kotlin 2.4.10 only when semantics and names remain identical and API compatibility baselines are generated before 1.0.

## 2. Language types

```kotlin
package io.linguum.translation

@JvmInline
public value class LanguageTag private constructor(
    public val value: String,
) {
    public companion object {
        public fun parse(value: String): LanguageTagOutcome
        public fun require(value: String): LanguageTag
    }

    override public fun toString(): String = value
}

public sealed interface LanguageTagOutcome {
    public data class Valid(public val tag: LanguageTag) : LanguageTagOutcome
    public data class Invalid(public val reason: LanguageTagFailure) : LanguageTagOutcome
}

public sealed interface LanguageTagFailure {
    public data object Empty : LanguageTagFailure
    public data class InvalidSyntax(public val inputLength: Int) : LanguageTagFailure
    public data class TooLong(public val inputLength: Int) : LanguageTagFailure
}

public object Languages {
    public val ENGLISH: LanguageTag
    public val SPANISH: LanguageTag
    public val FRENCH: LanguageTag
    public val GERMAN: LanguageTag
    public val ITALIAN: LanguageTag
    public val PORTUGUESE: LanguageTag
}

public data class LanguagePair(
    public val source: LanguageTag,
    public val target: LanguageTag,
) {
    init {
        require(source != target)
    }
}
```

Rules:

- parse and canonicalize BCP-47 syntax deterministically in common code;
- reject underscores and malformed subtags;
- canonical casing: language lower-case, script title-case, region upper-case, remaining subtags normalized per the parser contract;
- syntactic validity does not imply model support;
- `LanguagePair` is directional;
- no implicit pivot route.

## 3. Outcome and failures

```kotlin
public sealed interface TranslationOutcome<out T> {
    public data class Success<T>(public val value: T) : TranslationOutcome<T>
    public data class Failure(public val reason: TranslationFailure) : TranslationOutcome<Nothing>
}

public sealed interface TranslationFailure {
    public data class UnsupportedLanguagePair(public val pair: LanguagePair) : TranslationFailure
    public data class ModelNotInstalled(public val pair: LanguagePair) : TranslationFailure
    public data class ModelUnavailable(public val pair: LanguagePair) : TranslationFailure
    public data class ModelDownloadFailed(
        public val pair: LanguagePair,
        public val category: ModelDownloadFailureCategory,
    ) : TranslationFailure
    public data class ModelIntegrityViolation(public val pair: LanguagePair) : TranslationFailure
    public data class ModelIncompatible(public val pair: LanguagePair) : TranslationFailure
    public data class InsufficientStorage(
        public val requiredBytes: ULong,
        public val availableBytes: ULong?,
    ) : TranslationFailure
    public data class DownloadDisallowedByPolicy(public val pair: LanguagePair) : TranslationFailure
    public data class MeteredNetworkDisallowed(public val pair: LanguagePair) : TranslationFailure
    public data object NetworkUnavailable : TranslationFailure
    public data class RequestTooLarge(
        public val actualBytes: ULong,
        public val maximumBytes: ULong,
    ) : TranslationFailure
    public data object InvalidText : TranslationFailure
    public data object DeadlineExceeded : TranslationFailure
    public data object Superseded : TranslationFailure
    public data object Overloaded : TranslationFailure
    public data object ServiceClosed : TranslationFailure
    public data class NativeRuntimeUnavailable(public val code: RuntimeFailureCode) : TranslationFailure
    public data class PlatformUnsupported(public val platform: String) : TranslationFailure
    public data class AbiIncompatible(
        public val expectedMajor: UInt,
        public val actualMajor: UInt,
    ) : TranslationFailure
}

public enum class ModelDownloadFailureCategory {
    Transport,
    Interrupted,
    RemoteUnavailable,
    InvalidResponse,
    Storage,
}

public enum class RuntimeFailureCode {
    NativeLibraryMissing,
    NativeLibraryCorrupt,
    NativeInitializationFailed,
    ModelLoadFailed,
    TranslationFailed,
    InternalFailure,
}
```

Rules:

- expected operational failures use typed outcomes;
- coroutine cancellation propagates `CancellationException` in Kotlin and is not converted into a normal success/failure value;
- Java and Swift facades map cancellation to their native async cancellation semantics;
- `TranslationFailure.Cancelled` is not needed in the canonical Kotlin API because structured coroutine cancellation propagates; explicit supersession/deadline remain typed failures;
- catastrophic invariant violations may throw a documented `TranslationRuntimeException` and must never contain user text.

## 4. Service lifecycle

```kotlin
public interface TranslationService {
    public val state: StateFlow<TranslationServiceState>
    public val catalog: TranslationCatalog
    public val models: TranslationModels
    public val runtimeInfo: TranslationRuntimeInfo
    public val languageDetection: LanguageDetection?

    public suspend fun translator(
        pair: LanguagePair,
    ): TranslationOutcome<Translator>

    public suspend fun ensureTranslator(
        pair: LanguagePair,
        acquisition: ModelAcquisitionOptions = ModelAcquisitionOptions.Default,
    ): TranslationOutcome<Translator>

    public fun close()
}

public sealed interface TranslationServiceState {
    public data object Initializing : TranslationServiceState
    public data object Ready : TranslationServiceState
    public data class Degraded(public val reason: TranslationFailure) : TranslationServiceState
    public data object Closing : TranslationServiceState
    public data object Closed : TranslationServiceState
}
```

`close()` is deterministic and idempotent. It:

1. rejects new work;
2. removes/cancels queued work;
3. safely drains currently running native calls;
4. releases translator logical handles;
5. unloads model generations;
6. stops scheduler/native workers;
7. releases native runtime handles;
8. moves state to `Closed`.

`Translator` objects do not own native resources independently and become unusable when the parent service closes.

## 5. Platform factories

The canonical service interface remains platform-neutral. Factories are platform-specific overloads/facades.

### Desktop JVM/Kotlin

```kotlin
package io.linguum.translation

public object TranslationServices {
    public suspend fun create(
        applicationId: String,
        configure: TranslationConfiguration.Builder.() -> Unit = {},
    ): TranslationOutcome<TranslationService>
}
```

### Android Kotlin

```kotlin
package io.linguum.translation.android

public object AndroidTranslationServices {
    public suspend fun create(
        context: android.content.Context,
        configure: TranslationConfiguration.Builder.() -> Unit = {},
    ): TranslationOutcome<TranslationService>
}
```

The Android-specific `Context` appears only in the Android facade package, never the common API.

### Apple Kotlin

The Kotlin/Native API accepts an Apple platform environment created by the Apple adapter; the handwritten Swift facade hides it and exposes a normal Swift factory.

## 6. Configuration DSL

```kotlin
public class TranslationConfiguration private constructor(
    public val runtime: RuntimeConfiguration,
    public val models: ModelConfiguration,
    public val observability: ObservabilityConfiguration,
) {
    public class Builder internal constructor() {
        public fun runtime(block: RuntimeConfiguration.Builder.() -> Unit)
        public fun models(block: ModelConfiguration.Builder.() -> Unit)
        public fun observability(block: ObservabilityConfiguration.Builder.() -> Unit)
    }
}

public data class RuntimeConfiguration(
    public val concurrency: RuntimeConcurrency,
    public val maximumQueuedRequests: UInt,
    public val maximumQueuedBytes: ULong,
    public val maximumInputBytes: ULong,
    public val defaultDeadline: TranslationDeadline,
    public val modelMemoryBudget: ModelMemoryBudget,
)

public sealed interface RuntimeConcurrency {
    public data object Automatic : RuntimeConcurrency
    public data object Conservative : RuntimeConcurrency
    public data class MaximumConcurrentModels(public val count: UInt) : RuntimeConcurrency
}

public sealed interface ModelMemoryBudget {
    public data object Automatic : ModelMemoryBudget
    public data class Bytes(public val value: ULong) : ModelMemoryBudget
}

public data class ModelConfiguration(
    public val acquisitionPolicy: ModelAcquisitionPolicy,
    public val diskBudget: ModelDiskBudget,
    public val defaultSource: ModelSourceSelection,
)

public sealed interface ModelDiskBudget {
    public data object Automatic : ModelDiskBudget
    public data class Bytes(public val value: ULong) : ModelDiskBudget
}

public sealed interface ModelAcquisitionPolicy {
    public data object Automatic : ModelAcquisitionPolicy
    public data object WifiOnly : ModelAcquisitionPolicy
    public data object AllowMetered : ModelAcquisitionPolicy
    public data object OfflineOnly : ModelAcquisitionPolicy
}
```

Configuration is immutable after service creation.

No public configuration property exposes Bergamot worker count, beam size, FBGEMM, model YAML, native paths, or C ABI handles.

## 7. Translator

```kotlin
public interface Translator {
    public val pair: LanguagePair
    public val capabilities: TranslationCapabilities

    public suspend fun translate(
        text: String,
    ): TranslationOutcome<TranslationResult>

    public suspend fun translate(
        request: TranslationRequest,
    ): TranslationOutcome<TranslationResult>

    public suspend fun translateBatch(
        request: TranslationBatchRequest,
    ): TranslationBatchOutcome
}
```

A translator is bound to one direct language pair. It never auto-detects the source and never silently pivots.

## 8. Requests and scheduling

```kotlin
@JvmInline
public value class TranslationRequestId(public val value: String)

@JvmInline
public value class SupersessionKey(public val value: String)

public data class TranslationRequest(
    public val id: TranslationRequestId = TranslationRequestIds.random(),
    public val content: TranslationContent,
    public val workload: TranslationWorkload = TranslationWorkload.Interactive,
    public val deadline: TranslationDeadline = TranslationDeadline.None,
    public val supersessionKey: SupersessionKey? = null,
    public val segmentation: SegmentationPolicy = SegmentationPolicy.Automatic,
)

public enum class TranslationWorkload {
    Realtime,
    Interactive,
    Batch,
}

public sealed interface TranslationDeadline {
    public data object None : TranslationDeadline
    public data class After(public val duration: Duration) : TranslationDeadline
}

public enum class SegmentationPolicy {
    Automatic,
    PreserveInput,
    Sentence,
}
```

Semantics:

- deadlines are converted to monotonic internal deadlines at submission;
- expired queued work never enters native inference;
- a result is never delivered after its deadline;
- queued requests sharing a realtime supersession key may replace stale queued work;
- already-running native inference is not forcibly interrupted;
- stale/cancelled completed native results are discarded;
- queues are bounded by request count and total payload bytes;
- batch workload backpressures rather than silently dropping items.

## 9. Content and spans

```kotlin
public sealed interface TranslationContent {
    public data class PlainText(public val text: String) : TranslationContent
    public data class StructuredText(
        public val text: String,
        public val spans: List<TextSpan>,
    ) : TranslationContent
}

public data class TextRange(
    public val startInclusive: UInt,
    public val endExclusive: UInt,
)

public data class TextSpan(
    public val range: TextRange,
    public val kind: TextSpanKind,
)

public enum class TextSpanKind {
    Emphasis,
    Italic,
    Bold,
    NonTranslatable,
}
```

Rules:

- ranges are over Unicode scalar/code-point indexing as defined and tested by the library, never raw platform UTF-16 indices;
- ranges must be ordered, in bounds, and valid;
- overlapping spans are accepted only for combinations explicitly allowed by the span validator;
- `NonTranslatable` content must survive exactly;
- arbitrary HTML is not accepted as public input;
- WebVTT/SRT/HTML adapters live outside the core runtime;
- unsupported preservation returns a typed failure or documented degradation result, never malformed spans.

## 10. Results

```kotlin
public data class TranslationResult(
    public val requestId: TranslationRequestId,
    public val pair: LanguagePair,
    public val content: TranslatedContent,
    public val segments: List<TranslatedSegment>,
)

public sealed interface TranslatedContent {
    public data class PlainText(public val text: String) : TranslatedContent
    public data class StructuredText(
        public val text: String,
        public val spans: List<TextSpan>,
    ) : TranslatedContent
}

public data class TranslatedSegment(
    public val sourceRange: TextRange,
    public val translatedRange: TextRange,
)
```

The stable result does not expose quality score, alignment matrices, model path, backend name, or native timing internals. Privacy-safe timing belongs to diagnostics/metrics.

## 11. Batch API

```kotlin
public data class TranslationBatchRequest(
    public val requests: List<TranslationRequest>,
    public val maximumChunkItems: UInt? = null,
)

public data class TranslationBatchOutcome(
    public val items: List<TranslationBatchItemOutcome>,
    public val systemicFailure: TranslationFailure? = null,
)

public sealed interface TranslationBatchItemOutcome {
    public data class Success(public val result: TranslationResult) : TranslationBatchItemOutcome
    public data class Failure(
        public val requestId: TranslationRequestId,
        public val reason: TranslationFailure,
    ) : TranslationBatchItemOutcome
}
```

Ordering must match input ordering. A systemic runtime/service failure may fail remaining items. Per-item validation failures do not erase successful items.

## 12. Catalog and capabilities

```kotlin
public interface TranslationCatalog {
    public val supportedPairs: Set<LanguagePair>
    public fun supports(pair: LanguagePair): Boolean
    public fun targetsFor(source: LanguageTag): Set<LanguageTag>
    public fun sourcesFor(target: LanguageTag): Set<LanguageTag>
    public fun info(pair: LanguagePair): TranslationPairInfo?
}

public data class TranslationPairInfo(
    public val pair: LanguagePair,
    public val modelVersion: String,
    public val installation: ModelInstallationState,
    public val runtime: ModelRuntimeState,
    public val capabilities: TranslationCapabilities,
)

public data class TranslationCapabilities(
    public val batchTranslation: Boolean,
    public val structuredText: Boolean,
    public val alignment: CapabilityState,
    public val qualityEstimation: CapabilityState,
    public val pivotTranslation: CapabilityState,
)

public enum class CapabilityState {
    Unsupported,
    Experimental,
    Supported,
}
```

The catalog is derived from the immutable approved model manifest, not the live Mozilla registry.

## 13. Model management

```kotlin
public interface TranslationModels {
    public val installedModels: StateFlow<Set<LanguagePair>>
    public val loadedModels: StateFlow<Set<LanguagePair>>

    public fun state(pair: LanguagePair): StateFlow<ModelState>
    public suspend fun downloadRequirement(pair: LanguagePair): TranslationOutcome<ModelDownloadRequirement>
    public suspend fun install(
        pair: LanguagePair,
        options: ModelAcquisitionOptions = ModelAcquisitionOptions.Default,
    ): TranslationOutcome<ModelInstallation>
    public suspend fun preload(
        pair: LanguagePair,
        options: ModelAcquisitionOptions = ModelAcquisitionOptions.Default,
    ): TranslationOutcome<Unit>
    public suspend fun unload(pair: LanguagePair): TranslationOutcome<Unit>
    public suspend fun removeFromDisk(pair: LanguagePair): TranslationOutcome<Unit>
    public suspend fun pin(pair: LanguagePair): TranslationOutcome<ModelPinLease>
    public suspend fun retainOnDisk(pair: LanguagePair): TranslationOutcome<ModelRetentionLease>
    public suspend fun storageSnapshot(): TranslationOutcome<ModelStorageSnapshot>
}

public interface ModelPinLease {
    public val pair: LanguagePair
    public fun close()
}

public interface ModelRetentionLease {
    public val pair: LanguagePair
    public fun close()
}
```

Leases are idempotent and reference-counted internally. A model with active work or active leases cannot be evicted.

`translator()` is local-only and fails with `ModelNotInstalled` when necessary. `ensureTranslator()` and explicit model install/preload operations may acquire model bytes according to policy.

## 14. Model states

```kotlin
public sealed interface ModelState {
    public data object Unsupported : ModelState
    public data object NotInstalled : ModelState
    public data class Downloading(
        public val downloadedBytes: ULong,
        public val totalBytes: ULong,
    ) : ModelState
    public data object Verifying : ModelState
    public data object Installing : ModelState
    public data object Installed : ModelState
    public data object Loading : ModelState
    public data object Loaded : ModelState
    public data class Failed(public val reason: TranslationFailure) : ModelState
}

public enum class ModelInstallationState {
    NotInstalled,
    Installed,
}

public enum class ModelRuntimeState {
    Unloaded,
    Loaded,
}
```

## 15. Model acquisition options

```kotlin
public data class ModelAcquisitionOptions(
    public val networkPolicy: ModelNetworkPolicy,
    public val allowResume: Boolean,
) {
    public companion object {
        public val Default: ModelAcquisitionOptions
    }
}

public enum class ModelNetworkPolicy {
    UseServiceDefault,
    WifiOnly,
    AllowMetered,
    OfflineOnly,
}

public data class ModelDownloadRequirement(
    public val totalBytes: ULong,
    public val downloadedBytes: ULong,
    public val remainingBytes: ULong,
)
```

## 16. Runtime information and observability

```kotlin
public data class TranslationRuntimeInfo(
    public val libraryVersion: String,
    public val nativeAbiMajor: UInt,
    public val nativeAbiMinor: UInt,
    public val firefoxRevision: String,
    public val bergamotVersion: String,
    public val modelManifestRevision: String,
    public val platform: String,
    public val architecture: String,
    public val accelerationProfile: String,
)

public fun interface TranslationObserver {
    public fun onEvent(event: TranslationDiagnosticEvent)
}

public sealed interface TranslationDiagnosticEvent {
    public data class RuntimeInitialized(public val info: TranslationRuntimeInfo) : TranslationDiagnosticEvent
    public data class ModelStateChanged(public val pair: LanguagePair, public val state: ModelState) : TranslationDiagnosticEvent
    public data class TranslationCompleted(
        public val pair: LanguagePair,
        public val inputCharacters: UInt,
        public val duration: Duration,
    ) : TranslationDiagnosticEvent
    public data class QueueDepthChanged(public val requests: UInt, public val bytes: ULong) : TranslationDiagnosticEvent
    public data class FailureObserved(public val category: String) : TranslationDiagnosticEvent
}
```

No diagnostic type may contain source text, translated text, auth data, full sensitive URLs, native pointers, or arbitrary file contents.

## 17. Optional language detection

```kotlin
@ExperimentalTranslationApi
public interface LanguageDetection {
    public suspend fun detect(text: String): LanguageDetectionOutcome
}

public sealed interface LanguageDetectionOutcome {
    public data class Detected(
        public val language: LanguageTag,
        public val confidence: Double,
    ) : LanguageDetectionOutcome
    public data class Failure(public val reason: LanguageDetectionFailure) : LanguageDetectionOutcome
}
```

The 1.0 core publishes the capability contract and fakes. It does not bundle a detector unless a separate approved work package selects and validates one.

## 18. Experimental marker

```kotlin
@RequiresOptIn(
    message = "This API is experimental and may change before stabilization.",
    level = RequiresOptIn.Level.ERROR,
)
@Retention(AnnotationRetention.BINARY)
@Target(
    AnnotationTarget.CLASS,
    AnnotationTarget.FUNCTION,
    AnnotationTarget.PROPERTY,
    AnnotationTarget.TYPEALIAS,
)
public annotation class ExperimentalTranslationApi
```

Stable APIs may never be relabeled experimental to bypass compatibility rules.

## 19. API invariants

- public values are immutable;
- no public mutable collection;
- no global singleton service;
- no hidden network call from `translator`, `translate`, or `translateBatch`;
- no direct model pair silently pivots;
- no stale/cancelled/deadline-expired result is delivered;
- no native resource survives a closed service;
- no active/pinned model is evicted;
- same release/config/profile/request is deterministic;
- public behavior is identical across Kotlin, Java, and Swift facades.
