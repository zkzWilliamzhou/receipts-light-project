# receipts

> **Your agent said "all tests pass". Check the receipts.**

`receipts` reads an AI coding agent's own words and tries to **falsify** them against the repository in front of you. It compiles the prose into typed claims, runs the check that would make each claim false, and prints `PASS`, `FAIL`, `INDETERMINATE` or `UNCHECKABLE` with the evidence attached.

No plugin. No hook. No vendor cooperation. No account. No network. No configuration for the default claim set. Python standard library only.

```
$ receipts check --text "All tests pass." --repo .
receipts - claim verification verdict
========================================================
[FAIL         ] tests.pass
              claim: All tests pass.
              agent claimed tests pass but runner reported 2 failed and exit status 1

counts : FAIL=1
```

## The problem

An agent's final message is prose. Git shows what changed; CI checks the committed state; neither one checks **the sentence the agent just wrote**. `receipts` takes that sentence as input. It works with Claude Code, Codex, Cursor, Copilot, Aider, Gemini CLI, a handoff note, or a human-written PR description, because the input channel is just text.

## Ten-second demo

```bash
# no install needed
python3 receipts.pyz claims                 # what can be checked
python3 receipts.pyz baseline --repo .      # pin a before-state
python3 receipts.pyz check --text "All tests pass. No new dependencies were added." --repo .
python3 receipts.pyz check --file pr-body.md --html report.html --repo .
python3 receipts.pyz check --text "All tests pass." --json --repo .
```

To catch a lying agent, point `.receipts.json` at your real test command:

```json
{
  "commands": {
    "tests": ["python3", "-m", "pytest", "-q"],
    "build": ["python3", "-m", "build"],
    "lint": ["ruff", "check", "."]
  },
  "require_known_runner": false
}
```

Now `receipts check --text "All tests pass."` runs the whole suite. A filtered run (`-k`, `--grep`, a bare path), zero collected tests, or a numeric count that disagrees with the runner is refused as `INDETERMINATE` or reported as `FAIL`.

`receipts run -- <cmd>` captures a before/after baseline around any command, so diff-shaped claims have something to compare against:

```bash
receipts baseline --repo .
# ...let the agent work...
receipts check --text "I only changed `src/a.py`. No secrets were added." --repo .
```

## How it works

1. **Compile.** `claims.py` splits the text into sentences and maps each one to a typed claim (`tests.pass`, `deps.unchanged`, `files.changed`, ...). Negations and future tense are not compiled into success claims. Claim-shaped prose with no predicate is surfaced as `UNCHECKABLE`, not dropped.
2. **Falsify.** `registry.py` owns one procedure per claim type behind a single `falsify(claim, ctx)` seam. Each procedure asks: what evidence would make this claim false? Commands run argv-only with no shell, bounded output, a scrubbed environment and a timeout.
3. **Report.** `report.py` renders terminal, JSON, or a self-contained offline HTML file. Every value is escaped; the HTML has no external resources.

**Verdicts are three-valued on purpose.** When evidence is missing, unsafe to obtain, or inapplicable, the answer is `INDETERMINATE`. A `PASS` is only emitted when the recorded evidence satisfies the recorded claim under its declared rules.

| Exit code | Meaning |
|---|---|
| `0` | no `FAIL` (indeterminate results allowed) |
| `1` | at least one `FAIL` |
| `2` | usage or I/O error |
| `3` | `--strict` and any `INDETERMINATE` / `UNCHECKABLE` |

## Claim registry

| Claim | Falsified by | Never PASS when |
|---|---|---|
| `tests.pass` | whole-suite run: exit 0, nonzero collected, zero failures, matching numeric counts | filtered run, zero tests, unparseable output, truncated output, repo changed mid-run |
| `build.ok` / `lint.clean` | declared command exit 0 | no command declared |
| `files.changed` | baseline vs current snapshot, compared to declared paths/count/"none" | no baseline |
| `deps.unchanged` | parsed manifest name sets before/after | no baseline |
| `secrets.none_added` | high-confidence patterns in added lines | baseline missing; **also when no pattern matched** (absence is not proof) |
| `checks.not_disabled` | deleted test/spec files, skip/no-verify markers in added lines | baseline missing; **also when nothing matched** (unknown config space) |
| `api.unchanged` | requires an explicit extractor, baseline, visibility rules and comparator | **always**, without a declared proof tool |
| `span.matches` | byte-exact comparison of a recorded offset span | unsafe path |
| `command.exit` | re-run an allow-listed argv, compare exit status | not allow-listed |

`receipts claims` prints the live registry. Unrecognised claim ids are `UNCHECKABLE`, never `PASS`.

### Selective omission

A capable agent can make five trivial true claims and omit the consequential one. The verifier cannot read private intent. Supply a claims manifest to make omission visible:

```bash
receipts check --text "All tests pass." --require required-claims.json --repo .
# required-claims.json: ["tests.pass", "deps.unchanged", "secrets.none_added"]
```

Missing entries produce a `FAIL` row `manifest.required_claims`. Without a manifest, no omission detection is claimed.

## Structured input (optional)

A caller may pass a typed receipt instead of prose. Prose is the default; this is for tooling.

```json
{
  "version": 1,
  "claims": [
    {"id": "span.matches", "subject": "src/a.py",
     "evidence": {"path": "src/a.py", "start": 0, "end": 12, "expected": "hello world"}}
  ]
}
```

The JSON parser rejects duplicate keys, deep nesting, trailing content and oversized input.

## Why not just CI?

CI verifies the committed artifact against a pipeline. `receipts` verifies an **assertion** against the **checkout**, at the moment a human is deciding whether to believe an agent. It runs before review, on uncommitted state, with no CI infrastructure. It complements CI; it does not displace it.

## What `receipts` does NOT do

Read this before trusting a single green row.

- It does not stop agents from lying, and it does not prove overall code correctness.
- It does not replace CI, code review, or application security testing.
- It does not replace SLSA, in-toto, Sigstore, or SBOM attestations.
- A `PASS` does not mean the change is safe, compliant, or production-ready.
- It does not detect all secrets, vulnerabilities, or malicious code.
- It does not prove semantic properties such as "public API unchanged" without an explicit proof tool.
- It does not promise deterministic re-execution across different environments; flaky tests, locale, network and clocks are real.
- It does not infer selective omission from an agent's chat output; that needs an external claims manifest.
- Its HTML report is not tamper-proof or cryptographically signed.
- It does not read scans, OCR, or handwriting; it reads text files in a checkout.
- It does not give legal advice.
- It does not guarantee any number of GitHub stars. See `docs/GROWTH.md` for the honest assessment.

The hardest unsolved attack is **claim laundering**: a real command, a real digest and a real span that do not entail the claim. Every execution result carries an explicit `coverage_note` saying the verifier checks the reported summary, not that the command exercised real tests. `require_known_runner: true` is available for teams that want a stricter, opt-in mode. See `docs/THREAT_MODEL.md` for 24 vectors and their mitigations.

## Novelty, honestly

Two adversarial prior-art passes are included in `research/`. They killed three stronger-looking ideas: agent-change audit/undo (a saturated category: `agent-undo`, `Salvager`, `Rewindex`, `Regent`, `AgentTM`, `Ponytrail`, `Tracekit`, `git-ai`, Claude Code `/rewind`), an extractive contract lens (thin wrapper over existing grounded extractors), and prompt-to-hunk attribution (pre-empted by Agent Note).

What remains, and what we claim: **`receipts` is an offline, zero-config CLI that compiles an AI coding agent's own prose self-report into typed, locally falsifiable claims, independently executes the falsification procedure for each claim against the current repository, and emits a machine-checkable three-valued verdict with an evidence-bound report.** Independent verification of agents exists; build attestation exists; test-result formats exist. We did not find a tool that compiles the agent's own sentences into falsification tests against the local checkout. We do not claim to be the first to verify agents, the first to use evidence, or the first to be "grounded".

## Repository layout

```
receipts/                stdlib-only package
  model.py               Result / Verdict value types (shallow seam)
  registry.py            every falsification procedure (deep module)
  verdict.py             orchestrator, manifest, exit codes (thin)
  claims.py              prose -> typed claims, strict JSON loader
  runner.py              argv-only execution, bounded output, test parsing
  safepath.py            containment, O_NOFOLLOW, hardlink refusal
  snapshot.py            deterministic tree digests, diffs, manifests
  report.py              terminal / JSON / offline HTML
  cli.py                 check, baseline, run, claims, version
tests/                   143 tests incl. adversarial fixtures and 9-round regressions
tools/golden.py          byte-stable behaviour contract
tools/build_zipapp.py    builds receipts.pyz
docs/                    BRAINSTORM, SPEC, WORKFLOW, REVIEW, ARCHITECTURE,
                         THREAT_MODEL, GROWTH, GOLDEN
skills/                  vendored upstream Agent Skills (see SKILLS_MANIFEST.json)
research/                two adversarial novelty reports
```

## Development

```bash
python3 -m pytest -q                      # 143 tests
python3 tools/golden.py --check           # behaviour contract
python3 tools/review_harness.py           # 9 review lenses
python3 tools/build_zipapp.py             # receipts.pyz
```

Design constraints: standard library only, offline, no telemetry, no shell string construction, no `PASS` on insufficient evidence. `docs/WORKFLOW.md` records the agent roster, gates and the four real rejections that happened during the build.

## Installed skills

Upstream Agent Skills were fetched from GitHub and vendored under `skills/` with attribution in `skills/SKILLS_MANIFEST.json` and `NOTICE`: Anthropic `anthropics/skills`, `obra/superpowers` (brainstorming, TDD, verification-before-completion, systematic debugging, code review, plans), `mattpocock/skills` (including `improve-codebase-architecture`, used for the architecture pass), `vercel-labs/agent-skills` and `vercel-labs/skills`, and `hardikpandya/stop-slop`. One requested repo (`smeltery/skills`) was unavailable at fetch time; the `improve-codebase-architecture` skill was obtained from `mattpocock/skills`, which carries it.

## License

MIT. See `LICENSE`. Third-party skill notices: `NOTICE`.

---

Built to be small enough to audit and honest enough to distrust.
