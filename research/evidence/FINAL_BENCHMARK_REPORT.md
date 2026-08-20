TRANSLATION PERFORMANCE VALIDATION

Rounds completed: 6 / 6
Samples per engine per round: 500
Total measured samples per engine: 3000
Warmup per engine per run: 20
Warmup overlap with corpus: 0
Corpus order: deterministic and paired per round
Chrome model pre-downloaded: YES
Caches:
  WASM Bergamot: 0
  Native Bergamot: 0

NATIVE ENGINE SOURCE

Repository:
mozilla/translations

Firefox-pinned revision:
eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d

Bergamot:
v0.6.0

Service:
AsyncService

Workers:
1

Cache:
0

CPU backend:
FBGEMM

Build:
Release x64

Architecture:
AVX2

Machine
──────────────────────────
CPU: AMD Ryzen 9 5900X 12-Core Processor
RAM: 127.93 GB
Windows: Windows 11 Pro (10.0.26100)
GPU: NVIDIA GeForce RTX 3070
Chrome version: Google Chrome 151

                         Chrome       WASM       Native

Median run p50              15.80      21.65      11.13
Median run p95              44.31      64.73      30.00
Median run p99              48.05      69.05      38.26

Mean run p50                15.78      21.57      11.01
Mean run p95                44.40      64.82      30.05
Mean run p99                48.00      69.24      38.39

p95 stddev                   0.77       0.58       1.48

Pooled p50                  15.80      21.60      11.00
Pooled p95                  44.60      65.30      30.26
Pooled p99                  48.20      69.20      40.20

Median TPS                  49.35      34.83      71.74
Median words/sec           566.59     399.82     823.56

CURRENT FIREFOX NATIVE

Round 1
p50: 10.62
p95: 28.78
p99: 33.74
TPS: 75.00

Round 2
p50: 11.64
p95: 31.57
p99: 41.18
TPS: 67.55

Round 3
p50: 10.14
p95: 28.25
p99: 36.78
TPS: 77.33

Round 4
p50: 11.35
p95: 30.74
p99: 39.74
TPS: 70.04

Round 5
p50: 11.42
p95: 31.69
p99: 43.75
TPS: 68.32

Round 6
p50: 10.91
p95: 29.25
p99: 35.19
TPS: 73.44

CURRENT FIREFOX NATIVE AGGREGATE

Median p50: 11.13
Median p95: 30.00
Median p99: 38.26
Median TPS: 71.74

Mean p50: 11.01
Mean p95: 30.05
Mean p99: 38.39

p95 stddev: 1.48

| Metric              | Chrome | Firefox WASM | Old Native | Current Firefox Native |
| ------------------- | -----: | -----------: | ---------: | ---------------------: |
| Median p50          | 15.80 | 21.65 | 10.13 | 11.13 |
| Median p95          | 44.31 | 64.73 | 28.07 | 30.00 |
| Median p99          | 48.05 | 69.05 | 30.35 | 38.26 |
| TPS                 | 49.35 | 34.83 | 79.91 | 71.74 |
| Short subtitle p95  | 17.51 | 23.75 | 11.12 | 14.52 |
| Medium subtitle p95 | 34.69 | 45.75 | 19.75 | 28.75 |
| Long subtitle p95   | 48.83 | 70.17 | 30.81 | 41.06 |

CURRENT FIREFOX NATIVE VS CHROME

p50 wins: 6 / 6
p95 wins: 6 / 6
p99 wins: 6 / 6

median p50 ratio:
native / chrome = 0.707

median p95 ratio:
native / chrome = 0.682

median p99 ratio:
native / chrome = 0.806

CURRENT FIREFOX NATIVE VS OLD NATIVE

p50 delta: 1.00 ms (ratio 1.099)
p95 delta: 1.93 ms (ratio 1.069)
p99 delta: 7.90 ms (ratio 1.260)
throughput delta: -8.18 TPS (ratio 0.898)

STARTUP — INFORMATIONAL

Median engineSetupMs Chrome/WASM/Native: 81.95 / 364.80 / 60.35
Median firstTranslationMs Chrome/WASM/Native: 32.70 / 170.60 / 48.85

CURRENT FIREFOX NATIVE BERGAMOT

Source verification:
PASS

Firefox-pinned revision:
PASS

Six rounds completed:
PASS

Same frozen corpora:
PASS

Chrome/WASM baselines unchanged:
PASS

Absolute subtitle p95:
PASS

Absolute subtitle p99:
PASS

Throughput:
PASS

Native vs Chrome:
FASTER THAN CHROME

Output agreement with Firefox WASM:
480 / 500
96%

FINAL DECISION:

CURRENT MOZILLA NATIVE TRANSLATION
IS VALIDATED.

KOTLIN INTEGRATION: DO NOT START automatically. Return these results for architectural review first.
