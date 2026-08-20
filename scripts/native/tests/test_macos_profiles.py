#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Offline contract tests for the M1 macOS native profiles."""

import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]


def load_script(name: str):
    path = ROOT / "scripts" / "native" / "{}.py".format(name)
    spec = importlib.util.spec_from_file_location("linguum_macos_test_{}".format(name), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


macos_profiles = load_script("macos_profiles")
run_host_canary = load_script("run_host_canary")


class MacosProfileContractTests(unittest.TestCase):
    def test_lock_has_exact_architectures_runners_and_backends(self):
        document = macos_profiles.load_lock()
        profiles = macos_profiles.profile_map(document)
        self.assertEqual(set(macos_profiles.PROFILE_IDS), set(profiles))
        self.assertEqual("13.0", document["deploymentTarget"])
        self.assertEqual("macos-15", profiles["macos-arm64"]["runner"])
        self.assertEqual("macos-15-intel", profiles["macos-x64"]["runner"])
        self.assertEqual("armv8-a", profiles["macos-arm64"]["buildArch"])
        self.assertEqual("nehalem", profiles["macos-x64"]["buildArch"])
        self.assertEqual("Accelerate", profiles["macos-arm64"]["matrixMultiplicationBackend"])
        self.assertEqual("Ruy", profiles["macos-arm64"]["quantizedBackend"])
        self.assertEqual("intgemm-runtime-dispatch", profiles["macos-x64"]["quantizedBackend"])
        self.assertEqual(["ARMv8-A"], profiles["macos-arm64"]["minimumCpuFeatures"])
        self.assertEqual(["SSE4.2"], profiles["macos-x64"]["minimumCpuFeatures"])
        self.assertFalse(profiles["macos-arm64"]["intgemmRuntimeDispatch"])
        self.assertTrue(profiles["macos-x64"]["intgemmRuntimeDispatch"])

    def test_explicit_profiles_are_host_independent(self):
        with mock.patch.object(run_host_canary.platform, "system", return_value="Darwin"), \
             mock.patch.object(run_host_canary.platform, "machine", return_value="arm64"):
            arm_arch, arm_backend, arm_arguments = run_host_canary.host_profile("macos-arm64")
            x64_arch, x64_backend, x64_arguments = run_host_canary.host_profile("macos-x64")
        self.assertEqual("armv8-a", arm_arch)
        self.assertEqual("apple-accelerate-arm64", arm_backend)
        self.assertIn("-DCMAKE_OSX_ARCHITECTURES=arm64", arm_arguments)
        self.assertIn("-DUSE_RUY=ON", arm_arguments)
        self.assertEqual("nehalem", x64_arch)
        self.assertEqual("apple-accelerate-intgemm-runtime-x64", x64_backend)
        self.assertIn("-DCMAKE_OSX_ARCHITECTURES=x86_64", x64_arguments)
        self.assertNotIn("native", " ".join(x64_arguments))
        for arguments in (arm_arguments, x64_arguments):
            self.assertIn("-DCMAKE_OSX_DEPLOYMENT_TARGET=13.0", arguments)
            self.assertIn("-DUSE_APPLE_ACCELERATE=ON", arguments)
            self.assertIn("-DUSE_ONNX_SGEMM=OFF", arguments)

    def test_macos_profile_rejects_non_macos_host(self):
        with mock.patch.object(run_host_canary.platform, "system", return_value="Linux"), \
             mock.patch.object(run_host_canary.platform, "machine", return_value="x86_64"):
            with self.assertRaises(run_host_canary.HostCanaryError):
                run_host_canary.host_profile("macos-x64")

    def test_macho_architecture_parser_handles_archs_and_info_output(self):
        self.assertEqual(["arm64"], macos_profiles.macho_architectures("arm64\n"))
        self.assertEqual(["x86_64"], macos_profiles.macho_architectures("x86_64\n"))
        self.assertEqual(
            ["arm64", "x86_64"],
            macos_profiles.macho_architectures(
                "Architectures in the fat file: library are: x86_64 arm64\n"
            ),
        )
        with self.assertRaises(macos_profiles.MacosProfileError):
            macos_profiles.macho_architectures("unknown")

    def test_dependencies_require_accelerate_and_reject_non_system_dylibs(self):
        output = """library:\n\t@rpath/liblinguum_translation.dylib (compatibility version 0.0.0, current version 0.0.0)\n\t/System/Library/Frameworks/Accelerate.framework/Versions/A/Accelerate (compatibility version 1.0.0, current version 4.0.0)\n\t/usr/lib/libc++.1.dylib (compatibility version 1.0.0, current version 1900.178.0)\n"""
        dependencies = macos_profiles.parse_dependencies(output)
        self.assertEqual(2, len(dependencies))
        self.assertTrue(any("Accelerate.framework" in value for value in dependencies))
        with self.assertRaises(macos_profiles.MacosProfileError):
            macos_profiles.parse_dependencies(
                output + "\t@rpath/libthirdparty.dylib (compatibility version 1.0.0, current version 1.0.0)\n"
            )
        with self.assertRaises(macos_profiles.MacosProfileError):
            macos_profiles.parse_dependencies(
                "library:\n\t@rpath/liblinguum_translation.dylib (compatibility version 0.0.0, current version 0.0.0)\n\t/usr/lib/libc++.1.dylib (compatibility version 1.0.0, current version 1.0.0)\n"
            )

    def test_source_tree_hash_is_normalized_to_the_digest(self):
        self.assertRegex(macos_profiles.source_tree_sha256(), r"^[0-9a-f]{64}$")

    def test_compile_evidence_rejects_native_and_proves_each_backend(self):
        profiles = macos_profiles.profile_map(macos_profiles.load_lock())
        adapter = ROOT / "native" / "mozilla-adapter" / "src" / "linguum_translation.cpp"
        with tempfile.TemporaryDirectory() as temporary:
            build = Path(temporary)
            for profile_id, architecture, build_arch, backend_flag in (
                ("macos-arm64", "arm64", "armv8-a", "-DARM"),
                ("macos-x64", "x86_64", "nehalem", "-DUSE_INTGEMM=1"),
            ):
                acceleration = profiles[profile_id]["accelerationProfile"]
                common = "clang++ -arch {} -mmacosx-version-min=13.0 -march={}".format(
                    architecture, build_arch
                )
                commands = [
                    {
                        "file": str(ROOT / "source" / "marian-fork" / "src" / "graph.cpp"),
                        "command": "{} -DBLAS_FOUND=1 {} -c graph.cpp".format(common, backend_flag),
                    },
                    {
                        "file": str(adapter),
                        "command": '{} -DLINGUUM_ACCELERATION_PROFILE=\\"{}\\" -c adapter.cpp'.format(
                            common, acceleration
                        ),
                    },
                ]
                path = build / "compile_commands.json"
                path.write_text(json.dumps(commands), encoding="utf-8")
                evidence = macos_profiles.verify_compile_commands(profiles[profile_id], build)
                self.assertEqual(build_arch, evidence["buildArch"])
                self.assertFalse(evidence["hostDependentMarchNative"])
                commands[0]["command"] = commands[0]["command"].replace(
                    "-march={}".format(build_arch), "-march=native"
                )
                path.write_text(json.dumps(commands), encoding="utf-8")
                with self.assertRaises(macos_profiles.MacosProfileError):
                    macos_profiles.verify_compile_commands(profiles[profile_id], build)

    def test_deterministic_jar_has_sorted_epoch_entries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.jar"
            second = root / "second.jar"
            entries = {"z/file": b"last", "a/file": b"first"}
            macos_profiles.create_jar(first, entries)
            macos_profiles.create_jar(second, entries)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(str(first)) as jar:
                self.assertEqual(["a/file", "z/file"], jar.namelist())
                self.assertTrue(all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in jar.infolist()))

    def test_output_directory_is_confined_to_build(self):
        with self.assertRaises(macos_profiles.MacosProfileError):
            macos_profiles.safe_output_directory(ROOT)
        with self.assertRaises(macos_profiles.MacosProfileError):
            macos_profiles.safe_output_directory(ROOT / "build")
        expected = (ROOT / "build" / "macos-package-test").resolve()
        self.assertEqual(expected, macos_profiles.safe_output_directory(expected))

    def test_workflows_name_both_explicit_runner_architectures(self):
        workflow = (ROOT / ".github" / "workflows" / "pr.yml").read_text(encoding="utf-8")
        native_safety = (
            ROOT / ".github" / "workflows" / "native-safety.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("runs-on: macos-15", workflow)
        self.assertIn("runs-on: macos-15-intel", workflow)
        self.assertIn("LINGUUM_MACOS_PROFILE: macos-arm64", workflow)
        self.assertIn("LINGUUM_MACOS_PROFILE: macos-x64", workflow)
        self.assertIn("--profile macos-arm64", native_safety)
        self.assertIn("--profile macos-x64", native_safety)


if __name__ == "__main__":
    unittest.main()
