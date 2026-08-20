#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Offline tests for the native source, model, and tool materializers."""

import hashlib
import importlib.util
import io
import json
import re
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]


def load_script(name: str):
    path = ROOT / "scripts" / "native" / "{}.py".format(name)
    spec = importlib.util.spec_from_file_location("linguum_{}".format(name), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


bootstrap_tools = load_script("bootstrap_tools")
fetch_canary_model = load_script("fetch_canary_model")
stage_source = load_script("stage_source")
run_host_canary = load_script("run_host_canary")


class ArchiveSafetyTests(unittest.TestCase):
    def test_extracts_safe_zip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "tool.zip"
            destination = root / "output"
            with zipfile.ZipFile(str(archive), "w") as output:
                output.writestr("bin/tool", b"tool")
            bootstrap_tools.extract_archive(archive, destination)
            self.assertEqual((destination / "bin" / "tool").read_bytes(), b"tool")

    def test_rejects_zip_path_traversal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "tool.zip"
            with zipfile.ZipFile(str(archive), "w") as output:
                output.writestr("../escaped", b"unsafe")
            with self.assertRaises(bootstrap_tools.ToolBootstrapError):
                bootstrap_tools.extract_archive(archive, root / "output")
            self.assertFalse((root / "escaped").exists())

    def test_rejects_tar_symlink_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "tool.tar.gz"
            with tarfile.open(str(archive), "w:gz") as output:
                member = tarfile.TarInfo("bin/tool")
                member.type = tarfile.SYMTYPE
                member.linkname = "../../escaped"
                output.addfile(member)
            with self.assertRaises(bootstrap_tools.ToolBootstrapError):
                bootstrap_tools.extract_archive(archive, root / "output")
            self.assertFalse((root / "escaped").exists())

    def test_handles_internal_relative_tar_symlink_per_host(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "tool.tar.gz"
            with tarfile.open(str(archive), "w:gz") as output:
                payload = b"tool"
                target = tarfile.TarInfo("libexec/tool")
                target.size = len(payload)
                output.addfile(target, io.BytesIO(payload))
                link = tarfile.TarInfo("bin/tool")
                link.type = tarfile.SYMTYPE
                link.linkname = "../libexec/tool"
                output.addfile(link)
            destination = root / "output"
            with mock.patch.object(bootstrap_tools, "tar_links_supported", return_value=False):
                with self.assertRaises(bootstrap_tools.ToolBootstrapError):
                    bootstrap_tools.extract_archive(archive, destination)
            if sys.platform == "win32":
                return
            bootstrap_tools.extract_archive(archive, destination)
            self.assertEqual((destination / "bin" / "tool").read_bytes(), b"tool")


class ModelFetchTests(unittest.TestCase):
    @staticmethod
    def artifact(role: str, source: Path):
        payload = source.read_bytes()
        return {
            "role": role,
            "fileName": "{}.bin".format(role),
            "url": source.as_uri(),
            "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    def test_fetches_and_reuses_hash_locked_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sources = root / "sources"
            sources.mkdir()
            artifacts = []
            for role in ("model", "shortlist", "vocabulary"):
                source = sources / role
                source.write_bytes(role.encode("ascii"))
                artifacts.append(self.artifact(role, source))
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "schemaVersion": 1,
                "languagePair": "es-en",
                "artifacts": artifacts,
            }), encoding="utf-8")
            destination = root / "model"
            fetch_canary_model.fetch(destination, manifest)
            mtimes = {path.name: path.stat().st_mtime_ns for path in destination.iterdir()}
            with mock.patch.object(fetch_canary_model.urllib.request, "urlopen") as urlopen:
                fetch_canary_model.fetch(destination, manifest)
            urlopen.assert_not_called()
            self.assertEqual(mtimes, {path.name: path.stat().st_mtime_ns for path in destination.iterdir()})

    def test_rejects_unsafe_artifact_name_before_fetch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / "manifest.json"
            artifacts = [
                {"role": role, "fileName": "../escape" if role == "model" else role,
                 "url": "file:///unused", "size": 1, "sha256": "0" * 64}
                for role in ("model", "shortlist", "vocabulary")
            ]
            manifest.write_text(json.dumps({
                "schemaVersion": 1,
                "languagePair": "es-en",
                "artifacts": artifacts,
            }), encoding="utf-8")
            with self.assertRaises(fetch_canary_model.ModelFetchError):
                fetch_canary_model.fetch(root / "model", manifest)

    def test_removes_partial_file_after_identity_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.write_bytes(b"payload")
            artifact = self.artifact("model", source)
            artifact["sha256"] = "0" * 64
            destination = root / "model"
            with self.assertRaises(fetch_canary_model.ModelFetchError):
                fetch_canary_model.fetch_artifact(artifact, destination)
            self.assertFalse((destination / "model.bin.part").exists())
            self.assertFalse((destination / "model.bin").exists())

    def test_removes_stale_partial_after_download_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.write_bytes(b"payload")
            artifact = self.artifact("model", source)
            destination = root / "model"
            destination.mkdir()
            partial = destination / "model.bin.part"
            partial.write_bytes(b"stale")
            with mock.patch.object(
                fetch_canary_model.urllib.request, "urlopen", side_effect=OSError("offline")
            ):
                with self.assertRaises(OSError):
                    fetch_canary_model.fetch_artifact(artifact, destination)
            self.assertFalse(partial.exists())

    def test_rejects_duplicate_role_and_malformed_identity_before_fetch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.write_bytes(b"payload")
            artifacts = [self.artifact(role, source) for role in ("model", "shortlist", "vocabulary")]
            artifacts.append(dict(artifacts[0], fileName="duplicate.bin"))
            manifest = root / "duplicates.json"
            manifest.write_text(json.dumps({
                "schemaVersion": 1,
                "languagePair": "es-en",
                "artifacts": artifacts,
            }), encoding="utf-8")
            with self.assertRaises(fetch_canary_model.ModelFetchError):
                fetch_canary_model.fetch(root / "model", manifest)

            artifacts = artifacts[:3]
            artifacts[-1]["sha256"] = "not-a-sha256"
            manifest.write_text(json.dumps({
                "schemaVersion": 1,
                "languagePair": "es-en",
                "artifacts": artifacts,
            }), encoding="utf-8")
            with mock.patch.object(fetch_canary_model.urllib.request, "urlopen") as urlopen:
                with self.assertRaises(fetch_canary_model.ModelFetchError):
                    fetch_canary_model.fetch(root / "model", manifest)
            urlopen.assert_not_called()


class SourceStageTests(unittest.TestCase):
    def test_destination_must_be_below_build(self):
        with self.assertRaises(stage_source.SourceStageError):
            stage_source.safe_build_destination(ROOT)
        with self.assertRaises(stage_source.SourceStageError):
            stage_source.safe_build_destination(ROOT / "build")
        expected = (ROOT / "build" / "unit-stage").resolve()
        self.assertEqual(stage_source.safe_build_destination(expected), expected)

    def test_patch_identity_includes_names_order_and_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "0001.patch"
            second = root / "0002.patch"
            first.write_bytes(b"one")
            second.write_bytes(b"two")
            identity = stage_source.patch_identity([first, second])
            self.assertEqual(identity, stage_source.patch_identity([first, second]))
            self.assertNotEqual(identity, stage_source.patch_identity([second, first]))
            second.write_bytes(b"changed")
            self.assertNotEqual(identity, stage_source.patch_identity([first, second]))

    def test_patch_targets_are_safe_unique_in_place_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            patch = Path(temporary) / "safe.patch"
            patch.write_bytes(
                b"diff --git a/source/one.cpp b/source/one.cpp\n"
                b"diff --git a/source/two.cpp b/source/two.cpp\r\n"
            )
            self.assertEqual(
                [Path("source/one.cpp"), Path("source/two.cpp")],
                [Path(path) for path in stage_source.affected_paths(patch)],
            )

            unsafe_headers = (
                b"diff --git a/../escape b/../escape\n",
                b"diff --git a/source/one.cpp b/source/two.cpp\n",
                b"diff --git a/source/one.cpp b/source/one.cpp\n"
                b"diff --git a/source/one.cpp b/source/one.cpp\n",
            )
            for header in unsafe_headers:
                patch.write_bytes(header)
                with self.subTest(header=header):
                    with self.assertRaises(stage_source.SourceStageError):
                        stage_source.affected_paths(patch)

    def test_restores_crlf_without_changing_file_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target.h"
            target.write_bytes(b"first\nchanged\nlast\n")
            stage_source.restore_crlf([target])
            self.assertEqual(b"first\r\nchanged\r\nlast\r\n", target.read_bytes())
            self.assertTrue(stage_source.crlf_only(target))


class NativeContractMetadataTests(unittest.TestCase):
    def test_build_directory_must_be_below_build(self):
        with self.assertRaises(run_host_canary.HostCanaryError):
            run_host_canary.safe_build_directory(ROOT)
        with self.assertRaises(run_host_canary.HostCanaryError):
            run_host_canary.safe_build_directory(ROOT / "build")
        expected = (ROOT / "build" / "unit-canary").resolve()
        self.assertEqual(run_host_canary.safe_build_directory(expected), expected)

    def test_header_and_linker_allowlists_are_exactly_synchronized(self):
        expected = run_host_canary.expected_exports()
        header = (ROOT / "native" / "abi" / "include" / "linguum_translation.h").read_text(
            encoding="utf-8"
        )
        header_exports = set(re.findall(r"\b(linguum_translation_[a-z_]+)\s*\(", header))
        self.assertEqual(expected, header_exports)

        macos = (ROOT / "native" / "runtime-build" / "exports" / "macos.exports").read_text(
            encoding="utf-8"
        )
        macos_exports = {
            line.strip().lstrip("_")
            for line in macos.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        self.assertEqual(expected, macos_exports)

        linux = (ROOT / "native" / "runtime-build" / "exports" / "linux.map").read_text(
            encoding="utf-8"
        )
        linux_exports = set(re.findall(r"\b(linguum_translation_[a-z_]+);", linux))
        self.assertEqual(expected, linux_exports)

    def test_patch_metadata_matches_patch_bytes_and_affected_paths(self):
        patch = ROOT / "native" / "patches" / "0001-reproducible-flattened-source-build.patch"
        metadata = json.loads((ROOT / "native" / "patches" / "PATCHES.yaml").read_text(encoding="utf-8"))
        schema = json.loads(
            (ROOT / "schemas" / "patch-metadata.schema.json").read_text(encoding="utf-8")
        )
        self.assertTrue(set(schema["required"]).issubset(metadata))
        self.assertEqual(set(), set(metadata) - set(schema["properties"]))
        for name, rules in schema["properties"].items():
            if name not in metadata:
                continue
            value = metadata[name]
            if "const" in rules:
                self.assertEqual(rules["const"], value)
            if "pattern" in rules:
                self.assertIsNotNone(re.fullmatch(rules["pattern"], value), name)
            if "enum" in rules:
                self.assertIn(value, rules["enum"])
            if isinstance(value, str):
                self.assertGreaterEqual(len(value), rules.get("minLength", 0), name)
                self.assertLessEqual(len(value), rules.get("maxLength", len(value)), name)
        platform_rules = schema["properties"]["platforms"]
        self.assertGreaterEqual(len(metadata["platforms"]), platform_rules["minItems"])
        self.assertEqual(len(metadata["platforms"]), len(set(metadata["platforms"])))
        self.assertTrue(set(metadata["platforms"]).issubset(platform_rules["items"]["enum"]))
        self.assertEqual(1, metadata["schemaVersion"])
        self.assertEqual("LT-UPSTREAM-0001", metadata["id"])
        self.assertEqual(stage_source.bytes_sha256([patch.read_bytes()]), metadata["patchSha256"])
        affected_paths = set(re.findall(r"^diff --git a/(\S+) b/\S+$", patch.read_text(encoding="utf-8"), re.M))
        self.assertEqual(affected_paths, set(metadata["affectedPaths"]))

    def test_async_worker_failures_cross_the_c_abi_without_terminating_the_host(self):
        adapter = (
            ROOT / "native" / "mozilla-adapter" / "src" / "linguum_translation.cpp"
        ).read_text(encoding="utf-8")
        patch = (
            ROOT / "native" / "patches" / "0001-reproducible-flattened-source-build.patch"
        ).read_text(encoding="utf-8")

        self.assertIn("std::unique_lock<std::mutex> lock_", adapter)
        self.assertIn("configuration.workerExceptionHandler", adapter)
        self.assertIn("TranslationPromiseLease promise_lease", adapter)
        self.assertIn("MarianAbortMode abort_mode", adapter)
        self.assertIn("catch (const std::exception& error)", adapter)
        self.assertIn("workerExceptionHandler(std::current_exception())", patch)


if __name__ == "__main__":
    unittest.main()
