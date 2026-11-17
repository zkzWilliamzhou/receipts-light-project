"""Tests for prose -> typed claim compilation."""
import json

import pytest

from receipts import claims


def ids(text):
    return sorted(c.id for c in claims.parse(text).claims)


@pytest.mark.parametrize("text", [
    "All tests pass.",
    "The test suite is green.",
    "Tests are passing after my change.",
    "34/34 tests pass",
    "I ran the tests and they all pass.",
])
def test_tests_pass_triggers(text):
    assert "tests.pass" in ids(text)


@pytest.mark.parametrize("text", [
    "I didn't run the tests.",
    "Tests do not pass yet.",
    "The tests are failing.",
    "Tests should pass once you install deps.",
    "I will run tests later.",
])
def test_negation_and_future_tense_do_not_claim_success(text):
    assert "tests.pass" not in ids(text)


def test_numeric_count_extracted():
    p = claims.parse("34/34 tests pass")
    c = [x for x in p.claims if x.id == "tests.pass"][0]
    assert c.params.get("expected_passed") == 34
    assert c.params.get("expected_total") == 34


def test_two_digit_count_variant():
    p = claims.parse("7 tests passed in 0.1s")
    c = [x for x in p.claims if x.id == "tests.pass"][0]
    assert c.params.get("expected_passed") == 7


@pytest.mark.parametrize("text,expected", [
    ("The build succeeds.", "build.ok"),
    ("It compiles cleanly.", "build.ok"),
    ("The linter is clean.", "lint.clean"),
    ("No new dependencies were added.", "deps.unchanged"),
    ("I didn't add any packages.", "deps.unchanged"),
    ("No secrets were added.", "secrets.none_added"),
    ("I didn't disable any checks.", "checks.not_disabled"),
    ("No tests were deleted.", "checks.not_disabled"),
    ("The public API is unchanged.", "api.unchanged"),
    ("No breaking changes.", "api.unchanged"),
    ("No files were modified.", "files.changed"),
])
def test_other_triggers(text, expected):
    assert expected in ids(text)


def test_only_changed_paths_extracted():
    p = claims.parse("I only changed `src/a.py` and `src/b.py`.")
    c = [x for x in p.claims if x.id == "files.changed"][0]
    assert sorted(c.params.get("paths", [])) == ["src/a.py", "src/b.py"]


def test_file_count_extracted():
    p = claims.parse("I touched 2 files.")
    c = [x for x in p.claims if x.id == "files.changed"][0]
    assert c.params.get("count") == 2


def test_multiple_claims_in_one_report():
    text = "All tests pass. The build succeeds. No new dependencies were added. Public API unchanged."
    assert ids(text) == ["api.unchanged", "build.ok", "deps.unchanged", "tests.pass"]


def test_unknown_claim_shaped_sentence_is_visible():
    p = claims.parse("The change is production ready and fully secure.")
    assert p.unknown, "claim-shaped but unverifiable prose must be surfaced"


def test_empty_input_has_no_claims():
    p = claims.parse("")
    assert p.claims == [] and p.unknown == [] and p.errors == []


def test_text_size_cap():
    with pytest.raises(ValueError):
        claims.parse("x" * (1024 * 1024 + 1))


def test_json_receipt_parses_typed_claims():
    doc = {
        "version": 1,
        "claims": [
            {"id": "span.matches", "subject": "a.py",
             "evidence": {"path": "a.py", "start": 0, "end": 5, "expected": "hello"}},
        ],
    }
    p = claims.parse(json.dumps(doc))
    assert p.claims[0].id == "span.matches"
    assert p.claims[0].params["evidence"]["expected"] == "hello"


def test_json_receipt_rejects_unknown_fields():
    doc = {"version": 1, "claims": [{"id": "span.matches", "evil": 1}]}
    with pytest.raises(ValueError):
        claims.parse(json.dumps(doc))


def test_json_receipt_unknown_id_is_not_dropped():
    doc = {"version": 1, "claims": [{"id": "magic.proof"}]}
    p = claims.parse(json.dumps(doc))
    assert p.claims and p.claims[0].id == "magic.proof"


def test_claim_cap():
    text = " ".join(["All tests pass."] * 250)
    p = claims.parse(text)
    assert len(p.claims) <= 200
    assert any("cap" in e.lower() for e in p.errors)
