"""Jason Stys: independent malformed portable metadata/archive fixtures; no network or execution."""

# Index: copy@4, hashlib@5, io@6, stat@7, tarfile@8, zipfile@9, pytest@11, PUBLISHED_ASSETS@14, checked_asset@15, extract_archive@16, names_for@17, read_manifest@18, require@19, verify_file@20, release_fixture@24, release_fixture.name@38, release_fixture.sha@38, release_fixture.size@38, test_public_metadata_matches_exact_reviewed_bytes@43, test_public_metadata_matches_exact_reviewed_bytes.release@45, test_public_metadata_matches_exact_reviewed_bytes.name@46, test_public_metadata_rejects_changed_or_ambiguous_release.r@53, test_public_metadata_rejects_changed_or_ambiguous_release.r@54, test_public_metadata_rejects_changed_or_ambiguous_release.r@55, test_public_metadata_rejects_changed_or_ambiguous_release.r@56, test_public_metadata_rejects_changed_or_ambiguous_release.r@57, test_public_metadata_rejects_changed_or_ambiguous_release.r@58, test_public_metadata_rejects_changed_or_ambiguous_release.r@59, test_public_metadata_rejects_changed_or_ambiguous_release.r@60, test_public_metadata_rejects_changed_or_ambiguous_release.r@61, test_public_metadata_rejects_changed_or_ambiguous_release.r@62, test_public_metadata_rejects_changed_or_ambiguous_release@65, test_public_metadata_rejects_changed_or_ambiguous_release.mutation@65, test_public_metadata_rejects_changed_or_ambiguous_release.release@67, test_public_metadata_rejects_changed_or_ambiguous_release.name@68, test_platform_names_and_unsupported_abi@74, test_platform_names_and_unsupported_abi.machine@79, test_platform_names_and_unsupported_abi.system@79, test_platform_names_and_unsupported_abi.version@79, test_download_hash_and_length_are_both_required@88, test_download_hash_and_length_are_both_required.tmp_path@88, test_download_hash_and_length_are_both_required.target@90, test_download_hash_and_length_are_both_required.asset@92, test_download_hash_and_length_are_both_required.changed@94, test_checksum_manifest_rejects_incomplete_ambiguous_and_path_entries@109, test_checksum_manifest_rejects_incomplete_ambiguous_and_path_entries.text@109, test_checksum_manifest_rejects_incomplete_ambiguous_and_path_entries.tmp_path@109, test_checksum_manifest_rejects_incomplete_ambiguous_and_path_entries.target@111, create_archive@117, create_archive.entries@117, create_archive.path@117, create_archive.zip_mode@117, create_archive.archive@120, create_archive.body@121, create_archive.name@121, create_archive.member@122, create_archive.archive@127, create_archive.body@128, create_archive.name@128, create_archive.member@129, test_actual_archive_roundtrip_and_checksum@138, test_actual_archive_roundtrip_and_checksum.binary@138, test_actual_archive_roundtrip_and_checksum.suffix@138, test_actual_archive_roundtrip_and_checksum.tmp_path@138, test_actual_archive_roundtrip_and_checksum.archive@140, test_actual_archive_roundtrip_and_checksum.destination@142, test_actual_archive_roundtrip_and_checksum.extracted@144, test_current_archive_requires_both_exact_native_metadata_members@155, test_current_archive_requires_both_exact_native_metadata_members.binary@155, test_current_archive_requires_both_exact_native_metadata_members.suffix@155, test_current_archive_requires_both_exact_native_metadata_members.tmp_path@155, test_current_archive_requires_both_exact_native_metadata_members.archive@157, test_current_archive_requires_both_exact_native_metadata_members.entries@158, test_current_archive_requires_both_exact_native_metadata_members.destination@166, test_current_archive_requires_both_exact_native_metadata_members.legacy@170, test_current_archive_requires_both_exact_native_metadata_members.missing@174, test_current_archive_requires_both_exact_native_metadata_members.incomplete@176, test_archive_paths_are_exact_and_do_not_write_outside@185, test_archive_paths_are_exact_and_do_not_write_outside.bad_name@185, test_archive_paths_are_exact_and_do_not_write_outside.tmp_path@185, test_archive_paths_are_exact_and_do_not_write_outside.archive@187, test_archive_paths_are_exact_and_do_not_write_outside.destination@189, test_zip_links_and_tar_missing_execute_mode_are_rejected@196, test_zip_links_and_tar_missing_execute_mode_are_rejected.tmp_path@196, test_zip_links_and_tar_missing_execute_mode_are_rejected.archive@198, test_zip_links_and_tar_missing_execute_mode_are_rejected.destination@204, test_zip_links_and_tar_missing_execute_mode_are_rejected.tar@208, test_zip_links_and_tar_missing_execute_mode_are_rejected.bundle@209, test_zip_links_and_tar_missing_execute_mode_are_rejected.name@210, test_zip_links_and_tar_missing_execute_mode_are_rejected.member@211, test_explicit_gate_never_accepts_false_condition@218
import copy
import hashlib
import io
import stat
import tarfile
import zipfile

import pytest

from scripts.portable_acceptance import (
    PUBLISHED_ASSETS,
    checked_asset,
    extract_archive,
    names_for,
    read_manifest,
    require,
    verify_file,
)


def release_fixture():
    """An independently specified public release shape uses the reviewed byte identities."""
    return {
        "tag_name": "v0.3.0",
        "draft": False,
        "prerelease": False,
        "assets": [
            {
                "name": name,
                "size": size,
                "digest": "sha256:" + sha,
                "browser_download_url": "https://github.com/JasonStys/applicant-evidence-studio/releases/download/v0.3.0/"
                + name,
            }
            for name, (size, sha) in PUBLISHED_ASSETS.items()
        ],
    }


def test_public_metadata_matches_exact_reviewed_bytes():
    """Every known platform asset has one exact identity; no network trust fallback."""
    release = release_fixture()
    for name in PUBLISHED_ASSETS:
        assert checked_asset(release, name)["name"] == name


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r.update(draft=True),
        lambda r: r.update(prerelease=True),
        lambda r: r.update(tag_name="v0.3.1"),
        lambda r: r.update(assets=[]),
        lambda r: r["assets"].append(copy.deepcopy(r["assets"][0])),
        lambda r: r["assets"][0].update(size=0),
        lambda r: r["assets"][0].update(size=True),
        lambda r: r["assets"][0].update(digest=None),
        lambda r: r["assets"][0].update(digest="sha256:" + "0" * 64),
        lambda r: r["assets"][0].update(browser_download_url="https://outside.invalid/file"),
    ],
)
def test_public_metadata_rejects_changed_or_ambiguous_release(mutation):
    """Published/draft/source identity cannot be inferred from a matching basename alone."""
    release = release_fixture()
    name = release["assets"][0]["name"]
    mutation(release)
    with pytest.raises(ValueError):
        checked_asset(release, name)


def test_platform_names_and_unsupported_abi():
    """No silent architecture fallback or user-controlled package path."""
    assert names_for("windows", "amd64", "0.3.0")[0].endswith("windows-amd64.zip")
    assert names_for("linux", "x86_64", "0.3.0")[0].endswith("linux-x86_64.tar.gz")
    assert names_for("darwin", "arm64", "0.3.0")[0].endswith("darwin-arm64.tar.gz")
    for system, machine, version in [
        ("darwin", "x86_64", "0.3.0"),
        ("linux", "arm64", "0.3.0"),
        ("windows", "amd64", "../0.3"),
    ]:
        with pytest.raises(ValueError):
            names_for(system, machine, version)


def test_download_hash_and_length_are_both_required(tmp_path):
    """A known small SHA-256 vector checks actual bytes independently of metadata validation."""
    target = tmp_path / "abc"
    target.write_bytes(b"abc")
    asset = {"size": 3, "digest": "sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"}
    verify_file(target, asset)
    for changed in [{**asset, "size": 4}, {**asset, "digest": "sha256:" + "0" * 64}]:
        with pytest.raises(ValueError):
            verify_file(target, changed)


@pytest.mark.parametrize(
    "text",
    [
        "0" * 64 + "  ../outside\n",
        "0" * 64 + "  app.zip\n",
        ("0" * 64 + "  app.zip\n") * 2,
        "0" * 64 + " *app.zip\n",
        "x" * 4097,
    ],
)
def test_checksum_manifest_rejects_incomplete_ambiguous_and_path_entries(tmp_path, text):
    """Checksums must cover the exact archive and embedded executable with unique basenames."""
    target = tmp_path / "digest.sha256"
    target.write_text(text, encoding="ascii")
    with pytest.raises(ValueError):
        read_manifest(target, "app.zip", "ApplicantEvidenceStudio.exe")


def create_archive(path, entries, *, zip_mode=stat.S_IFREG | 0o600):
    """Construct archive bytes separately from the extractor under test."""
    if path.name.endswith(".zip"):
        with zipfile.ZipFile(path, "w") as archive:
            for name, body in entries:
                member = zipfile.ZipInfo(name)
                member.create_system = 3
                member.external_attr = zip_mode << 16
                archive.writestr(member, body)
    else:
        with tarfile.open(path, "w:gz") as archive:
            for name, body in entries:
                member = tarfile.TarInfo(name)
                member.size = len(body)
                member.mode = 0o755 if name == "ApplicantEvidenceStudio" else 0o644
                archive.addfile(member, io.BytesIO(body))


@pytest.mark.parametrize(
    "suffix,binary", [("zip", "ApplicantEvidenceStudio.exe"), ("tar.gz", "ApplicantEvidenceStudio")]
)
def test_actual_archive_roundtrip_and_checksum(tmp_path, suffix, binary):
    """Real ZIP/tar files preserve three exact members; fixtures are never executed."""
    archive = tmp_path / ("app." + suffix)
    create_archive(archive, [(binary, b"abc"), ("LICENSE", b"MIT"), ("INSTALL.md", b"Install")])
    destination = tmp_path / "out"
    destination.mkdir()
    extracted = extract_archive(archive, destination, binary)
    assert extracted.read_bytes() == b"abc"
    assert (
        hashlib.sha256(extracted.read_bytes()).hexdigest()
        == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


@pytest.mark.parametrize(
    "suffix,binary", [("zip", "ApplicantEvidenceStudio.exe"), ("tar.gz", "ApplicantEvidenceStudio")]
)
def test_current_archive_requires_both_exact_native_metadata_members(tmp_path, suffix, binary):
    """Real current archives include source/notices; historical mode cannot silently accept extra executables or members."""
    archive = tmp_path / ("current." + suffix)
    entries = [
        (binary, b"inert binary"),
        ("LICENSE", b"license"),
        ("INSTALL.md", b"help"),
        ("NATIVE_SOURCE.json", b'{"schema":1}'),
        ("NATIVE_NOTICES.txt", b"terms"),
    ]
    create_archive(archive, entries)
    destination = tmp_path / "current"
    destination.mkdir()
    assert extract_archive(archive, destination, binary, native_metadata=True).read_bytes() == b"inert binary"
    assert (destination / "NATIVE_NOTICES.txt").read_bytes() == b"terms"
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    with pytest.raises(ValueError, match="member count"):
        extract_archive(archive, legacy, binary)
    missing = tmp_path / ("missing." + suffix)
    create_archive(missing, entries[:-1])
    incomplete = tmp_path / "incomplete"
    incomplete.mkdir()
    with pytest.raises(ValueError):
        extract_archive(missing, incomplete, binary, native_metadata=True)


@pytest.mark.parametrize(
    "bad_name", ["../outside", "/outside", "C:/outside", "LICENSE/../outside", "license"]
)
def test_archive_paths_are_exact_and_do_not_write_outside(tmp_path, bad_name):
    """Even normalized aliases and alternate-case entries cannot stand in for package members."""
    archive = tmp_path / "bad.zip"
    create_archive(archive, [(bad_name, b"bad"), ("LICENSE", b"MIT"), ("INSTALL.md", b"Install")])
    destination = tmp_path / "out"
    destination.mkdir()
    with pytest.raises(ValueError):
        extract_archive(archive, destination, "ApplicantEvidenceStudio.exe")
    assert not (tmp_path / "outside").exists()


def test_zip_links_and_tar_missing_execute_mode_are_rejected(tmp_path):
    """The acceptance gate never repairs broken permissions or follows package links."""
    archive = tmp_path / "bad.zip"
    create_archive(
        archive,
        [("ApplicantEvidenceStudio.exe", b"target"), ("LICENSE", b"MIT"), ("INSTALL.md", b"Install")],
        zip_mode=stat.S_IFLNK | 0o777,
    )
    destination = tmp_path / "out"
    destination.mkdir()
    with pytest.raises(ValueError):
        extract_archive(archive, destination, "ApplicantEvidenceStudio.exe")
    tar = tmp_path / "bad.tar.gz"
    with tarfile.open(tar, "w:gz") as bundle:
        for name in ("ApplicantEvidenceStudio", "LICENSE", "INSTALL.md"):
            member = tarfile.TarInfo(name)
            member.mode = 0o644
            bundle.addfile(member, io.BytesIO(b""))
    with pytest.raises(ValueError):
        extract_archive(tar, destination, "ApplicantEvidenceStudio")


def test_explicit_gate_never_accepts_false_condition():
    """Release decisions do not depend on optimizable Python assert statements."""
    with pytest.raises(ValueError):
        require(False, "Independent gate rejection")
