"""Adversarial tests for path handling, snapshots, and command execution."""
import json
import os
import sys
from pathlib import Path

import pytest

from receipts import claims, policy, runner, safepath, snapshot


def write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ---------------- safepath ----------------

@pytest.mark.parametrize("bad", [
    "../outside.txt", "a/../../b", "/etc/passwd", "C:\\Windows\\win.ini",
    "", ".", "a\x00b", "a/" * (policy.MAX_PATH_DEPTH + 2) + "x",
])
def test_canonical_rejects_unsafe_paths(tmp_path, bad):
    with pytest.raises(safepath.UnsafePath):
        safepath.canonical(bad, tmp_path)


def test_canonical_accepts_clean_relative_path(tmp_path):
    write(tmp_path / "src" / "a.py", "hello")
    got = safepath.canonical("src/a.py", tmp_path)
    assert got == (tmp_path / "src" / "a.py").resolve()


def test_canonical_rejects_excluded_dirs(tmp_path):
    write(tmp_path / ".git" / "config", "x")
    with pytest.raises(safepath.UnsafePath):
        safepath.canonical(".git/config", tmp_path)
    with pytest.raises(safepath.UnsafePath):
        safepath.canonical("node_modules/pkg/index.js", tmp_path)


def test_symlink_escape_blocked(tmp_path):
    outside = tmp_path.parent / ("outside_" + tmp_path.name)
    outside.mkdir(exist_ok=True)
    write(outside / "secret.txt", "SECRET")
    (tmp_path / "link").mkdir()
    try:
        (tmp_path / "link" / "escape").symlink_to(outside / "secret.txt")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(safepath.UnsafePath):
        safepath.canonical("link/escape", tmp_path)


def test_safe_bytes_caps_file_size(tmp_path):
    big = tmp_path / "big.txt"
    big.write_bytes(b"x" * 100)
    limits = policy.Limits(max_file_bytes=10)
    with pytest.raises(safepath.UnsafePath):
        safepath.safe_bytes("big.txt", tmp_path, limits)


def test_iter_files_is_deterministic_and_excludes(tmp_path):
    write(tmp_path / "b.py", "b")
    write(tmp_path / "a.py", "a")
    write(tmp_path / ".git" / "config", "x")
    write(tmp_path / "node_modules" / "x.js", "x")
    first = [r for r, _ in safepath.iter_files(tmp_path)]
    second = [r for r, _ in safepath.iter_files(tmp_path)]
    assert first == second == ["a.py", "b.py"]


def test_unicode_homoglyph_path_is_not_silently_merged(tmp_path):
    write(tmp_path / "src" / "a.py", "ascii")
    write(tmp_path / "src" / "\u0430.py", "cyrillic")
    paths = [r for r, _ in safepath.iter_files(tmp_path)]
    assert len(paths) == 2
    assert any("\u0430" in p for p in paths)


# ---------------- snapshot ----------------

def test_capture_is_deterministic(tmp_path):
    write(tmp_path / "a.py", "one")
    write(tmp_path / "b.txt", "two")
    s1 = snapshot.capture(tmp_path)
    s2 = snapshot.capture(tmp_path)
    assert s1.tree_sha256 == s2.tree_sha256
    assert sorted(s1.files) == ["a.py", "b.txt"]


def test_capture_changes_when_file_changes(tmp_path):
    write(tmp_path / "a.py", "one")
    before = snapshot.capture(tmp_path)
    write(tmp_path / "a.py", "two")
    after = snapshot.capture(tmp_path)
    assert before.tree_sha256 != after.tree_sha256
    d = snapshot.diff(before, after)
    assert d.modified == ["a.py"] and not d.added and not d.deleted


def test_diff_added_deleted_and_added_lines(tmp_path):
    write(tmp_path / "a.py", "line1\n")
    before = snapshot.capture(tmp_path)
    write(tmp_path / "a.py", "line1\nAKIA1234567890123456\n")
    write(tmp_path / "new.py", "fresh\n")
    after = snapshot.capture(tmp_path)
    d = snapshot.diff(before, after)
    assert d.added == ["new.py"]
    assert "a.py" in d.modified
    assert any("AKIA" in ln for ln in d.added_lines.get("a.py", []))


def test_snapshot_roundtrip_json(tmp_path):
    write(tmp_path / "a.py", "one")
    s = snapshot.capture(tmp_path)
    restored = snapshot.from_json(snapshot.to_json(s))
    assert restored.tree_sha256 == s.tree_sha256
    assert restored.texts == s.texts


def test_manifest_parsers():
    reqs = b"requests==2.31.0\n# comment\nflask>=2.0 ; python_version>'3'\n"
    assert "requests" in snapshot.parse_manifest("requirements.txt", reqs)
    pkg = b'{"dependencies":{"react":"18.0.0"},"devDependencies":{"jest":"29"}}'
    got = snapshot.parse_manifest("package.json", pkg)
    assert got == {"react", "jest"}


def test_baseline_file_roundtrip(tmp_path):
    write(tmp_path / "a.py", "one")
    s = snapshot.capture(tmp_path)
    p = tmp_path / ".receipts" / "baseline.json"
    snapshot.save(s, p)
    assert snapshot.load(p).tree_sha256 == s.tree_sha256


# ---------------- runner ----------------

def test_selection_flags_detected_for_pytest_marker():
    assert runner.has_selection([sys.executable, "-m", "pytest", "-k", "trivial"])
    assert runner.has_selection([sys.executable, "-m", "pytest", "tests/test_one.py"])
    assert runner.has_selection(["npm", "test", "--", "--grep", "smoke"])


def test_python_minus_m_module_flag_is_not_marker_selection():
    assert not runner.has_selection([sys.executable, "-m", "pytest", "-q"])


def test_env_scrubbing_removes_secrets(monkeypatch):
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "hunter2")
    monkeypatch.setenv("MY_API_TOKEN", "abc")
    monkeypatch.setenv("PATH", os.environ.get("PATH", ""))
    env = runner.scrubbed_env()
    assert not any("SECRET" in k or "TOKEN" in k for k in env)
    assert "AWS_SECRET_ACCESS_KEY" not in env and "MY_API_TOKEN" not in env


def test_run_argv_only_no_shell(tmp_path):
    # Shell metacharacters must be inert: a shell would create pwned.txt.
    obs = runner.run([sys.executable, "-c", "print('hi; touch pwned.txt')"], tmp_path, timeout=10)
    assert obs.exit_code == 0
    assert "hi" in obs.stdout
    assert not (tmp_path / "pwned.txt").exists()


def test_run_output_cap_and_timeout(tmp_path):
    obs = runner.run([sys.executable, "-c", "print('x'*200000)"], tmp_path,
                     timeout=10, limits=policy.Limits(max_output_bytes=1000))
    assert obs.truncated is True
    assert len(obs.stdout.encode()) <= 1000 + 200


def test_parse_pytest_output():
    c = runner.parse_test_output("collected 34 items\n\n34 passed, 2 warnings in 0.4s\n")
    assert c.parse_ok and c.collected == 34 and c.passed == 34 and c.failed == 0


def test_parse_zero_tests_is_not_success():
    c = runner.parse_test_output("collected 0 items\n\nno tests ran in 0.1s\n")
    assert c.collected == 0
    assert c.parse_ok


def test_parse_failure_count():
    c = runner.parse_test_output("collected 5 items\n\n3 passed, 2 failed in 0.2s\n")
    assert c.failed == 2 and c.passed == 3


def test_detect_commands_from_pytest_layout(tmp_path):
    write(tmp_path / "pyproject.toml", "[project]\nname='x'\n")
    write(tmp_path / "tests" / "test_a.py", "def test_a(): pass\n")
    cmds = runner.detect_commands(tmp_path)
    assert "tests" in cmds and "pytest" in " ".join(cmds["tests"])


def test_strict_json_rejects_duplicate_keys_and_depth():
    with pytest.raises(ValueError):
        claims.strict_loads('{"a":1,"a":2}')
    with pytest.raises(ValueError):
        claims.strict_loads("[" * 30 + "0" + "]" * 30)
    with pytest.raises(ValueError):
        claims.strict_loads('{"a":1} trailing')
