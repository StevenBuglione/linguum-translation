#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Create and verify the immutable Firefox-pinned Mozilla source snapshot."""

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


REPOSITORY = "https://github.com/mozilla/translations.git"
REPOSITORY_NAME = "mozilla/translations"
REVISION = "eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d"
BERGAMOT_VERSION = "v0.6.0"
UPSTREAM_LICENSE = "MPL-2.0"
FIREFOX_REPOSITORY = "https://github.com/mozilla-firefox/firefox.git"
FIREFOX_REPOSITORY_NAME = "mozilla-firefox/firefox"
FIREFOX_PIN_REVISION = "48d55cf7ec80093903e2ef7f58b61a84a22ef716"
FIREFOX_PIN_PATH = "toolkit/components/translations/bergamot-translator/moz.yaml"
ARCHIVE_FORMAT = "linguum-source-tree-v1"
ATTRIBUTES_BEGIN = "# BEGIN LINGUUM IMMUTABLE UPSTREAM"
ATTRIBUTES_END = "# END LINGUUM IMMUTABLE UPSTREAM"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
LICENSE_NAMES = re.compile(r"^(?:licen[cs]e|copying|notice)(?:[._-].*)?$", re.IGNORECASE)


class SnapshotError(RuntimeError):
    """A deterministic snapshot invariant was violated."""


def run_git(checkout: Path, arguments: Sequence[str]) -> str:
    completed = subprocess.run(
        ["git", "-C", str(checkout), *arguments],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise SnapshotError("git {} failed: {}".format(" ".join(arguments), detail))
    return completed.stdout


def normalize_repository_url(url: str) -> str:
    value = url.strip().rstrip("/")
    ssh_match = re.fullmatch(r"git@github\.com:(.+)", value)
    if ssh_match:
        value = "https://github.com/{}".format(ssh_match.group(1))
    if value.startswith("git://github.com/"):
        value = "https://github.com/{}".format(value[len("git://github.com/") :])
    if value.startswith("http://github.com/"):
        value = "https://github.com/{}".format(value[len("http://github.com/") :])
    if value.startswith("https://github.com/") and not value.endswith(".git"):
        value += ".git"
    if not value.startswith("https://"):
        raise SnapshotError("submodule URL is not an HTTPS URL: {}".format(url))
    return value


def safe_relative_path(value: str) -> str:
    path = Path(value)
    windows_or_posix_absolute = bool(re.match(r"^(?:[A-Za-z]:[\\/]|[\\/])", value))
    if (
        path.is_absolute()
        or windows_or_posix_absolute
        or not value
        or ".." in path.parts
        or any(character in value for character in "\x00\r\n\t")
    ):
        raise SnapshotError("unsafe relative path: {!r}".format(value))
    normalized = path.as_posix()
    if normalized in (".", ""):
        raise SnapshotError("empty relative path")
    return normalized


def canonical_entries(root: Path) -> List[Tuple[str, Path]]:
    if not root.is_dir():
        raise SnapshotError("source tree is not a directory: {}".format(root))
    entries: List[Tuple[str, Path]] = []
    for current_root, directory_names, file_names in os.walk(root, topdown=True, followlinks=False):
        current = Path(current_root)
        directory_names[:] = sorted(name for name in directory_names if name != ".git")
        for name in directory_names:
            path = current / name
            relative = safe_relative_path(path.relative_to(root).as_posix())
            entries.append((relative, path))
        for name in sorted(file_names):
            if name == ".git":
                continue
            path = current / name
            relative = safe_relative_path(path.relative_to(root).as_posix())
            entries.append((relative, path))
    return sorted(entries, key=lambda entry: entry[0].encode("utf-8"))


def update_field(digest: "hashlib._Hash", value: bytes) -> None:
    digest.update(str(len(value)).encode("ascii"))
    digest.update(b":")
    digest.update(value)
    digest.update(b"\n")


def source_tree_sha256(root: Path) -> str:
    """Hash the canonical v1 archive stream without changing source bytes."""
    digest = hashlib.sha256()
    digest.update(b"LINGUUM_SOURCE_TREE_V1\n")
    for relative, path in canonical_entries(root):
        path_bytes = relative.encode("utf-8")
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            digest.update(b"L\n")
            update_field(digest, path_bytes)
            update_field(digest, os.readlink(path).encode("utf-8"))
        elif stat.S_ISDIR(metadata.st_mode):
            digest.update(b"D\n")
            update_field(digest, path_bytes)
            update_field(digest, b"0755")
        elif stat.S_ISREG(metadata.st_mode):
            digest.update(b"F\n")
            update_field(digest, path_bytes)
            mode = b"0755" if metadata.st_mode & stat.S_IXUSR else b"0644"
            update_field(digest, mode)
            update_field(digest, str(metadata.st_size).encode("ascii"))
            with path.open("rb") as source:
                while True:
                    block = source.read(1024 * 1024)
                    if not block:
                        break
                    digest.update(block)
            digest.update(b"\n")
        else:
            raise SnapshotError("unsupported filesystem entry: {}".format(path))
    return digest.hexdigest()


def index_entries(repository_root: Path, tree_root: Path) -> List[Tuple[str, str, str]]:
    try:
        relative_root = tree_root.resolve().relative_to(repository_root.resolve()).as_posix()
    except ValueError as error:
        raise SnapshotError("snapshot is outside its Git repository") from error
    output = subprocess.run(
        ["git", "-C", str(repository_root), "ls-files", "--stage", "-z", "--", relative_root],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if output.returncode != 0:
        raise SnapshotError("git ls-files failed: {}".format(output.stderr.decode("utf-8", errors="replace").strip()))
    records: List[Tuple[str, str, str]] = []
    prefix = relative_root + "/"
    for raw_record in output.stdout.split(b"\x00"):
        if not raw_record:
            continue
        try:
            raw_identity, raw_path = raw_record.split(b"\t", 1)
            mode, object_id, stage = raw_identity.decode("ascii").split()
            repository_path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as error:
            raise SnapshotError("unparseable Git index entry") from error
        if stage != "0" or not repository_path.startswith(prefix):
            raise SnapshotError("invalid Git index stage or path for {}".format(repository_path))
        relative = safe_relative_path(repository_path[len(prefix) :])
        if mode not in ("100644", "100755", "120000") or not GIT_SHA_RE.fullmatch(object_id):
            raise SnapshotError("unsupported Git index mode or object for {}".format(repository_path))
        records.append((relative, mode, repository_path))
    return sorted(records)


def assert_worktree_matches_index(
    repository_root: Path,
    tree_root: Path,
    tracked_paths: Iterable[str],
    expected_digest: str,
) -> None:
    relative_root = tree_root.resolve().relative_to(repository_root.resolve()).as_posix()
    difference = subprocess.run(
        ["git", "-C", str(repository_root), "diff", "--quiet", "--", relative_root],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if difference.returncode not in (0, 1):
        raise SnapshotError("git diff failed while checking the immutable snapshot")
    untracked = run_git(repository_root, ["ls-files", "--others", "--exclude-standard", "--", relative_root])
    if untracked.strip():
        raise SnapshotError("immutable snapshot contains untracked files")
    filesystem_paths = {
        relative
        for relative, path in canonical_entries(tree_root)
        if path.is_file() or path.is_symlink()
    }
    if filesystem_paths != set(tracked_paths):
        raise SnapshotError("immutable snapshot filesystem entries differ from the Git index")
    if difference.returncode == 1 and source_tree_sha256(tree_root) != expected_digest:
        raise SnapshotError("immutable snapshot working tree differs from both source bytes and the Git index")


def source_tree_sha256_from_index(repository_root: Path, tree_root: Path) -> str:
    """Hash committed snapshot bytes and modes portably from the Git index."""
    records = index_entries(repository_root, tree_root)
    if not records:
        raise SnapshotError("immutable snapshot has no tracked Git index entries")
    files = {relative: (mode, repository_path) for relative, mode, repository_path in records}
    directories = set()
    for relative in files:
        parent = Path(relative).parent
        while parent.as_posix() not in (".", ""):
            directories.add(parent.as_posix())
            parent = parent.parent

    process = subprocess.Popen(
        ["git", "-C", str(repository_root), "cat-file", "--batch"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None and process.stdout is not None
    digest = hashlib.sha256()
    digest.update(b"LINGUUM_SOURCE_TREE_V1\n")
    process_error = b""
    try:
        for relative in sorted(directories | set(files), key=lambda value: value.encode("utf-8")):
            path_bytes = relative.encode("utf-8")
            if relative in directories and relative not in files:
                digest.update(b"D\n")
                update_field(digest, path_bytes)
                update_field(digest, b"0755")
                continue
            mode, repository_path = files[relative]
            process.stdin.write((":" + repository_path + "\n").encode("utf-8"))
            process.stdin.flush()
            header = process.stdout.readline().decode("ascii").strip().split()
            if len(header) != 3 or header[1] != "blob":
                raise SnapshotError("Git index object is not a blob: {}".format(repository_path))
            size = int(header[2])
            content = process.stdout.read(size)
            if len(content) != size or process.stdout.read(1) != b"\n":
                raise SnapshotError("truncated Git blob: {}".format(repository_path))
            if mode == "120000":
                digest.update(b"L\n")
                update_field(digest, path_bytes)
                update_field(digest, content)
            else:
                digest.update(b"F\n")
                update_field(digest, path_bytes)
                update_field(digest, b"0755" if mode == "100755" else b"0644")
                update_field(digest, str(size).encode("ascii"))
                digest.update(content)
                digest.update(b"\n")
    finally:
        process.stdin.close()
        process.wait()
        process_error = process.stderr.read() if process.stderr else b""
        process.stdout.close()
        if process.stderr:
            process.stderr.close()
    if process.returncode != 0:
        detail = process_error.decode("utf-8", errors="replace").strip()
        raise SnapshotError("git cat-file failed: {}".format(detail))
    value = digest.hexdigest()
    assert_worktree_matches_index(repository_root, tree_root, (record[0] for record in records), value)
    return value


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while True:
            block = source.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def file_sha256_from_index(repository_root: Path, path: Path) -> str:
    try:
        repository_path = path.resolve().relative_to(repository_root.resolve()).as_posix()
    except ValueError as error:
        raise SnapshotError("locked file is outside its Git repository") from error
    completed = subprocess.run(
        ["git", "-C", str(repository_root), "cat-file", "blob", ":" + repository_path],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise SnapshotError(
            "Git index blob is unavailable for {}: {}".format(
                repository_path,
                completed.stderr.decode("utf-8", errors="replace").strip(),
            )
        )
    return hashlib.sha256(completed.stdout).hexdigest()


def parse_submodule_status(output: str) -> List[Tuple[str, str]]:
    submodules: List[Tuple[str, str]] = []
    for line in output.splitlines():
        if not line:
            continue
        state = line[0]
        parts = line[1:].split()
        if len(parts) < 2 or not GIT_SHA_RE.fullmatch(parts[0]):
            raise SnapshotError("unparseable recursive submodule status: {}".format(line))
        if state != " ":
            meanings = {"-": "uninitialized", "+": "different revision", "U": "conflicted"}
            raise SnapshotError(
                "submodule {} is {}".format(parts[1], meanings.get(state, "invalid ({})".format(state)))
            )
        submodules.append((safe_relative_path(parts[1]), parts[0]))
    paths = [path for path, _ in submodules]
    if len(paths) != len(set(paths)):
        raise SnapshotError("recursive submodule status contains duplicate paths")
    return sorted(submodules)


def validate_checkout(checkout: Path) -> List[Tuple[str, str]]:
    if run_git(checkout, ["rev-parse", "HEAD"]).strip() != REVISION:
        raise SnapshotError("checkout HEAD does not match the Firefox-pinned revision")
    status = run_git(checkout, ["status", "--porcelain=v1", "--untracked-files=all"])
    if status.strip():
        raise SnapshotError("checkout or one of its gitlinks is not clean:\n{}".format(status.rstrip()))
    submodules = parse_submodule_status(run_git(checkout, ["submodule", "status", "--recursive"]))
    if not submodules:
        raise SnapshotError("recursive checkout contains no initialized submodules")
    return submodules


def submodule_records(checkout: Path, statuses: Iterable[Tuple[str, str]]) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    for relative, revision in statuses:
        submodule = checkout / relative
        remote = run_git(submodule, ["config", "--get", "remote.origin.url"]).strip()
        records.append(
            {
                "path": relative,
                "url": normalize_repository_url(remote),
                "revision": revision,
                "treeSha256": source_tree_sha256(submodule),
            }
        )
    return records


def classify_license(path: str, content: bytes) -> str:
    text = content.decode("utf-8", errors="ignore").lower()
    name = Path(path).name.lower()
    if "mozilla public license version 2.0" in text or name == "copying.mpl2":
        return "MPL-2.0"
    if "apache license" in text and "version 2.0" in text:
        return "Apache-2.0"
    if "gnu lesser general public license" in text:
        return "LGPL-3.0-only" if "version 3" in text or ".lesser.3" in name else "LGPL-2.1-only"
    if "gnu general public license" in text:
        return "GPL-3.0-only" if "version 3" in text or name.endswith(".3") else "GPL-2.0-only"
    if "boost software license" in text or "license_1_0" in name:
        return "BSL-1.0"
    if "provided 'as-is', without any express or implied" in text and "alter it and redistribute it freely" in text:
        return "Zlib"
    if "the unlicense" in text:
        return "Unlicense"
    if "permission is hereby granted, free of charge" in text:
        return "MIT"
    if "redistribution and use in source and binary forms" in text:
        return "BSD-3-Clause" if "neither the name" in text else "BSD-2-Clause"
    if "isc license" in text:
        return "ISC"
    if "zlib license" in text:
        return "Zlib"
    if name == "copying.readme" and "eigen is primarily mpl2 licensed" in text:
        return "MPL-2.0 AND BSD-3-Clause AND LGPL-2.1-or-later"
    return "NOASSERTION"


def license_records(root: Path) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    for relative, path in canonical_entries(root):
        if not path.is_file() or not LICENSE_NAMES.fullmatch(path.name):
            continue
        content = path.read_bytes()
        records.append(
            {
                "path": relative,
                "spdx": classify_license(relative, content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    if not records or not any(record["path"] == "LICENSE" for record in records):
        raise SnapshotError("source tree does not contain its root LICENSE file")
    return records


def verify_firefox_pin(pin_file: Path) -> str:
    if not pin_file.is_file():
        raise SnapshotError("Firefox pin metadata file is missing: {}".format(pin_file))
    content = pin_file.read_bytes()
    text = content.decode("utf-8")
    expectations = (
        ("url", "https://github.com/mozilla/translations.git"),
        ("release", BERGAMOT_VERSION),
        ("revision", REVISION),
        ("license", UPSTREAM_LICENSE),
    )
    for key, value in expectations:
        pattern = re.compile(r"^\s*{}:\s*{}\s*$".format(re.escape(key), re.escape(value)), re.MULTILINE)
        if not pattern.search(text):
            raise SnapshotError("Firefox pin metadata does not contain {}: {}".format(key, value))
    return hashlib.sha256(content).hexdigest()


def copy_source_tree(checkout: Path, destination: Path) -> None:
    if destination.exists():
        raise SnapshotError("snapshot destination already exists: {}".format(destination))

    def ignore_git(_directory: str, names: List[str]) -> List[str]:
        return [".git"] if ".git" in names else []

    shutil.copytree(checkout, destination, symlinks=True, ignore=ignore_git, copy_function=shutil.copy2)
    git_entries = [path for path in destination.rglob(".git")]
    if git_entries:
        raise SnapshotError("Git administrative data survived snapshot creation")


def prepare_snapshot_worktree(metadata_root: Path) -> None:
    repository_root = Path(run_git(metadata_root, ["rev-parse", "--show-toplevel"]).strip())
    git_attributes_value = run_git(repository_root, ["rev-parse", "--git-path", "info/attributes"]).strip()
    git_attributes = Path(git_attributes_value)
    if not git_attributes.is_absolute():
        git_attributes = repository_root / git_attributes
    git_attributes.parent.mkdir(parents=True, exist_ok=True)
    existing = git_attributes.read_text(encoding="utf-8") if git_attributes.exists() else ""
    managed_pattern = re.compile(
        re.escape(ATTRIBUTES_BEGIN) + r".*?" + re.escape(ATTRIBUTES_END) + r"\n?",
        re.DOTALL,
    )
    unmanaged = managed_pattern.sub("", existing).rstrip()
    managed = "{}\nnative/upstream/mozilla-translations/** -text\n{}\n".format(
        ATTRIBUTES_BEGIN,
        ATTRIBUTES_END,
    )
    content = (unmanaged + "\n\n" if unmanaged else "") + managed
    if existing != content:
        git_attributes.write_text(content, encoding="utf-8")
    snapshot = metadata_root / "upstream" / "mozilla-translations"
    relative_snapshot = snapshot.resolve().relative_to(repository_root.resolve()).as_posix()
    tracked = index_entries(repository_root, snapshot)
    if not tracked:
        raise SnapshotError("immutable snapshot must be staged before worktree preparation")
    checkout_input = b"".join(
        (relative_snapshot + "/" + relative).encode("utf-8") + b"\x00"
        for relative, _mode, _repository_path in tracked
    )
    checkout = subprocess.run(
        ["git", "-C", str(repository_root), "checkout-index", "-f", "-z", "--stdin"],
        input=checkout_input,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if checkout.returncode != 0:
        raise SnapshotError(
            "git checkout-index failed while preparing upstream bytes: {}".format(
                checkout.stderr.decode("utf-8", errors="replace").strip()
            )
        )


def prepare_snapshot(arguments: argparse.Namespace) -> None:
    metadata_root = arguments.metadata_root.resolve()
    prepare_snapshot_worktree(metadata_root)
    print("prepared immutable upstream Git attribute boundary")


def stage_snapshot(arguments: argparse.Namespace) -> None:
    """Stage the generated tree byte-for-byte without Git clean filters."""
    metadata_root = arguments.metadata_root.resolve()
    snapshot = metadata_root / "upstream" / "mozilla-translations"
    repository_root = Path(run_git(metadata_root, ["rev-parse", "--show-toplevel"]).strip())
    relative_root = snapshot.relative_to(repository_root).as_posix()
    records: List[Tuple[str, str]] = []
    for relative, source in canonical_entries(snapshot):
        metadata = source.lstat()
        if stat.S_ISDIR(metadata.st_mode):
            continue
        repository_path = relative_root + "/" + relative
        if "\n" in repository_path or "\t" in repository_path or "\x00" in repository_path:
            raise SnapshotError("snapshot path cannot be represented safely in a batch Git index update")
        if stat.S_ISLNK(metadata.st_mode):
            content = os.readlink(source).encode("utf-8")
            hashed_link = subprocess.run(
                ["git", "-C", str(repository_root), "hash-object", "-w", "--stdin"],
                input=content,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if hashed_link.returncode != 0:
                raise SnapshotError(
                    "git hash-object failed for symlink {}: {}".format(
                        relative,
                        hashed_link.stderr.decode("utf-8", errors="replace").strip(),
                    )
                )
            object_id = hashed_link.stdout.decode("ascii").strip()
            records.append(("120000", object_id + "\t" + repository_path))
        elif stat.S_ISREG(metadata.st_mode):
            mode = "100755" if metadata.st_mode & stat.S_IXUSR else "100644"
            records.append((mode, repository_path))
        else:
            raise SnapshotError("unsupported filesystem entry while staging: {}".format(source))

    regular = [(mode, repository_path) for mode, repository_path in records if "\t" not in repository_path]
    if regular:
        input_paths = "".join(repository_path + "\n" for _, repository_path in regular).encode("utf-8")
        hashed = subprocess.run(
            ["git", "-C", str(repository_root), "hash-object", "-w", "--no-filters", "--stdin-paths"],
            input=input_paths,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if hashed.returncode != 0:
            raise SnapshotError(
                "git hash-object failed: {}".format(hashed.stderr.decode("utf-8", errors="replace").strip())
            )
        object_ids = hashed.stdout.decode("ascii").splitlines()
        if len(object_ids) != len(regular) or any(not GIT_SHA_RE.fullmatch(value) for value in object_ids):
            raise SnapshotError("git hash-object returned an invalid object list")
        regular_records = iter(zip(regular, object_ids))
        staged_records: List[Tuple[str, str]] = []
        for mode, value in records:
            if "\t" in value:
                object_id, repository_path = value.split("\t", 1)
                staged_records.append((mode, object_id + "\t" + repository_path))
            else:
                (regular_mode, repository_path), object_id = next(regular_records)
                if mode != regular_mode or value != repository_path:
                    raise SnapshotError("internal staging order mismatch")
                staged_records.append((mode, object_id + "\t" + repository_path))
        records = staged_records

    batch = b"".join((mode + " " + value).encode("utf-8") + b"\x00" for mode, value in records)
    updated = subprocess.run(
        ["git", "-C", str(repository_root), "update-index", "--add", "-z", "--index-info"],
        input=batch,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if updated.returncode != 0:
        raise SnapshotError(
            "git update-index failed: {}".format(updated.stderr.decode("utf-8", errors="replace").strip())
        )
    prepare_snapshot_worktree(metadata_root)
    actual_digest = source_tree_sha256_from_index(repository_root, snapshot)
    expected_digest = json.loads((metadata_root / "UPSTREAM_LOCK.json").read_text(encoding="utf-8"))["sourceTreeSha256"]
    if actual_digest != expected_digest:
        raise SnapshotError("byte-exact staged snapshot differs from UPSTREAM_LOCK.json")
    print("staged byte-exact immutable snapshot")
    print("sourceTreeSha256={}".format(actual_digest))
    print("entries={}".format(len(records)))


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_sha(label: str, value: object, length: int) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{{{}}}".format(length), value):
        raise SnapshotError("{} is not a lowercase {}-character digest".format(label, length))
    return value


def validate_lock_shape(lock: object) -> Dict[str, object]:
    if not isinstance(lock, dict):
        raise SnapshotError("UPSTREAM_LOCK.json must contain an object")
    required = {
        "schemaVersion",
        "repository",
        "revision",
        "bergamotVersion",
        "sourceTreeSha256",
        "generatedAt",
        "submodules",
        "licenses",
    }
    allowed = required | {"generatorRevision"}
    if set(lock) != required and set(lock) != allowed:
        raise SnapshotError("UPSTREAM_LOCK.json keys do not match the schema contract")
    if lock["schemaVersion"] != 1 or lock["repository"] != REPOSITORY:
        raise SnapshotError("UPSTREAM_LOCK.json repository identity is invalid")
    if lock["revision"] != REVISION or lock["bergamotVersion"] != BERGAMOT_VERSION:
        raise SnapshotError("UPSTREAM_LOCK.json does not match the locked Firefox pin")
    validate_sha("sourceTreeSha256", lock["sourceTreeSha256"], 64)
    if "generatorRevision" in lock:
        validate_sha("generatorRevision", lock["generatorRevision"], 40)
    if not isinstance(lock["generatedAt"], str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", lock["generatedAt"]
    ):
        raise SnapshotError("generatedAt must be a UTC RFC 3339 timestamp with whole seconds")
    if not isinstance(lock["submodules"], list) or not lock["submodules"]:
        raise SnapshotError("UPSTREAM_LOCK.json must contain recursive submodules")
    if not isinstance(lock["licenses"], list) or not lock["licenses"]:
        raise SnapshotError("UPSTREAM_LOCK.json must contain license records")
    return lock


def create_snapshot(arguments: argparse.Namespace) -> None:
    checkout = arguments.checkout.resolve()
    metadata_root = arguments.metadata_root.resolve()
    destination = metadata_root / "upstream" / "mozilla-translations"
    statuses = validate_checkout(checkout)
    pin_sha256 = verify_firefox_pin(arguments.firefox_pin_file.resolve())
    records = submodule_records(checkout, statuses)
    checkout_sha256 = source_tree_sha256(checkout)
    licenses = license_records(checkout)
    metadata_root.mkdir(parents=True, exist_ok=True)
    staging_parent = destination.parent
    staging_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".mozilla-translations-", dir=str(staging_parent)))
    staged_snapshot = staging / "snapshot"
    try:
        copy_source_tree(checkout, staged_snapshot)
        staged_sha256 = source_tree_sha256(staged_snapshot)
        if staged_sha256 != checkout_sha256:
            raise SnapshotError("snapshot bytes differ from the clean recursive checkout")
        if destination.exists():
            raise SnapshotError("refusing to replace existing immutable snapshot: {}".format(destination))
        staged_snapshot.rename(destination)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    lock = {
        "schemaVersion": 1,
        "repository": REPOSITORY,
        "revision": REVISION,
        "bergamotVersion": BERGAMOT_VERSION,
        "sourceTreeSha256": checkout_sha256,
        "generatedAt": arguments.generated_at,
        "submodules": records,
        "licenses": licenses,
    }
    summary = {
        "schemaVersion": 1,
        "repository": REPOSITORY_NAME,
        "repositoryUrl": REPOSITORY,
        "revision": REVISION,
        "bergamotVersion": BERGAMOT_VERSION,
        "license": UPSTREAM_LICENSE,
        "sourceTreeSha256": checkout_sha256,
        "firefoxPin": {
            "repository": FIREFOX_REPOSITORY_NAME,
            "repositoryUrl": FIREFOX_REPOSITORY,
            "revision": FIREFOX_PIN_REVISION,
            "path": FIREFOX_PIN_PATH,
            "sha256": pin_sha256,
        },
        "snapshot": {
            "format": ARCHIVE_FORMAT,
            "generatedAt": arguments.generated_at,
            "runId": arguments.run_id,
            "submoduleCount": len(records),
            "licenseFileCount": len(licenses),
        },
    }
    write_json(metadata_root / "UPSTREAM_LOCK.json", lock)
    write_json(metadata_root / "UPSTREAM.json", summary)
    (metadata_root / "SOURCE_TREE.sha256").write_text(
        "{}  upstream/mozilla-translations\n".format(checkout_sha256), encoding="utf-8"
    )
    print("created {} from {}".format(destination, REVISION))
    print("sourceTreeSha256={}".format(checkout_sha256))
    print("submodules={}".format(len(records)))
    print("licenses={}".format(len(licenses)))


def verify_snapshot(arguments: argparse.Namespace) -> None:
    metadata_root = arguments.metadata_root.resolve()
    snapshot = metadata_root / "upstream" / "mozilla-translations"
    lock = validate_lock_shape(json.loads((metadata_root / "UPSTREAM_LOCK.json").read_text(encoding="utf-8")))
    summary = json.loads((metadata_root / "UPSTREAM.json").read_text(encoding="utf-8"))
    digest_line = (metadata_root / "SOURCE_TREE.sha256").read_text(encoding="utf-8")
    expected_digest = str(lock["sourceTreeSha256"])
    if digest_line != "{}  upstream/mozilla-translations\n".format(expected_digest):
        raise SnapshotError("SOURCE_TREE.sha256 does not match UPSTREAM_LOCK.json")
    repository_root_text = run_git(metadata_root, ["rev-parse", "--show-toplevel"]).strip()
    repository_root = Path(repository_root_text)
    tracked_snapshot = bool(index_entries(repository_root, snapshot))
    if tracked_snapshot:
        prepare_snapshot_worktree(metadata_root)
    actual_digest = (
        source_tree_sha256_from_index(repository_root, snapshot)
        if tracked_snapshot
        else source_tree_sha256(snapshot)
    )
    if actual_digest != expected_digest:
        raise SnapshotError(
            "immutable snapshot digest mismatch: expected {}, got {}".format(expected_digest, actual_digest)
        )
    if any(path.name == ".git" for path in snapshot.rglob(".git")):
        raise SnapshotError("immutable snapshot contains Git administrative data")

    submodules = lock["submodules"]
    assert isinstance(submodules, list)
    paths: List[str] = []
    for index, raw_record in enumerate(submodules):
        if not isinstance(raw_record, dict) or set(raw_record) != {"path", "url", "revision", "treeSha256"}:
            raise SnapshotError("submodule record {} does not match the schema contract".format(index))
        relative = safe_relative_path(str(raw_record["path"]))
        paths.append(relative)
        normalize_repository_url(str(raw_record["url"]))
        validate_sha("submodule revision", raw_record["revision"], 40)
        expected_tree = validate_sha("submodule treeSha256", raw_record["treeSha256"], 64)
        actual_tree = (
            source_tree_sha256_from_index(repository_root, snapshot / relative)
            if tracked_snapshot
            else source_tree_sha256(snapshot / relative)
        )
        if actual_tree != expected_tree:
            raise SnapshotError("submodule tree digest mismatch: {}".format(relative))
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise SnapshotError("submodule lock paths must be sorted and unique")

    licenses = lock["licenses"]
    assert isinstance(licenses, list)
    license_paths: List[str] = []
    for index, raw_record in enumerate(licenses):
        if not isinstance(raw_record, dict) or set(raw_record) != {"path", "spdx", "sha256"}:
            raise SnapshotError("license record {} does not match the schema contract".format(index))
        relative = safe_relative_path(str(raw_record["path"]))
        license_paths.append(relative)
        expected_file = validate_sha("license sha256", raw_record["sha256"], 64)
        if not isinstance(raw_record["spdx"], str) or not raw_record["spdx"]:
            raise SnapshotError("license SPDX identity is empty: {}".format(relative))
        actual_file = (
            file_sha256_from_index(repository_root, snapshot / relative)
            if tracked_snapshot
            else file_sha256(snapshot / relative)
        )
        if actual_file != expected_file:
            raise SnapshotError("license file digest mismatch: {}".format(relative))
    if license_paths != sorted(license_paths) or len(license_paths) != len(set(license_paths)):
        raise SnapshotError("license paths must be sorted and unique")
    discovered_licenses = [record["path"] for record in license_records(snapshot)]
    if license_paths != discovered_licenses:
        raise SnapshotError("license inventory is not exhaustive")

    expected_summary = {
        "schemaVersion": 1,
        "repository": REPOSITORY_NAME,
        "repositoryUrl": REPOSITORY,
        "revision": REVISION,
        "bergamotVersion": BERGAMOT_VERSION,
        "license": UPSTREAM_LICENSE,
        "sourceTreeSha256": expected_digest,
    }
    for key, value in expected_summary.items():
        if summary.get(key) != value:
            raise SnapshotError("UPSTREAM.json {} does not match the lock".format(key))
    firefox_pin = summary.get("firefoxPin")
    if not isinstance(firefox_pin, dict) or firefox_pin.get("revision") != FIREFOX_PIN_REVISION:
        raise SnapshotError("UPSTREAM.json Firefox pin source revision is invalid")
    if firefox_pin.get("path") != FIREFOX_PIN_PATH or not SHA256_RE.fullmatch(str(firefox_pin.get("sha256", ""))):
        raise SnapshotError("UPSTREAM.json Firefox pin metadata identity is invalid")
    snapshot_metadata = summary.get("snapshot")
    if not isinstance(snapshot_metadata, dict) or snapshot_metadata.get("format") != ARCHIVE_FORMAT:
        raise SnapshotError("UPSTREAM.json snapshot format is invalid")
    if snapshot_metadata.get("submoduleCount") != len(submodules):
        raise SnapshotError("UPSTREAM.json submodule count is invalid")
    if snapshot_metadata.get("licenseFileCount") != len(licenses):
        raise SnapshotError("UPSTREAM.json license count is invalid")

    if arguments.checkout:
        checkout = arguments.checkout.resolve()
        statuses = validate_checkout(checkout)
        checkout_records = submodule_records(checkout, statuses)
        if checkout_records != submodules:
            raise SnapshotError("clean checkout recursive lock differs from UPSTREAM_LOCK.json")
        if source_tree_sha256(checkout) != expected_digest:
            raise SnapshotError("clean checkout source digest differs from immutable snapshot")

    print("verified immutable Firefox-pinned snapshot")
    print("revision={}".format(REVISION))
    print("sourceTreeSha256={}".format(expected_digest))
    print("submodules={}".format(len(submodules)))
    print("licenses={}".format(len(licenses)))


def parser() -> argparse.ArgumentParser:
    command_parser = argparse.ArgumentParser(description=__doc__)
    subcommands = command_parser.add_subparsers(dest="command", required=True)

    create = subcommands.add_parser("create", help="create the initial immutable snapshot")
    create.add_argument("--checkout", required=True, type=Path)
    create.add_argument("--firefox-pin-file", required=True, type=Path)
    create.add_argument("--metadata-root", type=Path, default=Path("native"))
    create.add_argument("--generated-at", required=True)
    create.add_argument("--run-id", required=True)
    create.set_defaults(handler=create_snapshot)

    verify = subcommands.add_parser("verify", help="verify committed metadata and source bytes")
    verify.add_argument("--metadata-root", type=Path, default=Path("native"))
    verify.add_argument("--checkout", type=Path)
    verify.set_defaults(handler=verify_snapshot)

    stage = subcommands.add_parser("stage", help="stage snapshot bytes without Git line-ending filters")
    stage.add_argument("--metadata-root", type=Path, default=Path("native"))
    stage.set_defaults(handler=stage_snapshot)

    prepare = subcommands.add_parser("prepare", help="restore the flattened submodule attribute boundary")
    prepare.add_argument("--metadata-root", type=Path, default=Path("native"))
    prepare.set_defaults(handler=prepare_snapshot)
    return command_parser


def main(arguments: Optional[Sequence[str]] = None) -> int:
    try:
        parsed = parser().parse_args(arguments)
        parsed.handler(parsed)
        return 0
    except (OSError, ValueError, json.JSONDecodeError, SnapshotError) as error:
        print("upstream snapshot error: {}".format(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
