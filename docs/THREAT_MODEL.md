# Threat Model

Scope: `receipts` is a **local, offline falsifier of claims about a checkout**. It is not a sandbox, not a policy gate, and not an authentication system. An agent that controls the repository can always produce a repository consistent with a false claim. A receipt proves only that *the recorded evidence, under the recorded constraints, supports the recorded claim*.

Trust boundary: the human reviewer + this CLI are trusted. Agent prose, PR bodies, receipt files, repository contents and command output are untrusted. Commands in `.receipts.json` are trusted **human** configuration, not agent output. Agent prose is never used to build a command.

## The single most dangerous attack: claim laundering

An agent supplies `pytest -k trivial`, a real output digest, and a real span in an irrelevant file, then claims `all_tests_pass`. Every individual fact is authentic; none entails the claim.

Mitigations: selection flags and bare path arguments are refused for whole-suite claims; zero collected tests is `INDETERMINATE`; numeric claims are cross-checked against the parsed runner count; semantic claims always `INDETERMINATE`; `coverage_note` is attached to every execution result; `require_known_runner: true` is available as an opt-in stricter mode; internally consistent but insufficient evidence yields `INDETERMINATE`, never `PASS`.

**Residual risk:** a hand-written script can print a plausible passing summary. `receipts` cannot prove the command exercised real tests. We say so in the report rather than hiding it.

## Attack vectors

| # | Vector | Mitigation | Fixture |
|---|---|---|---|
| 1 | Path traversal (`../`, absolute, `a/../../b`) | `canonical()` normalises, rejects `..`, absolute paths, and re-checks containment | `test_canonical_rejects_unsafe_paths` |
| 2 | Symlink escape / swap (TOCTOU) | `O_NOFOLLOW` on resolved path, `fstat`, post-open containment re-check | `test_symlink_escape_blocked`, `test_r1_o_nofollow_does_not_break_plain_read` |
| 3 | Hardlink to a file outside root | refuse `st_nlink > 1` | `test_r1_hardlinked_file_is_refused` |
| 4 | Windows drive / backslash / UNC forms | rejected outright; POSIX relative paths only | `test_canonical_rejects_unsafe_paths` |
| 5 | NUL / control characters in paths | rejected before normalisation | `test_nul_and_control_chars_rejected` |
| 6 | Unicode homoglyph path confusion | paths compared as bytes; NFC used only for display, documented; distinct names stay distinct | `test_unicode_homoglyph_path_is_not_silently_merged` |
| 7 | Shell injection via prose or receipt | argv-only execution; no `shell=True`; prose never builds a command; static AST gate | `test_cli_prose_cannot_inject_shell`, `test_banned_constructs_absent` |
| 8 | Command re-execution escape | no shell, `stdin=DEVNULL`, scrubbed env, allow-listed runners by config, timeout | `test_run_argv_only_no_shell` |
| 9 | Unbounded output / zip bomb | 1 MiB output cap, 8 MiB file cap, 512 KiB retained text, 20k lines, reader threads drain pipes | `test_run_output_cap_and_timeout`, `test_r5_text_is_capped_per_file` |
| 10 | JSON parser bombs | 1 MiB input, depth 20, duplicate keys rejected, trailing garbage rejected, `RecursionError` converted to `ValueError` | `test_strict_json_rejects_duplicate_keys_and_depth`, `test_r3_extreme_json_depth_raises_value_error` |
| 11 | Unbounded claim count | `MAX_CLAIMS = 200` with a visible `input.parse_note` | `test_claim_cap`, `test_r7_claim_cap_error_is_surfaced` |
| 12 | HTML report XSS | all values `html.escape`d, no `<script>`, evidence rendered as escaped JSON, inline CSS only | `test_html_escapes_hostile_data`, `test_html_xss_from_prose` |
| 13 | ANSI injection into terminal verdict | `_plain()` strips C0 controls | `test_r6_ansi_escape_cannot_spoof_terminal` |
| 14 | External resource / telemetry in report | no URLs, no CDN, no `<script>`, offline-only; `_esc()` neutralises literal URL schemes | `test_html_is_self_contained_offline`, `test_r6_html_has_no_external_urls` |
| 15 | Stale baseline / evidence drift | baseline and current tree digests recorded; diff claims recomputed from both | `test_stale_baseline_detected` |
| 16 | TOCTOU between verify and use | tree re-captured after command execution; a would-be PASS downgrades to `INDETERMINATE` | `test_r5_toctou_downgrades_pass` |
| 17 | Forged evidence span | byte-exact comparison at verification time; out-of-range spans `FAIL` | `test_forged_span_is_rejected` |
| 18 | Receipt replay / downgrade | receipt `version` pinned to 1; unknown claim ids `UNCHECKABLE`; required-claim manifest catches downgrade/omission | `test_json_receipt_unknown_id_is_not_dropped`, `test_required_claim_manifest_missing` |
| 19 | Environment variable leakage into reports | env allow-list + secret-name scrubbing; no raw env echoed | `test_env_scrubbing_removes_secrets` |
| 20 | `.git` / runtime-state writes | `.git`, `.receipts`, `node_modules`, caches excluded from capture; capture is read-only | `test_git_dir_is_never_captured` |
| 21 | Verifier self-modification / dependency confusion | stdlib-only AST gate; no network; zipapp built from local sources; hashes recorded in evidence | `test_r8_no_third_party_runtime_imports` |
| 22 | Clock / timestamp manipulation | timestamps are metadata only; trust decisions never use them; golden strips them | `docs/GOLDEN.txt` denylist |
| 23 | Selective omission by a capable agent | externally supplied claims manifest required to detect omission; without it, the tool does **not** claim detection | `test_required_claim_manifest_missing` |
| 24 | Flaky / nondeterministic re-runs | three-valued verdict; fresh execution labelled `OBSERVED_AT_VERIFY`; timestamps/digests recorded separately | `SPEC.md` §3 |

## Honest non-goals

`receipts` does not: stop agents lying, prove correctness, replace CI/code review/appsec, replace SLSA/in-toto/Sigstore/SBOM, detect all secrets, prove semantic properties, guarantee deterministic re-execution, infer selective omission from chat, or produce tamper-proof HTML. A `PASS` is not proof of safety, compliance, or production readiness.

## Reporting a vulnerability

Open an issue with a minimal repository fixture that reproduces the failure. Please include the `receipts check --json` output. Do not include real credentials.
