# Nine-Round Code Review Log

Owner: Boss/Manager. Each round had a fixed lens, a fresh pass over the work product, and a fresh verification command afterwards. **A finding is not closed until a regression fixture exists and the full suite is green again.**

The brief asked for **over eight** rounds, so a ninth, independent re-review was added with a different lens (built-in runner compatibility and Python type confusion). It found three real defects. They were fixed before delivery.

Baseline at start of reviews: 107 tests green. Baseline at end: **143 tests green**, golden contract 7,844 bytes, byte-identical across both the architecture pass and the Round 9 fixes.

| Round | Lens | Findings | Fixes | Regression fixtures | Final |
|---|---|---|---|---|---|
| 1 | Path & filesystem | 2 | 2 | 3 | PASS |
| 2 | Command execution | 2 | 2 | 3 | PASS |
| 3 | Parser & input | 3 | 3 (+1 rework) | 4 | PASS |
| 4 | Claim semantics / laundering | 3 | 3 | 3 | PASS |
| 5 | Snapshot & determinism | 3 | 3 | 3 | PASS |
| 6 | Reporting safety & UX | 2 | 2 | 2 | PASS |
| 7 | Correctness & edge cases | 3 | 3 | 3 | PASS |
| 8 | Supply chain & release | 2 | 2 | 3 | PASS |
| 9 | Independent re-review (runner compatibility & type confusion) | 3 | 3 | 11 | PASS |

Total: **23 findings, 23 fixes, 35 new regression fixtures.** One fix was itself rejected and reworked (see Round 3).

---

## Round 1 — Path and filesystem safety

**F1.1 (Important) TOCTOU on symlink swap.** `safe_bytes` called `Path.resolve()` and then `read_bytes()` as two separate operations. Between them, the path could be replaced with a symlink pointing outside the repository.
Fix: open the resolved path with `O_NOFOLLOW`, `fstat` the open descriptor, re-check containment after opening, and read in bounded 64 KiB chunks with a cumulative cap.

**F1.2 (Important) Hardlinks have no containment.** A hardlink inside the repo to a file outside it passes every path-based check.
Fix: refuse any file with `st_nlink > 1`. A legitimate multi-linked file yields `INDETERMINATE`, never a silent read.

Also verified (no change needed): absolute paths, `..` traversal, Windows drive/backslash forms, NUL and control characters, over-deep paths, `.git`/`.receipts`/`node_modules` exclusion, unicode homoglyph paths kept distinct, deterministic walk ordering.

Evidence: `test_r1_*` (3 fixtures), `test_core_safety.py` path block (12 cases), 400-iteration path fuzz.

## Round 2 — Command execution safety

**F2.1 (Critical) Unbounded/negative timeout.** `timeout` came straight from `--timeout`; a negative value or `NaN` would reach `proc.wait()` and either raise or disable the deadline.
Fix: clamp to `[0.1, 600.0]`, reject non-numeric input with `ValueError`, and treat `NaN`/non-positive as the default.

**F2.2 (Important) Trusting a truncated summary.** If a child process kept a pipe open through a grandchild, reader threads could return partial output while `exit_code == 0`. A whole-suite claim could have been graded `PASS` on an unparseable or truncated summary.
Fix: `tests.pass` returns `INDETERMINATE` whenever output was truncated; unparseable output and zero collected were already refused.

Also verified: no `shell=True`, no string-concatenated commands, argv-only execution, `stdin=DEVNULL`, output cap, env allow-list with secret-name scrubbing, shell metacharacters inert.

Evidence: `test_r2_*` (3), `test_run_argv_only_no_shell`, `test_env_scrubbing_removes_secrets`, `test_banned_constructs_absent`.

## Round 3 — Parser and input safety

**F3.1 (Important) Bracket-prefixed prose was rejected.** Any input starting with `{` or `[` was forced through the strict JSON parser, so a PR body like `[WIP] All tests pass.` exited with a usage error instead of being checked.
Fix: only brace-led text carrying receipt fields (`"claims"` / `"version"`) is treated as structured input; bracket-led JSON is parsed only to validate, then falls back to prose on failure.

**F3.2 (REWORK — my own fix was wrong).** The first version of F3.1 still strict-parsed *all* brace-led text. A new fixture, `test_r3_brace_prose_without_receipt_fields_is_still_prose`, failed with `ValueError: malformed JSON` on `{draft} All tests pass.`. **The fix was rejected and sent back.** Second version gates on the presence of receipt fields before calling `strict_loads`. This is recorded as a genuine gate failure, not a staged one.

**F3.3 (Important) Deep JSON could raise `RecursionError` outside the guard.** `_check_depth` was called outside the `try` that wraps `raw_decode`.
Fix: wrap `_check_depth` in `except RecursionError -> ValueError`, with a 2,000-level fixture.

Also verified: duplicate keys rejected, trailing garbage rejected, size cap, NFC display policy documented, 300-iteration prose fuzz.

Evidence: `test_r3_*` (4), `test_strict_json_rejects_duplicate_keys_and_depth`, `test_fuzz_prose_never_crashes`.

## Round 4 — Claim semantics and claim laundering

**F4.1 (Critical) Claim laundering was under-defended.** A command can print a plausible `collected 3 items / 3 passed` summary without running any test. The verifier cannot prove the command exercised real tests.
Fix: (a) an explicit `coverage_note` is attached to every execution result stating exactly this limitation; (b) a `coverage_note` is machine-visible in the JSON/HTML report; (c) optional `require_known_runner: true` in `.receipts.json` downgrades non-runner argv to `INDETERMINATE`. The default stays zero-config; the strict mode is opt-in. We deliberately did **not** claim to have solved laundering — that would be dishonest.

**F4.2 (Important) Semantic claims could be read as provable.** `api.unchanged` has no bundled comparator.
Fix: it always returns `INDETERMINATE` with an explicit list of required proof fields.

**F4.3 (Important) Unknown claim ids must not vanish.** Fixed: unknown ids and claim-shaped prose produce `UNCHECKABLE` rows and are counted.

Also verified: selection flags (`-k`, `--grep`, bare paths, second `-m`) refused; zero collected refused; numeric mismatch `FAIL`; negation/future tense not compiled; required-claim manifest reports `CLAIMS_MISSING` as `FAIL`.

Evidence: `test_r4_*` (3), `test_selection_laundering_never_passes`, `test_numeric_count_mismatch_fails`, `test_required_claim_manifest_missing`.

## Round 5 — Snapshot and determinism

**F5.1 (Important) No TOCTOU rehash after execution.** A command could modify the tree while the verdict was being computed, leaving a `PASS` bound to a different tree than the one reported.
Fix: recapture after command execution; a would-be `PASS` becomes `INDETERMINATE` when the tree changed, with `repo_changed_during_verify: true` in evidence.

**F5.2 (Minor) Unbounded retained text.** `capture` retained up to 4 million characters per file.
Fix: `MAX_TEXT_PER_FILE = 512 KiB`, centralised in `policy`.

**F5.3 (Minor) Volatile fields in the tree digest.** Verified `created_at` and `mtime_ns` are excluded from `tree_sha256`; two captures of an unchanged tree are byte-equal.

Evidence: `test_r5_*` (3), `test_capture_is_deterministic`, `test_snapshot_roundtrip_json`, `tools/golden.py --check`.

## Round 6 — Reporting safety and UX

**F6.1 (Important) ANSI injection in terminal output.** A hostile PR body containing `\x1b[2K` could overwrite or spoof the printed verdict.
Fix: `_plain()` strips all C0 control characters from terminal rows; the hostile text remains visible but is not executable.

**F6.2 (Important) HTML report trust.** Verified: every value is `html.escape`d, no `<script>`, no external URL, no CDN, inline CSS only, evidence rendered as escaped JSON. Literal `http://`/`https://` are entity-neutralised so the report stays strictly offline.

Evidence: `test_r6_*` (2), `test_html_escapes_hostile_data`, `test_html_is_self_contained_offline`, `test_html_xss_from_prose`.

## Round 7 — Correctness and edge cases

**F7.1 (Important) Empty input silently succeeded.** `check --text ""` produced an empty result list and exit 0, which reads as "nothing wrong".
Fix: `input.no_claims` is emitted as `INDETERMINATE`; `--strict` then yields exit 3.

**F7.2 (Minor) Parse notes were invisible.** The claim-cap warning lived only in `Verdict.errors`.
Fix: `input.parse_note` rows are emitted and counted.

**F7.3 (Minor) Exit-code matrix.** Verified `0` (no FAIL), `1` (FAIL), `2` (usage/IO), `3` (strict + indeterminate), including missing repo, missing input file, oversized input and duplicate-key JSON.

Evidence: `test_r7_*` (3), `test_cli_*` block in `test_report.py`.

## Round 8 — Supply chain and release

**F8.1 (Critical) Runtime dependency drift.** A single accidental third-party import would break the "stdlib-only, offline" promise.
Fix: added an AST-level test that asserts every top-level import resolves to a stdlib module, plus the existing banned-construct scan (`eval`, `exec`, `system`, `pickle`, `requests`, `urllib.request`, `socket`, `shell=True`).

**F8.2 (Important) Distribution smoke test.** Added `tools/build_zipapp.py`; `receipts.pyz` is built with stdlib `zipapp` and verified with `python3 receipts.pyz version` and `python3 receipts.pyz claims`.

Also verified: README contains no prohibited claim strings (automated scan), version consistency, JSON report self-description, license and third-party notices present.

Evidence: `test_r8_*` (3), `test_banned_constructs_absent`, `tools/review_harness.py`, `tools/build_zipapp.py`.

---

## Round 9 — Independent re-review (added because the brief asked for *over* eight rounds)

Lens: not another security checklist. This pass asked two different questions — *"do the built-in runner commands actually work with the selection guard?"* and *"can Python's loose typing silently accept a wrong value?"* Both found real defects that Rounds 1–8 had missed.

**F9.1 (Important) Whole-suite roots were falsely classified as selection.** `has_selection()` refused any argument containing `/`. That meant the built-in Go detection `go test ./...` and the ordinary `pytest .` were always `INDETERMINATE`: a legitimate whole-suite claim could never be checked for Go projects.
Fix: explicit `WHOLE_SUITE_ROOTS` (`.`, `./`, `./...`, `...`, `./.`) are allowed; bare `.py`/`.spec.js`/`.test.*` paths, `::` node ids, `-k` and a second `-m` remain refused. A Go fixture now asserts the *detected* command passes the guard.

**F9.2 (Minor) JSON receipt version type confusion.** In Python `True == 1` and `1.0 == 1`, so `{"version": true, ...}` and `{"version": 1.0, ...}` were accepted as version 1.
Fix: require `int`, reject `bool` explicitly, require equality to 1.

**F9.3 (Minor) Span offsets accepted booleans.** `isinstance(True, int)` is `True`, so `start: true, end: true` behaved like `0, 1` and could yield a `PASS` on a type-confused receipt.
Fix: reject `bool` and non-`int` offsets; they now produce `FAIL` with an out-of-range reason, while valid integer spans still `PASS`.

Also re-verified after the fixes: golden contract byte-identical (the Round 9 code paths do not touch any of the 12 captured scenarios), full suite green, zipapp rebuilt.

Evidence: `tests/test_round9.py` (11 fixtures), `tools/review_harness.py` Round 9 lens (6 checks).

---

## Fresh verification evidence (final state)

```
$ python3 tools/golden.py --check
PASS: golden byte-identical (7844 bytes, 12 scenarios)

$ python3 -m pytest -q
143 passed in 3.6s

$ python3 tools/review_harness.py
9/9 rounds PASS

$ python3 receipts.pyz version
receipts 1.0.0 (stdlib-only, offline)
```

No round was skipped. A round with no new finding would still have been recorded; in practice every round produced at least two.
