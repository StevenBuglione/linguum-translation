#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Offline contract tests for the M1 Apple export feasibility proof."""

import importlib.util
import json
import plistlib
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def load_script(name: str):
    path = ROOT / "scripts" / "native" / "{}.py".format(name)
    spec = importlib.util.spec_from_file_location(
        "linguum_apple_export_test_{}".format(name), path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


apple_export = load_script("apple_export")


class AppleExportContractTests(unittest.TestCase):
    def test_lock_has_exact_modules_targets_and_execution_tiers(self):
        document = apple_export.load_lock()
        self.assertEqual(1, document["schemaVersion"])
        self.assertEqual("15.0", document["deploymentTarget"])
        self.assertEqual("2.4.10", document["kotlinVersion"])
        self.assertEqual("6.0", document["swiftToolsVersion"])
        self.assertEqual("5", document["swiftLanguageMode"])
        self.assertEqual("LinguumTranslationCore", document["coreFramework"])
        self.assertEqual("LinguumTranslation", document["swiftModule"])
        self.assertEqual(
            "LinguumTranslation.xcframework", document["distributionXcframework"]
        )
        self.assertEqual(list(apple_export.PROFILE_IDS), document["profiles"])
        self.assertEqual(
            ["self-hosted", "macos", "arm64", "ios-device"],
            document["physicalArm64RunnerLabels"],
        )

    def test_output_directory_is_confined_to_build(self):
        build = ROOT / "build"
        build.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=build) as temporary:
            self.assertEqual(
                Path(temporary).resolve(),
                apple_export.safe_output_directory(Path(temporary)),
            )
        for forbidden in (ROOT, ROOT / "build"):
            with self.assertRaises(apple_export.AppleExportError):
                apple_export.safe_output_directory(forbidden)

    def test_profile_selection_is_exact_and_requires_execution_slice(self):
        self.assertEqual(
            apple_export.PROFILE_IDS, apple_export.selected_profiles("all")
        )
        self.assertEqual(
            ("ios-simulator-x64",),
            apple_export.selected_profiles("ios-simulator-x64"),
        )
        with self.assertRaises(apple_export.AppleExportError):
            apple_export.validate_execution_selection(
                ("ios-arm64",), "simulator-arm64"
            )
        apple_export.validate_execution_selection(
            ("ios-simulator-arm64",), "simulator-arm64"
        )

    def test_gradle_framework_command_is_locked_clean_and_profile_correlated(self):
        archive = Path("/tmp/liblinguum_translation.a")
        build_directory = Path("/tmp/framework-build")
        command = apple_export.framework_gradle_command(
            {"id": "ios-simulator-arm64", "kotlinTarget": "iosSimulatorArm64"},
            archive,
            build_directory,
        )
        joined = " ".join(str(value) for value in command)
        self.assertIn("linkReleaseFrameworkIosSimulatorArm64", command)
        self.assertIn("--no-build-cache", command)
        self.assertIn("--rerun-tasks", command)
        self.assertIn("--no-configuration-cache", command)
        self.assertIn("-PlinguumAppleProfile=ios-simulator-arm64", joined)
        self.assertIn("-PlinguumAppleArchive={}".format(archive), command)
        self.assertIn(
            "-PlinguumAppleBuildDirectory={}".format(build_directory), command
        )

    def test_framework_identity_requires_exact_arch_platform_minimum_and_header(self):
        profile = {
            "id": "ios-simulator-arm64",
            "architecture": "arm64",
            "platform": "IOSSIMULATOR",
        }
        header = """
@interface LinguumTranslationCoreOutcome : LTCKotlinBase
@end
@interface LinguumTranslationCoreService : LTCKotlinBase
- (BOOL)supportsLanguagePairSource:(NSString *)source target:(NSString *)target;
- (LinguumTranslationCoreOutcome *)translateText:(NSString *)text;
- (void)close;
@end
"""
        evidence = apple_export.verify_framework_identity(
            profile,
            "arm64\n",
            "platform IOSSIMULATOR\nminos 15.0\n",
            header,
        )
        self.assertEqual(["arm64"], evidence["architectures"])
        self.assertTrue(evidence["swiftBoundaryHasNoPointers"])
        with self.assertRaises(apple_export.AppleExportError):
            apple_export.verify_framework_identity(
                profile,
                "x86_64\n",
                "platform IOSSIMULATOR\nminos 15.0\n",
                header,
            )
        with self.assertRaises(apple_export.AppleExportError):
            apple_export.verify_framework_identity(
                profile,
                "arm64\n",
                "platform IOSSIMULATOR\nminos 16.0\n",
                header + "void *rawPointer;\n",
            )

    def test_static_framework_members_require_exact_numeric_platform_and_minimum(self):
        profile = {"platform": "IOSSIMULATOR"}
        output = """
      cmd LC_BUILD_VERSION
 platform 7
    minos 15.0
      cmd LC_BUILD_VERSION
 platform 7
    minos 15.0
"""
        self.assertEqual(
            "platform IOSSIMULATOR\nminos 15.0\n",
            apple_export.verify_static_framework_build_versions(profile, output),
        )
        with self.assertRaises(apple_export.AppleExportError):
            apple_export.verify_static_framework_build_versions(
                profile, output.replace("platform 7", "platform 2")
            )
        with self.assertRaises(apple_export.AppleExportError):
            apple_export.verify_static_framework_build_versions(
                profile, output.replace("minos 15.0", "minos 16.0")
            )

    def test_simulator_framework_merge_requires_matching_public_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.framework"
            second = root / "second.framework"
            for framework in (first, second):
                (framework / "Headers").mkdir(parents=True)
                (framework / "Modules").mkdir()
                (framework / "Headers" / "LinguumTranslationCore.h").write_text(
                    "public header\n", encoding="utf-8"
                )
                (framework / "Modules" / "module.modulemap").write_text(
                    "framework module LinguumTranslationCore {}\n", encoding="utf-8"
                )
            apple_export.verify_merge_compatible(first, second)
            (second / "Headers" / "LinguumTranslationCore.h").write_text(
                "different\n", encoding="utf-8"
            )
            with self.assertRaises(apple_export.AppleExportError):
                apple_export.verify_merge_compatible(first, second)

    def test_xcframework_plist_requires_device_and_universal_simulator_slices(self):
        document = {
            "AvailableLibraries": [
                {
                    "LibraryIdentifier": "ios-arm64",
                    "LibraryPath": "LinguumTranslationCore.framework",
                    "SupportedArchitectures": ["arm64"],
                    "SupportedPlatform": "ios",
                },
                {
                    "LibraryIdentifier": "ios-arm64_x86_64-simulator",
                    "LibraryPath": "LinguumTranslationCore.framework",
                    "SupportedArchitectures": ["arm64", "x86_64"],
                    "SupportedPlatform": "ios",
                    "SupportedPlatformVariant": "simulator",
                },
            ],
            "CFBundlePackageType": "XFWK",
            "XCFrameworkFormatVersion": "1.0",
        }
        evidence = apple_export.verify_xcframework_plist(
            document, apple_export.PROFILE_IDS
        )
        self.assertEqual(2, evidence["libraryCount"])
        self.assertEqual(
            ["arm64", "x86_64"], evidence["simulatorArchitectures"]
        )
        document["AvailableLibraries"][1]["SupportedArchitectures"] = ["arm64"]
        with self.assertRaises(apple_export.AppleExportError):
            apple_export.verify_xcframework_plist(document, apple_export.PROFILE_IDS)

    def test_single_profile_xcframework_plist_is_supported_for_tier_execution(self):
        document = {
            "AvailableLibraries": [
                {
                    "LibraryIdentifier": "ios-x86_64-simulator",
                    "LibraryPath": "LinguumTranslationCore.framework",
                    "SupportedArchitectures": ["x86_64"],
                    "SupportedPlatform": "ios",
                    "SupportedPlatformVariant": "simulator",
                }
            ],
            "CFBundlePackageType": "XFWK",
            "XCFrameworkFormatVersion": "1.0",
        }
        evidence = apple_export.verify_xcframework_plist(
            document, ("ios-simulator-x64",)
        )
        self.assertEqual(["x86_64"], evidence["simulatorArchitectures"])

    def test_deterministic_xcframework_zip_has_sorted_epoch_entries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            framework = root / "LinguumTranslation.xcframework"
            (framework / "slice" / "Headers").mkdir(parents=True)
            (framework / "Info.plist").write_bytes(
                plistlib.dumps({"XCFrameworkFormatVersion": "1.0"})
            )
            (framework / "slice" / "Headers" / "Header.h").write_text(
                "header\n", encoding="utf-8"
            )
            first = root / "first.zip"
            second = root / "second.zip"
            apple_export.write_deterministic_tree_zip(framework, first)
            apple_export.write_deterministic_tree_zip(framework, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(sorted(archive.namelist()), archive.namelist())
                self.assertTrue(
                    all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist())
                )

    def test_swift_api_snapshot_is_exact_and_forbids_core_leaks(self):
        declarations = apple_export.read_swift_api_snapshot()
        self.assertIn("LinguumTranslationService.create(configuration:)", declarations)
        self.assertIn("Translator.translate(text:)", declarations)
        self.assertIn("LinguumTranslationError", declarations)
        self.assertFalse(any("Core" in value or "Kotlin" in value for value in declarations))

    def test_swift_canary_output_is_exact_profile_correlated_and_async(self):
        output = (
            "LINGUUM_SWIFT_CANARY_START profile=iosSimulatorArm64 iterations=100 async=true\n"
            "LINGUUM_SWIFT_CANARY_PASS profile=iosSimulatorArm64 iterations=100 "
            "async=true abi=1.0\n"
        )
        evidence = apple_export.verify_swift_canary_output(
            output, "iosSimulatorArm64", 100
        )
        self.assertTrue(evidence["async"])
        with self.assertRaises(apple_export.AppleExportError):
            apple_export.verify_swift_canary_output(
                output.replace("iosSimulatorArm64", "iosX64"),
                "iosSimulatorArm64",
                100,
            )
        with self.assertRaises(apple_export.AppleExportError):
            apple_export.verify_swift_canary_output(
                output + "LINGUUM_SWIFT_CANARY_FAIL reason=unexpected\n",
                "iosSimulatorArm64",
                100,
            )

    def test_swift_consumer_compile_proofs_cover_unexecuted_device_and_x64_slices(self):
        commands = apple_export.swift_compile_commands(
            "LinguumTranslationFeasibility",
            Path("/tmp/derived"),
            {
                "deviceArchitectures": ["arm64"],
                "simulatorArchitectures": ["arm64", "x86_64"],
            },
            "simulator-arm64",
        )
        self.assertEqual(["ios-arm64", "ios-simulator-x64"], sorted(commands))
        device = " ".join(str(value) for value in commands["ios-arm64"])
        intel = " ".join(str(value) for value in commands["ios-simulator-x64"])
        self.assertIn("generic/platform=iOS build-for-testing", device)
        self.assertIn("ARCHS=x86_64", intel)
        self.assertIn("ONLY_ACTIVE_ARCH=NO", intel)
        self.assertTrue(
            all(
                "CODE_SIGNING_ALLOWED=NO" in command
                for command in (device, intel)
            )
        )
        self.assertEqual(
            {},
            apple_export.swift_compile_commands(
                "LinguumTranslationFeasibility",
                Path("/tmp/derived"),
                {
                    "deviceArchitectures": [],
                    "simulatorArchitectures": ["x86_64"],
                },
                "simulator-x64",
            ),
        )

    def test_physical_profile_requires_exact_or_wildcard_bundle_entitlement(self):
        exact = {
            "TeamIdentifier": ["TEAM123"],
            "UUID": "PROFILE-UUID",
            "Entitlements": {
                "application-identifier": "TEAM123.io.linguum.canary"
            },
        }
        self.assertEqual(
            ("TEAM123", "PROFILE-UUID"),
            apple_export.verify_physical_profile(exact, "io.linguum.canary"),
        )
        wildcard = {
            **exact,
            "Entitlements": {"application-identifier": "TEAM123.io.linguum.*"},
        }
        self.assertEqual(
            ("TEAM123", "PROFILE-UUID"),
            apple_export.verify_physical_profile(
                wildcard, "io.linguum.translation.canary"
            ),
        )
        with self.assertRaises(apple_export.AppleExportError):
            apple_export.verify_physical_profile(
                wildcard, "com.example.outside"
            )
        with self.assertRaises(apple_export.AppleExportError):
            apple_export.verify_physical_profile(exact, "invalid bundle")
    def test_fixture_is_real_swiftpm_overlay_and_kotlin_framework_build(self):
        fixture = ROOT / "testing" / "platform-smoke" / "apple-export-canary"
        gradle = (fixture / "kotlin-core" / "build.gradle.kts").read_text(
            encoding="utf-8"
        )
        package = (fixture / "swift-package" / "Package.swift").read_text(
            encoding="utf-8"
        )
        overlay = (
            fixture
            / "swift-package"
            / "Sources"
            / "LinguumTranslation"
            / "LinguumTranslation.swift"
        ).read_text(encoding="utf-8")
        canary = (
            fixture
            / "swift-package"
            / "Tests"
            / "LinguumTranslationCanaryTests"
            / "LinguumTranslationCanaryTests.swift"
        ).read_text(encoding="utf-8")
        for target in ("iosArm64", "iosSimulatorArm64", "iosX64"):
            self.assertIn(target, gradle)
        self.assertIn('baseName = "LinguumTranslationCore"', gradle)
        self.assertIn("isStatic = true", gradle)
        self.assertIn('.binaryTarget(', package)
        self.assertIn('name: "LinguumTranslation"', package)
        self.assertIn('.linkedLibrary("iconv")', package)
        self.assertIn("import LinguumTranslationCore", overlay)
        self.assertIn("async throws", overlay)
        self.assertIn("withCheckedThrowingContinuation", overlay)
        self.assertIn("import LinguumTranslation", canary)
        self.assertIn("await", canary)

    def test_scope_is_isolated_from_m3_and_m9_production_boundaries(self):
        settings = (ROOT / "settings.gradle.kts").read_text(encoding="utf-8")
        plugin = (
            ROOT
            / "build-logic"
            / "src"
            / "main"
            / "kotlin"
            / "io"
            / "linguum"
            / "translation"
            / "buildlogic"
            / "ArchitecturePlugin.kt"
        ).read_text(encoding="utf-8")
        self.assertNotIn(":platform:apple", settings)
        self.assertNotIn(":facades:apple-export", settings)
        self.assertIn("testing/platform-smoke/apple-export-canary/**", plugin)
        self.assertFalse((ROOT / "platform" / "apple").exists())
        self.assertFalse((ROOT / "facades" / "apple-export").exists())
        self.assertFalse((ROOT / "swift-overlay").exists())
        self.assertFalse(any(ROOT.glob("*.xcframework")))

    def test_ci_runs_pr_arm64_intel_and_physical_swift_export_tiers(self):
        scope = (ROOT / "scripts" / "ci" / "verify-scope.sh").read_text(
            encoding="utf-8"
        )
        pr = (ROOT / ".github" / "workflows" / "pr.yml").read_text(encoding="utf-8")
        native = (ROOT / ".github" / "workflows" / "native-safety.yml").read_text(
            encoding="utf-8"
        )
        nightly = (ROOT / ".github" / "workflows" / "nightly.yml").read_text(
            encoding="utf-8"
        )
        release = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("test_apple_export", scope)
        self.assertIn("apple_export.py", scope)
        self.assertIn("--profile all", scope)
        self.assertIn("--execution-tier simulator-arm64", scope)
        self.assertIn("timeout-minutes: 180", pr)
        self.assertIn("testing/platform-smoke/apple-export-canary/**", native)
        self.assertIn("--profile ios-simulator-x64", native)
        self.assertIn("--execution-tier simulator-x64", native)
        for workflow in (nightly, release):
            self.assertIn("apple_export.py", workflow)
            self.assertIn("--profile ios-arm64", workflow)
            self.assertIn("--execution-tier physical-arm64", workflow)

    def test_cli_and_evidence_names_are_m1_wp08_specific(self):
        driver = (ROOT / "scripts" / "native" / "apple_export.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("M1-WP08-apple-export-evidence.json", driver)
        self.assertIn("LinguumTranslation.xcframework.zip", driver)
        self.assertIn("swift package compute-checksum", driver)
        self.assertIn("--execution-tier", driver)
        self.assertNotIn('"-packagePath"', driver)
        self.assertIn('capture(["xcodebuild", "-list", "-json"], cwd=stage)', driver)
        self.assertIn("capture(command, cwd=stage, timeout_seconds=1800)", driver)
        self.assertIn('TemporaryDirectory(prefix="linguum-apple-export-derived-")', driver)
        self.assertIn('"-parallel-testing-enabled",', driver)
        self.assertIn('"build-for-testing",', driver)
        self.assertIn('"CODE_SIGNING_ALLOWED=NO",', driver)
        self.assertIn('command.extend(["-destination", destination, "test"])', driver)


if __name__ == "__main__":
    unittest.main()
