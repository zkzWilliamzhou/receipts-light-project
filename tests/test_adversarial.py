"""End-to-end attack fixtures: a lying agent, laundering, forgery, and fuzz."""
import json
import random
import string
import sys
from pathlib import Path

import pytest

from receipts import claims, cli, policy, report, safepath, snapshot, verdict


def build_ctx(root, *, baseline=None, config=None, allow_run=True, required=None, strict=False):
    current = snapshot.capture(root)
    d = snapshot.diff(baseline, current) if baseline is not None else None
    return verdict.Context(
        root=Path(root), current=current, baseline=baseline, diff=d,
        config=config or {}, limits=policy.DEFAULT_LIMITS,
        allow_run=allow_run, allow_commands=False, timeout=15,
        required=required or [], strict=strict,
    )


def test_hero_demo_lying_agent_is_caught(tmp_path, capsys):
    """The 10-second demo: agent says green, runner says red."""
    cfg = {"commands": {"tests": [sys.executable, "-c",
            "import sys; print('collected 4 items'); print('2 passed, 2 failed in 0.2s'); sys.exit(1)"]}}
    (tmp_path / ".receipts.json").write_text(json.dumps(cfg), encoding="utf-8")
    code = cli.main(["check", "--text", "All tests pass. The build succeeds. No new dependencies.",
                     "--repo", str(tmp_path)])
    assert code == 1
    out = capsys.readouterr().out
    assert "FAIL" in out
    assert "tests.pass" in out


def test_laundered_command_never_passes(tmp_path):
    cfg = {"commands": {"tests": [sys.executable, "-m", "pytest", "-k", "trivial", "-q"]}}
    v = verdict.verify(claims.parse("All tests pass."), build_ctx(tmp_path, config=cfg))
    r = [x for x in v.results if x.claim_id == "tests.pass"][0]
    assert r.status != "PASS"


def test_stale_baseline_detected(tmp_path):
    (tmp_path / "a.py").write_text("one", encoding="utf-8")
    base = snapshot.capture(tmp_path)
    (tmp_path / "a.py").write_text("two", encoding="utf-8")
    (tmp_path / "b.py").write_text("new", encoding="utf-8")
    v = verdict.verify(claims.parse("No files were modified."), build_ctx(tmp_path, baseline=base))
    r = v.results[0]
    assert r.status == "FAIL"
    assert "b.py" in json.dumps(r.evidence)


def test_forged_span_is_rejected(tmp_path):
    (tmp_path / "a.py").write_text("legitimate content", encoding="utf-8")
    doc = {"version": 1, "claims": [{"id": "span.matches", "subject": "a.py",
            "evidence": {"path": "a.py", "start": 0, "end": 10, "expected": "FABRICATED"}}]}
    v = verdict.verify(claims.parse(json.dumps(doc)), build_ctx(tmp_path))
    assert v.results[0].status == "FAIL"


def test_html_xss_from_prose(tmp_path):
    text = "All tests pass <script>alert(document.cookie)</script>"
    v = verdict.verify(claims.parse(text), build_ctx(tmp_path, allow_run=False))
    html = report.render(v, "html")
    assert "<script>alert(document.cookie)</script>" not in html
    assert "&lt;script&gt;" in html


def test_duplicate_json_keys_rejected(tmp_path):
    path = tmp_path / "receipt.json"
    path.write_text('{"version":1,"claims":[],"claims":[]}', encoding="utf-8")
    assert cli.main(["check", "--file", str(path), "--repo", str(tmp_path)]) == 2


def test_oversized_input_rejected(tmp_path):
    path = tmp_path / "big.txt"
    path.write_text("a" * (policy.MAX_TEXT_BYTES + 1), encoding="utf-8")
    assert cli.main(["check", "--file", str(path), "--repo", str(tmp_path)]) == 2


def test_fuzz_paths_never_escape_or_crash(tmp_path):
    rng = random.Random(1337)
    alphabet = string.printable + "\u0430\u00e9\u4e2d"
    for _ in range(400):
        s = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 60)))
        try:
            p = safepath.canonical(s, tmp_path)
            assert str(p).startswith(str(tmp_path.resolve()))
        except (safepath.UnsafePath, ValueError, OSError):
            pass


def test_fuzz_prose_never_crashes():
    rng = random.Random(20261113)
    alphabet = string.printable + "\u00e9\u4e2d\U0001f600"
    for _ in range(300):
        s = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 300)))
        try:
            p = claims.parse(s)
            assert len(p.claims) <= policy.MAX_CLAIMS
        except ValueError:
            pass


def test_nul_and_control_chars_rejected(tmp_path):
    with pytest.raises(safepath.UnsafePath):
        safepath.canonical("a\x00b.py", tmp_path)


def test_git_dir_is_never_captured(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("secret", encoding="utf-8")
    (tmp_path / "a.py").write_text("ok", encoding="utf-8")
    s = snapshot.capture(tmp_path)
    assert not any(k.startswith(".git") for k in s.files)


def test_banned_constructs_absent():
    """Static supply-chain gate: no shell, eval, pickle or network imports."""
    import ast
    root = Path(__file__).resolve().parents[1] / "receipts"
    banned_calls = {"eval", "exec", "system"}
    banned_imports = {"pickle", "requests", "urllib.request", "socket", "subprocess.list2cmdline"}
    for f in sorted(root.glob("*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in banned_calls, f"{f}: {node.func.id}"
            if isinstance(node, ast.Import):
                for a in node.names:
                    assert a.name not in banned_imports, f"{f}: {a.name}"
            if isinstance(node, ast.ImportFrom):
                assert (node.module or "") not in banned_imports, f"{f}: {node.module}"
            if isinstance(node, ast.keyword) and node.arg == "shell":
                if isinstance(node.value, ast.Constant) and node.value.value is True:
                    raise AssertionError(f"{f}: shell=True")
