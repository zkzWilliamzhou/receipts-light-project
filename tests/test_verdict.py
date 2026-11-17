"""Tests for the falsification engine."""
import sys
from pathlib import Path

import pytest

from receipts import claims, policy, snapshot, verdict


def write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


PY_PASS = "print('collected 3 items'); print('3 passed in 0.1s')"
PY_FAIL = "import sys; print('collected 3 items'); print('1 passed, 2 failed in 0.1s'); sys.exit(1)"
PY_ZERO = "print('collected 0 items'); print('no tests ran in 0.1s')"


def ctx_for(root, *, baseline=None, config=None, allow_run=False, allow_commands=False,
            required=None, strict=False, timeout=10):
    current = snapshot.capture(root)
    d = snapshot.diff(baseline, current) if baseline is not None else None
    return verdict.Context(
        root=Path(root), current=current, baseline=baseline, diff=d,
        config=config or {}, limits=policy.DEFAULT_LIMITS,
        allow_run=allow_run, allow_commands=allow_commands, timeout=timeout,
        required=required or [], strict=strict,
    )


def one_result(parsed_text, **kw):
    root = kw.pop("root")
    c = ctx_for(root, **kw)
    v = verdict.verify(claims.parse(parsed_text), c)
    return v.results[0] if v.results else None, v


def test_api_unchanged_is_never_pass(tmp_path):
    r, _ = one_result("The public API is unchanged.", root=tmp_path)
    assert r.status == "INDETERMINATE"
    assert "extractor" in r.reason.lower() or "semantic" in r.reason.lower()


def test_no_run_makes_execution_claims_indeterminate(tmp_path):
    r, _ = one_result("All tests pass.", root=tmp_path, allow_run=False)
    assert r.status == "INDETERMINATE"


def test_tests_pass_verified_against_real_output(tmp_path):
    r, _ = one_result(
        "All tests pass.", root=tmp_path, allow_run=True,
        config={"commands": {"tests": [sys.executable, "-c", PY_PASS]}},
    )
    assert r.status == "PASS", r.reason
    assert r.evidence["counts"]["passed"] == 3
    assert r.evidence["observation"].startswith("OBSERVED_AT_VERIFY")


def test_tests_fail_when_runner_reports_failures(tmp_path):
    r, _ = one_result(
        "All tests pass.", root=tmp_path, allow_run=True,
        config={"commands": {"tests": [sys.executable, "-c", PY_FAIL]}},
    )
    assert r.status == "FAIL", r.reason


def test_zero_collected_is_not_pass(tmp_path):
    r, _ = one_result(
        "All tests pass.", root=tmp_path, allow_run=True,
        config={"commands": {"tests": [sys.executable, "-c", PY_ZERO]}},
    )
    assert r.status == "INDETERMINATE"
    assert "0" in r.reason or "no tests" in r.reason.lower()


def test_selection_laundering_never_passes(tmp_path):
    r, _ = one_result(
        "All tests pass.", root=tmp_path, allow_run=True,
        config={"commands": {"tests": [sys.executable, "-m", "pytest", "-k", "trivial"]}},
    )
    assert r.status == "INDETERMINATE"
    assert "selection" in r.reason.lower() or "coverage" in r.reason.lower()


def test_numeric_count_mismatch_fails(tmp_path):
    r, _ = one_result(
        "34/34 tests pass", root=tmp_path, allow_run=True,
        config={"commands": {"tests": [sys.executable, "-c", PY_PASS]}},
    )
    assert r.status == "FAIL"
    assert "34" in r.reason


def test_span_matches_pass(tmp_path):
    write(tmp_path / "a.py", "hello world")
    doc = '{"version":1,"claims":[{"id":"span.matches","subject":"a.py","evidence":{"path":"a.py","start":0,"end":5,"expected":"hello"}}]}'
    r, _ = one_result(doc, root=tmp_path)
    assert r.status == "PASS"


def test_fabricated_span_fails(tmp_path):
    write(tmp_path / "a.py", "hello world")
    doc = '{"version":1,"claims":[{"id":"span.matches","subject":"a.py","evidence":{"path":"a.py","start":0,"end":5,"expected":"HACKED"}}]}'
    r, _ = one_result(doc, root=tmp_path)
    assert r.status == "FAIL"


def test_unsafe_span_path_is_indeterminate(tmp_path):
    doc = '{"version":1,"claims":[{"id":"span.matches","subject":"x","evidence":{"path":"../../etc/passwd","start":0,"end":5,"expected":"root"}}]}'
    r, _ = one_result(doc, root=tmp_path)
    assert r.status == "INDETERMINATE"


def test_files_changed_no_files_claim_fails_when_repo_dirty(tmp_path):
    write(tmp_path / "a.py", "one")
    base = snapshot.capture(tmp_path)
    write(tmp_path / "a.py", "two")
    r, _ = one_result("No files were modified.", root=tmp_path, baseline=base)
    assert r.status == "FAIL"


def test_files_changed_exact_paths_pass(tmp_path):
    write(tmp_path / "a.py", "one")
    base = snapshot.capture(tmp_path)
    write(tmp_path / "a.py", "two")
    r, _ = one_result("I only changed `a.py`.", root=tmp_path, baseline=base)
    assert r.status == "PASS"


def test_deps_unchanged_fails_on_new_dependency(tmp_path):
    write(tmp_path / "requirements.txt", "requests==2.31.0\n")
    base = snapshot.capture(tmp_path)
    write(tmp_path / "requirements.txt", "requests==2.31.0\nflask==3.0.0\n")
    r, _ = one_result("No new dependencies were added.", root=tmp_path, baseline=base)
    assert r.status == "FAIL"


def test_secrets_none_added_fails_on_key(tmp_path):
    write(tmp_path / "cfg.py", "x = 1\n")
    base = snapshot.capture(tmp_path)
    write(tmp_path / "cfg.py", "x = 1\nAWS_KEY = 'AKIA1234567890123456'\n")
    r, _ = one_result("No secrets were added.", root=tmp_path, baseline=base)
    assert r.status == "FAIL"


def test_checks_not_disabled_fails_on_deleted_test(tmp_path):
    write(tmp_path / "tests" / "test_a.py", "def test_a(): pass\n")
    base = snapshot.capture(tmp_path)
    (tmp_path / "tests" / "test_a.py").unlink()
    r, _ = one_result("I didn't disable any checks.", root=tmp_path, baseline=base)
    assert r.status == "FAIL"


def test_required_claim_manifest_missing(tmp_path):
    v = verdict.verify(
        claims.parse("All tests pass."),
        ctx_for(tmp_path, required=["deps.unchanged", "secrets.none_added"]),
    )
    assert any("manifest" in r.claim_id for r in v.results)
    assert any(r.status == "FAIL" for r in v.results if "manifest" in r.claim_id)


def test_unknown_claim_is_uncheckable(tmp_path):
    v = verdict.verify(claims.parse("The change is production ready and fully secure."),
                       ctx_for(tmp_path))
    assert any(r.status == "UNCHECKABLE" for r in v.results)


def test_exit_codes(tmp_path):
    v = verdict.verify(claims.parse("No files were modified."), ctx_for(tmp_path))
    # no baseline -> INDETERMINATE, non-strict exit 0
    assert verdict.exit_code(v, strict=False) == 0
    assert verdict.exit_code(v, strict=True) == 3
    v2 = verdict.verify(claims.parse("All tests pass."), ctx_for(
        tmp_path, allow_run=True,
        config={"commands": {"tests": [sys.executable, "-c", PY_FAIL]}}))
    assert verdict.exit_code(v2, strict=False) == 1
