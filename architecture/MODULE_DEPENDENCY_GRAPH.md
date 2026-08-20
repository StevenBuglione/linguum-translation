# Module Dependency Graph and Enforcement Rules

## Canonical graph

```text
translation-api
     ▲
     │
translation-model-contracts ◄──── translation-diagnostics
     ▲                                  ▲
     │                                  │
translation-model-management      translation-runtime
     ▲                                  ▲
     └──────────────┬───────────────────┘
                    │
        translation-structured-text
                    ▲
                    │
        platform adapters / facades
                    ▲
                    │
              translation umbrella

native/abi ◄── native/mozilla-adapter ◄── immutable Mozilla source
    ▲
    ├── JVM JNI binding
    ├── Android JNI binding
    └── Apple cinterop binding
```

## Allowed dependencies

### `translation-api`

May depend only on:

- Kotlin standard library;
- `kotlinx-coroutines-core` for `Flow`, `StateFlow`, and suspend semantics;
- explicitly approved annotations needed for API stability.

It may not depend on:

- any platform module;
- JNI/cinterop;
- HTTP/network libraries;
- filesystem libraries;
- Mozilla/Bergamot/Marian;
- serialization libraries in public type signatures;
- a logging backend.

### `translation-model-contracts`

May depend on `translation-api` and standard/coroutines APIs. It contains immutable internal manifest/catalog/storage contracts.

### `translation-runtime`

May depend on:

- `translation-api`;
- model contracts;
- diagnostics contracts;
- structured-text orchestration;
- internal runtime ports.

It may not import JNI, Android, Foundation, filesystem, HTTP, or Mozilla APIs.

### `translation-model-management`

May depend on:

- API/model contracts;
- runtime ports;
- platform-neutral state machines.

All actual filesystem/network behavior is injected through internal ports implemented by platform adapters.

### `platform:jvm`

May depend on runtime/model modules, JDK APIs, JNI loader code, and an approved HTTP implementation isolated here.

It may not own model-selection policy, scheduling semantics, or public failure definitions.

### `platform:android`

May depend on runtime/model modules, Android Context/storage/network APIs, and JNI. It may not expose `Context` through common public contracts.

### `platform:apple`

May depend on runtime/model modules, Foundation/Security/network APIs, and the generated C interop bindings. It may not expose C pointers through stable Kotlin/Swift APIs.

### Native adapter

May depend on the C ABI, immutable Mozilla source, and approved patch queue. It contains no Kotlin/public API knowledge.

### Testing modules

May depend on production modules. Production modules may never depend on testing modules.

## Custom architecture checks

`architectureCheck` must fail for:

- forbidden Gradle project edges;
- imports from `io.linguum.translation.internal` in public API modules;
- public declarations containing internal/native/platform types;
- networking imports outside platform acquisition adapters;
- native calls outside platform binding modules;
- Mozilla includes outside `native/mozilla-adapter` and vendored source;
- edits inside the upstream tree not produced by the update workflow;
- public mutable collections;
- global mutable state;
- runtime OS checks in `commonMain`;
- unclassified modules;
- cycles;
- production dependencies on tests/fixtures;
- generic/vague module names;
- unsupported target declarations.

## Package rule

Stable public packages are allowlisted in `architecture/public-packages.txt`.

All other Kotlin implementation code must be `internal` and use:

```text
io.linguum.translation.internal...
```

The Java facade is allowlisted under:

```text
io.linguum.translation.java
```

The Swift overlay module name is:

```text
LinguumTranslation
```
