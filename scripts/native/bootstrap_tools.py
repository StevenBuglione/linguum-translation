#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Install hash-locked native build tools into ignored build storage."""

import argparse
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, Tuple


ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = ROOT / "toolchains" / "native-tools.lock.json"
DEFAULT_ROOT = ROOT / "build" / "toolchains" / "locked"


class ToolBootstrapError(RuntimeError):
    """The locked native toolchain could not be materialized safely."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def platform_key() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "darwin":
        return "darwin-universal"
    if system == "linux" and machine in {"aarch64", "arm64"}:
        return "linux-aarch64"
    if system == "linux" and machine in {"x86_64", "amd64"}:
        return "linux-x86_64"
    if system == "windows" and machine in {"x86_64", "amd64"}:
        return "windows-x86_64"
    raise ToolBootstrapError("unsupported native tool host: {} {}".format(system, machine))


def load_lock(path: Path = LOCK_PATH) -> Dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schemaVersion") != 1 or not isinstance(document.get("tools"), dict):
        raise ToolBootstrapError("unsupported native tool lock schema")
    return document


def validate_archive_member(name: str, destination: Path) -> None:
    normalized = name.replace("\\", "/")
    member = Path(normalized)
    if not normalized or member.is_absolute() or ".." in member.parts:
        raise ToolBootstrapError("unsafe archive member: {!r}".format(name))
    resolved = (destination / member).resolve()
    try:
        resolved.relative_to(destination.resolve())
    except ValueError as error:
        raise ToolBootstrapError("archive member escapes destination: {!r}".format(name)) from error


def validate_tar_link(member: tarfile.TarInfo, destination: Path) -> None:
    normalized = member.linkname.replace("\\", "/")
    link = Path(normalized)
    if not normalized or link.is_absolute():
        raise ToolBootstrapError("unsafe archive link: {!r}".format(member.linkname))
    base = destination if member.islnk() else (destination / Path(member.name)).parent
    resolved = (base / link).resolve()
    try:
        resolved.relative_to(destination.resolve())
    except ValueError as error:
        raise ToolBootstrapError("archive link escapes destination: {!r}".format(member.linkname)) from error


def extract_archive(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    if archive.suffix == ".zip":
        with zipfile.ZipFile(str(archive)) as source:
            for member in source.infolist():
                validate_archive_member(member.filename, destination)
            source.extractall(str(destination))
        return
    if archive.name.endswith(".tar.gz"):
        with tarfile.open(str(archive), mode="r:gz") as source:
            for member in source.getmembers():
                validate_archive_member(member.name, destination)
                if member.issym() or member.islnk():
                    validate_tar_link(member, destination)
            source.extractall(str(destination))
        return
    raise ToolBootstrapError("unsupported tool archive: {}".format(archive.name))


def download(url: str, destination: Path, expected_sha256: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and sha256(destination) == expected_sha256:
        return
    partial = destination.with_name(destination.name + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "Linguum-Translation-Tool-Bootstrap/1"})
    with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as output:
        shutil.copyfileobj(response, output)
    actual = sha256(partial)
    if actual != expected_sha256:
        partial.unlink(missing_ok=True)
        raise ToolBootstrapError(
            "tool archive SHA-256 mismatch for {}: expected {}, got {}".format(url, expected_sha256, actual)
        )
    os.replace(str(partial), str(destination))


def checked_tool_version(executable: Path, expected: str) -> bool:
    if not executable.is_file():
        return False
    try:
        completed = subprocess.run(
            [str(executable), "--version"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except OSError:
        return False
    return completed.returncode == 0 and expected in completed.stdout.splitlines()[0]


def bootstrap_tool(name: str, document: Dict[str, object], destination: Path, host: str) -> Path:
    tools = document["tools"]
    tool = tools[name]
    version = str(tool["version"])
    asset = tool["assets"].get(host)
    if not asset:
        raise ToolBootstrapError("{} {} has no asset for {}".format(name, version, host))
    install_root = destination / "{}-{}-{}".format(name, version, host)
    executable = install_root / asset["executable"]
    if checked_tool_version(executable, version):
        return executable
    archive = destination / "downloads" / asset["archive"]
    download(str(asset["url"]), archive, str(asset["sha256"]))
    if install_root.exists():
        shutil.rmtree(str(install_root))
    extract_archive(archive, install_root)
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    if not checked_tool_version(executable, version):
        raise ToolBootstrapError("{} executable failed version validation: {}".format(name, executable))
    return executable


def bootstrap(destination: Path = DEFAULT_ROOT) -> Tuple[Path, Path]:
    document = load_lock()
    host = platform_key()
    cmake = bootstrap_tool("cmake", document, destination, host)
    ninja = bootstrap_tool("ninja", document, destination, host)
    return cmake, ninja


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--json", action="store_true", help="print machine-readable tool paths")
    arguments = parser.parse_args()
    try:
        cmake, ninja = bootstrap(arguments.destination.resolve())
    except (OSError, ValueError, ToolBootstrapError, json.JSONDecodeError) as error:
        print("native tool bootstrap failed: {}".format(error), file=sys.stderr)
        return 1
    if arguments.json:
        print(json.dumps({"cmake": str(cmake), "ninja": str(ninja)}, sort_keys=True))
    else:
        print("cmake={}".format(cmake))
        print("ninja={}".format(ninja))
    return 0


if __name__ == "__main__":
    sys.exit(main())
