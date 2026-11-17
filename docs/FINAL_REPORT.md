# Final Delivery Report

Date: 2026-11-13. Status: **DONE**. Owner: Boss/Manager.

## What was delivered

**`receipts`** — an offline, stdlib-only, zero-config CLI that reads an AI coding agent's own prose ("All tests pass", "No new dependencies", "I only changed `src/a.py`") and **falsifies** each checkable claim against the current repository. Verdicts are `PASS` / `FAIL` / `INDETERMINATE` / `UNCHECKABLE`, with an evidence-bound terminal, JSON and self-contained offline HTML report.

Tagline: *Your agent said "all tests pass". Check the receipts.*

The function is narrow in mechanism and universal in audience. It requires no cooperation from Claude Code, Codex, Cursor, Copilot, Aider, Gemini CLI, or any other agent, because the input channel is text the agent already emits. That pivot is what survived two adversarial prior-art passes.

## What was installed from GitHub

| Upstream | Status | Where |
|---|---|---|
| `anthropics/skills` | installed | `skills/anthropics/` (4 skills) |
| `obra/superpowers` | installed | `skills/superpowers/` (9 skills, incl. brainstorming, TDD, verification-before-completion) |
| `mattpocock/skills` | installed | `skills/mattpocock/` (8 skills, incl. **improve-codebase-architecture**) |
| `vercel-labs/agent-skills` + `vercel-labs/skills` | installed | `skills/vercel-labs/` (3 skills) |
| `hardikpandya/stop-slop` | installed | `skills/stop-slop/` |
| `smeltery/skills` | unavailable (non-tarball response) | the required `improve-codebase-architecture` skill was obtained from `mattpocock/skills` |

25 vendored skill groups, 271 files, `skills/SKILLS_MANIFEST.json`, `NOTICE`, and `research/upstream-install-manifest.json` for attribution.

## Brainstorming, self-grilling, decisions

Three ideas killed with evidence, one revised, one winner. Four real rejections are recorded in `docs/WORKFLOW.md` and one rejected fix is recorded in `docs/REVIEW.md` Round 3. The self-grilling Q&A (including "isn't this just run the tests yourself plus a regex?" and "what if nobody cares?") is in `docs/BRAINSTORM.md`. The locked spec is `docs/SPEC.md`.

## Agents and workflow

Nine named agents (Scout, Griller, Architect, Implementer, Red Team, Test Engineer, Reviewer ×9, Architecture Improver, Docs/Growth) with acceptance criteria, ten stages, nine gates, and a rejection log. Agents were run as independent fresh-context passes, not handed the full session history. Full detail: `docs/WORKFLOW.md`.

## Review rounds

**Nine rounds** (the brief said *over* eight), 23 findings, 23 fixes, 35 new regression fixtures, 143 tests. Lenses: path safety, command execution, parser safety, claim laundering, snapshot determinism, reporting safety, correctness, supply chain, and an independent ninth re-review that found three genuine defects:

1. `go test ./...` / `pytest .` were falsely refused as "selection", making whole-suite claims permanently unverifiable for Go.
2. `{"version": true}` was accepted as version 1 (`True == 1`).
3. Boolean span offsets were accepted as `0`/`1`.

All three fixed; golden contract stayed byte-identical. Log: `docs/REVIEW.md`, machine evidence: `docs/REVIEW_EVIDENCE.txt`.

## Architecture deepening without changing any function

`improve-codebase-architecture` vocabulary applied: module, interface, depth, seam, adapter, locality, leverage, deletion test. `verdict.py` shrank 393 → 86 lines; 11-branch dispatch ladder removed; all ten falsification procedures moved into the deep `registry.py` behind one `falsify(claim, ctx)` seam.

**Proof that no function changed:** `docs/GOLDEN.txt` (12 scenarios, 7,844 bytes) was captured before and compared byte-for-byte after, and again after the Round 9 fixes. Both checks passed. Full suite green both times. Detail: `docs/ARCHITECTURE.md`.

## Security

24 threat vectors with mitigations and fixtures in `docs/THREAT_MODEL.md`. The single most dangerous unsolved attack, **claim laundering**, is named and bounded rather than hidden: every execution result carries an explicit `coverage_note`, and opt-in `require_known_runner` is available. No `PASS` is emitted on insufficient evidence.

## Honest limits

`docs/GROWTH.md` refuses to promise 105,000 stars: possible but unlikely, with the three biggest blockers named. `README.md` lists 23 explicit non-goals. The tool does not stop agents lying, prove correctness, replace CI, or replace supply-chain attestation.

## Final verification (fresh, from the packaged zip)

```
$ python3 -m pytest -q
143 passed

$ python3 tools/golden.py --check
PASS: golden byte-identical (7844 bytes, 12 scenarios)

$ python3 tools/review_harness.py
RESULT: 9/9 rounds PASS

$ python3 receipts.pyz version
receipts 1.0.0 (stdlib-only, offline)

$ python3 -m receipts check --file examples/lying-agent.md --config examples/.receipts.json
exit 1; tests.pass FAIL
```

Delivery: a single `receipts.zip` containing the full source, tests, tools, docs, vendored skills, research reports, examples, licence, and the ready-to-run `receipts.pyz`.
