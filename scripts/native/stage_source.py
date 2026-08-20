#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Stage the immutable upstream tree and apply Linguum's external patch queue."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from pathlib import PurePosixPath
from typing import Dict, Iterable, List, Sequence


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "native" / "upstream" / "mozilla-translations"
PATCHES = ROOT / "native" / "patches"
DEFAULT_DESTINATION = ROOT / "build" / "native-source" / "mozilla-translations"
SOURCE_DIGEST = ROOT / "native" / "SOURCE_TREE.sha256"


class SourceStageError(RuntimeError):
    """The immutable upstream source could not be staged safely."""


DIFF_HEADER = re.compile(rb"^diff --git a/([^\r\n ]+) b/([^\r\n ]+)$")


def bytes_sha256(chunks: Iterable[bytes]) -> str:
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk)
    return digest.hexdigest()


def patch_identity(patches: Sequence[Path]) -> str:
    return bytes_sha256(
        part
        for patch in patches
        for part in (patch.name.encode("utf-8") + b"\0", patch.read_bytes(), b"\0")
    )


def expected_identity(patches: Sequence[Path]) -> Dict[str, str]:
    source_digest = SOURCE_DIGEST.read_text(encoding="utf-8").strip()
    return {"patchesSha256": patch_identity(patches), "sourceTreeSha256": source_digest}


def affected_paths(patch: Path) -> List[PurePosixPath]:
    """Return validated in-place file targets declared by a unified patch."""
    paths = []
    for line in patch.read_bytes().splitlines():
        match = DIFF_HEADER.fullmatch(line)
        if match is None:
            continue
        old_path, new_path = (part.decode("utf-8") for part in match.groups())
        path = PurePosixPath(old_path)
        unsafe_part = any(part in ("", ".", "..") for part in path.parts)
        if old_path != new_path or path.is_absolute() or unsafe_part:
            raise SourceStageError(
                "external patches may only modify safe in-place paths: {}".format(
                    line.decode("utf-8")
                )
            )
        paths.append(path)
    if not paths:
        raise SourceStageError(
            "patch does not declare an in-place file modification: {}".format(patch.name)
        )
    if len(paths) != len(set(paths)):
        raise SourceStageError("patch declares a target more than once: {}".format(patch.name))
    return paths


def crlf_only(path: Path) -> bool:
    payload = path.read_bytes()
    return b"\r\n" in payload and b"\n" not in payload.replace(b"\r\n", b"")


def preserve_crlf_targets(destination: Path, patch: Path) -> List[Path]:
    """Record patch targets whose immutable input uses CRLF exclusively."""
    targets = []
    for relative in affected_paths(patch):
        target = destination.joinpath(*relative.parts)
        if target.is_symlink() or not target.is_file():
            raise SourceStageError("patch target is not a regular staged file: {}".format(relative))
        try:
            target.resolve().relative_to(destination)
        except ValueError as error:
            raise SourceStageError("patch target escapes the staged source: {}".format(relative)) from error
        if crlf_only(target):
            targets.append(target)
    return targets


def restore_crlf(targets: Sequence[Path]) -> None:
    """Undo git-apply's Unix newline normalization for known CRLF-only inputs."""
    for target in targets:
        payload = target.read_bytes().replace(b"\r\n", b"\n")
        if b"\r" in payload:
            raise SourceStageError("patched CRLF file contains a stray carriage return: {}".format(target))
        target.write_bytes(payload.replace(b"\n", b"\r\n"))


def safe_build_destination(destination: Path) -> Path:
    resolved = destination.resolve()
    build_root = (ROOT / "build").resolve()
    try:
        resolved.relative_to(build_root)
    except ValueError as error:
        raise SourceStageError("staged source destination must be under {}".format(build_root)) from error
    if resolved == build_root:
        raise SourceStageError("staged source destination cannot be the build root")
    return resolved


def run_git_apply(destination: Path, patch: Path, check_only: bool) -> None:
    relative_destination = destination.relative_to(ROOT.resolve())
    command = [
        "git",
        "apply",
        "--unidiff-zero",
        "--directory={}".format(relative_destination),
    ]
    if check_only:
        command.append("--check")
    command.append(str(patch))
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise SourceStageError("git apply failed for {}: {}".format(patch.name, detail))


def stage(destination: Path = DEFAULT_DESTINATION, force: bool = False) -> Path:
    destination = safe_build_destination(destination)
    patches = sorted(PATCHES.glob("*.patch"))
    if not patches:
        raise SourceStageError("native external patch queue is empty")
    identity = expected_identity(patches)
    marker = destination.parent / ".linguum-stage.json"
    if not force and destination.is_dir() and marker.is_file():
        try:
            if json.loads(marker.read_text(encoding="utf-8")) == identity:
                return destination
        except json.JSONDecodeError:
            pass
    if destination.exists():
        shutil.rmtree(str(destination))
    marker.unlink(missing_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(str(SOURCE), str(destination), symlinks=True, copy_function=shutil.copy2)
    for patch in patches:
        crlf_targets = preserve_crlf_targets(destination, patch)
        run_git_apply(destination, patch, check_only=True)
        run_git_apply(destination, patch, check_only=False)
        restore_crlf(crlf_targets)
    marker.write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument("--clean", action="store_true", help="replace any existing staged build tree")
    arguments = parser.parse_args()
    try:
        destination = stage(arguments.destination, force=arguments.clean)
    except (OSError, SourceStageError, subprocess.SubprocessError) as error:
        print("native source staging failed: {}".format(error), file=sys.stderr)
        return 1
    print(destination)
    return 0


if __name__ == "__main__":
    sys.exit(main())
