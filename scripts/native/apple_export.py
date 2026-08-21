#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build, inspect, package, and execute the locked M1 Apple export proof."""

import argparse
import hashlib
import json
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

import ios_profiles


ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = ROOT / "toolchains" / "apple-export.lock.json"
FIXTURE = ROOT / "testing" / "platform-smoke" / "apple-export-canary"
KOTLIN_CORE = FIXTURE / "kotlin-core"
SWIFT_PACKAGE = FIXTURE / "swift-package"
SWIFT_API_SNAPSHOT = FIXTURE / "swift-api.txt"
HEADER_DIRECTORY = ROOT / "native" / "abi" / "include"
DEFAULT_OUTPUT = ROOT / "build" / "native-packages" / "apple-export"
PROFILE_IDS = ios_profiles.PROFILE_IDS
CORE_FRAMEWORK = "LinguumTranslationCore"
XCFRAMEWORK_NAME = "LinguumTranslation.xcframework"
XCFRAMEWORK_ZIP = "LinguumTranslation.xcframework.zip"
SWIFT_CHECKSUM_COMMAND = "swift package compute-checksum"
EXECUTION_PROFILES = {
    "simulator-arm64": "ios-simulator-arm64",
    "simulator-x64": "ios-simulator-x64",
    "physical-arm64": "ios-arm64",
}
SWIFT_API_TOKENS = {
    "LanguagePair": "public struct LanguagePair",
    "LanguagePair.init(source:target:)": "public init(source: String, target: String) throws",
    "LinguumTranslationConfiguration": "public struct LinguumTranslationConfiguration",
    "LinguumTranslationConfiguration.init(modelDirectory:configurationPath:)": (
        "public init(modelDirectory: String, configurationPath: String)"
    ),
    "LinguumTranslationError": "public enum LinguumTranslationError",
    "LinguumTranslationService": "public final class LinguumTranslationService",
    "LinguumTranslationService.close()": "public func close()",
    "LinguumTranslationService.create(configuration:)": "public static func create(",
    "LinguumTranslationService.translator(pair:)": "public func translator(pair: LanguagePair)",
    "TranslationResult": "public struct TranslationResult",
    "TranslationResult.init(text:)": "public init(text: String)",
    "Translator": "public final class Translator",
    "Translator.translate(text:)": "public func translate(text: String) async throws",
}


class AppleExportError(RuntimeError):
    """An Apple export build or evidence invariant failed."""


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_lock(path: Path = LOCK_PATH) -> Dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "schemaVersion": 1,
        "deploymentTarget": "15.0",
        "kotlinVersion": "2.4.10",
        "swiftToolsVersion": "6.0",
        "swiftLanguageMode": "5",
        "coreFramework": CORE_FRAMEWORK,
        "swiftModule": "LinguumTranslation",
        "distributionXcframework": XCFRAMEWORK_NAME,
        "profiles": list(PROFILE_IDS),
        "physicalArm64RunnerLabels": [
            "self-hosted",
            "macos",
            "arm64",
            "ios-device",
        ],
    }
    if document != expected:
        raise AppleExportError("Apple export lock differs from the M1-WP08 contract")
    ios_lock = ios_profiles.load_lock()
    if (
        ios_lock["deploymentTarget"] != document["deploymentTarget"]
        or ios_lock["kotlinVersion"] != document["kotlinVersion"]
        or ios_lock["physicalArm64RunnerLabels"]
        != document["physicalArm64RunnerLabels"]
    ):
        raise AppleExportError("Apple export and iOS native profile locks diverge")
    return document


def safe_output_directory(path: Path) -> Path:
    resolved = path.resolve()
    build_root = (ROOT / "build").resolve()
    try:
        resolved.relative_to(build_root)
    except ValueError as error:
        raise AppleExportError("Apple export output must be below build") from error
    if resolved == build_root:
        raise AppleExportError("Apple export output cannot be the build root")
    return resolved


def selected_profiles(selection: str) -> Tuple[str, ...]:
    if selection == "all":
        return PROFILE_IDS
    if selection not in PROFILE_IDS:
        raise AppleExportError("unsupported Apple export profile selection")
    return (selection,)


def validate_execution_selection(profiles: Sequence[str], execution_tier: str) -> None:
    if execution_tier == "none":
        return
    required = EXECUTION_PROFILES.get(execution_tier)
    if required is None or required not in profiles:
        raise AppleExportError(
            "execution tier {} requires profile {}".format(execution_tier, required)
        )


def run(
    command: Sequence[object],
    *,
    cwd: Path = ROOT,
    environment: Optional[Mapping[str, str]] = None,
) -> None:
    printable = [str(value) for value in command]
    print("+ {}".format(" ".join(printable)), flush=True)
    subprocess.run(
        printable,
        cwd=str(cwd),
        env=None if environment is None else dict(environment),
        check=True,
    )


def capture(
    command: Sequence[object],
    *,
    cwd: Path = ROOT,
    environment: Optional[Mapping[str, str]] = None,
    timeout_seconds: Optional[int] = None,
) -> str:
    completed = subprocess.run(
        [str(value) for value in command],
        cwd=str(cwd),
        env=None if environment is None else dict(environment),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout_seconds,
    )
    if completed.returncode != 0:
        raise AppleExportError(
            "command failed ({}): {}\n{}".format(
                completed.returncode,
                " ".join(str(value) for value in command),
                completed.stdout.strip(),
            )
        )
    return completed.stdout


def verify_host() -> None:
    if platform.system().lower() != "darwin":
        raise AppleExportError("Apple export requires macOS and Xcode")
    for command in (
        ["xcrun", "--find", "swiftc"],
        ["xcrun", "--find", "xcodebuild"],
        ["xcrun", "--find", "lipo"],
        ["swift", "--version"],
    ):
        capture(command)


def framework_gradle_command(
    profile: Mapping[str, object],
    static_archive: Path,
    build_directory: Path,
) -> List[object]:
    kotlin_target = str(profile["kotlinTarget"])
    task = "linkReleaseFramework{}".format(
        kotlin_target[:1].upper() + kotlin_target[1:]
    )
    return [
        ROOT / "gradlew",
        "-p",
        KOTLIN_CORE,
        "--no-daemon",
        "--warning-mode=fail",
        "--no-build-cache",
        "--rerun-tasks",
        "--no-configuration-cache",
        task,
        "-PlinguumAppleProfile={}".format(profile["id"]),
        "-PlinguumAppleArchive={}".format(static_archive),
        "-PlinguumAppleHeaders={}".format(HEADER_DIRECTORY),
        "-PlinguumAppleBuildDirectory={}".format(build_directory),
    ]


def verify_framework_identity(
    profile: Mapping[str, object],
    architectures_output: str,
    build_output: str,
    header: str,
) -> Dict[str, object]:
    try:
        macho = ios_profiles.verify_macho_identity(
            profile, architectures_output, build_output
        )
    except ios_profiles.IosProfileError as error:
        raise AppleExportError(str(error)) from error
    required = (
        "LinguumTranslationCoreOutcome",
        "LinguumTranslationCoreService",
        "translateText",
        "supportsLanguagePair",
        "close",
    )
    missing = [value for value in required if value not in header]
    if missing:
        raise AppleExportError(
            "Objective-C export header lacks required declarations: {}".format(missing)
        )
    pointer_patterns = (
        r"\b(?:void|char|linguum_translation_[A-Za-z0-9_]+)\s*\*",
        r"\b(?:CPointer|COpaquePointer)\b",
    )
    if any(re.search(pattern, header) for pattern in pointer_patterns):
        raise AppleExportError("Objective-C export leaks a native pointer type")
    return {
        **macho,
        "objectiveCDeclarations": list(required),
        "swiftBoundaryHasNoPointers": True,
    }


def verify_static_framework_build_versions(
    profile: Mapping[str, object], output: str
) -> str:
    platforms = sorted(
        set(re.findall(r"^\s*platform\s+([0-9]+)\s*$", output, re.MULTILINE))
    )
    minimums = sorted(
        set(
            re.findall(
                r"^\s*minos\s+([0-9]+(?:\.[0-9]+)+)\s*$",
                output,
                re.MULTILINE,
            )
        )
    )
    expected_number = "7" if profile["platform"] == "IOSSIMULATOR" else "2"
    if platforms != [expected_number] or minimums != ["15.0"]:
        raise AppleExportError(
            "static framework platform/minimum differs: platforms={}, minimums={}".format(
                platforms, minimums
            )
        )
    return "platform {}\nminos 15.0\n".format(profile["platform"])


def verify_merge_compatible(first: Path, second: Path) -> None:
    for relative in (
        Path("Headers") / "LinguumTranslationCore.h",
        Path("Modules") / "module.modulemap",
    ):
        first_path = first / relative
        second_path = second / relative
        if (
            not first_path.is_file()
            or first_path.is_symlink()
            or not second_path.is_file()
            or second_path.is_symlink()
            or first_path.read_bytes() != second_path.read_bytes()
        ):
            raise AppleExportError(
                "simulator frameworks differ at {}".format(relative.as_posix())
            )


def framework_binary(framework: Path) -> Path:
    binary = framework / CORE_FRAMEWORK
    if not binary.is_file() or binary.is_symlink():
        raise AppleExportError("Apple framework lacks its regular static binary")
    return binary


def build_framework(
    profile: Mapping[str, object],
    static_archive: Path,
    output: Path,
    clean: bool,
) -> Dict[str, object]:
    profile_id = str(profile["id"])
    build_directory = ROOT / "build" / "native-canary" / "apple-export" / profile_id
    if clean and build_directory.exists():
        shutil.rmtree(str(build_directory))
    run(framework_gradle_command(profile, static_archive, build_directory))
    frameworks = sorted(
        path
        for path in build_directory.rglob("{}.framework".format(CORE_FRAMEWORK))
        if path.is_dir()
    )
    if len(frameworks) != 1:
        raise AppleExportError(
            "expected one release framework for {}, found {}".format(
                profile_id, frameworks
            )
        )
    source = frameworks[0]
    destination = output / "frameworks" / profile_id / source.name
    if destination.exists():
        shutil.rmtree(str(destination))
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, symlinks=False)
    binary = framework_binary(destination)
    header_path = destination / "Headers" / "LinguumTranslationCore.h"
    if not header_path.is_file() or header_path.is_symlink():
        raise AppleExportError("Apple framework lacks its Objective-C header")
    identity = verify_framework_identity(
        profile,
        capture(["xcrun", "lipo", "-archs", binary]),
        verify_static_framework_build_versions(
            profile, capture(["xcrun", "otool", "-l", binary])
        ),
        header_path.read_text(encoding="utf-8"),
    )
    return {
        "binarySha256": file_sha256(binary),
        "framework": str(destination),
        "headerSha256": file_sha256(header_path),
        "identity": identity,
        "profile": profile,
    }


def merge_simulator_frameworks(
    arm64: Path, x64: Path, destination: Path
) -> Path:
    verify_merge_compatible(arm64, x64)
    if destination.exists():
        shutil.rmtree(str(destination))
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(arm64, destination, symlinks=False)
    destination_binary = framework_binary(destination)
    temporary_binary = destination / ".LinguumTranslationCore.universal"
    run(
        [
            "xcrun",
            "lipo",
            "-create",
            framework_binary(arm64),
            framework_binary(x64),
            "-output",
            temporary_binary,
        ]
    )
    os.replace(str(temporary_binary), str(destination_binary))
    for source in sorted((x64 / "Modules").rglob("*")):
        if not source.is_file() or source.is_symlink():
            continue
        relative = source.relative_to(x64)
        target = destination / relative
        if target.exists():
            if target.read_bytes() != source.read_bytes():
                raise AppleExportError(
                    "simulator module metadata conflicts at {}".format(relative)
                )
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    architectures = sorted(
        capture(["xcrun", "lipo", "-archs", destination_binary]).split()
    )
    if architectures != ["arm64", "x86_64"]:
        raise AppleExportError("merged simulator framework is not universal")
    return destination


def expected_slice_keys(profile_ids: Sequence[str]) -> Dict[Tuple[str, str], List[str]]:
    expected: Dict[Tuple[str, str], List[str]] = {}
    for profile_id in profile_ids:
        if profile_id == "ios-arm64":
            key = ("ios", "")
            architecture = "arm64"
        elif profile_id == "ios-simulator-arm64":
            key = ("ios", "simulator")
            architecture = "arm64"
        elif profile_id == "ios-simulator-x64":
            key = ("ios", "simulator")
            architecture = "x86_64"
        else:
            raise AppleExportError("unsupported profile in XCFramework evidence")
        expected.setdefault(key, []).append(architecture)
    return {key: sorted(values) for key, values in expected.items()}


def verify_xcframework_plist(
    document: Mapping[str, object], profile_ids: Sequence[str]
) -> Dict[str, object]:
    if (
        document.get("CFBundlePackageType") != "XFWK"
        or document.get("XCFrameworkFormatVersion") != "1.0"
    ):
        raise AppleExportError("XCFramework root identity differs from the contract")
    libraries = document.get("AvailableLibraries")
    if not isinstance(libraries, list) or not libraries:
        raise AppleExportError("XCFramework has no available libraries")
    actual: Dict[Tuple[str, str], List[str]] = {}
    identifiers = []
    for library in libraries:
        if not isinstance(library, dict):
            raise AppleExportError("XCFramework library entry is malformed")
        identifier = str(library.get("LibraryIdentifier", ""))
        identifiers.append(identifier)
        if library.get("LibraryPath") != "{}.framework".format(CORE_FRAMEWORK):
            raise AppleExportError("XCFramework library path differs from the core module")
        key = (
            str(library.get("SupportedPlatform", "")),
            str(library.get("SupportedPlatformVariant", "")),
        )
        architectures = sorted(str(value) for value in library.get("SupportedArchitectures", []))
        if key in actual or not architectures:
            raise AppleExportError("XCFramework has duplicate or empty platform slices")
        actual[key] = architectures
    expected = expected_slice_keys(profile_ids)
    if actual != expected or len(set(identifiers)) != len(identifiers):
        raise AppleExportError(
            "XCFramework slices differ: expected {}, got {}".format(expected, actual)
        )
    return {
        "deviceArchitectures": actual.get(("ios", ""), []),
        "libraryCount": len(libraries),
        "libraryIdentifiers": sorted(identifiers),
        "simulatorArchitectures": actual.get(("ios", "simulator"), []),
    }


def create_xcframework(
    profile_ids: Sequence[str],
    framework_results: Mapping[str, Mapping[str, object]],
    output: Path,
) -> Tuple[Path, Dict[str, object]]:
    inputs: List[Path] = []
    if "ios-arm64" in profile_ids:
        inputs.append(Path(str(framework_results["ios-arm64"]["framework"])))
    simulator_ids = [
        value
        for value in ("ios-simulator-arm64", "ios-simulator-x64")
        if value in profile_ids
    ]
    if len(simulator_ids) == 2:
        inputs.append(
            merge_simulator_frameworks(
                Path(str(framework_results[simulator_ids[0]]["framework"])),
                Path(str(framework_results[simulator_ids[1]]["framework"])),
                output / "frameworks" / "ios-simulator-universal" / "{}.framework".format(CORE_FRAMEWORK),
            )
        )
    else:
        inputs.extend(
            Path(str(framework_results[value]["framework"]))
            for value in simulator_ids
        )
    xcframework = output / XCFRAMEWORK_NAME
    if xcframework.exists():
        shutil.rmtree(str(xcframework))
    command: List[object] = ["xcodebuild", "-create-xcframework"]
    for framework in inputs:
        command.extend(["-framework", framework])
    command.extend(["-output", xcframework])
    run(command)
    info_path = xcframework / "Info.plist"
    if not info_path.is_file() or info_path.is_symlink():
        raise AppleExportError("XCFramework lacks a regular Info.plist")
    evidence = verify_xcframework_plist(
        plistlib.loads(info_path.read_bytes()), profile_ids
    )
    return xcframework, evidence


def write_deterministic_tree_zip(source: Path, destination: Path) -> None:
    entries = [path for path in source.rglob("*") if path.is_file() and not path.is_symlink()]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(entries, key=lambda value: value.relative_to(source.parent).as_posix()):
            name = path.relative_to(source.parent).as_posix()
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, path.read_bytes())


def read_swift_api_snapshot(path: Path = SWIFT_API_SNAPSHOT) -> List[str]:
    declarations = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if declarations != sorted(set(declarations)) or set(declarations) != set(SWIFT_API_TOKENS):
        raise AppleExportError("Swift API snapshot is not exact, sorted, and unique")
    return declarations


def verify_swift_api_source() -> Dict[str, object]:
    source_path = SWIFT_PACKAGE / "Sources" / "LinguumTranslation" / "LinguumTranslation.swift"
    source = source_path.read_text(encoding="utf-8")
    declarations = read_swift_api_snapshot()
    missing = [name for name in declarations if SWIFT_API_TOKENS[name] not in source]
    if missing:
        raise AppleExportError("Swift overlay differs from its API snapshot: {}".format(missing))
    forbidden = ("LinguumTranslationCoreOutcome", "KotlinBase", "UnsafePointer", "OpaquePointer")
    public_lines = [line.strip() for line in source.splitlines() if line.strip().startswith("public ")]
    if any(token in line for token in forbidden for line in public_lines):
        raise AppleExportError("Swift overlay public API leaks a core/native type")
    if "withCheckedThrowingContinuation" not in source or "async throws" not in source:
        raise AppleExportError("Swift overlay lacks the async throws feasibility bridge")
    return {
        "declarations": declarations,
        "snapshotSha256": file_sha256(SWIFT_API_SNAPSHOT),
    }


def verify_swift_canary_output(
    output: str, kotlin_target: str, iterations: int
) -> Dict[str, object]:
    if "LINGUUM_SWIFT_CANARY_FAIL" in output:
        raise AppleExportError("Swift canary emitted an explicit failure marker")
    start = (
        "LINGUUM_SWIFT_CANARY_START profile={} iterations={} async=true".format(
            kotlin_target, iterations
        )
    )
    passed = (
        "LINGUUM_SWIFT_CANARY_PASS profile={} iterations={} async=true abi=1.0".format(
            kotlin_target, iterations
        )
    )
    if output.count(start) != 1 or output.count(passed) != 1:
        raise AppleExportError("Swift canary markers are missing, duplicated, or mismatched")
    return {"abi": "1.0", "async": True, "iterations": iterations, "target": kotlin_target}


def copy_regular(source: Path, destination: Path) -> None:
    if not source.is_file() or source.is_symlink():
        raise AppleExportError("required regular fixture file is missing: {}".format(source))
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def stage_swift_package(
    xcframework: Path,
    model_directory: Path,
    configuration: Path,
    kotlin_target: str,
    output: Path,
) -> Path:
    stage = output / "swift-package"
    if stage.exists():
        shutil.rmtree(str(stage))
    shutil.copytree(
        SWIFT_PACKAGE,
        stage,
        ignore=shutil.ignore_patterns(".swiftpm", ".build", "DerivedData"),
    )
    binary = stage / "Binary" / XCFRAMEWORK_NAME
    binary.parent.mkdir(parents=True)
    shutil.copytree(xcframework, binary, symlinks=False)
    fixtures = stage / "Tests" / "LinguumTranslationCanaryTests" / "Fixtures"
    models = fixtures / "Models"
    models.mkdir(parents=True, exist_ok=True)
    for name in (
        "lex.50.50.esen.s2t.bin",
        "model.esen.intgemm.alphas.bin",
        "vocab.esen.spm",
    ):
        copy_regular(model_directory / name, models / name)
    copy_regular(configuration, fixtures / "es-en.yml")
    (fixtures / "profile.txt").write_text(kotlin_target + "\n", encoding="utf-8")
    package = json.loads(capture(["swift", "package", "--package-path", stage, "dump-package"]))
    if package.get("name") != "LinguumTranslationFeasibility":
        raise AppleExportError("staged Swift package identity differs from the contract")
    return stage


def parse_json_object(output: str) -> Mapping[str, object]:
    start = output.find("{")
    end = output.rfind("}")
    if start < 0 or end < start:
        raise AppleExportError("command output lacks a JSON object")
    value = json.loads(output[start : end + 1])
    if not isinstance(value, dict):
        raise AppleExportError("command JSON output must be an object")
    return value


def package_scheme(stage: Path) -> str:
    document = parse_json_object(
        capture(["xcodebuild", "-list", "-json"], cwd=stage)
    )
    workspace = document.get("workspace")
    if not isinstance(workspace, dict) or not isinstance(
        workspace.get("schemes"), list
    ):
        raise AppleExportError("Swift package scheme document is malformed")
    schemes = workspace["schemes"]
    candidates = [
        str(value)
        for value in schemes
        if str(value) == "LinguumTranslationFeasibility"
    ]
    if len(candidates) != 1:
        raise AppleExportError("Swift package exposes an unexpected scheme set: {}".format(schemes))
    return candidates[0]


def swift_compile_commands(
    scheme: str,
    derived_data: Path,
    xcframework_evidence: Mapping[str, object],
    execution_tier: str,
) -> Dict[str, List[object]]:
    commands: Dict[str, List[object]] = {}
    common: List[object] = ["xcodebuild", "-scheme", scheme]
    device_architectures = xcframework_evidence.get("deviceArchitectures", [])
    simulator_architectures = xcframework_evidence.get(
        "simulatorArchitectures", []
    )
    if "arm64" in device_architectures and execution_tier != "physical-arm64":
        commands["ios-arm64"] = [
            *common,
            "-derivedDataPath",
            derived_data / "ios-arm64",
            "-destination",
            "generic/platform=iOS",
            "build-for-testing",
            "CODE_SIGNING_ALLOWED=NO",
        ]
    if "x86_64" in simulator_architectures and execution_tier != "simulator-x64":
        commands["ios-simulator-x64"] = [
            *common,
            "-derivedDataPath",
            derived_data / "ios-simulator-x64",
            "-destination",
            "generic/platform=iOS Simulator",
            "build-for-testing",
            "ARCHS=x86_64",
            "ONLY_ACTIVE_ARCH=NO",
            "CODE_SIGNING_ALLOWED=NO",
        ]
    return commands


def verify_physical_profile(
    profile: Mapping[str, object], bundle_identifier: str
) -> Tuple[str, str]:
    teams = profile.get("TeamIdentifier")
    uuid = str(profile.get("UUID", ""))
    entitlements = profile.get("Entitlements")
    if (
        not isinstance(teams, list)
        or not teams
        or not uuid
        or not isinstance(entitlements, dict)
        or re.fullmatch(r"[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)+", bundle_identifier)
        is None
    ):
        raise AppleExportError(
            "physical provisioning profile or bundle identifier is malformed"
        )
    team = str(teams[0])
    application_identifier = "{}.{}".format(team, bundle_identifier)
    allowed_identifier = str(entitlements.get("application-identifier", ""))
    if not (
        allowed_identifier == application_identifier
        or (
            allowed_identifier.endswith(".*")
            and application_identifier.startswith(allowed_identifier[:-1])
        )
    ):
        raise AppleExportError(
            "physical Swift bundle identifier is outside the provisioning profile"
        )
    return team, uuid


def physical_signing_settings() -> List[str]:
    required = (
        "LINGUUM_IOS_DEVICE_UDID",
        "LINGUUM_IOS_SIGNING_IDENTITY",
        "LINGUUM_IOS_PROVISIONING_PROFILE",
        "LINGUUM_IOS_BUNDLE_ID",
    )
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise AppleExportError(
            "physical Swift execution requires signed-device inputs: {}".format(
                ", ".join(missing)
            )
        )
    profile_path = Path(os.environ["LINGUUM_IOS_PROVISIONING_PROFILE"]).resolve()
    if not profile_path.is_file() or profile_path.is_symlink():
        raise AppleExportError("physical provisioning profile is not a regular file")
    profile = plistlib.loads(
        subprocess.check_output(["security", "cms", "-D", "-i", str(profile_path)])
    )
    bundle_identifier = os.environ["LINGUUM_IOS_BUNDLE_ID"]
    team, uuid = verify_physical_profile(profile, bundle_identifier)
    return [
        "CODE_SIGN_STYLE=Manual",
        "DEVELOPMENT_TEAM={}".format(team),
        "CODE_SIGN_IDENTITY={}".format(os.environ["LINGUUM_IOS_SIGNING_IDENTITY"]),
        "PROVISIONING_PROFILE={}".format(uuid),
        "PROVISIONING_PROFILE_SPECIFIER={}".format(uuid),
        "PRODUCT_BUNDLE_IDENTIFIER={}".format(bundle_identifier),
    ]


def run_swift_canary(
    stage: Path,
    profile: Mapping[str, object],
    xcframework_evidence: Mapping[str, object],
    execution_tier: str,
    iterations: int,
) -> Dict[str, object]:
    scheme = package_scheme(stage)
    with tempfile.TemporaryDirectory(prefix="linguum-apple-export-derived-") as temporary:
        derived_data = Path(temporary)
        compile_commands = swift_compile_commands(
            scheme, derived_data, xcframework_evidence, execution_tier
        )
        for command in compile_commands.values():
            capture(command, cwd=stage, timeout_seconds=900)
        command: List[object] = [
            "xcodebuild",
            "-scheme",
            scheme,
            "-derivedDataPath",
            derived_data / "execution",
            "-parallel-testing-enabled",
            "NO",
        ]
        if execution_tier == "physical-arm64":
            destination = "platform=iOS,id={}".format(
                os.environ.get("LINGUUM_IOS_DEVICE_UDID", "")
            )
            command.extend(["-destination", destination, "test"])
            command.extend(physical_signing_settings())
        else:
            machine = platform.machine().lower()
            expected = "x86_64" if execution_tier == "simulator-x64" else "arm64"
            if expected == "x86_64" and machine not in {"x86_64", "amd64"}:
                raise AppleExportError("x64 Swift simulator execution requires an Intel runner")
            if expected == "arm64" and machine not in {"arm64", "aarch64"}:
                raise AppleExportError("arm64 Swift simulator execution requires Apple Silicon")
            simulator = ios_profiles.select_simulator()
            destination = "platform=iOS Simulator,id={}".format(simulator["udid"])
            command.extend(["-destination", destination, "test"])
        result = capture(command, cwd=stage, timeout_seconds=1800)
    evidence = verify_swift_canary_output(
        result, str(profile["kotlinTarget"]), iterations
    )
    return {
        **evidence,
        "destination": destination,
        "scheme": scheme,
        "consumerCompileProofs": sorted(compile_commands),
        "ephemeralDerivedData": True,
    }


def swift_toolchain_evidence() -> Dict[str, object]:
    swift = capture(["swift", "--version"]).splitlines()
    xcode = capture(["xcodebuild", "-version"]).splitlines()
    if not swift or not xcode or not xcode[0].startswith("Xcode "):
        raise AppleExportError("Swift/Xcode identity could not be parsed")
    return {
        "swiftVersionLine": swift[0],
        "xcodeVersion": xcode[0].removeprefix("Xcode ").strip(),
    }


def execute(
    selected_profile: str,
    output: Path,
    iterations: int,
    clean: bool,
    execution_tier: str,
) -> Dict[str, object]:
    if iterations != 100:
        raise AppleExportError("M1-WP08 requires exactly 100 canary iterations")
    verify_host()
    document = load_lock()
    profile_ids = selected_profiles(selected_profile)
    validate_execution_selection(profile_ids, execution_tier)
    output = safe_output_directory(output)
    if clean and output.exists():
        shutil.rmtree(str(output))
    output.mkdir(parents=True, exist_ok=True)
    swift_api = verify_swift_api_source()
    native_output = output / "native-profiles"
    native_evidence = ios_profiles.execute(
        selected_profile,
        native_output,
        iterations,
        clean,
        execution_tier,
    )
    profiles = ios_profiles.profile_map(ios_profiles.load_lock())
    frameworks: Dict[str, Mapping[str, object]] = {}
    for profile_id in profile_ids:
        archive = Path(str(native_evidence["profiles"][profile_id]["archive"]))
        frameworks[profile_id] = build_framework(
            profiles[profile_id], archive, output, clean
        )
    xcframework, xcframework_evidence = create_xcframework(
        profile_ids, frameworks, output
    )
    package_zip = output / XCFRAMEWORK_ZIP
    write_deterministic_tree_zip(xcframework, package_zip)
    reproduction = output / "{}.reproduction".format(XCFRAMEWORK_ZIP)
    write_deterministic_tree_zip(xcframework, reproduction)
    try:
        if package_zip.read_bytes() != reproduction.read_bytes():
            raise AppleExportError("deterministic XCFramework ZIP reproduction differs")
    finally:
        reproduction.unlink(missing_ok=True)
    swiftpm_checksum = capture(
        [*SWIFT_CHECKSUM_COMMAND.split(), package_zip]
    ).strip()
    if swiftpm_checksum != file_sha256(package_zip):
        raise AppleExportError("SwiftPM checksum differs from SHA-256")
    execution = None
    if execution_tier != "none":
        execution_profile_id = EXECUTION_PROFILES[execution_tier]
        model = ios_profiles.fetch_canary_model.fetch()
        stage = stage_swift_package(
            xcframework,
            model,
            ROOT / "testing" / "native" / "fixtures" / "es-en.yml",
            str(profiles[execution_profile_id]["kotlinTarget"]),
            output,
        )
        execution = run_swift_canary(
            stage,
            profiles[execution_profile_id],
            xcframework_evidence,
            execution_tier,
            iterations,
        )
    evidence = {
        "deploymentTarget": document["deploymentTarget"],
        "evidencePath": str(output / "M1-WP08-apple-export-evidence.json"),
        "execution": execution,
        "frameworks": frameworks,
        "nativeProfileEvidence": native_evidence["evidencePath"],
        "profiles": list(profile_ids),
        "swiftApi": swift_api,
        "swiftModule": document["swiftModule"],
        "swiftPmChecksum": swiftpm_checksum,
        "toolchain": {**native_evidence["toolchain"], **swift_toolchain_evidence()},
        "xcframework": {
            **xcframework_evidence,
            "path": str(xcframework),
            "zip": str(package_zip),
            "zipSha256": file_sha256(package_zip),
            "zipSize": package_zip.stat().st_size,
        },
    }
    evidence_path = output / "M1-WP08-apple-export-evidence.json"
    evidence_path.write_bytes(json_bytes(evidence))
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return evidence


EXPORT_ERRORS = (
    AppleExportError,
    ios_profiles.IosProfileError,
    json.JSONDecodeError,
    OSError,
    plistlib.InvalidFileException,
    subprocess.SubprocessError,
    ValueError,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("all", *PROFILE_IDS), required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument(
        "--execution-tier",
        choices=("none", *EXECUTION_PROFILES),
        default="none",
    )
    arguments = parser.parse_args()
    try:
        execute(
            arguments.profile,
            arguments.output,
            arguments.iterations,
            arguments.clean,
            arguments.execution_tier,
        )
    except EXPORT_ERRORS as error:
        print("Apple export gate failed: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
