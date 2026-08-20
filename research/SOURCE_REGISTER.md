# Primary Source Register

Validated on 2026-08-20. External facts must be rechecked through the dedicated update workflow before a future toolchain or upstream upgrade.

## Frozen architecture and benchmark evidence

- `architecture/LOCKED_DECISIONS.md` — owner-approved 76-decision source of truth.
- `research/evidence/translation-benchmark-validation.zip` — complete corrected benchmark harness/results.
- `research/evidence/FINAL_BENCHMARK_REPORT.md` — summarized validated result.

## Linguum architectural conventions

- `https://github.com/StevenBuglione/Linguum/blob/codex/m4-daily-review-1-0/AGENTS.md`
- `https://github.com/StevenBuglione/Linguum/blob/codex/m4-daily-review-1-0/CODEX_EXECUTION_CONTRACT.md`
- `https://github.com/StevenBuglione/Linguum/blob/codex/m4-daily-review-1-0/architecture/REPOSITORY_LAYOUT.md`
- `https://github.com/StevenBuglione/Linguum/blob/codex/m4-daily-review-1-0/architecture/ARCHITECTURE_CONSTITUTION.yaml`
- `https://github.com/StevenBuglione/Linguum/blob/codex/m4-daily-review-1-0/implementation/TEST_CI_AND_QUALITY_GATES.md`

## Firefox and Mozilla translation source

- Firefox repository: `https://github.com/mozilla-firefox/firefox`
- Firefox pin metadata: `toolkit/components/translations/bergamot-translator/moz.yaml`
- Mozilla translations repository: `https://github.com/mozilla/translations`
- pinned revision: `eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d`
- native inference root: `inference/`
- service API: `inference/src/translator/service.h`
- native CLI example: `inference/src/app/translator_cli.cpp`
- native build script: `inference/scripts/build.py`
- model registry JSON: `https://storage.googleapis.com/moz-fx-translations-data--303e-prod-translations-data/db/models.json`
- Firefox translations docs: `https://firefox-source-docs.mozilla.org/toolkit/components/translations/`

## Kotlin and Gradle

- Kotlin releases: `https://kotlinlang.org/docs/releases.html`
- KGP/Gradle/AGP compatibility: `https://kotlinlang.org/docs/gradle-configure-project.html`
- Kotlin/Native target support: `https://kotlinlang.org/docs/native-target-support.html`
- C interop: `https://kotlinlang.org/docs/native-c-interop.html`
- Apple framework export: `https://kotlinlang.org/docs/apple-framework.html`
- Swift export status: `https://kotlinlang.org/docs/native-swift-export.html`
- SwiftPM/XCFramework export: `https://kotlinlang.org/docs/multiplatform/multiplatform-spm-export.html`
- Maven Central publishing: `https://kotlinlang.org/docs/multiplatform/multiplatform-publish-libraries-to-maven.html`
- KMP publication structure: `https://kotlinlang.org/docs/multiplatform-publish-lib-setup.html`
- ABI validation: Kotlin 2.4 documentation and built-in `abiValidation` DSL.
- Gradle Module Metadata: `https://docs.gradle.org/current/userguide/publishing_gradle_module_metadata.html`
- Gradle variants/attributes: `https://docs.gradle.org/current/userguide/variant_attributes.html`

## Android

- AGP 9.1 release notes: `https://developer.android.com/build/releases/agp-9-1-0-release-notes`
- NDK configuration: `https://developer.android.com/studio/projects/configure-agp-ndk`
- Android ABIs: `https://developer.android.com/ndk/guides/abis.html`
- AGP 9 KMP migration: `https://kotlinlang.org/docs/multiplatform/multiplatform-project-agp-9-migration.html`

## Publishing and GitHub

- GitHub repository creation: `https://cli.github.com/manual/gh_repo_create`
- GitHub branch protection: `https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches`
- GitHub artifact attestations: `https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations`
- Maven Central tutorial and namespace requirements: Kotlin Maven Central publishing documentation.

## Licensing

- MPL 2.0: `https://www.mozilla.org/en-US/MPL/2.0/`
- MPL 2.0 FAQ: `https://www.mozilla.org/en-US/MPL/2.0/FAQ/`
- Apache License 2.0: `https://www.apache.org/licenses/LICENSE-2.0`
