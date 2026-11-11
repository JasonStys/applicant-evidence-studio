"""Jason Stys: exact-source draft-only uploads and complete portable verification.

Called only by the trusted main-branch release workflow. Never overwrites an
existing asset, accepts a published release, or logs token/environment values.
"""

# Index: argparse@8, json@9, os@10, platform@11, re@12, tempfile@13, tomllib@14, Path@15, MAX_DOWNLOAD@19, REPO@20, ROOT@21, command@22, digest@23, names_for@24, read_manifest@25, require@26, MAX_DOWNLOAD@30, REPO@31, ROOT@32, command@33, digest@34, names_for@35, read_manifest@36, require@37, version@41, version.value@43, api@48, api.endpoint@48, successful_source_run@53, successful_source_run.data@53, successful_source_run.source@53, successful_source_run.workflow@53, successful_source_run.rows@59, successful_source_run.run@61, source_ready@80, source_ready.source@80, source_ready.workflow@83, source_ready.data@84, security_ready@93, security_ready.alerts@93, security_ready.analyses@93, security_ready.source@93, security_ready.expected@97, security_ready.current@98, security_ready.row@99, security_ready.category@107, security_ready.name@110, security_ready.row@129, accepted_build@135, accepted_build.product_version@135, accepted_build.report@135, accepted_build.source@135, draft_ready@150, draft_ready.product_version@150, draft_ready.release@150, draft_ready.source@150, release_for_version@162, release_for_version.product_version@162, release_for_version.rows@162, release_for_version.row@165, release_for_version.matches@166, release_for_version.row@166, release_for_version.row@170, load_draft@175, load_draft.product_version@175, load_draft.source@175, load_draft.listed@177, load_draft.release@179, prepare_draft@185, prepare_draft.product_version@185, prepare_draft.source@185, prepare_draft.listed@188, prepare_draft.notes@190, prepare_draft.payload@192, prepare_draft.temporary@200, prepare_draft.path@201, assets_ready@207, assets_ready.complete@207, assets_ready.product_version@207, assets_ready.release@207, assets_ready.expected@209, assets_ready.machine@210, assets_ready.system@210, assets_ready.assets@212, assets_ready.result@214, assets_ready.asset@215, assets_ready.name@216, main@233, main.parser@235, main.args@237, main.source@238, main.product_version@246, main.release@253, main.attached@254, main.machine@256, main.system@256, main.names@257, main.report@258, main.files@262, main.name@262, main.file@263, main.binary@273, main.manifest@274, main.file@280, main.fresh@298, main.actual@300
import argparse
import json
import os
import platform
import re
import tempfile
import tomllib
from pathlib import Path

if __package__:
    from .portable_acceptance import (
        MAX_DOWNLOAD,
        REPO,
        ROOT,
        command,
        digest,
        names_for,
        read_manifest,
        require,
    )
else:
    from portable_acceptance import (
        MAX_DOWNLOAD,
        REPO,
        ROOT,
        command,
        digest,
        names_for,
        read_manifest,
        require,
    )


def version():
    """Read data-only product metadata without importing or executing the service."""
    value = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    require(bool(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value)), "Invalid release version")
    return value


def api(endpoint):
    """Read only fixed repository metadata; writes use explicit gh subcommands below."""
    return json.loads(command(["gh", "api", f"repos/{REPO}/{endpoint}"]))


def successful_source_run(data, source, workflow):
    """Require returned identity/status as well as server-side query filters."""
    require(
        isinstance(data, dict) and isinstance(data.get("workflow_runs"), list),
        "Malformed source workflow response",
    )
    rows = data["workflow_runs"]
    require(len(rows) == 1 and data.get("total_count") == 1, "Exactly one complete main-push run is required")
    run = rows[0]
    require(type(run.get("id")) is int and 0 < run["id"] < 2**63, "Invalid source workflow identity")
    require(
        run.get("head_sha") == source and run.get("head_branch") == "main" and run.get("event") == "push",
        "Source run does not match the requested main commit",
    )
    require(
        run.get("path") in {f".github/workflows/{workflow}", f".github/workflows/{workflow}@refs/heads/main"},
        "Wrong validation workflow",
    )
    require(
        run.get("html_url") == f"https://github.com/{REPO}/actions/runs/{run['id']}", "Foreign source run URL"
    )
    require(
        run.get("status") == "completed" and run.get("conclusion") == "success",
        "Source validation must complete successfully",
    )


def source_ready(source):
    """Require original/source/new native gates plus processed security results at exact current main."""
    require(api("git/ref/heads/main")["object"]["sha"] == source, "Main moved during release preparation")
    for workflow in ("validate.yml", "published-acceptance.yml", "native-validation.yml", "codeql.yml"):
        data = api(f"actions/workflows/{workflow}/runs?branch=main&event=push&head_sha={source}&per_page=100")
        successful_source_run(data, source, workflow)
    security_ready(
        api("code-scanning/analyses?ref=refs/heads/main&tool_name=CodeQL&per_page=100"),
        api("code-scanning/alerts?ref=refs/heads/main&state=open&per_page=1"),
        source,
    )


def security_ready(analyses, alerts, source):
    """Require actual processed analyses for all configured languages, with no open default-branch alert."""
    require(isinstance(analyses, list) and isinstance(alerts, list), "Malformed security result response")
    require(not alerts, "Open default-branch code-scanning alerts require review before a release")
    expected = {"/language:python", "/language:javascript-typescript", "/language:actions"}
    current = {}
    for row in analyses:
        if row.get("commit_sha") != source or row.get("ref") != "refs/heads/main":
            continue
        if (
            row.get("tool", {}).get("name") != "CodeQL"
            or row.get("analysis_key") != ".github/workflows/codeql.yml:analyze"
        ):
            continue
        category = next(
            (
                name
                for name in expected
                if row.get("category") == name
                or row.get("category") == ".github/workflows/codeql.yml:analyze" + name
            ),
            None,
        )
        if category is None:
            continue
        # The API returns newest first; do not replace the latest processed run
        # with an older successful analysis of the same source/category.
        if category not in current:
            current[category] = row
    require(set(current) == expected, "Every configured language requires processed exact-source CodeQL")
    require(
        all(
            row.get("error") == ""
            and row.get("warning") == ""
            and type(row.get("rules_count")) is int
            and row["rules_count"] > 0
            for row in current.values()
        ),
        "CodeQL must finish actual rules without errors or unresolved analyzer warnings",
    )


def accepted_build(report, source, product_version):
    """A source-server run, old/dirty archive or forced process cleanup cannot authorize an upload."""
    require(
        report.get("mode") == "built"
        and report.get("version") == product_version
        and report.get("built_source") == source
        and report.get("source_dirty") is False
        and report.get("native_ui", {}).get("compiled_native") is True
        and report["native_ui"].get("normal_owned_exit") is True
        and report["native_ui"].get("normal_exit_code") == 0
        and report["native_ui"].get("embedded_identity_matches_archive") is True,
        "Actual clean exact-source extracted native UI and normal-exit acceptance are required",
    )


def draft_ready(release, source, product_version):
    """Reject published or retargeted releases immediately before every upload/publication."""
    require(
        release.get("draft") is True and release.get("prerelease") is False,
        "A stable unpublished draft is required; published bytes are immutable",
    )
    require(
        release.get("tag_name") == "v" + product_version and release.get("target_commitish") == source,
        "Draft tag/version/source differs from this checked workflow",
    )


def release_for_version(rows, product_version):
    """Find one version in the bounded authenticated release listing, including an unpublished draft."""
    require(isinstance(rows, list) and len(rows) < 100, "Release listing is malformed or incomplete")
    require(all(isinstance(row, dict) for row in rows), "Malformed release entry")
    matches = [row for row in rows if row.get("tag_name") == "v" + product_version]
    require(len(matches) <= 1, "Ambiguous release version; no release changed")
    if not matches:
        return None
    row = matches[0]
    require(type(row.get("id")) is int and 0 < row["id"] < 2**63, "Invalid release identity")
    return row


def load_draft(source, product_version):
    """Use the actual release ID; a draft need not have a published tag-name endpoint."""
    listed = release_for_version(api("releases?per_page=100"), product_version)
    require(listed is not None, "Create the exact-source unpublished draft first")
    release = api("releases/" + str(listed["id"]))
    require(type(release.get("id")) is int and release["id"] == listed["id"], "Release identity changed")
    draft_ready(release, source, product_version)
    return release


def prepare_draft(source, product_version):
    """Create only a missing draft with structured JSON; never retarget or replace an existing release."""
    source_ready(source)
    listed = release_for_version(api("releases?per_page=100"), product_version)
    if listed is None:
        notes = ROOT / "docs/releases" / ("v" + product_version + ".md")
        require(notes.is_file() and notes.stat().st_size <= 128 * 1024, "Reviewed release notes required")
        payload = {
            "tag_name": "v" + product_version,
            "target_commitish": source,
            "name": "Applicant Evidence Studio " + product_version,
            "body": notes.read_text(encoding="utf-8"),
            "draft": True,
            "prerelease": False,
        }
        with tempfile.TemporaryDirectory(prefix="aes-release-request-") as temporary:
            path = Path(temporary) / "release.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            command(["gh", "api", f"repos/{REPO}/releases", "--method", "POST", "--input", str(path)])
    load_draft(source, product_version)


def assets_ready(release, product_version, *, complete):
    """Only the documented six platform artifacts may be attached to this draft."""
    expected = set()
    for system, machine in (("windows", "amd64"), ("linux", "x86_64"), ("darwin", "arm64")):
        expected.update(names_for(system, machine, product_version))
    assets = release.get("assets")
    require(isinstance(assets, list), "Missing draft asset metadata")
    result = {}
    for asset in assets:
        name = asset.get("name")
        require(name in expected and name not in result, "Unexpected or duplicate draft asset")
        require(
            type(asset.get("size")) is int and 0 < asset["size"] <= MAX_DOWNLOAD, "Invalid draft asset size"
        )
        require(
            isinstance(asset.get("digest"), str)
            and bool(re.fullmatch(r"sha256:[0-9a-f]{64}", asset["digest"])),
            "Provider SHA-256 digest is required",
        )
        result[name] = asset
    require(
        not complete or set(result) == expected, "All three verified platform packages/checksums are required"
    )
    return result


def main():
    """Perform one explicitly named release operation; there is no force/clobber path."""
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("source", "prepare", "draft", "upload", "verify"))
    args = parser.parse_args()
    source = os.environ.get("GITHUB_SHA", "")
    require(
        os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("GITHUB_REF") == "refs/heads/main"
        and os.environ.get("GITHUB_REPOSITORY") == REPO,
        "Release operations require the trusted main workflow",
    )
    require(bool(re.fullmatch(r"[0-9a-f]{40}", source)), "Exact workflow source SHA required")
    product_version = version()
    if args.operation == "source":
        source_ready(source)
        return
    if args.operation == "prepare":
        prepare_draft(source, product_version)
        return
    release = load_draft(source, product_version)
    attached = assets_ready(release, product_version, complete=args.operation == "verify")
    if args.operation == "upload":
        system, machine = platform.system().lower(), platform.machine().lower()
        names = names_for(system, machine, product_version)
        report = json.loads(
            (ROOT / "artifacts" / f"portable-acceptance-{system}.json").read_text(encoding="utf-8")
        )
        accepted_build(report, source, product_version)
        files = [(ROOT / "release" / name) for name in names]
        for file in files:
            require(file.is_file() and not file.is_symlink(), "Release asset must be a regular built file")
            require(file.stat().st_size <= MAX_DOWNLOAD, "Built asset exceeds release budget")
            if file.name in attached:
                require(
                    attached[file.name]["size"] == file.stat().st_size
                    and attached[file.name]["digest"] == "sha256:" + digest(file),
                    "Existing draft asset differs; refusing replacement",
                )
        require(digest(files[0]) == report.get("archive_sha256"), "Package changed after native acceptance")
        binary = "ApplicantEvidenceStudio" + (".exe" if system == "windows" else "")
        manifest = read_manifest(files[1], files[0].name, binary)
        require(
            manifest[files[0].name] == report["archive_sha256"]
            and manifest[binary] == report["binary_sha256"],
            "Checksum sidecar changed after native acceptance",
        )
        for file in files:
            if file.name not in attached:
                draft_ready(api("releases/" + str(release["id"])), source, product_version)
                # Fixed official upload host and verified numeric release ID;
                # no tag-name lookup, clobber flag or caller-selected endpoint.
                command(
                    [
                        "gh",
                        "api",
                        f"https://uploads.github.com/repos/{REPO}/releases/{release['id']}/assets?name={file.name}",
                        "--method",
                        "POST",
                        "-H",
                        "Content-Type: application/octet-stream",
                        "--input",
                        str(file),
                    ]
                )
            fresh = api("releases/" + str(release["id"]))
            draft_ready(fresh, source, product_version)
            actual = assets_ready(fresh, product_version, complete=False)[file.name]
            require(
                actual["digest"] == "sha256:" + digest(file) and actual["size"] == file.stat().st_size,
                "Provider asset differs from accepted local bytes",
            )
    elif args.operation == "verify":
        source_ready(source)
        print("All six immutable draft assets and exact-source gates verified; release remains unpublished.")


if __name__ == "__main__":
    main()
