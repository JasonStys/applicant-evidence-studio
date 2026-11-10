"""Jason Stys: independent exact-source, draft and portable-asset publication boundaries."""

# Index: copy@4, pytest@6, assets_ready@8, draft_ready@8, successful_source_run@8, names_for@9, SOURCE@11, run_fixture@14, test_source_run_requires_exact_completed_main_identity@33, test_source_run_rejects_unrelated_or_unfinished_metadata@53, test_source_run_rejects_unrelated_or_unfinished_metadata.field@53, test_source_run_rejects_unrelated_or_unfinished_metadata.value@53, test_source_run_rejects_unrelated_or_unfinished_metadata.data@55, test_empty_duplicate_and_incomplete_run_pages_fail_closed@61, test_empty_duplicate_and_incomplete_run_pages_fail_closed.data@63, test_draft_never_accepts_published_or_different_source@82, test_draft_never_accepts_published_or_different_source.change@82, test_draft_never_accepts_published_or_different_source.data@84, assets_fixture@90, assets_fixture.names@92, assets_fixture.machine@94, assets_fixture.system@94, assets_fixture.name@95, assets_fixture.name@97, test_publication_requires_all_six_platform_assets@100, test_publication_requires_all_six_platform_assets.data@102, test_publication_requires_all_six_platform_assets.partial@104, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.r@113, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.r@114, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.r@115, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.r@116, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.r@117, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes@120, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.mutation@120, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.data@122
import copy

import pytest

from scripts.desktop_release_guard import assets_ready, draft_ready, successful_source_run
from scripts.portable_acceptance import names_for

SOURCE = "a" * 40


def run_fixture():
    """A complete main-push record, independent of query filtering and workflow code."""
    return {
        "total_count": 1,
        "workflow_runs": [
            {
                "id": 123,
                "head_sha": SOURCE,
                "head_branch": "main",
                "event": "push",
                "path": ".github/workflows/validate.yml",
                "html_url": "https://github.com/JasonStys/applicant-evidence-studio/actions/runs/123",
                "status": "completed",
                "conclusion": "success",
            }
        ],
    }


def test_source_run_requires_exact_completed_main_identity():
    """Passing unrelated jobs cannot stand in for this exact source workflow."""
    successful_source_run(run_fixture(), SOURCE, "validate.yml")


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", True),
        ("id", 0),
        ("head_sha", "b" * 40),
        ("head_branch", "feature"),
        ("event", "workflow_dispatch"),
        ("path", ".github/workflows/other.yml"),
        ("html_url", "https://github.com/Other/repo/actions/runs/123"),
        ("status", "in_progress"),
        ("conclusion", "failure"),
        ("conclusion", "skipped"),
    ],
)
def test_source_run_rejects_unrelated_or_unfinished_metadata(field, value):
    """No guessed branch, event, completion, URL or skip substitutions."""
    data = run_fixture()
    data["workflow_runs"][0][field] = value
    with pytest.raises(ValueError):
        successful_source_run(data, SOURCE, "validate.yml")


def test_empty_duplicate_and_incomplete_run_pages_fail_closed():
    """An ambiguous response is not reduced to a convenient successful entry."""
    for data in (
        {"total_count": 0, "workflow_runs": []},
        {"total_count": 2, "workflow_runs": run_fixture()["workflow_runs"]},
        {"total_count": 2, "workflow_runs": run_fixture()["workflow_runs"] * 2},
    ):
        with pytest.raises(ValueError):
            successful_source_run(data, SOURCE, "validate.yml")


@pytest.mark.parametrize(
    "change",
    [
        {"draft": False},
        {"prerelease": True},
        {"target_commitish": "main"},
        {"target_commitish": "b" * 40},
        {"tag_name": "v0.2.0"},
    ],
)
def test_draft_never_accepts_published_or_different_source(change):
    """Old/public release assets cannot become an upload target."""
    data = {"draft": True, "prerelease": False, "tag_name": "v0.3.0", "target_commitish": SOURCE}
    draft_ready(data, SOURCE, "0.3.0")
    with pytest.raises(ValueError):
        draft_ready({**data, **change}, SOURCE, "0.3.0")


def assets_fixture():
    """Six distinct current platform artifacts, each with an independent provider digest."""
    names = [
        name
        for system, machine in (("windows", "amd64"), ("linux", "x86_64"), ("darwin", "arm64"))
        for name in names_for(system, machine, "0.3.0")
    ]
    return {"assets": [{"name": name, "size": 42, "digest": "sha256:" + "a" * 64} for name in names]}


def test_publication_requires_all_six_platform_assets():
    """Partial drafts are resumable, but cannot be published as complete releases."""
    data = assets_fixture()
    assert len(assets_ready(data, "0.3.0", complete=True)) == 6
    partial = {"assets": data["assets"][:2]}
    assert len(assets_ready(partial, "0.3.0", complete=False)) == 2
    with pytest.raises(ValueError):
        assets_ready(partial, "0.3.0", complete=True)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r["assets"].append(copy.deepcopy(r["assets"][0])),
        lambda r: r["assets"][0].update(name="unexpected.exe"),
        lambda r: r["assets"][0].update(size=True),
        lambda r: r["assets"][0].update(digest=None),
        lambda r: r["assets"][0].update(size=0),
    ],
)
def test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes(mutation):
    """Never infer a valid bundle from asset count alone."""
    data = assets_fixture()
    mutation(data)
    with pytest.raises(ValueError):
        assets_ready(data, "0.3.0", complete=True)
