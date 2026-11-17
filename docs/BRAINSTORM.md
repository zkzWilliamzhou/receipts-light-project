# Brainstorm & Self-Grilling Record

Date: 2026-11-13. Owner: Boss/Manager. Status: **LOCKED**.

This file is the record of the deep-thinking pass. It is deliberately written as an argument, not a pitch. Three ideas were killed. One survived in a narrowed form.

## 0. What we were actually asked to find

A program whose **core function does not already exist**, that **can truly make a difference**, and that can **aim at >105,000 GitHub stars**. Those three constraints fight each other. "Does not exist" pushes toward a narrow research prototype. "105k stars" pushes toward a universal, zero-friction, instantly demoable tool. Anything that satisfies the first by being obscure fails the third. The resolution is to find a function that is **narrow in mechanism but universal in audience**.

## 1. The pain we chose to attack

Every developer who uses a coding agent has been told "all tests pass" when they did not. The agent's final message is prose, not evidence. Git shows what changed but not what was claimed. CI is the shared source of truth — but CI runs *after* the human has already trusted the summary, and it runs on the committed state, not on the claim that was made about it. There is no tool that takes the agent's own words as input and mechanically asks: **is that sentence true of this checkout, right now?**

That gap is not "we need better logging". It is "we need a falsifier for self-reports".

## 2. Candidates generated, then grilled

| # | Idea | One-line core function | Verdict |
|---|---|---|---|
| A | Black-box ledger | Offline tamper-evident record of agent file changes + selective undo | **KILLED** — saturated |
| B | Grounded clause lens | Offline extractive-only contract/ToS/bill analysis with exact spans and `--verify` | **KILLED** — thin wrapper, high false negatives |
| C | Unasked-change separation | Hunk-level separation of requested vs unrequested agent edits with 3-way revert | **KILLED** — preempted |
| D | Agent-emitted evidence receipts | Agent writes typed JSON claim+evidence receipts; independent verifier replays them | **REVISED** — right mechanism, wrong adoption boundary |
| E | **Prose claim falsifier** | **Read the agent's own prose, compile each checkable claim into a falsification test, independently verify against the repo, emit PASS/FAIL/INDETERMINATE** | **WINNER** |

### 2.1 Why A died

`agent-undo`, `Salvager`, `Rewindex`, `Regent`, `AgentTM`, `Ponytrail`, `Tracekit`, `Arcaeon Ledger`, `git-ai`, `Kintsugi`, `Rewind`, `Sentient`, `Turnback`, `Turnal` and Claude Code `/rewind` already cover local snapshots, attribution, hash chains, and rollback. A new entrant would compete on adapter count, not on a missing function. Building it would have been a me-too project dressed up as innovation. Source: `novelty-landscape.md` §2, `novelty-landscape-2.md`.

### 2.2 Why B died even though the Scout ranked it first

The Scout's own report conceded the strongest attack: "an existing grounded extractor plus a post-processing script could reproduce the core function." It also conceded that strict substring matching produces high false-negative rates on synonyms, tables, OCR and implied obligations. A tool that silently misses the clause that lets a company raise your price is worse than no tool for a consumer. Prior art: ToS;DR, SourceryForge (exact spans), ClauseLM/CUAD (verbatim spans), DocuOCR, FinePrint Phantom, Spellbook. Its novelty was a *bundle of constraints*, not a function. **Manager override: rejected.**

### 2.3 Why C died

Agent Note already records pre-edit/post-edit file states, subtracts later human edits, and supports Claude Code, Codex CLI, Cursor and Gemini CLI with line-level attribution and conservative file-level fallback. Grouping attributed lines into hunks is a data-structure change, not a new semantic capability. `novelty-landscape.md` §4.

### 2.4 Why D was revised rather than accepted

Scout-2 found real adjacent prior art (OpenSquilla self-verification, Hermes completion contract, ECA evidence-carrying agents, ExplainBench, SLSA provenance, TAP, JUnit, SARIF) and named the two fatal adoption blockers plainly: **no agent vendor has an incentive to emit a neutral format**, and **every repo needs its own test command/ignore/plugin config**. A format that nobody emits is a spec, not a program.

The pivot that fixes both: **do not ask the agent to emit anything.** Read the prose it already produces. Parse natural-language claims into a typed registry. Falsify each one against the checkout. Zero integration, zero config, works with Claude Code, Codex, Cursor, Copilot, Aider, Gemini CLI, or a human writing a PR description — because the input channel is just text.

## 3. Self-grilling (the uncomfortable questions)

**Q: Isn't this just "run the tests yourself plus a regex?"**
A: Partly. The defence is not "but we add HTML". It is the **falsification contract per claim type**: each claim declares what would make it false, what evidence is required, and what coverage is demanded. `all tests pass` is not satisfied by a green command. We reject `-k`/`--grep`/`--filter`/path-limited runs, reject `0 tests collected`, reject a numeric count claim that disagrees with the runner's parsed count, and bind the observation to a repo snapshot digest. That is the difference between "I ran something green" and "I ran the thing that would have falsified the claim".

**Q: Can't a lying agent just lie in a way you cannot detect?**
A: Yes. We do not claim to stop lying. We claim to falsify the checkable subset and to label everything else `UNCHECKABLE` or `INDETERMINATE` with a visible count. A tool that says "3 of 7 claims could not be verified" is more useful than one that says nothing.

**Q: What about claim laundering — a real command, a real span, that does not entail the claim?**
A: This is the single most dangerous attack. Mitigations: (1) no test-selection flags accepted for whole-suite claims, (2) parsed runner output must include a nonzero collected count, (3) numeric claims are cross-checked against the parsed count, (4) commands are never taken from agent prose — only from project config or built-in runner detection, (5) `api.unchanged` and similar semantic claims return `INDETERMINATE` unless an explicit extractor/baseline/comparator is supplied, (6) evidence that is internally consistent but insufficient yields `INDETERMINATE`, never `PASS`.

**Q: Flaky tests, timestamps, network, locale — won't re-runs disagree with the original claim?**
A: Yes. Hence a three-valued verdict. Fresh execution is always labelled `OBSERVED_AT_VERIFY` with its own digest and timestamp, never presented as a replay of the original evidence. `--strict` lets CI decide how to treat `INDETERMINATE`.

**Q: Could a malicious PR body inject a shell command into the verifier?**
A: Not by design. Commands are argv arrays only, never shell strings. Agent prose is never used to construct a command. `shell=True` is banned by a static check in the review harness. Only allow-listed runners from project config or built-in detection may be executed, under a timeout, output cap and scrubbed environment.

**Q: Can the verifier be tricked into reading outside the repo?**
A: That is Round 1–3 of the review plan. Canonicalise within root, reject absolute/`..`/non-normal paths, resolve symlinks once and re-check containment, exclude `.git`, cap file sizes and nesting, reject duplicate JSON keys.

**Q: Doesn't CI already do this?**
A: CI verifies the committed artifact against a pipeline. This verifies the *assertion* against the *checkout*, at the moment a human is deciding whether to believe an agent. It is a pre-review tool, not a CI replacement. The README says so.

**Q: Why would this reach 105k stars rather than 5k?**
A: It may not. 105k is extraordinary and no honest analysis can promise it. The route is: universal pain, one command, no account, no config, offline, a 10-second demo where a lying agent gets caught, and a shareable HTML verdict. `docs/GROWTH.md` gives the honest blockers and numbers. We aim at it; we do not claim it.

**Q: What exactly is new here?**
A: The **input channel** (unstructured self-report text), the **compilation step** (prose → typed falsification procedure with coverage requirements), and the **three-valued, evidence-bound verdict** — combined in one offline zero-config CLI. Independent verification of agents exists; build attestation exists; test-result formats exist. Nobody in two research passes was found to compile an agent's own sentences into falsification tests that run against the local checkout.

**Q: What if nobody cares?**
A: Then the project is a well-tested, honest, small tool. The engineering still stands on its own. We would rather ship that than a grand claim we cannot defend.

## 4. The locked novelty claim

> `receipts` is an offline, zero-configuration CLI that converts an AI coding agent's own prose self-report into typed, locally falsifiable claims, independently executes the falsification procedure for each claim against the current repository, and emits a machine-checkable `PASS` / `FAIL` / `INDETERMINATE` verdict with an evidence-bound, self-contained HTML report. It requires no cooperation from the agent, no account, no network, and no per-repository configuration for its default claim set.

## 5. What we will NOT claim

Stops agents lying · proves correctness · replaces CI, review or appsec · replaces SLSA/in-toto/Sigstore/SBOM · PASS means safe or production-ready · detects all secrets or vulnerabilities · proves semantic properties · deterministic re-execution · infers selective omission from chat · tamper-proof HTML · works on scans/OCR · legal advice · 105k stars guaranteed.

## 6. Decision

Build E. Name: **`receipts`**. Tagline: *"Your agent said 'all tests pass'. Check the receipts."* Primary command: `receipts check`. See `docs/SPEC.md`.
