# Can this reach 105,000 GitHub stars? An honest assessment

The brief asked for a program that could aim at **>105,000 GitHub stars**. This file refuses to inflate the answer.

## Short answer

**It is possible but unlikely, and nobody can promise it.** 105,000 stars is an extraordinary threshold. For scale, that is the territory of a handful of canonical developer tools and large skill repositories, not of a focused CLI. No comparable repository's star trajectory was verified in either research pass, so any numeric projection here would be invented. This project is built to be genuinely useful first; the star target is an ambition, not a forecast.

## Why the idea has a real shot at broad adoption

1. **Universal, daily pain.** Anyone who has used Claude Code, Codex, Cursor, Copilot, Aider or Gemini CLI has been told "all tests pass" when they did not. The sentence is older than the tools.
2. **Zero integration.** The input is prose the agent already emits. No plugin, no hook, no vendor cooperation, no account, no network, no config for the default claim set. This removes the two adoption blockers that killed the earlier "agent-emitted receipt format" idea.
3. **A ten-second demo.** Give the tool a lying agent and it prints `FAIL` with the real runner output. That is immediately legible, shareable, and tweetable.
4. **A visible artifact.** `--html` produces a self-contained evidence report that can be attached to a PR. Reviewers understand it without reading the tool's docs.
5. **Single-file distribution.** `receipts.pyz` runs with `python3 receipts.pyz ...` and no install. Stdlib-only means it works in air-gapped and locked-down environments.
6. **Honest positioning.** The README lists what the tool cannot do. Developer tools that overclaim get corrected publicly; tools that scope themselves precisely get trusted.

## The three biggest blockers

1. **"CI already does this."** It does not (CI checks the committed artifact, not the assertion made about an uncommitted checkout), but the objection is the single biggest conversion hurdle. The README answers it in one paragraph and links `docs/THREAT_MODEL.md`.
2. **Per-repository command diversity.** Every project has its own test command, shell, package manager, locale and flaky-test culture. Zero-config detection covers common Python/Node/Go/Rust layouts; everything else needs a five-line `.receipts.json`. A plugin model would help adoption but would breach the stdlib-only/offline promise.
3. **Indifference to another local checker.** Developers already have linters, pre-commit, CI and IDE checkpoints. A new tool must earn a place in the loop, most plausibly as a PR-review artifact rather than a mandatory gate.

## Three viral hooks (and why they are not sufficient)

- **"Your agent said 'all tests pass'. Check the receipts."** A one-line tagline with a screenshot of a caught lie.
- **Attack fixtures as documentation.** The repository ships a lying agent, a `pytest -k trivial` laundering attempt, a forged span, a stale baseline, a path-traversal receipt and an XSS PR body. Developers love a tool that demonstrates its own scepticism.
- **A PR badge.** `receipts check --json` is designed to be consumed by a bot that posts a compact `3 PASS / 1 FAIL / 2 INDETERMINATE` summary.

None of these produces 105k stars on its own. Sustained maintenance, a stable claim schema, and adoption by at least one major agent runtime as a *convention* would be needed. Even then the outcome is uncertain.

## What we will not do to chase stars

- We will not claim the function "does not exist" without the two prior-art reports in `research/`.
- We will not claim to stop lying, prove correctness, or replace CI.
- We will not add telemetry, accounts, cloud features, or a marketplace.
- We will not add a plugin system that executes third-party code.
- We will not add a `105k stars` badge or a roadmap promise.

## Honest success criteria

If in a year this tool is used in real PR reviews, catches real false claims, and stays dependency-free, it succeeded. Stars are a lagging indicator of that, not the goal itself.
