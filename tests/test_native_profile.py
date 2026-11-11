"""Jason Stys: actual native lock contention and file-preserving profile boundary controls."""

# Index: os@5, subprocess@6, sys@7, Path@8, pytest@10, DesktopOwnership@12, external_directory@12, test_fixed_sqlite_aliases_refused_before_lock_or_account_writes@24, test_fixed_sqlite_aliases_refused_before_lock_or_account_writes.name@24, test_fixed_sqlite_aliases_refused_before_lock_or_account_writes.tmp_path@24, test_fixed_sqlite_aliases_refused_before_lock_or_account_writes.profile@26, test_fixed_sqlite_aliases_refused_before_lock_or_account_writes.original@28, test_ordinary_recovery_files_are_retained_without_being_opened@37, test_ordinary_recovery_files_are_retained_without_being_opened.tmp_path@37, test_ordinary_recovery_files_are_retained_without_being_opened.profile@39, test_ordinary_recovery_files_are_retained_without_being_opened.expected@41, test_ordinary_recovery_files_are_retained_without_being_opened.name@42, test_ordinary_recovery_files_are_retained_without_being_opened.name@46, test_ordinary_recovery_files_are_retained_without_being_opened.raw@46, test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts@49, test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts.tmp_path@49, test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts.directory@51, test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts.protected@53, test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts.before@55, test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts.program@56, test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts.first@57, test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts.child@58, test_actual_installation_boundary_refuses_before_creating_descendants@74, test_actual_installation_boundary_refuses_before_creating_descendants.nested@74, test_actual_installation_boundary_refuses_before_creating_descendants.tmp_path@74, test_actual_installation_boundary_refuses_before_creating_descendants.installation@76, test_actual_installation_boundary_refuses_before_creating_descendants.target@78, test_unknown_lock_and_hardlink_are_preserved_without_mutating_account_files@85, test_unknown_lock_and_hardlink_are_preserved_without_mutating_account_files.tmp_path@85, test_unknown_lock_and_hardlink_are_preserved_without_mutating_account_files.directory@87, test_unknown_lock_and_hardlink_are_preserved_without_mutating_account_files.marker@89, test_unknown_lock_and_hardlink_are_preserved_without_mutating_account_files.original@95, test_actual_directory_alias_refused_without_following_or_creating_account_data@103, test_actual_directory_alias_refused_without_following_or_creating_account_data.tmp_path@103, test_actual_directory_alias_refused_without_following_or_creating_account_data.destination@105, test_actual_directory_alias_refused_without_following_or_creating_account_data.important@107, test_actual_directory_alias_refused_without_following_or_creating_account_data.alias@109, test_context_failure_releases_owner_without_resetting_existing_directory@133, test_context_failure_releases_owner_without_resetting_existing_directory.tmp_path@133, test_context_failure_releases_owner_without_resetting_existing_directory.reopened@137

import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.native_profile import DesktopOwnership, external_directory


@pytest.mark.parametrize(
    "name",
    [
        "private-accounts.db",
        "private-accounts.db-journal",
        "private-accounts.db-wal",
        "private-accounts.db-shm",
    ],
)
def test_fixed_sqlite_aliases_refused_before_lock_or_account_writes(tmp_path, name):
    """An actual hard-linked database/recovery name cannot redirect native initialization writes."""
    profile = tmp_path / "profile"
    profile.mkdir()
    original = tmp_path / "retain.bin"
    original.write_bytes(b"private fixture retained exactly")
    os.link(original, profile / name)
    with pytest.raises(ValueError, match="ordinary single-link"):
        DesktopOwnership(profile)
    assert original.read_bytes() == b"private fixture retained exactly"
    assert not (profile / ".aes-native-owner.lock").exists()


def test_ordinary_recovery_files_are_retained_without_being_opened(tmp_path):
    """Native ownership does not discard ordinary recovery evidence or reinterpret SQLite content."""
    profile = tmp_path / "profile"
    profile.mkdir()
    expected = {}
    for name in ("private-accounts.db-journal", "private-accounts.db-wal", "private-accounts.db-shm"):
        expected[name] = ("retained " + name).encode()
        (profile / name).write_bytes(expected[name])
    with DesktopOwnership(profile):
        assert all((profile / name).read_bytes() == raw for name, raw in expected.items())


def test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts(tmp_path):
    """A second real interpreter cannot own the profile; closing preserves exact existing bytes."""
    directory = tmp_path / "accounts"
    directory.mkdir()
    protected = directory / "existing-vault.encrypted.json"
    protected.write_bytes(b"synthetic opaque encrypted archive bytes")
    before = protected.read_bytes()
    program = "from pathlib import Path; import sys; from app.native_profile import DesktopOwnership; DesktopOwnership(Path(sys.argv[1]))"
    with DesktopOwnership(directory) as first:
        child = subprocess.run(  # noqa: S603 -- fixed trusted interpreter and literal contract probe; no user code.
            [sys.executable, "-c", program, str(directory)],
            capture_output=True,
            timeout=10,
            cwd=Path(__file__).resolve().parents[1],
            check=False,
        )
        assert child.returncode != 0
        assert first.descriptor >= 0
        assert protected.read_bytes() == before
    with DesktopOwnership(directory):
        assert protected.read_bytes() == before
    assert protected.read_bytes() == before


@pytest.mark.parametrize("nested", ["data", "child/data"])
def test_actual_installation_boundary_refuses_before_creating_descendants(tmp_path, nested):
    """Profile admission cannot create account data in the installed payload or resource tree."""
    installation = tmp_path / "installation"
    installation.mkdir()
    target = installation / nested
    with pytest.raises(ValueError, match="outside"):
        DesktopOwnership(target, (installation,))
    assert not target.exists()
    assert list(installation.iterdir()) == []


def test_unknown_lock_and_hardlink_are_preserved_without_mutating_account_files(tmp_path):
    """Unknown ownership content and aliased files cannot silently become a native profile lock."""
    directory = tmp_path / "accounts"
    directory.mkdir()
    marker = directory / ".aes-native-owner.lock"
    marker.write_bytes(b"important unknown file")
    with pytest.raises(ValueError):
        DesktopOwnership(directory)
    assert marker.read_bytes() == b"important unknown file"
    marker.unlink()
    original = tmp_path / "original"
    original.write_bytes(b"0")
    os.link(original, marker)
    with pytest.raises(ValueError):
        DesktopOwnership(directory)
    assert marker.read_bytes() == original.read_bytes() == b"0"


def test_actual_directory_alias_refused_without_following_or_creating_account_data(tmp_path):
    """Use a real Windows junction or POSIX symlink, not a mocked Path predicate."""
    destination = tmp_path / "preserve"
    destination.mkdir()
    important = destination / "important"
    important.write_bytes(b"preserve exactly")
    alias = tmp_path / "alias"
    if sys.platform == "win32":
        subprocess.run(  # noqa: S603 -- literal mklink/J uses only pytest-owned paths, no deletion or user content.
            [
                str(Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32/cmd.exe"),
                "/d",
                "/c",
                "mklink",
                "/J",
                str(alias),
                str(destination),
            ],
            check=True,
            capture_output=True,
            timeout=10,
        )
    else:
        alias.symlink_to(destination, target_is_directory=True)
    with pytest.raises(ValueError, match="links or junctions"):
        external_directory(alias / "new-profile")
    assert important.read_bytes() == b"preserve exactly"
    assert not (destination / "new-profile").exists()


def test_context_failure_releases_owner_without_resetting_existing_directory(tmp_path):
    """A genuine startup exception releases this process's lock, allowing a later normal launch."""
    with pytest.raises(RuntimeError, match="synthetic startup failure"), DesktopOwnership(tmp_path):
        raise RuntimeError("synthetic startup failure")
    with DesktopOwnership(tmp_path) as reopened:
        assert reopened.descriptor >= 0
    # Windows byte-range ownership correctly prevents an unrelated read while
    # held. Verify marker bytes after the second ordinary owner has closed.
    assert (tmp_path / ".aes-native-owner.lock").read_bytes() == b"0"
