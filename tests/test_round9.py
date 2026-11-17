"""Independent ninth review round: fresh-eyes findings and their regressions.

Round 9 was added because the brief asked for *over* eight rounds. It used a
different lens: built-in runner compatibility and Python type confusion.
"""
import json

import pytest

from receipts import claims, runner, safepath, verdict
from receipts import snapshot, policy
from pathlib import Path


def ctx(root):
    current = snapshot.capture(root)
    return verdict.Context(root=Path(root), current=current, baseline=None, diff=None,
                           config={}, limits=policy.DEFAULT_LIMITS, allow_run=False,
                           allow_commands=False, timeout=10, required=[], strict=False)


# F9.1 - whole-suite roots were falsely classified as selection

def test_r9_go_whole_suite_root_is_allowed():
    assert not runner.has_selection(["go", "test", "./..."])


def test_r9_pytest_dot_root_is_allowed():
    assert not runner.has_selection(["python3", "-m", "pytest", "-q", "."])
    assert not runner.has_selection(["python3", "-m", "pytest", "./..."])


def test_r9_detected_go_command_is_usable(tmp_path):
    (tmp_path / "go.mod").write_text("module example.com/x\n", encoding="utf-8")
    cmds = runner.detect_commands(tmp_path)
    assert not runner.has_selection(cmds["tests"])


def test_r9_bare_test_file_still_refused():
    assert runner.has_selection(["python3", "-m", "pytest", "tests/test_one.py"])
    assert runner.has_selection(["python3", "-m", "pytest", "./tests/test_one.py"])
    assert runner.has_selection(["python3", "-m", "pytest", "-k", "trivial"])


def test_r9_marker_selection_still_refused():
    assert runner.has_selection(["python3", "-m", "pytest", "-m", "smoke"])


# F9.2 - JSON version type confusion

def test_r9_boolean_version_rejected():
    doc = '{"version":true,"claims":[]}'
    with pytest.raises(ValueError):
        claims.parse(doc)


def test_r9_float_version_rejected():
    with pytest.raises(ValueError):
        claims.parse('{"version":1.0,"claims":[]}')


def test_r9_integer_version_accepted():
    p = claims.parse('{"version":1,"claims":[]}')
    assert p.input_kind == "receipt"


# F9.3 - span offset type confusion

def test_r9_boolean_span_offset_is_failed(tmp_path):
    (tmp_path / "a.py").write_bytes(b"hello world")
    doc = json.dumps({"version": 1, "claims": [{
        "id": "span.matches", "subject": "a.py",
        "evidence": {"path": "a.py", "start": True, "end": True, "expected": "hello"}}]})
    r = verdict.verify(claims.parse(doc), ctx(tmp_path)).results[0]
    assert r.status == "FAIL"


def test_r9_float_span_offset_is_failed(tmp_path):
    (tmp_path / "a.py").write_bytes(b"hello world")
    doc = json.dumps({"version": 1, "claims": [{
        "id": "span.matches", "subject": "a.py",
        "evidence": {"path": "a.py", "start": 0.0, "end": 5.0, "expected": "hello"}}]})
    r = verdict.verify(claims.parse(doc), ctx(tmp_path)).results[0]
    assert r.status == "FAIL"


def test_r9_valid_span_still_passes(tmp_path):
    (tmp_path / "a.py").write_bytes(b"hello world")
    doc = json.dumps({"version": 1, "claims": [{
        "id": "span.matches", "subject": "a.py",
        "evidence": {"path": "a.py", "start": 0, "end": 5, "expected": "hello"}}]})
    assert verdict.verify(claims.parse(doc), ctx(tmp_path)).results[0].status == "PASS"
