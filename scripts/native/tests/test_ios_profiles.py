#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Offline contract tests for the M1 iOS native profile proof."""

import importlib.util
import json
import plistlib
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def load_script(name: str):
    path = ROOT / "scripts" / "native" / "{}.py".format(name)
    spec = importlib.util.spec_from_file_location(
        "linguum_ios_test_{}".format(name), path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ios_profiles = load_script("ios_profiles")


class IosProfileContractTests(unittest.TestCase):
    def test_lock_has_exact_targets_backends_and_execution_tiers(self):
        document = ios_profiles.load_lock()
        profiles = ios_profiles.profile_map(document)
        self.assertEqual(set(ios_profiles.PROFILE_IDS), set(profiles))
        self.assertEqual("15.0", document["deploymentTarget"])
        self.assertEqual("2.4.10", document["kotlinVersion"])
        self.assertEqual("runner-default", document["xcodeSelection"])
        self.assertEqual(
            {
                "archive": "pcre2-10.39.tar.gz",
                "sha256": "0781bd2536ef5279b1943471fdcdbd9961a2845e1d2c9ad849b9bd98ba1a9bd4",
                "url": "https://github.com/PCRE2Project/pcre2/releases/download/pcre2-10.39/pcre2-10.39.tar.gz",
                "version": "10.39",
            },
            document["dependencies"]["pcre2"],
        )
        self.assertEqual(
            ["self-hosted", "macos", "arm64", "ios-device"],
            document["physicalArm64RunnerLabels"],
        )

        device = profiles["ios-arm64"]
        self.assertEqual("iosArm64", device["kotlinTarget"])
        self.assertEqual("iphoneos", device["sdk"])
        self.assertEqual("arm64", device["architecture"])
        self.assertEqual("apple-accelerate-ruy-arm64", device["accelerationProfile"])
        self.assertEqual("Ruy", device["quantizedBackend"])
        self.assertTrue(device["physicalDeviceExecutionRequired"])

        simulator_arm64 = profiles["ios-simulator-arm64"]
        self.assertEqual("iosSimulatorArm64", simulator_arm64["kotlinTarget"])
        self.assertEqual("iphonesimulator", simulator_arm64["sdk"])
        self.assertEqual("macos-15", simulator_arm64["runner"])
        self.assertTrue(simulator_arm64["runInPullRequest"])

        simulator_x64 = profiles["ios-simulator-x64"]
        self.assertEqual("iosX64", simulator_x64["kotlinTarget"])
        self.assertEqual("x86_64", simulator_x64["architecture"])
        self.assertEqual("macos-15-intel", simulator_x64["runner"])
        self.assertEqual(
            "apple-accelerate-intgemm-runtime-x64",
            simulator_x64["accelerationProfile"],
        )
        self.assertEqual("intgemm-runtime-dispatch", simulator_x64["quantizedBackend"])

    def test_ios_patch_forbids_nested_pcre2_network_downloads(self):
        patch = (
            ROOT / "native" / "patches" / "0001-reproducible-flattened-source-build.patch"
        ).read_text(encoding="utf-8")
        self.assertIn("iOS builds require the checksum-verified preseeded PCRE2 source", patch)
        self.assertIn("if((IOS OR CMAKE_SYSTEM_NAME STREQUAL \"iOS\")", patch)

    def test_output_directory_is_confined_to_build(self):
        build = ROOT / "build"
        build.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=build) as temporary:
            self.assertEqual(
                Path(temporary).resolve(),
                ios_profiles.safe_output_directory(Path(temporary)),
            )
        with self.assertRaises(ios_profiles.IosProfileError):
            ios_profiles.safe_output_directory(ROOT)

    def test_source_tree_hash_uses_the_locked_snapshot_identity(self):
        self.assertRegex(ios_profiles.source_tree_sha256(), r"^[0-9a-f]{64}$")
        with self.assertRaises(ios_profiles.IosProfileError):
            ios_profiles.safe_output_directory(ROOT / "build")

    def test_cmake_arguments_pin_ios_15_static_sdk_arch_and_backend(self):
        profiles = ios_profiles.profile_map(ios_profiles.load_lock())
        for profile_id in ios_profiles.PROFILE_IDS:
            arguments = ios_profiles.cmake_arguments(
                profiles[profile_id],
                Path("/source"),
                Path("/build"),
                Path("/cmake"),
                Path("/ninja"),
            )
            joined = " ".join(str(value) for value in arguments)
            profile = profiles[profile_id]
            self.assertIn("-DCMAKE_SYSTEM_NAME=iOS", arguments)
            self.assertIn("-DCMAKE_OSX_DEPLOYMENT_TARGET=15.0", arguments)
            self.assertIn("-DCMAKE_OSX_SYSROOT={}".format(profile["sdk"]), arguments)
            self.assertIn(
                "-DCMAKE_OSX_ARCHITECTURES={}".format(profile["architecture"]),
                arguments,
            )
            self.assertIn("-DLINGUUM_APPLE_STATIC=ON", arguments)
            self.assertIn("-DBUILD_TESTING=OFF", arguments)
            self.assertNotIn("-march=native", joined)
        explicit_sdk = Path("/Applications/Xcode.app/iPhoneSimulator.platform/SDK")
        explicit_arguments = ios_profiles.cmake_arguments(
            profiles["ios-simulator-arm64"],
            Path("/s"),
            Path("/b"),
            Path("/c"),
            Path("/n"),
            sdk_root=explicit_sdk,
        )
        self.assertIn("-DCMAKE_OSX_SYSROOT={}".format(explicit_sdk), explicit_arguments)
        arm = ios_profiles.cmake_arguments(
            profiles["ios-arm64"], Path("/s"), Path("/b"), Path("/c"), Path("/n")
        )
        self.assertIn("-DUSE_RUY=ON", arm)
        self.assertIn("-DUSE_APPLE_ACCELERATE=ON", arm)
        x64 = ios_profiles.cmake_arguments(
            profiles["ios-simulator-x64"],
            Path("/s"),
            Path("/b"),
            Path("/c"),
            Path("/n"),
        )
        self.assertIn("-DUSE_RUY=OFF", x64)
        self.assertIn("-DUSE_APPLE_ACCELERATE=ON", x64)

    def test_compile_commands_prove_target_minimum_backend_and_no_host_native(self):
        profiles = ios_profiles.profile_map(ios_profiles.load_lock())
        adapter = ROOT / "native" / "mozilla-adapter" / "src" / "linguum_translation.cpp"
        with tempfile.TemporaryDirectory() as temporary:
            build = Path(temporary)
            for profile_id, target, backend, sdk_platform in (
                (
                    "ios-arm64",
                    "arm64-apple-ios15.0",
                    "-DBLAS_FOUND=1 -DARM -DUSE_RUY=1",
                    "iPhoneOS.platform",
                ),
                (
                    "ios-simulator-arm64",
                    "arm64-apple-ios15.0-simulator",
                    "-DBLAS_FOUND=1 -DARM -DUSE_RUY=1",
                    "iPhoneSimulator.platform",
                ),
                (
                    "ios-simulator-x64",
                    "x86_64-apple-ios15.0-simulator",
                    "-DBLAS_FOUND=1 -DUSE_INTGEMM=1",
                    "iPhoneSimulator.platform",
                ),
            ):
                sdk = "-isysroot /Applications/Xcode.app/{}/SDK".format(
                    sdk_platform
                )
                commands = [
                    {
                        "file": str(ROOT / "source" / "marian-fork" / "graph.cpp"),
                        "command": "clang++ -target {} {} {} -c graph.cpp".format(
                            target, backend, sdk
                        ),
                    },
                    {
                        "file": str(adapter),
                        "command": (
                            "clang++ -target {} {} "
                            "-DLINGUUM_ACCELERATION_PROFILE=\\\"{}\\\" "
                            "-c adapter.cpp"
                        ).format(
                            target,
                            sdk,
                            profiles[profile_id]["accelerationProfile"],
                        ),
                    },
                ]
                if profile_id != "ios-simulator-x64":
                    commands.extend(
                        [
                            {
                                "file": str(
                                    ROOT
                                    / "source"
                                    / "marian-fork"
                                    / "src"
                                    / "3rd_party"
                                    / "ruy"
                                    / "ruy"
                                    / name
                                ),
                                "command": "clang++ -target {} {} -DARM -c {}".format(
                                    target, sdk, name
                                ),
                            }
                            for name in ("kernel_arm64.cc", "pack_arm.cc")
                        ]
                    )
                (build / "compile_commands.json").write_text(
                    json.dumps(commands), encoding="utf-8"
                )
                evidence = ios_profiles.verify_compile_commands(
                    profiles[profile_id], build
                )
                self.assertEqual("15.0", evidence["deploymentTarget"])
                self.assertFalse(evidence["hostDependentMarchNative"])
                self.assertFalse(evidence["hostMacosSdkReferences"])
                original_command = commands[0]["command"]
                commands[0]["command"] += " -march=native"
                (build / "compile_commands.json").write_text(
                    json.dumps(commands), encoding="utf-8"
                )
                with self.assertRaises(ios_profiles.IosProfileError):
                    ios_profiles.verify_compile_commands(profiles[profile_id], build)
                commands[0]["command"] = original_command.replace(
                    sdk_platform, "MacOSX.sdk"
                )
                (build / "compile_commands.json").write_text(
                    json.dumps(commands), encoding="utf-8"
                )
                with self.assertRaises(ios_profiles.IosProfileError):
                    ios_profiles.verify_compile_commands(profiles[profile_id], build)

    def test_macho_identity_requires_exact_arch_platform_and_ios_15(self):
        profiles = ios_profiles.profile_map(ios_profiles.load_lock())
        device = "platform IOS\nminos 15.0\nsdk 26.5\n"
        simulator = "platform IOSSIMULATOR\nminos 15.0\nsdk 26.5\n"
        self.assertEqual(
            "IOS",
            ios_profiles.verify_macho_identity(
                profiles["ios-arm64"], "arm64\n", device
            )["platform"],
        )
        self.assertEqual(
            "IOSSIMULATOR",
            ios_profiles.verify_macho_identity(
                profiles["ios-simulator-x64"], "x86_64\n", simulator
            )["platform"],
        )
        with self.assertRaises(ios_profiles.IosProfileError):
            ios_profiles.verify_macho_identity(
                profiles["ios-arm64"], "arm64\n", simulator
            )
        with self.assertRaises(ios_profiles.IosProfileError):
            ios_profiles.verify_macho_identity(
                profiles["ios-simulator-arm64"],
                "arm64\n",
                simulator.replace("15.0", "16.0"),
            )

    def test_static_archive_requires_the_complete_c_abi(self):
        symbols = "\n".join(
            "0000000000000000 T _{}".format(name)
            for name in ios_profiles.EXPECTED_C_ABI_SYMBOLS
        )
        evidence = ios_profiles.verify_static_symbols(symbols)
        self.assertEqual(
            sorted(ios_profiles.EXPECTED_C_ABI_SYMBOLS), evidence["cAbiSymbols"]
        )
        with self.assertRaises(ios_profiles.IosProfileError):
            ios_profiles.verify_static_symbols(
                symbols.replace("_linguum_translation_abi_major", "_missing")
            )

    def test_cinterop_output_is_target_correlated_and_exact(self):
        output = (
            "LINGUUM_IOS_CANARY_START target=iosSimulatorArm64 iterations=100\n"
            "LINGUUM_IOS_CANARY_PASS target=iosSimulatorArm64 iterations=100 abi=1.0\n"
        )
        evidence = ios_profiles.verify_cinterop_output(
            output, "iosSimulatorArm64", 100
        )
        self.assertEqual("1.0", evidence["abi"])
        with self.assertRaises(ios_profiles.IosProfileError):
            ios_profiles.verify_cinterop_output(
                output.replace("iosSimulatorArm64", "iosX64"),
                "iosSimulatorArm64",
                100,
            )
        with self.assertRaises(ios_profiles.IosProfileError):
            ios_profiles.verify_cinterop_output(
                output + "LINGUUM_IOS_CANARY_FAIL target=iosSimulatorArm64\n",
                "iosSimulatorArm64",
                100,
            )

    def test_app_bundle_embeds_exact_model_configuration_and_platform_identity(self):
        profiles = ios_profiles.profile_map(ios_profiles.load_lock())
        build = ROOT / "build"
        build.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=build) as temporary:
            root = Path(temporary)
            executable = root / "canary.kexe"
            executable.write_bytes(b"executable")
            executable.chmod(0o755)
            model = root / "model"
            model.mkdir()
            for name in (
                "lex.50.50.esen.s2t.bin",
                "model.esen.intgemm.alphas.bin",
                "vocab.esen.spm",
            ):
                (model / name).write_bytes(name.encode("ascii"))
            configuration = root / "es-en.yml"
            configuration.write_text("models: []\n", encoding="utf-8")
            bundle = ios_profiles.build_app_bundle(
                profiles["ios-simulator-arm64"],
                executable,
                model,
                configuration,
                "io.linguum.translation.canary.test",
            )
            try:
                info = plistlib.loads((bundle / "Info.plist").read_bytes())
                self.assertEqual(
                    "io.linguum.translation.canary.test",
                    info["CFBundleIdentifier"],
                )
                self.assertEqual(["iPhoneSimulator"], info["CFBundleSupportedPlatforms"])
                self.assertEqual("15.0", info["MinimumOSVersion"])
                self.assertEqual(b"executable", (bundle / "LinguumIosCanary").read_bytes())
                self.assertEqual(
                    configuration.read_bytes(), (bundle / "es-en.yml").read_bytes()
                )
                self.assertEqual(
                    sorted(path.name for path in model.iterdir()),
                    sorted(path.name for path in (bundle / "Models").iterdir()),
                )
            finally:
                shutil.rmtree(str(bundle.parent))
            with self.assertRaises(ios_profiles.IosProfileError):
                ios_profiles.build_app_bundle(
                    profiles["ios-simulator-arm64"],
                    executable,
                    model,
                    configuration,
                    "invalid/bundle",
                )
    def test_deterministic_profile_zip_contains_provenance_and_one_archive(self):
        profiles = ios_profiles.profile_map(ios_profiles.load_lock())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "liblinguum_translation.a"
            archive.write_bytes(b"archive")
            first = root / "first.zip"
            second = root / "second.zip"
            ios_profiles.package_profile(
                profiles["ios-simulator-arm64"], archive, first
            )
            ios_profiles.package_profile(
                profiles["ios-simulator-arm64"], archive, second
            )
            self.assertEqual(first.read_bytes(), second.read_bytes())
            evidence = ios_profiles.verify_profile_package(
                profiles["ios-simulator-arm64"], first
            )
            self.assertTrue(evidence["deterministicEpoch"])
            with zipfile.ZipFile(first) as package:
                self.assertEqual(sorted(package.namelist()), package.namelist())
                self.assertEqual(
                    (ROOT / "LICENSE").read_bytes(), package.read("META-INF/LICENSE")
                )
                self.assertEqual(
                    (ROOT / "native" / "UPSTREAM_LOCK.json").read_bytes(),
                    package.read("META-INF/linguum/UPSTREAM_LOCK.json"),
                )

    def test_static_archive_metadata_must_be_normalized(self):
        def member(date: bytes, uid: bytes = b"0", gid: bytes = b"0") -> bytes:
            content = b"object"
            header = (
                b"object.o/       "
                + date.ljust(12)
                + uid.ljust(6)
                + gid.ljust(6)
                + b"644".ljust(8)
                + str(len(content)).encode("ascii").ljust(10)
                + b"`\n"
            )
            return header + content

        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "library.a"
            archive.write_bytes(b"!<arch>\n" + member(b"0"))
            evidence = ios_profiles.verify_deterministic_archive_metadata(archive)
            self.assertTrue(evidence["normalizedArchiveHeaders"])
            self.assertEqual(1, evidence["archiveMembers"])
            archive.write_bytes(b"!<arch>\n" + member(b"1"))
            self.assertTrue(
                ios_profiles.verify_deterministic_archive_metadata(archive)[
                    "normalizedArchiveHeaders"
                ]
            )
            archive.write_bytes(b"!<arch>\n" + member(b"123"))
            with self.assertRaises(ios_profiles.IosProfileError):
                ios_profiles.verify_deterministic_archive_metadata(archive)
            ios_profiles.normalize_static_archive_metadata(archive)
            normalized = ios_profiles.verify_deterministic_archive_metadata(archive)
            self.assertTrue(normalized["normalizedArchiveHeaders"])
            header = archive.read_bytes()[8:68]
            self.assertEqual(b"0", header[16:28].strip())
            self.assertEqual(b"0", header[28:34].strip())
            self.assertEqual(b"0", header[34:40].strip())

    def test_cmake_and_fixture_use_static_c_abi_through_cinterop(self):
        cmake = (ROOT / "native" / "runtime-build" / "CMakeLists.txt").read_text(
            encoding="utf-8"
        )
        fixture = (
            ROOT
            / "testing"
            / "platform-smoke"
            / "ios-canary"
            / "src"
            / "nativeMain"
            / "kotlin"
            / "Main.kt"
        ).read_text(encoding="utf-8")
        definition = (
            ROOT
            / "testing"
            / "platform-smoke"
            / "ios-canary"
            / "src"
            / "nativeInterop"
            / "cinterop"
            / "linguum.def"
        ).read_text(encoding="utf-8")
        driver = (ROOT / "scripts" / "native" / "ios_profiles.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("LINGUUM_APPLE_STATIC", cmake)
        self.assertIn("add_library(linguum_translation STATIC", cmake)
        self.assertIn("headers = linguum_translation.h", definition)
        self.assertIn("staticLibraries = liblinguum_translation.a", definition)
        self.assertIn("linguum_translation_runtime_create", fixture)
        self.assertIn("linguum_translation_model_load", fixture)
        self.assertIn("linguum_translation_translator_create", fixture)
        self.assertIn("linguum_translation_translator_translate", fixture)
        self.assertIn("linguum_translation_result_destroy", fixture)
        self.assertIn("linguum_translation_translator_destroy", fixture)
        self.assertIn("linguum_translation_model_destroy", fixture)
        self.assertIn("linguum_translation_runtime_destroy", fixture)
        self.assertIn("repeat(iterations)", fixture)
        self.assertIn("NSBundle.mainBundle.resourcePath", fixture)
        self.assertIn("fputs", fixture)
        self.assertNotIn("println(", fixture)
        self.assertIn('["xcrun", "libtool", "-static", "-D"', driver)
        self.assertIn('["xcrun", "ranlib", "-D", destination]', driver)

    def test_workflows_build_all_profiles_and_run_simulator_and_device_tiers(self):
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
        scope = (ROOT / "scripts" / "ci" / "verify-scope.sh").read_text(
            encoding="utf-8"
        )
        runners = (ROOT / "toolchains" / "ci-runners.lock.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("LINGUUM_IOS_EXECUTION_TIER: simulator-arm64", pr)
        self.assertIn("--profile all", scope)
        self.assertIn("ios-arm64", scope)
        self.assertIn("ios-simulator-arm64", scope)
        self.assertIn("ios-simulator-x64", scope)
        self.assertIn("runs-on: macos-15-intel", native)
        self.assertIn("--execution-tier simulator-x64", native)
        for workflow in (nightly, release):
            self.assertIn("ios-device", workflow)
            self.assertIn("--execution-tier physical-arm64", workflow)
        self.assertIn("ios_physical_arm64", runners)

    def test_fixture_is_isolated_and_does_not_cross_wp08_boundary(self):
        settings = (ROOT / "settings.gradle.kts").read_text(encoding="utf-8")
        fixture_settings = (
            ROOT / "testing" / "platform-smoke" / "ios-canary" / "settings.gradle.kts"
        ).read_text(encoding="utf-8")
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
        self.assertNotIn(":testing:platform-smoke:ios-canary", settings)
        self.assertIn("testing/platform-smoke/ios-canary/**", plugin)
        self.assertIn('rootProject.name = "linguum-ios-canary"', fixture_settings)
        self.assertFalse((ROOT / "platform" / "apple").exists())
        self.assertFalse(
            (ROOT / "testing" / "platform-smoke" / "ios-canary" / "Package.swift").exists()
        )
        source_xcframeworks = [
            path
            for path in ROOT.glob("**/*.xcframework")
            if path.relative_to(ROOT).parts[0] != "build"
        ]
        self.assertEqual([], source_xcframeworks)


if __name__ == "__main__":
    unittest.main()
