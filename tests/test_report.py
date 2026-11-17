"""Tests for terminal/JSON/HTML rendering."""
import json
import sys
from pathlib import Path

from receipts import claims, cli, policy, report, snapshot, verdict


def make_verdict(tmp_path, text="All tests pass."):
    current = snapshot.capture(tmp_path)
    c = verdict.Context(
        root=Path(tmp_path), current=current, baseline=None, diff=None,
        config={}, limits=policy.DEFAULT_LIMITS, allow_run=False,
        allow_commands=False, timeout=10, required=[], strict=False,
    )
    return verdict.verify(claims.parse(text), c)


def test_terminal_contains_status(tmp_path):
    out = report.render(make_verdict(tmp_path), "terminal")
    assert "INDETERMINATE" in out
    assert "receipts" in out


def test_json_output_is_parseable_and_complete(tmp_path):
    out = report.render(make_verdict(tmp_path), "json")
    doc = json.loads(out)
    assert "results" in doc and "counts" in doc and "tree_sha256" in doc


def test_html_is_self_contained_offline(tmp_path):
    out = report.render(make_verdict(tmp_path), "html")
    assert "<html" in out and "<style" in out
    assert "http://" not in out and "https://" not in out
    assert "<script" not in out.lower()
    assert "cdn" not in out.lower()


def test_html_escapes_hostile_data(tmp_path):
    hostile = verdict.Result(
        claim_id="span.matches", subject="<script>alert(1)</script>",
        status="FAIL", reason="<img src=x onerror=alert(1)> & done",
        evidence={"note": "<b>bold</b>"},
    )
    v = verdict.Verdict(results=[hostile], counts={"FAIL": 1}, tree_sha256="x",
                        generated_at="2026-01-01T00:00:00Z", version="1.0.0", strict=False)
    out = report.render(v, "html")
    assert "<script>alert(1)</script>" not in out
    assert "&lt;script&gt;" in out
    assert "<img src=x onerror=alert(1)>" not in out
    assert "&lt;img" in out
    assert "<b>bold</b>" not in out


def test_render_unknown_format_raises(tmp_path):
    try:
        report.render(make_verdict(tmp_path), "pdf")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


# ---------------- CLI ----------------

def test_cli_version_and_claims():
    assert cli.main(["version"]) == 0
    assert cli.main(["claims"]) == 0


def test_cli_check_no_run_is_indeterminate(tmp_path, capsys):
    code = cli.main(["check", "--text", "All tests pass.", "--no-run", "--repo", str(tmp_path)])
    out = capsys.readouterr().out
    assert code == 0
    assert "INDETERMINATE" in out


def test_cli_check_strict_indeterminate(tmp_path):
    code = cli.main(["check", "--text", "No new dependencies were added.", "--no-run",
                     "--strict", "--repo", str(tmp_path)])
    assert code == 3


def test_cli_check_json(tmp_path, capsys):
    code = cli.main(["check", "--text", "All tests pass.", "--no-run", "--json",
                     "--repo", str(tmp_path)])
    doc = json.loads(capsys.readouterr().out)
    assert code == 0 and doc["results"][0]["status"] == "INDETERMINATE"


def test_cli_writes_html(tmp_path, capsys):
    out = tmp_path / "report.html"
    code = cli.main(["check", "--text", "All tests pass.", "--no-run", "--repo", str(tmp_path),
                     "--html", str(out)])
    assert code == 0 and out.exists()
    assert "<html" in out.read_text(encoding="utf-8")


def test_cli_baseline_and_run(tmp_path, capsys):
    (tmp_path / "a.py").write_text("one", encoding="utf-8")
    assert cli.main(["baseline", "--repo", str(tmp_path)]) == 0
    assert (tmp_path / ".receipts" / "baseline.json").exists()
    assert cli.main(["run", "--repo", str(tmp_path), "--", sys.executable,
                     "-c", "print('ok')"]) == 0
    assert (tmp_path / ".receipts" / "session.json").exists()


def test_cli_missing_file_is_usage_error(tmp_path):
    assert cli.main(["check", "--file", str(tmp_path / "nope.md"), "--repo", str(tmp_path)]) == 2


def test_cli_prose_cannot_inject_shell(tmp_path, capsys):
    marker = tmp_path / "pwned.txt"
    text = "All tests pass. ; touch pwned.txt && echo $(whoami)"
    cli.main(["check", "--text", text, "--no-run", "--repo", str(tmp_path)])
    assert not marker.exists()


def test_cli_lying_agent_exit_one(tmp_path, capsys):
    cfg = {"commands": {"tests": [sys.executable, "-c",
            "import sys; print('collected 3 items'); print('1 passed, 2 failed'); sys.exit(1)"]}}
    (tmp_path / ".receipts.json").write_text(json.dumps(cfg), encoding="utf-8")
    code = cli.main(["check", "--text", "All tests pass.", "--repo", str(tmp_path)])
    assert code == 1
    assert "FAIL" in capsys.readouterr().out
