"""Capture and compare a byte-stable behaviour contract.

Used as the hard gate for the architecture-deepening pass: if the golden
output changes by even one byte, the refactor changed program behaviour and
must be reverted.

Usage:
    python3 tools/golden.py --write   # capture docs/GOLDEN.txt
    python3 tools/golden.py --check   # compare, exit 1 on any difference
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from receipts import claims, policy, snapshot, verdict  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "docs" / "GOLDEN.txt"

VOLATILE = {"observation", "duration", "started_at", "generated_at", "timestamp"}


def _stable(value):
    if isinstance(value, dict):
        return {k: _stable(v) for k, v in sorted(value.items()) if k not in VOLATILE}
    if isinstance(value, (list, tuple)):
        return [_stable(v) for v in value]
    if isinstance(value, float):
        return round(value, 2)
    return value


def _context(root, *, baseline=None, config=None, allow_run=False, required=None):
    current = snapshot.capture(root)
    diff = snapshot.diff(baseline, current) if baseline is not None else None
    return verdict.Context(
        root=Path(root), current=current, baseline=baseline, diff=diff,
        config=config or {}, limits=policy.DEFAULT_LIMITS, allow_run=allow_run,
        allow_commands=False, timeout=10, required=required or [], strict=False,
    )


def _canonical(v):
    rows = []
    for r in v.results:
        rows.append({
            "claim_id": r.claim_id, "status": r.status, "reason": r.reason,
            "evidence": _stable(r.evidence),
        })
    return json.dumps({
        "tree_sha256": v.tree_sha256, "counts": dict(sorted(v.counts.items())),
        "results": rows,
    }, indent=2, sort_keys=True, ensure_ascii=False)


def _write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _one(root, text, *, baseline=None, config=None, allow_run=False, required=None):
    v = verdict.verify(claims.parse(text), _context(
        root, baseline=baseline, config=config, allow_run=allow_run, required=required))
    return _canonical(v)


def build() -> str:
    blocks = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "repo"
        root.mkdir()
        _write(root / "a.py", "hello world\n")
        _write(root / "requirements.txt", "requests==2.31.0\n")
        _write(root / "tests" / "test_a.py", "def test_a(): pass\n")

        blocks.append(("01_no_run", _one(root, "All tests pass.")))
        blocks.append(("02_semantic", _one(root, "Public API unchanged.")))
        blocks.append(("03_uncheckable", _one(root, "The change is production ready and fully secure.")))

        base = snapshot.capture(root)
        _write(root / "a.py", "hello world\nAKIA1234567890123456\n")
        _write(root / "new.py", "fresh\n")
        _write(root / "requirements.txt", "requests==2.31.0\nflask==3.0.0\n")
        (root / "tests" / "test_a.py").unlink()

        blocks.append(("04_files", _one(root, "No files were modified.", baseline=base)))
        blocks.append(("05_deps", _one(root, "No new dependencies were added.", baseline=base)))
        blocks.append(("06_secrets", _one(root, "No secrets were added.", baseline=base)))
        blocks.append(("07_checks", _one(root, "I didn't disable any checks.", baseline=base)))
        blocks.append(("08_span_ok", _one(root, json.dumps({
            "version": 1, "claims": [{"id": "span.matches", "subject": "a.py",
                "evidence": {"path": "a.py", "start": 0, "end": 5, "expected": "hello"}}]}))))
        blocks.append(("09_span_forged", _one(root, json.dumps({
            "version": 1, "claims": [{"id": "span.matches", "subject": "a.py",
                "evidence": {"path": "a.py", "start": 0, "end": 5, "expected": "HACKED"}}]}))))
        blocks.append(("10_manifest", _one(root, "All tests pass.",
                                           required=["deps.unchanged", "secrets.none_added"])))
        blocks.append(("11_execution", _one(
            root, "All tests pass.", config={"commands": {"tests": [
                sys.executable, "-c",
                "print('collected 3 items'); print('3 passed in 0.1s')"]}},
            allow_run=True)))
        blocks.append(("12_multi", _one(
            root, "All tests pass. The build succeeds. No new dependencies were added. "
                  "Public API unchanged.", baseline=base)))

    return "\n\n".join(f"===== {name} =====\n{body}" for name, body in blocks) + "\n"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    current = build()
    if "--write" in argv:
        OUT.write_text(current, encoding="utf-8")
        print(f"golden written: {OUT} ({len(current)} bytes, 12 scenarios)")
        return 0
    if "--check" in argv:
        if not OUT.is_file():
            print("FAIL: no golden file; run --write first")
            return 1
        expected = OUT.read_text(encoding="utf-8")
        if expected == current:
            print(f"PASS: golden byte-identical ({len(current)} bytes, 12 scenarios)")
            return 0
        import difflib
        diff = "".join(difflib.unified_diff(
            expected.splitlines(True), current.splitlines(True),
            fromfile="GOLDEN.txt", tofile="current"))
        print("FAIL: behaviour changed\n" + diff[:4000])
        return 1
    print("usage: golden.py --write | --check")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
