# Performance Validation Plan

## 1. Existing baseline

Retained evidence establishes current Firefox-pinned native Windows performance around:

```text
p50         11.13 ms
p95         30.00 ms
p99         38.26 ms
throughput  71.74 lines/sec
```

This is the initial `windows-x64-avx2` raw-engine reference, not a universal target.

## 2. Benchmark layers

### L0 Raw native

C++ harness invokes the adapter/C ABI or directly comparable native path with loaded model.

### L1 C ABI

C harness measures full stable C ABI overhead and result ownership.

### L2 Platform binding

- JVM → JNI → C ABI;
- Android → JNI → C ABI;
- iOS → cinterop → C ABI.

### L3 Kotlin service

Includes scheduler, request validation, model lookup, and result conversion.

### L4 End-to-end application boundary

Optional ECS/IPC integration benchmark after library completion; not part of the core Maven library gate but required by Linguum desktop integration.

## 3. Fixed benchmark corpus

Retain the validated 500 unique Spanish→English corpus and six deterministic shuffled rounds. Add versioned corpora for:

- short subtitles;
- medium/long prose;
- Unicode/structured spans;
- batch;
- model switching;
- other approved architecture classes.

No warmup overlap. Cache disabled for raw comparison unless a production cache behavior is separately benchmarked.

## 4. Profile baselines

```text
windows-x64-avx2
windows-x64-baseline
macos-arm64
macos-x64
linux-x64-avx2
linux-x64-baseline
linux-arm64
android-arm64
android-x86_64
ios-arm64
ios-simulator-arm64
ios-simulator-x64
```

Each baseline records:

- hardware model/CPU features;
- OS/build;
- power mode/session state;
- compiler/toolchain;
- native backend/flags;
- model hashes;
- library/ABI/Firefox revisions;
- raw runs and summary.

## 5. Absolute gates

For warm subtitle-sized translation:

```text
p95 <= 150 ms
p99 <= 250 ms
throughput >= 10 lines/sec
```

All production profiles must satisfy these unless an owner-approved platform-specific architecture amendment exists.

## 6. Relative gates

Against the approved baseline on the same controlled profile:

```text
p50 regression <= 10%
p95 regression <= 10%
p99 regression <= 15%
throughput regression <= 10%
```

A candidate may improve one metric while regressing another; all limits are independent.

## 7. Wrapper overhead gates

No-op boundary benchmark, 10,000+ operations:

```text
desktop JNI/cinterop p50 < 1 ms target
p95 <= 2 ms
p99 <= 5 ms
```

Translation wrapper overhead:

```text
integrated p95 - raw native p95 <= 3 ms target
```

If a profile cannot meet 3 ms but remains under absolute/relative gates, report exact cause; do not hide it.

## 8. Model load/switch

Measure separately:

```text
cold runtime initialization
cold model read/load
first translation after load
warm cached translator acquisition
A→B load/activation
A→B→A with both models warm
unload time
memory before/after unload
```

Model load is cold path and must not be included in warm translation latency.

## 9. Concurrency/scheduler

Measure:

- one realtime translator;
- two independent pairs concurrently;
- queue saturation;
- realtime supersession;
- interactive bounded wait;
- batch 2/4/8;
- deadlines/cancellation;
- model switching under load.

Throughput uses actual wall-clock duration, never sum of overlapping per-item durations.

## 10. Playback coexistence

For Linguum desktop integration after library end-to-end:

- play DRM video in accepted browser runtime;
- run simulated subtitle arrival workload;
- measure translation p95/p99;
- inspect dropped frames/audio/DRM stability;
- compare video baseline vs translation active;
- translation under playback p95 target <= 200 ms;
- dropped-frame impact target <= 1 percentage point.

## 11. Mobile validation

Use representative physical devices.

Measure:

- cold/warm latency;
- memory per loaded model;
- sustained 10-minute subtitle workload;
- thermal throttling;
- battery/power sample where practical;
- app background/foreground lifecycle;
- memory warning eviction;
- model install storage/network behavior.

Simulator/emulator numbers are diagnostic only, not mobile release performance authority.

## 12. Baseline governance

Performance baseline files are protected.

A baseline update requires:

- dedicated workflow;
- old/new raw results;
- reason;
- hardware/profile identity;
- trend report;
- maintainer approval;
- no absolute gate violation.

Agents cannot regenerate baselines in normal PRs.
