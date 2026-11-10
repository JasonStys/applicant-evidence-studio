"""Jason Stys: verify, extract and exercise actual portable bytes, never source-server fallbacks.

Published mode is pinned to the reviewed 0.3.0 tag and GitHub asset digests.
Built mode tests the current platform's archive before release upload. Neither
mode changes releases, tags, user profiles or the selected archive directory.
"""

# Index: argparse@9, hashlib@10, json@11, platform@12, re@13, stat@14, subprocess@15, sys@16, tarfile@17, tempfile@18, zipfile@19, Path@20, REPO@22, PUBLISHED_VERSION@23, PUBLISHED_SOURCE@24, ROOT@25, MAX_DOWNLOAD@26, MAX_EXPANDED@27, PUBLISHED_ASSETS@28, require@56, require.condition@56, require.message@56, command@62, command.arguments@62, command.timeout@62, command.completed@64, command.detail@75, api@82, api.suffix@82, names_for@87, names_for.machine@87, names_for.system@87, names_for.version@87, names_for.stem@94, digest@98, digest.path@98, digest.stream@100, checked_asset@104, checked_asset.filename@104, checked_asset.release@104, checked_asset.asset@112, checked_asset.matches@112, checked_asset.asset@114, checked_asset.known_digest@116, checked_asset.known_size@116, verify_file@134, verify_file.asset@134, verify_file.path@134, read_manifest@143, read_manifest.archive_name@143, read_manifest.binary_name@143, read_manifest.path@143, read_manifest.result@146, read_manifest.line@147, read_manifest.match@148, extract_archive@157, extract_archive.archive@157, extract_archive.binary_name@157, extract_archive.destination@157, extract_archive.expected@163, extract_archive.total@165, extract_archive.seen@166, extract_archive.write@168, extract_archive.write.mode@168, extract_archive.write.name@168, extract_archive.write.size@168, extract_archive.write.stream@168, extract_archive.write.target@177, extract_archive.write.copied@179, extract_archive.write.output@180, extract_archive.write.chunk@181, extract_archive.write.copied@182, extract_archive.write.total@188, extract_archive.bundle@192, extract_archive.member@194, extract_archive.mode@195, extract_archive.stream@200, extract_archive.bundle@203, extract_archive.member@204, extract_archive.stream@207, published_files@215, published_files.archive_name@215, published_files.downloads@215, published_files.sidecar_name@215, published_files.ref@217, published_files._@218, published_files.ref@223, published_files.release@225, published_files.filename@226, published_files.asset@227, main@247, main.parser@249, main.choice@250, main.args@253, main.VERSION@254, main.version@256, main.machine@257, main.system@257, main.archive_name@258, main.sidecar_name@258, main.binary_name@259, main.folder@260, main.temporary@261, main.downloads@262, main.source@264, main.source@266, main.downloads@268, main.archive@269, main.sidecar@269, main.manifest@270, main.extracted@272, main.binary@274, main.native@277, main.report@280, main.output@293
import argparse
import hashlib
import json
import platform
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

REPO = "JasonStys/applicant-evidence-studio"
PUBLISHED_VERSION = "0.3.0"
PUBLISHED_SOURCE = "71d51b1fcd228f89d3ff81ee166bee2ce37d7a60"
ROOT = Path(__file__).resolve().parents[1]
MAX_DOWNLOAD = 128 * 1024 * 1024
MAX_EXPANDED = 256 * 1024 * 1024
PUBLISHED_ASSETS = {
    "ApplicantEvidenceStudio-0.3.0-darwin-arm64.sha256": (
        206,
        "bdc5474de880af913f2663e01ccd796b4ba3aa46e0db388d32eae916049fea78",
    ),
    "ApplicantEvidenceStudio-0.3.0-darwin-arm64.tar.gz": (
        18198097,
        "3628caf115ecd710c38618f7026c3206e08dc6a3a445ceeb7d5092452de141ae",
    ),
    "ApplicantEvidenceStudio-0.3.0-linux-x86_64.sha256": (
        206,
        "e14a4b99f797b82f380d7ec1b5aaf7235294214d71106a09c1c3df00ad4fa651",
    ),
    "ApplicantEvidenceStudio-0.3.0-linux-x86_64.tar.gz": (
        32844757,
        "b0bf8f6fa4fc26bcaeaef0960ada1275e9d88ad3febc20ffb39fb6400c997287",
    ),
    "ApplicantEvidenceStudio-0.3.0-windows-amd64.sha256": (
        210,
        "e99aedc097cd7a477f875e9ea9bd74530918ef680ad24f7c624fd3ca770e31e2",
    ),
    "ApplicantEvidenceStudio-0.3.0-windows-amd64.zip": (
        19555411,
        "434065a4e285d2595ec82d6fa6c67894db20c285cf13378c9515a6dbd7102e79",
    ),
}


def require(condition, message):
    """Fail closed even when a caller enables Python optimization."""
    if not condition:
        raise ValueError(message)


def command(arguments, *, timeout=120):
    """Run literal trusted argument arrays; no shell or credential output."""
    completed = subprocess.run(  # noqa: S603 -- fixed QA commands and a digest-verified owned native binary; no shell.
        arguments,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )  # noqa: S603 -- literal trusted build/QA commands; no shell.
    if completed.returncode:
        detail = completed.stderr[-2500:] if arguments[0] == "node" else ""
        raise RuntimeError(
            f"Acceptance command failed: {Path(arguments[0]).name} (exit {completed.returncode}) {detail}"
        )
    return completed.stdout


def api(suffix):
    """Request metadata only from this fixed repository through authenticated gh."""
    return json.loads(command(["gh", "api", f"repos/{REPO}/{suffix}"]))


def names_for(system, machine, version):
    """Use only the three architectures actually published; never guess an ABI."""
    require(
        (system, machine) in {("windows", "amd64"), ("linux", "x86_64"), ("darwin", "arm64")},
        "No reviewed portable archive exists for this OS/architecture",
    )
    require(bool(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version)), "Invalid product version")
    stem = f"ApplicantEvidenceStudio-{version}-{system}-{machine}"
    return stem + (".zip" if system == "windows" else ".tar.gz"), stem + ".sha256"


def digest(path):
    """Stream file hashes without loading an executable into controller memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def checked_asset(release, filename):
    """Require a unique bounded same-release asset with a provider SHA-256 digest."""
    require(
        release.get("tag_name") == "v" + PUBLISHED_VERSION
        and release.get("draft") is False
        and release.get("prerelease") is False,
        "Expected an existing public stable release",
    )
    matches = [asset for asset in release.get("assets", []) if asset.get("name") == filename]
    require(len(matches) == 1, "Missing or ambiguous public package asset")
    asset = matches[0]
    require(filename in PUBLISHED_ASSETS, "Asset is outside the reviewed immutable package set")
    known_size, known_digest = PUBLISHED_ASSETS[filename]
    require(
        asset.get("size") == known_size and asset.get("digest") == "sha256:" + known_digest,
        "Published bytes changed since independent release verification",
    )
    require(type(asset.get("size")) is int and 0 < asset["size"] <= MAX_DOWNLOAD, "Invalid asset byte budget")
    require(
        isinstance(asset.get("digest"), str) and bool(re.fullmatch(r"sha256:[0-9a-f]{64}", asset["digest"])),
        "Provider digest missing or malformed",
    )
    require(
        asset.get("browser_download_url")
        == f"https://github.com/{REPO}/releases/download/v{PUBLISHED_VERSION}/{filename}",
        "Public asset URL does not match the fixed release",
    )
    return asset


def verify_file(path, asset):
    """Check downloaded length and digest against independently retrieved provider metadata."""
    require(path.is_file() and not path.is_symlink(), "Downloaded asset must be a regular file")
    require(
        path.stat().st_size == asset["size"] and digest(path) == asset["digest"][7:],
        "Downloaded asset differs from provider metadata",
    )


def read_manifest(path, archive_name, binary_name):
    """Only two literal basename entries are expected; reject duplicates and traversal."""
    require(path.stat().st_size <= 4096, "Checksum sidecar exceeds its budget")
    result = {}
    for line in path.read_text(encoding="ascii").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_.-]+)", line)
        require(match is not None and match[2] not in result, "Malformed or ambiguous checksum sidecar")
        result[match[2]] = match[1]
    require(
        set(result) == {archive_name, binary_name}, "Checksum sidecar does not cover exact package/binary"
    )
    return result


def extract_archive(archive, destination, binary_name):
    """Extract only the published three regular files into a newly owned empty directory.

    AES is one-file PyInstaller, so no archive links are necessary. POSIX binary
    executable bits must already exist; tests never repair missing archive modes.
    """
    expected = {binary_name, "LICENSE", "INSTALL.md"}
    require(destination.is_dir() and not any(destination.iterdir()), "Extraction directory must be empty")
    total = 0
    seen = set()

    def write(name, size, mode, stream):
        nonlocal total
        require(name in expected and name not in seen, "Unexpected/duplicate portable member")
        require(
            0 <= size <= MAX_DOWNLOAD and total + size <= MAX_EXPANDED, "Expanded package exceeds byte budget"
        )
        require(not mode & 0o7000, "Special executable permission bits are forbidden")
        if not archive.name.endswith(".zip") and name == binary_name:
            require(bool(mode & 0o100), "POSIX executable mode was lost in the archive")
        target = destination / name
        require(target.parent.resolve() == destination.resolve(), "Portable member escapes extraction root")
        copied = 0
        with target.open("xb") as output:
            while chunk := stream.read(min(1024 * 1024, size - copied + 1)):
                copied += len(chunk)
                require(copied <= size, "Archive member exceeds declared length")
                output.write(chunk)
        require(copied == size, "Truncated portable member")
        if sys.platform != "win32":
            target.chmod(mode & 0o777)
        total += copied
        seen.add(name)

    if archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as bundle:
            require(len(bundle.infolist()) == 3, "Unexpected ZIP member count")
            for member in bundle.infolist():
                mode = member.external_attr >> 16
                require(
                    not member.is_dir() and stat.S_IFMT(mode) in {0, stat.S_IFREG},
                    "ZIP links or special files are forbidden",
                )
                with bundle.open(member) as stream:
                    write(member.filename, member.file_size, mode, stream)
    else:
        with tarfile.open(archive, "r:gz") as bundle:
            for member in bundle:
                require(len(seen) < 3, "Unexpected tar member count")
                require(member.isfile(), "Tar links or special files are forbidden")
                stream = bundle.extractfile(member)
                require(stream is not None, "Missing tar member bytes")
                with stream:
                    write(member.name, member.size, member.mode, stream)
    require(seen == expected, "Incomplete portable archive")
    return destination / binary_name


def published_files(downloads, archive_name, sidecar_name):
    """Resolve immutable tag source, then download only two exact allowlisted assets."""
    ref = api(f"git/ref/tags/v{PUBLISHED_VERSION}")["object"]
    for _ in range(8):
        require(bool(re.fullmatch(r"[0-9a-f]{40}", ref.get("sha", ""))), "Invalid tag object")
        if ref.get("type") == "commit":
            break
        require(ref.get("type") == "tag", "Unexpected tag object type")
        ref = api("git/tags/" + ref["sha"])["object"]
    require(ref.get("type") == "commit" and ref["sha"] == PUBLISHED_SOURCE, "Published tag source changed")
    release = api(f"releases/tags/v{PUBLISHED_VERSION}")
    for filename in (archive_name, sidecar_name):
        asset = checked_asset(release, filename)
        command(
            [
                "gh",
                "release",
                "download",
                "v" + PUBLISHED_VERSION,
                "--repo",
                REPO,
                "--pattern",
                filename,
                "--dir",
                str(downloads),
            ],
            timeout=180,
        )
        verify_file(downloads / filename, asset)
    return release["html_url"]


def main():
    """Verify a built or published archive and run an actual encrypted native UI journey."""
    parser = argparse.ArgumentParser()
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--published", action="store_true")
    choice.add_argument("--built-directory", type=Path)
    args = parser.parse_args()
    from app import VERSION

    version = PUBLISHED_VERSION if args.published else VERSION
    system, machine = platform.system().lower(), platform.machine().lower()
    archive_name, sidecar_name = names_for(system, machine, version)
    binary_name = "ApplicantEvidenceStudio" + (".exe" if system == "windows" else "")
    with tempfile.TemporaryDirectory(prefix="aes-portable-acceptance-") as folder:
        temporary = Path(folder)
        downloads = temporary / "downloads"
        downloads.mkdir()
        source = None
        if args.published:
            source = published_files(downloads, archive_name, sidecar_name)
        else:
            downloads = args.built_directory.resolve()
        archive, sidecar = downloads / archive_name, downloads / sidecar_name
        manifest = read_manifest(sidecar, archive_name, binary_name)
        require(digest(archive) == manifest[archive_name], "Portable archive checksum mismatch")
        extracted = temporary / "extracted"
        extracted.mkdir()
        binary = extract_archive(archive, extracted, binary_name)
        require(digest(binary) == manifest[binary_name], "Extracted native binary checksum mismatch")
        command([sys.executable, "scripts/private_fixtures.py"])
        native = json.loads(
            command(["node", "scripts/native_ui_smoke.mjs", str(binary), version], timeout=150)
        )
        report = {
            "mode": "published" if args.published else "built",
            "platform": system,
            "architecture": machine,
            "version": version,
            "published_source": PUBLISHED_SOURCE if args.published else None,
            "release_url": source,
            "archive": archive_name,
            "archive_sha256": manifest[archive_name],
            "binary_sha256": manifest[binary_name],
            "provider_digests_verified": args.published,
            "native_ui": native,
        }
        output = ROOT / "artifacts" / f"portable-acceptance-{system}.json"
        output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report))


if __name__ == "__main__":
    main()
