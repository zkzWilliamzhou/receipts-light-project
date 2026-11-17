"""Regression fixtures for findings from review rounds 1-8.

Each test is tied to a specific finding in docs/REVIEW.md. If a mitigation is
removed, the corresponding test fails.
"""
import json
import os
import sys
from pathlib import Path

import pytest

from receipts import claims, cli, policy, report, runner, safepath, snapshot, verdict


def ctx(root, *, config=None, allow_run=True, strict=False):
    current = snapshot.capture(root)
    return verdict.Context(
        root=Path(root), current=current, baseline=None, diff=None,
        config=config or {}, limits=policy.DEFAULT_LIMITS, allow_run=allow_run,
        allow_commands=False, timeout=10, required=[], strict=strict,
    )


PY_PASS = "print('collected 3 items'); print('3 passed in 0.1s')"


# Round 1 - path and filesystem safety

def test_r1_hardlinked_file_is_refused(tmp_path):
    (tmp_path / "a.py").write_text("x", encoding="utf-8")
    try:
        os.link(tmp_path / "a.py", tmp_path / "b.py")
    except OSError:
        pytest.skip("hardlinks unavailable")
    with pytest.raises(safepath.UnsafePath):
        safepath.safe_bytes("b.py", tmp_path)


def test_r1_o_nofollow_does_not_break_plain_read(tmp_path):
    (tmp_path / "a.py").write_bytes(b"hello world")
    assert safepath.safe_bytes("a.py", tmp_path) == b"hello world"


def test_r1_symlink_to_inside_root_is_allowed(tmp_path):
    (tmp_path / "a.py").write_text("inside", encoding="utf-8")
    try:
        (tmp_path / "alias.py").symlink_to(tmp_path / "a.py")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    assert safepath.safe_bytes("alias.py", tmp_path) == b"inside"


# Round 2 - command execution safety

@pytest.mark.parametrize("bad_timeout", [-5, float("nan"), "oops"])
def test_r2_timeout_is_clamped_or_rejected(tmp_path, bad_timeout):
    if bad_timeout == "oops":
        with pytest.raises(ValueError):
            runner.run([sys.executable, "-c", "print(1)"], tmp_path, timeout=bad_timeout)
        return
    obs = runner.run([sys.executable, "-c", "print(1)"], tmp_path, timeout=bad_timeout)
    assert obs.exit_code == 0


def test_r2_no_shell_metacharacter_execution(tmp_path):
    obs = runner.run([sys.executable, "-c", "print('$(touch pwned)')"], tmp_path)
    assert not (tmp_path / "pwned").exists()
    assert obs.exit_code == 0


# Round 3 - parser and input safety

def test_r3_bracket_prefixed_prose_is_still_parsed():
    p = claims.parse("[WIP] All tests pass.")
    assert "tests.pass" in [c.id for c in p.claims]


def test_r3_brace_prose_without_receipt_fields_is_still_prose():
    p = claims.parse("{draft} All tests pass.")
    assert "tests.pass" in [c.id for c in p.claims]


def test_r3_extreme_json_depth_raises_value_error():
    with pytest.raises(ValueError):
        claims.strict_loads("[" * 2000 + "0" + "]" * 2000)


def test_r3_duplicate_keys_still_rejected():
    with pytest.raises(ValueError):
        claims.strict_loads('{"version":1,"claims":[],"claims":[]}')


# Round 4 - claim semantics and laundering

def test_r4_require_known_runner_blocks_handwritten_summary(tmp_path):
    cfg = {"require_known_runner": True,
           "commands": {"tests": [sys.executable, "-c", PY_PASS]}}
    v = verdict.verify(claims.parse("All tests pass."), ctx(tmp_path, config=cfg))
    r = v.results[0]
    assert r.status == "INDETERMINATE"
    assert "recognised" in r.reason.lower()


def test_r4_coverage_note_is_present(tmp_path):
    cfg = {"commands": {"tests": [sys.executable, "-c", PY_PASS]}}
    v = verdict.verify(claims.parse("All tests pass."), ctx(tmp_path, config=cfg))
    assert "coverage_note" in v.results[0].evidence


def test_r4_semantic_claim_never_passes(tmp_path):
    v = verdict.verify(claims.parse("Public API unchanged."), ctx(tmp_path))
    assert v.results[0].status == "INDETERMINATE"


# Round 5 - snapshot and determinism

def test_r5_toctou_downgrades_pass(tmp_path):
    code = ("import pathlib; print('collected 3 items'); print('3 passed in 0.1s'); "
            "pathlib.Path('late.txt').write_text('surprise')")
    cfg = {"commands": {"tests": [sys.executable, "-c", code]}}
    v = verdict.verify(claims.parse("All tests pass."), ctx(tmp_path, config=cfg))
    r = v.results[0]
    assert r.status == "INDETERMINATE"
    assert r.evidence.get("repo_changed_during_verify") is True


def test_r5_text_is_capped_per_file(tmp_path):
    (tmp_path / "big.py").write_text("x" * 600_000, encoding="utf-8")
    s = snapshot.capture(tmp_path)
    assert len(s.texts["big.py"]) <= policy.MAX_TEXT_PER_FILE


def test_r5_baseline_roundtrip_is_deterministic(tmp_path):
    (tmp_path / "a.py").write_text("one", encoding="utf-8")
    s = snapshot.capture(tmp_path)
    assert snapshot.from_json(snapshot.to_json(s)).tree_sha256 == s.tree_sha256


# Round 6 - reporting safety and UX

def test_r6_ansi_escape_cannot_spoof_terminal(tmp_path):
    v = verdict.verify(claims.parse("All tests pass."), ctx(tmp_path, allow_run=False))
    v.results[0].subject = "\x1b[2K\x1b[32m[PASS] fake\x1b[0m"
    out = report.render(v, "terminal")
    assert "\x1b" not in out
    assert "[PASS] fake" in out  # text is visible, not executable


def test_r6_html_has_no_external_urls(tmp_path):
    v = verdict.verify(claims.parse("All tests pass."), ctx(tmp_path, allow_run=False))
    out = report.render(v, "html")
    assert "http://" not in out and "https://" not in out
    assert "<script" not in out.lower()


# Round 7 - correctness and edge cases

def test_r7_empty_input_is_indeterminate(tmp_path):
    v = verdict.verify(claims.parse(""), ctx(tmp_path))
    assert v.results[0].claim_id == "input.no_claims"
    assert v.results[0].status == "INDETERMINATE"


def test_r7_empty_input_strict_exit_code(tmp_path):
    assert cli.main(["check", "--text", "", "--no-run", "--repo", str(tmp_path)]) == 0
    assert cli.main(["check", "--text", "", "--no-run", "--strict",
                     "--repo", str(tmp_path)]) == 3


def test_r7_claim_cap_error_is_surfaced(tmp_path):
    v = verdict.verify(claims.parse(" ".join(["All tests pass."] * 250)),
                       ctx(tmp_path, allow_run=False))
    assert any(r.claim_id == "input.parse_note" for r in v.results)


# Round 8 - supply chain and release

def test_r8_no_third_party_runtime_imports():
    import ast
    root = Path(__file__).resolve().parents[1] / "receipts"
    stdlib_ok = {
        "__future__", "argparse", "dataclasses", "datetime", "hashlib", "html",
        "json", "os", "pathlib", "posixpath", "re", "subprocess", "sys",
        "threading", "time", "zipapp", "collections", "typing",
    }
    for f in sorted(root.glob("*.py")):
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                for a in node.names:
                    assert a.name.split(".")[0] in stdlib_ok, (f, a.name)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                assert (node.module or "").split(".")[0] in stdlib_ok, (f, node.module)


def test_r8_version_matches_package():
    import receipts
    assert receipts.__version__ == policy.VERSION


def test_r8_json_report_is_self_describing(tmp_path):
    v = verdict.verify(claims.parse("All tests pass."), ctx(tmp_path, allow_run=False))
    doc = json.loads(report.render(v, "json"))
    assert doc["version"] == policy.VERSION
    assert "tree_sha256" in doc and "results" in doc
