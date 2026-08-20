#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "snapshot.py"
SPEC = importlib.util.spec_from_file_location("upstream_snapshot", SCRIPT)
assert SPEC and SPEC.loader
snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot)


class SnapshotTest(unittest.TestCase):
    def test_canonical_hash_is_stable_and_sensitive_to_bytes_and_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "z.txt").write_bytes(b"z\n")
            (root / "nested").mkdir()
            executable = root / "nested" / "tool"
            executable.write_bytes(b"#!/bin/sh\n")
            executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
            first = snapshot.source_tree_sha256(root)
            self.assertEqual(first, snapshot.source_tree_sha256(root))
            executable.chmod(executable.stat().st_mode & ~stat.S_IXUSR)
            self.assertNotEqual(first, snapshot.source_tree_sha256(root))
            executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
            executable.write_bytes(b"#!/bin/sh\nexit 0\n")
            self.assertNotEqual(first, snapshot.source_tree_sha256(root))

    def test_git_administration_is_excluded_but_gitmodules_is_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            (root / ".git" / "config").write_text("secret", encoding="utf-8")
            (root / ".gitmodules").write_text("[submodule]\n", encoding="utf-8")
            digest = snapshot.source_tree_sha256(root)
            (root / ".git" / "config").write_text("changed", encoding="utf-8")
            self.assertEqual(digest, snapshot.source_tree_sha256(root))
            (root / ".gitmodules").write_text("changed", encoding="utf-8")
            self.assertNotEqual(digest, snapshot.source_tree_sha256(root))

    @unittest.skipIf(os.name == "nt", "symlink creation is not guaranteed on Windows")
    def test_symlink_target_is_hashed_without_dereferencing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a").write_text("same", encoding="utf-8")
            (root / "b").write_text("same", encoding="utf-8")
            (root / "link").symlink_to("a")
            first = snapshot.source_tree_sha256(root)
            (root / "link").unlink()
            (root / "link").symlink_to("b")
            self.assertNotEqual(first, snapshot.source_tree_sha256(root))

    def test_recursive_status_rejects_uninitialized_or_changed_submodule(self):
        valid = " 0123456789abcdef0123456789abcdef01234567 vendor/a (heads/main)\n"
        self.assertEqual(
            [("vendor/a", "0123456789abcdef0123456789abcdef01234567")],
            snapshot.parse_submodule_status(valid),
        )
        with self.assertRaises(snapshot.SnapshotError):
            snapshot.parse_submodule_status(valid.replace(" ", "-", 1))
        with self.assertRaises(snapshot.SnapshotError):
            snapshot.parse_submodule_status(valid.replace(" ", "+", 1))

    def test_repository_url_normalization_is_https_and_explicit(self):
        expected = "https://github.com/mozilla/translations.git"
        self.assertEqual(expected, snapshot.normalize_repository_url("git@github.com:mozilla/translations.git"))
        self.assertEqual(expected, snapshot.normalize_repository_url("https://github.com/mozilla/translations"))
        with self.assertRaises(snapshot.SnapshotError):
            snapshot.normalize_repository_url("../translations")

    def test_license_classification_covers_primary_contracts(self):
        self.assertEqual("MPL-2.0", snapshot.classify_license("LICENSE", b"Mozilla Public License Version 2.0"))
        self.assertEqual("Apache-2.0", snapshot.classify_license("LICENSE", b"Apache License\nVersion 2.0"))
        self.assertEqual("BSL-1.0", snapshot.classify_license("LICENSE_1_0.txt", b"Boost Software License"))
        self.assertEqual(
            "Zlib",
            snapshot.classify_license(
                "LICENSE.md",
                b"This software is provided 'as-is', without any express or implied warranty. "
                b"Permission is granted to alter it and redistribute it freely.",
            ),
        )
        self.assertEqual(
            "MPL-2.0 AND BSD-3-Clause AND LGPL-2.1-or-later",
            snapshot.classify_license("COPYING.README", b"Eigen is primarily MPL2 licensed."),
        )
        self.assertEqual("NOASSERTION", snapshot.classify_license("NOTICE", b"project-specific terms"))

    def test_safe_relative_path_rejects_traversal_and_absolute_paths(self):
        self.assertEqual("nested/file", snapshot.safe_relative_path("nested/file"))
        for value in ("", "../outside", "nested/../../outside", "/absolute"):
            with self.subTest(value=value):
                with self.assertRaises(snapshot.SnapshotError):
                    snapshot.safe_relative_path(value)

    def test_index_hash_uses_unfiltered_blob_bytes_and_git_modes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
            source = root / "native" / "upstream" / "mozilla-translations"
            source.mkdir(parents=True)
            (root / ".gitattributes").write_text("*.txt text eol=lf\n", encoding="utf-8")
            payload = source / "payload.txt"
            payload.write_bytes(b"first\r\nsecond\r\n")
            repository_path = "native/upstream/mozilla-translations/payload.txt"
            object_id = subprocess.run(
                ["git", "-C", str(root), "hash-object", "-w", "--no-filters", repository_path],
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            ).stdout.strip()
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "update-index",
                    "--add",
                    "--cacheinfo",
                    "100644,{},{}".format(object_id, repository_path),
                ],
                check=True,
            )
            self.assertEqual(snapshot.source_tree_sha256(source), snapshot.source_tree_sha256_from_index(root, source))


if __name__ == "__main__":
    unittest.main()
