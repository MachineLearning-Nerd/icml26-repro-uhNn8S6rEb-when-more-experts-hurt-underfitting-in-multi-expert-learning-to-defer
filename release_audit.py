import hashlib
import json
import re
import sys
from pathlib import Path


ALLOWED_VERDICTS = {"VERIFIED", "FALSIFIED", "BLOCKED"}
REQUIRED_EVIDENCE_FIELDS = ["code", "raw", "checker", "control", "environment"]
TEXT_SUFFIXES = {"", ".css", ".html", ".js", ".json", ".md", ".py", ".toml", ".txt", ".lock"}
SECRET_PATTERNS = [
    re.compile(r"hf_[A-Za-z0-9]{24,}"),
    re.compile(r"ghp_[A-Za-z0-9]{24,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{24,}"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flatten(node: dict) -> list[dict]:
    return [node, *[descendant for child in node.get("children", []) for descendant in flatten(child)]]


def linked_paths(markdown_path: Path, candidate: Path) -> set[str]:
    links = set()
    for destination in re.findall(r"\[[^]]*\]\(([^)]+)\)", markdown_path.read_text()):
        destination = destination.split("#", 1)[0]
        if not destination or destination.startswith(("http://", "https://", "mailto:", "#/")):
            continue
        resolved = (markdown_path.parent / destination).resolve()
        resolved.relative_to(candidate.resolve())
        links.add(resolved.relative_to(candidate.resolve()).as_posix())
    return links


def main() -> None:
    candidate = Path(sys.argv[1]).resolve()
    judged_manifest = json.loads(Path(sys.argv[2]).read_text())
    judged_files = judged_manifest["files"]
    candidate_files = {
        path.relative_to(candidate).as_posix(): path
        for path in candidate.rglob("*")
        if path.is_file() and ".cache" not in path.parts
    }
    assert set(judged_files) <= set(candidate_files)

    mutable = set(judged_manifest["mutable_root_paths"])
    revision = judged_manifest["revision"]
    for relative, expected_sha in judged_files.items():
        if relative not in mutable:
            assert sha256(candidate_files[relative]) == expected_sha
            continue
        archived = candidate / "historical" / f"judged-{revision}" / relative
        assert archived.is_file()
        assert sha256(archived) == expected_sha

    logbook = json.loads((candidate / "logbook.json").read_text())
    archived_logbook = json.loads(
        (candidate / "historical" / f"judged-{revision}" / "logbook.json").read_text()
    )
    nodes = flatten(logbook["root"])
    assert len({node["slug"] for node in nodes}) == len(nodes)
    assert all((candidate / node["file"]).is_file() for node in nodes)
    assert logbook["root"]["children"][0]["slug"] == "current-verification"
    historical = [node for node in nodes if node["title"] == "Historical rejected baseline"]
    assert len(historical) == 1
    assert historical[0]["children"] == [archived_logbook["root"]]

    visibility_path = candidate / "evidence" / "release" / "visibility_matrix.json"
    visibility = json.loads(visibility_path.read_text())
    rows = visibility["rows"]
    assert [row["claim"] for row in rows] == [1, 2, 3, 4, 5, 6]
    tree_files = {node["file"] for node in nodes}
    for row in rows:
        assert row["reviewer_verdict"] in ALLOWED_VERDICTS
        assert row["canonical_page"] in tree_files
        assert row["data_inline"] is True
        assert row["exact_claim_tested"] is True
        assert row["limitations_inline"] is True
        assert row["source_quantifiers_inline"] is True
        page = candidate / row["canonical_page"]
        direct_links = linked_paths(page, candidate)
        for field in REQUIRED_EVIDENCE_FIELDS:
            assert row[field]
            for relative in row[field]:
                assert relative in candidate_files
                assert relative in direct_links

    root_file = candidate / logbook["root"]["file"]
    root_text = root_file.read_text()
    assert "Previous live judged score: `5/12`" in root_text
    assert "forecast" in root_text.lower()
    assert "awaiting judge" not in root_text.lower()
    assert "12/12" not in root_text or "forecast" in root_text.lower()

    scanned = 0
    for relative, path in candidate_files.items():
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(errors="replace")
        assert not any(pattern.search(text) for pattern in SECRET_PATTERNS), relative
        scanned += 1

    print(
        json.dumps(
            {
                "verdict": "PASS",
                "judged_file_subset": True,
                "unchanged_historical_files": len(judged_files) - len(mutable),
                "archived_mutable_files": len(mutable),
                "navigation_nodes": len(nodes),
                "current_verification_first": True,
                "visibility_rows_complete": len(rows),
                "text_files_scanned_for_secrets": scanned,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
