# Research index

Two independent, adversarial prior-art passes were run before any code was written. Both are included in full, with their sources, so a reviewer can attack the novelty claim.

| File | Mission | Outcome |
|---|---|---|
| `novelty-landscape.md` | Kill three candidate ideas (agent audit/undo, extractive clause lens, prompt-to-hunk attribution); rank by novelty/usefulness/adoption | Recommended Candidate B. **The manager overrode it** because the report itself conceded the idea was a thin wrapper with high false-negative risk. Documented in `docs/BRAINSTORM.md` §2.2. |
| `novelty-landscape-2.md` | Try to kill a fourth idea (agent-emitted evidence receipts) and build a 20+ vector threat model | Narrowed the idea but exposed two fatal adoption blockers. **The manager rejected the framing** and pivoted the input channel from agent-emitted JSON to the agent's existing prose. Threat model and prohibitions retained. |
| `upstream-install-manifest.json` | Fetch record for the six GitHub skill repos | 6 installed, 1 unavailable (`smeltery/skills`), whose `improve-codebase-architecture` skill was obtained from `mattpocock/skills` instead. |

## What the research established

- The **audit/checkpoint/undo** category is saturated: `agent-undo`, `Salvager`, `Rewindex`, `Regent`, `AgentTM`, `Ponytrail`, `Tracekit`, `Arcaeon Ledger`, `git-ai`, `Kintsugi`, `Rewind`, `Sentient`, `Turnback`, `Turnal`, Claude Code `/rewind`.
- **Cross-agent policy compilation** exists: AIES, Vectimus, Yolonot.
- **Prompt-to-diff attribution** exists: Agent Note (line-level for four agents).
- **Grounded extraction** exists: ToS;DR, SourceryForge, ClauseLM/CUAD, DocuOCR, FinePrint Phantom, Spellbook.
- **Agent self-verification** exists: OpenSquilla, Hermes, ECA, ExplainBench; plus SLSA/TAP/JUnit/SARIF as evidence formats.

## What it did not establish

No tool was found that **compiles an agent's own prose self-report into typed falsification procedures and runs them against the local checkout**, with zero agent cooperation and zero configuration. That is the exact, narrow claim in `README.md` §"Novelty, honestly". Neither report proves no obscure or private implementation exists; both state this coverage limit explicitly.

Caveat: some secondary sources in `novelty-landscape-2.md` are news/aggregator pages rather than primary repositories, and several items are marked "unverified" in the report. They are retained as leads, not as proof. Primary sources (SLSA spec, TAP spec, Claude Agent SDK docs, GitHub repos) were checked where available. Star counts were not verified and are not used in any claim.
