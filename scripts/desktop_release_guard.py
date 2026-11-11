"""Jason Stys: exact-source draft-only uploads and complete portable verification.

Called only by the trusted main-branch release workflow. Never overwrites an
existing asset, accepts a published release, or logs token/environment values.
"""

# Index: argparse@8, json@9, os@10, platform@11, re@12, tomllib@13, MAX_DOWNLOAD@17, REPO@18, ROOT@19, command@20, digest@21, names_for@22, read_manifest@23, require@24, MAX_DOWNLOAD@28, REPO@29, ROOT@30, command@31, digest@32, names_for@33, read_manifest@34, require@35, version@39, version.value@41, api@46, api.endpoint@46, successful_source_run@51, successful_source_run.data@51, successful_source_run.source@51, successful_source_run.workflow@51, successful_source_run.rows@57, successful_source_run.run@59, source_ready@78, source_ready.source@78, source_ready.workflow@81, source_ready.data@82, security_ready@91, security_ready.alerts@91, security_ready.analyses@91, security_ready.source@91, security_ready.expected@95, security_ready.current@96, security_ready.row@97, security_ready.category@105, security_ready.name@108, security_ready.row@127, accepted_build@133, accepted_build.product_version@133, accepted_build.report@133, accepted_build.source@133, draft_ready@148, draft_ready.product_version@148, draft_ready.release@148, draft_ready.source@148, assets_ready@160, assets_ready.complete@160, assets_ready.product_version@160, assets_ready.release@160, assets_ready.expected@162, assets_ready.machine@163, assets_ready.system@163, assets_ready.assets@165, assets_ready.result@167, assets_ready.asset@168, assets_ready.name@169, main@186, main.parser@188, main.args@190, main.source@191, main.product_version@199, main.tag@200, main.release@204, main.attached@206, main.machine@208, main.system@208, main.names@209, main.report@210, main.files@214, main.name@214, main.file@215, main.binary@225, main.manifest@226, main.file@232, main.fresh@236, main.actual@238
import argparse
import json
import os
import platform
import re
import tomllib

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
    parser.add_argument("operation", choices=("source", "draft", "upload", "verify"))
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
    tag = "v" + product_version
    if args.operation == "source":
        source_ready(source)
        return
    release = api("releases/tags/" + tag)
    draft_ready(release, source, product_version)
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
                draft_ready(api("releases/tags/" + tag), source, product_version)
                command(["gh", "release", "upload", tag, str(file), "--repo", REPO])
            fresh = api("releases/tags/" + tag)
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
