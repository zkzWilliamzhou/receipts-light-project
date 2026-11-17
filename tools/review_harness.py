"""Eight independent review lenses with fresh runtime evidence.

Run after any change. Writes docs/REVIEW_EVIDENCE.txt and exits 1 if any lens
fails. This is the automated half of docs/REVIEW.md; the human half is the
findings log itself.
"""
from __future__ import annotations

import ast
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from receipts import claims, cli, policy, report, runner, safepath, snapshot, verdict  # noqa: E402

EVIDENCE = ROOT / "docs" / "REVIEW_EVIDENCE.txt"
LINES = []


def note(text):
    LINES.append(text)
    print(text)


def check(name, fn):
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001 - a raised error is a failed lens
        ok, detail = False, f"{type(exc).__name__}: {exc}"
    note(f"    [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    return bool(ok)


def round1(root):
    note("ROUND 1  path & filesystem safety")
    out = []
    out.append(check("traversal / absolute / windows paths rejected", lambda: (
        all(_raises(lambda p=p: safepath.canonical(p, root))
            for p in ["../x", "a/../../b", "/etc/passwd", "C:\\W\\x", "a\x00b"]),
        "5 hostile forms refused")))
    (root / ".git").mkdir(exist_ok=True)
    (root / ".git" / "config").write_text("x", encoding="utf-8")
    out.append(check(".git excluded from capture", lambda: (
        not any(k.startswith(".git") for k in snapshot.capture(root).files),
        "no .git entry in snapshot")))
    (root / "big.bin").write_bytes(b"x" * 100)
    out.append(check("file size cap enforced", lambda: (
        _raises(lambda: safepath.safe_bytes("big.bin", root, policy.Limits(max_file_bytes=10))),
        "oversize read refused")))
    out.append(check("hardlink refused", lambda: _hardlink_check(root)))
    return all(out)


def round2(root):
    note("ROUND 2  command execution safety")
    out = []
    bad = []
    for p in (ROOT / "receipts").glob("*.py"):
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        bad += [n.func.id for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id in {"eval", "exec", "system"}]
        bad += [f"shell=True@{n.lineno}" for n in ast.walk(tree)
                if isinstance(n, ast.keyword) and n.arg == "shell"
                and isinstance(n.value, ast.Constant) and n.value.value is True]
    out.append(check("no eval/exec/system/shell=True", lambda: (not bad, f"{len(bad)} banned constructs")))
    out.append(check("selection flags refused", lambda: (
        runner.has_selection([sys.executable, "-m", "pytest", "-k", "trivial"])
        and not runner.has_selection([sys.executable, "-m", "pytest", "-q"]),
        "-k refused, -q allowed")))
    out.append(check("timeout clamped", lambda: (
        runner.run([sys.executable, "-c", "print(1)"], root, timeout=-5).exit_code == 0,
        "negative timeout still executes safely")))
    env = runner.scrubbed_env()
    out.append(check("secret env names scrubbed", lambda: (
        not any("SECRET" in k or "TOKEN" in k for k in env), f"{len(env)} allow-listed vars")))
    return all(out)


def round3(root):
    note("ROUND 3  parser & input safety")
    out = []
    out.append(check("duplicate JSON keys rejected", lambda: (
        _raises(lambda: claims.strict_loads('{"a":1,"a":2}')), "duplicate refused")))
    out.append(check("deep JSON rejected", lambda: (
        _raises(lambda: claims.strict_loads("[" * 2000 + "0" + "]" * 2000)), "depth refused")))
    out.append(check("trailing garbage rejected", lambda: (
        _raises(lambda: claims.strict_loads('{"a":1} trailing')), "trailing refused")))
    out.append(check("bracket/brace prose parsed", lambda: (
        "tests.pass" in [c.id for c in claims.parse("[WIP] All tests pass.").claims]
        and "tests.pass" in [c.id for c in claims.parse("{draft} All tests pass.").claims],
        "PR-body prefixes accepted as prose")))
    out.append(check("input size cap", lambda: (
        _raises(lambda: claims.parse("x" * (policy.MAX_TEXT_BYTES + 1))), "1 MiB cap")))
    return all(out)


def round4(root):
    note("ROUND 4  claim semantics & laundering")
    out = []
    cfg = {"commands": {"tests": [sys.executable, "-m", "pytest", "-k", "trivial"]}}
    out.append(check("filtered run never PASS", lambda: (
        verdict.verify(claims.parse("All tests pass."), _ctx(root, cfg)).results[0].status != "PASS",
        "INDETERMINATE")))
    cfg2 = {"commands": {"tests": [sys.executable, "-c", "print('collected 0 items'); print('no tests ran')"]}}
    out.append(check("zero collected never PASS", lambda: (
        verdict.verify(claims.parse("All tests pass."), _ctx(root, cfg2)).results[0].status != "PASS",
        "INDETERMINATE")))
    cfg3 = {"commands": {"tests": [sys.executable, "-c", "print('collected 3 items'); print('3 passed')"]}}
    out.append(check("numeric mismatch FAIL", lambda: (
        verdict.verify(claims.parse("34/34 tests pass"), _ctx(root, cfg3)).results[0].status == "FAIL",
        "34 vs 3 reported")))
    out.append(check("semantic claim never PASS", lambda: (
        verdict.verify(claims.parse("Public API unchanged."), _ctx(root)).results[0].status == "INDETERMINATE",
        "INDETERMINATE")))
    out.append(check("unknown claim id UNCHECKABLE", lambda: (
        verdict.verify(claims.parse('{"version":1,"claims":[{"id":"magic.proof"}]}'),
                       _ctx(root)).results[0].status == "UNCHECKABLE", "UNCHECKABLE")))
    return all(out)


def round5(root):
    note("ROUND 5  snapshot & determinism")
    out = []
    (root / "a.py").write_text("one", encoding="utf-8")
    s1, s2 = snapshot.capture(root), snapshot.capture(root)
    out.append(check("capture deterministic", lambda: (s1.tree_sha256 == s2.tree_sha256, "identical tree digest")))
    out.append(check("baseline JSON roundtrip", lambda: (
        snapshot.from_json(snapshot.to_json(s1)).tree_sha256 == s1.tree_sha256, "digest preserved")))
    (root / "big.py").write_text("x" * 600_000, encoding="utf-8")
    out.append(check("retained text capped", lambda: (
        len(snapshot.capture(root).texts["big.py"]) <= policy.MAX_TEXT_PER_FILE, "512 KiB cap")))
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "golden.py"), "--check"],
                       cwd=ROOT, capture_output=True, text=True)
    out.append(check("golden byte-identical", lambda: (r.returncode == 0, r.stdout.strip().splitlines()[0])))
    return all(out)


def round6(root):
    note("ROUND 6  reporting safety & UX")
    out = []
    v = verdict.verify(claims.parse("All tests pass."), _ctx(root))
    v.results[0].subject = "<script>alert(1)</script> https://evil.example \x1b[2K"
    h = report.render(v, "html")
    out.append(check("HTML escaped and offline", lambda: (
        "<script>alert(1)</script>" not in h and "&lt;script&gt;" in h
        and "http://" not in h and "https://" not in h and "<script" not in h.lower(),
        "escaped, no URLs, no script tag")))
    t = report.render(v, "terminal")
    out.append(check("terminal ANSI stripped", lambda: ("\x1b" not in t, "no escape byte")))
    d = json.loads(report.render(v, "json"))
    out.append(check("JSON self-describing", lambda: (
        all(k in d for k in ("results", "counts", "tree_sha256", "version")), "4 keys present")))
    return all(out)


def round7(root):
    note("ROUND 7  correctness & edge cases")
    import contextlib
    import io
    out = []
    out.append(check("negation not compiled as success", lambda: (
        "tests.pass" not in [c.id for c in claims.parse("Tests do not pass yet.").claims]
        and "tests.pass" in [c.id for c in claims.parse("All tests pass.").claims],
        "guarded")))
    out.append(check("numeric claims extracted", lambda: (
        claims.parse("34/34 tests pass").claims[0].params.get("expected_passed") == 34, "34")))
    out.append(check("empty input INDETERMINATE", lambda: (
        verdict.verify(claims.parse(""), _ctx(root)).results[0].status == "INDETERMINATE",
        "input.no_claims")))
    def exit_matrix():
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return (cli.main(["check", "--text", "", "--no-run", "--repo", str(root)]) == 0
                    and cli.main(["check", "--text", "", "--no-run", "--strict",
                                  "--repo", str(root)]) == 3
                    and cli.main(["check", "--file", str(root / "nope"),
                                  "--repo", str(root)]) == 2)
    out.append(check("exit codes 0/1/2/3", lambda: (exit_matrix(), "0 / 3 / 2 verified")))
    return all(out)


def round8(root):
    note("ROUND 8  supply chain & release")
    out = []
    stdlib = {"__future__", "argparse", "dataclasses", "datetime", "hashlib", "html",
              "json", "os", "pathlib", "posixpath", "re", "subprocess", "sys",
              "threading", "time", "zipapp", "shutil", "stat", "tempfile",
              "difflib", "collections", "typing"}
    bad = []
    for p in (ROOT / "receipts").glob("*.py"):
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Import):
                bad += [a.name for a in n.names if a.name.split(".")[0] not in stdlib]
            elif isinstance(n, ast.ImportFrom) and n.level == 0:
                if (n.module or "").split(".")[0] not in stdlib:
                    bad.append(n.module or "")
    out.append(check("stdlib-only runtime", lambda: (not bad, f"{len(bad)} foreign imports")))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    prohibited = ["hallucination-free", "guaranteed 105", "we prevent agents from lying",
                  "a PASS means the change is safe", "cryptographically signed HTML report"]
    found = [x for x in prohibited if x in readme]
    non_goals = readme.count("does not") + readme.count("It does not")
    out.append(check("README scoped honestly", lambda: (
        not found and non_goals >= 10, f"{non_goals} explicit non-goals, 0 overclaims")))
    pyz = ROOT / "receipts.pyz"
    out.append(check("zipapp present", lambda: (pyz.is_file() and pyz.stat().st_size > 1000,
                                                f"{pyz.stat().st_size if pyz.is_file() else 0} bytes")))
    if pyz.is_file():
        r = subprocess.run([sys.executable, str(pyz), "version"], capture_output=True, text=True)
        out.append(check("zipapp smoke", lambda: (r.returncode == 0 and "receipts" in r.stdout,
                                                  r.stdout.strip() or r.stderr.strip())))
    return all(out)


def round9(root):
    note("ROUND 9  independent re-review (runner compatibility & type confusion)")
    out = []
    out.append(check("go ./... and pytest . are whole-suite, not selection", lambda: (
        not runner.has_selection(["go", "test", "./..."])
        and not runner.has_selection([sys.executable, "-m", "pytest", "-q", "."]),
        "explicit whole-suite roots allowed")))
    out.append(check("bare test files / -k still refused", lambda: (
        runner.has_selection([sys.executable, "-m", "pytest", "tests/test_one.py"])
        and runner.has_selection([sys.executable, "-m", "pytest", "-k", "trivial"]),
        "selection still refused")))
    out.append(check("JSON boolean version rejected", lambda: (
        _raises(lambda: claims.parse('{"version":true,"claims":[]}')), "True != 1")))
    out.append(check("JSON float version rejected", lambda: (
        _raises(lambda: claims.parse('{"version":1.0,"claims":[]}')), "1.0 != 1")))
    (root / "a.py").write_bytes(b"hello world")
    doc = json.dumps({"version": 1, "claims": [{
        "id": "span.matches", "subject": "a.py",
        "evidence": {"path": "a.py", "start": True, "end": True, "expected": "hello"}}]})
    out.append(check("boolean span offsets FAIL", lambda: (
        verdict.verify(claims.parse(doc), _ctx(root)).results[0].status == "FAIL",
        "type confusion refused")))
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "golden.py"), "--check"],
                       cwd=ROOT, capture_output=True, text=True)
    out.append(check("golden still byte-identical after Round 9 fixes", lambda: (
        r.returncode == 0, r.stdout.strip().splitlines()[0])))
    return all(out)


def _ctx(root, config=None, allow_run=True):
    cur = snapshot.capture(root)
    return verdict.Context(root=Path(root), current=cur, baseline=None, diff=None,
                           config=config or {}, limits=policy.DEFAULT_LIMITS,
                           allow_run=allow_run, allow_commands=False, timeout=10,
                           required=[], strict=False)


def _raises(fn):
    try:
        fn()
    except (ValueError, safepath.UnsafePath, OSError):
        return True
    return False


def _hardlink_check(root):
    import os
    a, b = root / "hl_a.txt", root / "hl_b.txt"
    a.write_text("x", encoding="utf-8")
    try:
        os.link(a, b)
    except OSError:
        return True, "hardlinks unavailable (skipped)"
    try:
        return _raises(lambda: safepath.safe_bytes("hl_b.txt", root)), "multi-link file refused"
    finally:
        b.unlink(missing_ok=True)


def main():
    results = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "repo"
        root.mkdir()
        for fn in (round1, round2, round3, round4, round5, round6, round7, round8, round9):
            results.append(fn(root))
    passed = sum(results)
    note("")
    note(f"RESULT: {passed}/9 rounds PASS")
    EVIDENCE.write_text("\n".join(LINES) + "\n", encoding="utf-8")
    return 0 if passed == 9 else 1


if __name__ == "__main__":
    raise SystemExit(main())
