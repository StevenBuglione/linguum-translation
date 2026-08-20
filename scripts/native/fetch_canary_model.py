#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Fetch the immutable Mozilla Spanish-to-English feasibility model."""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import urllib.request
from pathlib import Path
from typing import Dict


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "testing" / "native" / "fixtures" / "es-en-v2.0.json"
DEFAULT_DESTINATION = ROOT / "build" / "models" / "es-en-v2.0"


class ModelFetchError(RuntimeError):
    """The pinned canary model could not be materialized safely."""


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_file(path: Path, artifact: Dict[str, object]) -> bool:
    return (
        path.is_file()
        and not path.is_symlink()
        and path.stat().st_size == int(artifact["size"])
        and file_sha256(path) == artifact["sha256"]
    )


def fetch_artifact(artifact: Dict[str, object], destination: Path) -> None:
    target = destination / str(artifact["fileName"])
    if validate_file(target, artifact):
        return
    destination.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    partial.unlink(missing_ok=True)
    request = urllib.request.Request(
        str(artifact["url"]),
        headers={"User-Agent": "Linguum-Translation-Canary/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as output:
            shutil.copyfileobj(response, output)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    if not validate_file(partial, artifact):
        actual_size = partial.stat().st_size if partial.exists() else -1
        actual_hash = file_sha256(partial) if partial.exists() else "missing"
        partial.unlink(missing_ok=True)
        raise ModelFetchError(
            "model artifact identity mismatch for {}: size={}, sha256={}".format(
                artifact["fileName"], actual_size, actual_hash
            )
        )
    os.replace(str(partial), str(target))


def fetch(destination: Path = DEFAULT_DESTINATION, manifest_path: Path = MANIFEST) -> Path:
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    if document.get("schemaVersion") != 1 or document.get("languagePair") != "es-en":
        raise ModelFetchError("unsupported canary model manifest")
    artifacts = document.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 3 or not all(
        isinstance(item, dict) for item in artifacts
    ) or {item.get("role") for item in artifacts} != {
        "model",
        "shortlist",
        "vocabulary",
    }:
        raise ModelFetchError("canary model manifest must contain model, shortlist, and vocabulary")
    file_names = [str(item.get("fileName", "")) for item in artifacts]
    if len(set(file_names)) != len(file_names):
        raise ModelFetchError("canary model artifact file names must be unique")
    for artifact in artifacts:
        file_name = str(artifact.get("fileName", ""))
        if not file_name or Path(file_name).name != file_name:
            raise ModelFetchError("unsafe model artifact file name: {!r}".format(file_name))
        size = artifact.get("size")
        sha256 = artifact.get("sha256")
        url = artifact.get("url")
        if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
            raise ModelFetchError("invalid model artifact size for {}".format(file_name))
        if not isinstance(sha256, str) or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
            raise ModelFetchError("invalid model artifact SHA-256 for {}".format(file_name))
        if not isinstance(url, str) or not url:
            raise ModelFetchError("invalid model artifact URL for {}".format(file_name))
    for artifact in artifacts:
        fetch_artifact(artifact, destination)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    arguments = parser.parse_args()
    try:
        destination = fetch(arguments.destination.resolve(), arguments.manifest.resolve())
    except (OSError, ValueError, ModelFetchError, json.JSONDecodeError) as error:
        print("canary model fetch failed: {}".format(error), file=sys.stderr)
        return 1
    print(destination)
    return 0


if __name__ == "__main__":
    sys.exit(main())
