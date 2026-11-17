# receipts — Technical Specification v1.0

Status: LOCKED, pre-implementation. Date: 2026-11-13.

## 1. Product

**One-liner:** Your agent said "all tests pass". Check the receipts.

`receipts` reads unstructured self-report text (an agent's final answer, a PR body, a commit message, a handoff note, stdin), extracts checkable claims, and independently falsifies each claim against the current repository. It emits a verdict and a self-contained evidence report.

**Design constraints (non-negotiable):**
1. Python standard library only. No third-party runtime imports.
2. Offline. No network calls, no telemetry, no account.
3. Zero configuration for the default claim set.
4. Zero cooperation required from any agent.
5. Never construct a shell command from agent prose.
6. Three-valued verdict. Never report `PASS` on insufficient evidence.
7. Works on Linux, macOS, Windows (Python 3.9+).

**Non-goals:** audit logs, checkpoints, undo, policy enforcement, model evaluation, supply-chain attestation, semantic proofs, CI replacement.

## 2. CLI

```
receipts check [--text TEXT | --file PATH | --stdin] [--repo PATH]
               [--baseline PATH] [--require PATH] [--config PATH]
               [--json] [--html PATH] [--no-run] [--strict]
               [--timeout SECONDS] [--allow-command ARG ...]
receipts run -- <cmd> [args...]       # capture baseline, execute, capture final state
receipts baseline [--repo PATH]       # write/refresh a baseline snapshot only
receipts claims                      # list the claim registry and what falsifies each
receipts version
```

Default input is stdin when no `--text`/`--file` is given. `--no-run` performs static, snapshot and span checks only; execution claims become `INDETERMINATE`.

Exit codes: `0` = no FAIL (INDETERMINATE allowed), `1` = at least one FAIL, `2` = usage/IO error, `3` = `INDETERMINATE` present and `--strict` was passed.

## 3. Claim registry

Every claim type has: `id`, `version`, trigger patterns, required evidence, a falsification procedure, and an explicit `INDETERMINATE` condition. Unknown-but-claim-shaped sentences are reported as `UNCHECKABLE` and counted.

| id | Trigger (examples) | Falsification procedure | INDETERMINATE when |
|---|---|---|---|
| `tests.pass` | "all tests pass", "tests are green", "34/34 tests pass", "test suite passes" | Run the declared whole-suite test command; parse runner output; require exit 0, `collected > 0`, `failed == 0`; cross-check any numeric count in the claim | no known runner, `--no-run`, selection flag present, unparseable output, flake suspected |
| `build.ok` | "build succeeds", "compiles cleanly", "build passes" | Run declared build command, require exit 0 | no build command declared |
| `lint.clean` | "linter is clean", "no lint errors" | Run declared lint command, require exit 0 | no lint command declared |
| `files.changed` | "only changed X and Y", "I touched 2 files", "no files were modified" | Compare baseline snapshot with current snapshot; compare the declared path/count set to the real diff | baseline missing |
| `deps.unchanged` | "no new dependencies", "didn't add any packages" | Parse known manifests/lockfiles before and after; compare dependency name sets | baseline missing or no recognised manifest |
| `secrets.none_added` | "no secrets were added", "no keys committed" | Scan added lines with high-confidence patterns + entropy check | baseline missing; scanner coverage incomplete |
| `checks.not_disabled` | "didn't disable any checks", "no tests were deleted", "didn't skip CI" | Diff scan for deleted test files, added skip/xfail markers, `--no-verify`, `[skip ci]`, lowered coverage thresholds, removed CI steps | baseline missing |
| `api.unchanged` | "public API unchanged", "no breaking changes" | Requires an explicit extractor + baseline + comparator; otherwise none | **always** without explicit proof tool |
| `span.matches` | structured receipt with `path`, `start`, `end`, `expected` | Byte-exact comparison at canonical path within root | span path unsafe |
| `command.exit` | structured receipt with recorded argv + exit code | Re-run argv under SafeRunner, compare exit status | command not allow-listed |

**Verdicts:** `PASS` (evidence satisfies claim under declared rules), `FAIL` (evidence contradicts claim), `INDETERMINATE` (insufficient/unsafe/inapplicable evidence), `UNCHECKABLE` (claim-shaped prose with no registered predicate).

**Coverage rules for `tests.pass` (anti-laundering):**
- Reject selection flags: `-k`, `--grep`, `-m`, `--filter`, `--include`, `--exclude`, `--testNamePattern`, a bare path argument, `::` node ids.
- Require a nonzero collected/test count parsed from the runner output.
- A numeric claim (`34/34`, `34 passed`) must match the parsed count; mismatch is `FAIL`.
- Output digest, exit code, argv, cwd, duration and `OBSERVED_AT_VERIFY` timestamp are recorded separately from the original claim.

## 4. Snapshot format

A baseline is a JSON file (`.receipts/baseline.json`) with `version`, `root`, `created_at`, `algorithm: sha256`, `files: {relative_posix_path: {sha256, size, mtime_ns}}`, `tree_sha256`, and `manifests` (parsed dependency name sets). Rules: `.git`, `.receipts`, `node_modules`, `.venv`, `__pycache__` and files above `MAX_FILE_BYTES` are excluded; paths are POSIX-normalised and must be relative and canonical within root; symlinks are not followed outside root.

`receipts run -- <cmd>` writes the baseline before execution and a `session.json` after, containing before/after tree digests and the changed-path set. This is a *baseline for diff claims*, not an audit log; it stores no commands history and no conversation.

## 5. Structured receipt input (optional)

A caller may pass a JSON document instead of prose. Schema (v1):

```json
{
  "version": 1,
  "repo_root": ".",
  "claims": [
    {"id": "span.matches", "subject": "src/a.py", "evidence": {"path": "src/a.py", "start": 0, "end": 12, "expected": "hello world"}}
  ]
}
```

Parser limits: max 1 MiB, max nesting 20, duplicate keys rejected, unknown keys rejected, trailing garbage rejected, all strings NFC-normalised for display but compared by bytes. Unknown `id` → `UNCHECKABLE`, never `PASS`.

## 6. Security limits (enforced centrally)

`MAX_FILE_BYTES = 8 MiB`, `MAX_OUTPUT_BYTES = 1 MiB`, `MAX_LINES = 20000`, `MAX_JSON_DEPTH = 20`, `MAX_CLAIMS = 200`, `MAX_TEXT_BYTES = 1 MiB`, `DEFAULT_TIMEOUT = 30s`, `MAX_PATH_DEPTH = 32`. No `shell=True`, no `eval`, no `exec`, no `pickle`, no `os.system`, no network. Environment for child processes is an explicit allow-list (`PATH`, `HOME`, `LANG`, `LC_ALL`, `PYTHONPATH`, `VIRTUAL_ENV`, `CI`) with all `*KEY*`, `*TOKEN*`, `*SECRET*`, `*PASSWORD*` names stripped. HTML output is produced from an escaped data model only.

## 7. Module seams

| Module | Interface (what a caller must know) | Hidden complexity |
|---|---|---|
| `policy` | constants + `Limits` | all numeric limits in one place |
| `safepath` | `canonical(rel, root)`, `safe_read(path)` | traversal, symlink, unicode, `.git`, size caps |
| `snapshot` | `capture(root) -> Snapshot`, `diff(a,b)` | hashing, manifests, exclusion, deterministic ordering |
| `runner` | `run(argv, root, limits) -> Observation` | argv-only execution, selection-flag detection, output parsing, timeout, env scrub |
| `claims` | `parse(text_or_json) -> ParsedClaims` | trigger registry, negation handling, numeric extraction, unknown detection |
| `verdict` | `verify(claims, ctx) -> Verdict` | per-claim falsification procedures, coverage, three-valued outcomes |
| `report` | `render(verdict, fmt)` | terminal/JSON/HTML escaping, offline self-contained HTML |
| `cli` | `main(argv)` | argument handling, exit codes, error messages |

## 8. Acceptance criteria

- `pytest` suite green, including adversarial fixtures: lying agent, `pytest -k trivial` laundering, zero-test run, fabricated span, stale baseline, dependency addition, deleted test, path traversal, symlink escape, shell injection attempt, HTML XSS, duplicate JSON keys, oversized input, unicode homoglyph path.
- Static review harness reports zero banned constructs (`shell=True`, `eval`, `exec`, `pickle`, `os.system`, `requests`, `urllib.request`, raw `innerHTML`).
- Golden behaviour file byte-identical before and after the architecture-deepening pass.
- Single-file `receipts.pyz` build via stdlib `zipapp` runs the CLI with no install.
- README states every "we do NOT claim" item from `docs/BRAINSTORM.md` §5.
