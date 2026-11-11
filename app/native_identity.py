"""Jason Stys: bounded packaged-resource checks before opening private account data.

Hashes detect inconsistent package bytes; they are not code signing or a defense
against an OS owner replacing the entire application. Source indexes are generated
by scripts/code_index.py. No user document, credential or account is read here.
"""

# Index: annotations@10, hashlib@12, json@13, os@14, platform@15, re@16, stat@17, sys@18, Path@19, PurePosixPath@19, Any@20, VERSION@22, PRODUCT@24, WINDOWS_PYTHON_SHA256@25, MAX_UI_FILES@26, MAX_UI_TOTAL@27, MAX_UI_MEMBER@28, bounded_bytes@31, bounded_bytes.maximum@31, bounded_bytes.path@31, bounded_bytes.before@33, bounded_bytes.flags@36, bounded_bytes.stream@39, bounded_bytes.opened@40, bounded_bytes.value@47, bounded_bytes.after@48, ui_files@58, ui_files.root@58, ui_files.folder@60, ui_files.observed@63, ui_files.pending@63, ui_files.total@63, ui_files.visited@63, ui_files.directory@65, ui_files.members@66, ui_files.member@67, ui_files.visited@68, ui_files.path@71, ui_files.info@74, ui_files.value@78, ui_files.total@79, unique_pairs@91, unique_pairs.items@91, unique_pairs.output@93, unique_pairs.key@94, unique_pairs.value@94, verify_bundle@101, verify_bundle.root@101, verify_bundle.value@105, verify_bundle.actual@139, verify_bundle.name@140, verify_bundle.data@141, verify_bundle.library@145, verify_bundle.expected_name@146, verify_bundle.runtime@160, verify_bundle.raw@163, verify_bundle.digest@164, verify_gui@175, verify_gui.interpreter@175, verify_gui.metadata@175

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from app import VERSION

PRODUCT = "applicant-evidence-studio"
WINDOWS_PYTHON_SHA256 = "d8a06cc6ca3348925ea29e343e1c5c5895fe0bb433ff913e1cee44caf358aa6a"
MAX_UI_FILES = 1024
MAX_UI_TOTAL = 64 * 1024 * 1024
MAX_UI_MEMBER = 8 * 1024 * 1024


def bounded_bytes(path: Path, maximum: int) -> bytes:
    """Read one ordinary descriptor with exact size and identity checks, refusing links and growth."""
    before = path.lstat()
    if path.is_symlink() or path.is_junction() or not stat.S_ISREG(before.st_mode):
        raise ValueError("Packaged resource is not an ordinary file")
    flags = (
        os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    with os.fdopen(os.open(path, flags), "rb") as stream:
        opened = os.fstat(stream.fileno())
        if (
            (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)
            or not stat.S_ISREG(opened.st_mode)
            or not 0 <= opened.st_size <= maximum
        ):
            raise ValueError("Packaged resource changed or exceeded its bound")
        value = stream.read(opened.st_size + 1)
        after = os.fstat(stream.fileno())
        if len(value) != opened.st_size or (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ValueError("Packaged resource changed while being read")
        return value


def ui_files(root: Path) -> dict[str, dict[str, int | str]]:
    """Inventory only a bounded ordinary UI tree without traversing unknown linked directories."""
    folder = root / "dist"
    if folder.is_symlink() or folder.is_junction() or not folder.is_dir():
        raise ValueError("Packaged UI directory unavailable")
    pending, observed, visited, total = [folder], {}, 0, 0
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as members:
            for member in members:
                visited += 1
                if visited > MAX_UI_FILES:
                    raise ValueError("Packaged UI inventory exceeds its bound")
                path = Path(member.path)
                if member.is_symlink() or path.is_junction():
                    raise ValueError("Linked UI resource refused")
                info = member.stat(follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    pending.append(path)
                else:
                    value = bounded_bytes(path, MAX_UI_MEMBER)
                    total += len(value)
                    if total > MAX_UI_TOTAL:
                        raise ValueError("Packaged UI bytes exceed their bound")
                    observed[path.relative_to(root).as_posix()] = {
                        "bytes": len(value),
                        "sha256": hashlib.sha256(value).hexdigest(),
                    }
    if "dist/index.html" not in observed:
        raise ValueError("Packaged UI entry point missing")
    return observed


def unique_pairs(items: list[tuple[str, Any]]) -> dict:
    """Refuse ambiguous metadata rather than accepting last-value-wins package identity."""
    output = {}
    for key, value in items:
        if key in output:
            raise ValueError("Duplicate packaged metadata key")
        output[key] = value
    return output


def verify_bundle(root: Path) -> dict:
    """Verify the exact source/version, runtime and UI/notice bytes before profile admission."""
    if not getattr(sys, "frozen", False):
        return {"source": "development", "source_dirty": True}
    value = json.loads(bounded_bytes(root / "NATIVE_SOURCE.json", 256 * 1024), object_pairs_hook=unique_pairs)
    if not isinstance(value, dict) or set(value) != {
        "schema",
        "product",
        "version",
        "source",
        "source_dirty",
        "python",
        "platform",
        "machine",
        "runtime_library",
        "tcl_version",
        "tk_version",
        "resources",
    }:
        raise ValueError("Invalid packaged source manifest")
    if (
        type(value["schema"]) is not int
        or value["schema"] != 1
        or value["product"] != PRODUCT
        or value["version"] != VERSION
        or type(value["source_dirty"]) is not bool
        or re.fullmatch(r"[a-f0-9]{40}", str(value["source"])) is None
    ):
        raise ValueError("Packaged source/version identity differs")
    if (
        value["python"] != platform.python_version()
        or sys.version_info[:3] != (3, 14, 10)
        or sys.version_info.releaselevel != "final"
        or value["platform"] != sys.platform
        or not isinstance(value["machine"], str)
        or value["machine"].casefold() != platform.machine().casefold()
    ):
        raise ValueError("Packaged runtime identity differs")
    actual = ui_files(root)
    for name in ("LICENSE", "NATIVE_NOTICES.txt"):
        data = bounded_bytes(root / name, 4 * 1024 * 1024)
        actual[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    if value["resources"] != actual:
        raise ValueError("Packaged resource hashes differ")
    library = value["runtime_library"]
    expected_name = {"win32": "python314.dll", "linux": "libpython3.14.so.1.0", "darwin": "Python"}.get(
        sys.platform
    )
    if (
        expected_name is None
        or not isinstance(library, dict)
        or set(library) != {"file", "bytes", "sha256", "sdk_sha256"}
        or re.fullmatch(r"[a-f0-9]{64}", str(library["sdk_sha256"])) is None
        or library["file"] != expected_name
        or PurePosixPath(library["file"]).name != library["file"]
    ):
        raise ValueError("Unknown packaged Python library")
    # PyInstaller's macOS framework alias may be an internal symlink. Resolve it
    # only within this extraction root; external links are never accepted.
    runtime = (root / library["file"]).resolve()
    if not runtime.is_relative_to(root.resolve()):
        raise ValueError("Python library escapes the packaged runtime")
    raw = bounded_bytes(runtime, 64 * 1024 * 1024)
    digest = hashlib.sha256(raw).hexdigest()
    if (
        library["bytes"] != len(raw)
        or library["sha256"] != digest
        or (sys.platform == "win32" and digest != WINDOWS_PYTHON_SHA256)
        or (sys.platform == "win32" and library["sdk_sha256"] != WINDOWS_PYTHON_SHA256)
    ):
        raise ValueError("Packaged Python library identity differs")
    return value


def verify_gui(interpreter: Any, metadata: dict) -> None:
    """Match actual loaded Tcl/Tk patch levels to the built manifest before account initialization."""
    if metadata.get("source") == "development":
        return
    if (
        str(interpreter.call("info", "patchlevel")) != metadata["tcl_version"]
        or str(interpreter.call("package", "require", "Tk")) != metadata["tk_version"]
    ):
        raise ValueError("Packaged GUI runtime identity differs")
