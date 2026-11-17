# Novelty Landscape for a Program Whose Core Function Does Not Yet Exist

## Executive verdict: build Candidate B, but only as strict extractive evidence—not as legal AI

**Rank the candidates in this order: B, C, A.** Candidate A is the least defensible because “one policy compiled to many agent runtimes” already exists as a directly implemented core function. AIES documents a shared guard wired into Claude Code, Cursor, GitHub Copilot, Kiro, Codex, Gemini CLI, Devin Desktop, and OpenCode, and its guard accepts a `--target` so one policy script answers in each runtime’s native hook shape [1]. Vectimus similarly describes plain, editable Cedar policies with local enforcement across Claude Code, Cursor, Copilot, Gemini CLI, Codex CLI, and agent frameworks [2]. Yolonot claims one policy engine across 24 harnesses and supplies `doctor`, `audit`, and harness profiles [3]. Candidate C is closer, but Agent Note already maps prompts, responses, and edits to files; compares AI edits, later human edits, and final diffs; and explicitly falls back from line-level attribution to file-level attribution rather than guessing [4].

Candidate B survives only because the requested **combination** is not proven to be a single existing tool: offline operation, no generative summarization, a fixed taxonomy covering contracts/ToS/privacy/insurance/medical bills, exact source character offsets, and a mandatory `--verify` mode that re-checks every evidence span. ToS;DR manually breaks policies into community-reviewed points and ratings, but it is a curated knowledge base rather than a local document extractor and does not address medical bills or exact offsets [5]. Source-grounded extraction frameworks and CUAD span models show the individual primitives exist. The defensible unoccupied gap is therefore an **extractive contract lens**, not “the first grounded legal AI” or “a hallucination-free legal copilot.” The winning claim must be about strict textual evidence and auditability, never legal advice.

## Audit-log and checkpoint/undo tools already cover the rejected premise

The proposed audit/undo family should remain rejected. The named prior art is not merely conceptually similar: several products explicitly implement the same claimed core of local recording, snapshots, safe rollback, and tamper-evident verification. Kintsugi describes a local deterministic guard that intercepts agent commands, snapshots files before destructive operations, makes changes reversible, and records an append-only hash-chained log; it also documents native pre-tool hooks for Claude Code, Cursor, Codex, Gemini, Copilot, OpenCode, and other runtimes [13]. Rewind documents private Git snapshots under isolated refs, a signed append-only event log, policy receipts, and signed replay [14]. AgentTM records Codex file changes as SHA-256 content-addressed checkpoints in an SQLite ledger and restores them to an isolated worktree [15]. Sentient captures file, process, and network events with eBPF and correlates them to agent sessions [16].

A second cluster provides undo at turn, step, command, or session granularity: Turnback snapshots workspaces before every shell command and edit; Turnal provides private Git checkpoints, diffs per turn, line attribution, rollback, and bisect; bashback snapshots every shell command; logbook records sessions, scrubs secrets, detects risky actions, and reverts qualifying sessions; and codex-rewind adds `/rewind` and `/redo` to Codex [17]. Zerostel’s comparison also acknowledges that the native agents themselves increasingly contain checkpoint and undo behavior [17]. Claude Code’s `/rewind` and related session behavior are part of this established category, not a novelty opening.

The strongest honest summary is therefore simple: **recording, checkpointing, and rolling back AI-agent actions is now a populated product category**. Any new program in this family would need a substantially different core function—such as causal attribution, cross-agent replay, or a novel security property—rather than another local ledger plus undo command. The original formulation does not satisfy that test.

## Candidate A: portable policy compiler exists, and “prove enforcement works” is only a partial opening

### What exists

AIES is the strongest direct hit. Its documentation states that one shared policy script is wired into eight agent runtimes and that the guard emits output in the target runtime’s required form [1]. It also describes deterministic, regex-based rules, denial outside the model, and fail-closed handling when the guard has an internal error. Vectimus supplies a second, strong form: human-readable Cedar policies, local evaluation, and Ed25519-signed receipts that can be verified offline [2]. Yolonot demonstrates the same pattern at larger runtime breadth: one policy engine, per-harness adapters, and `doctor` and `audit` diagnostics [3].

The native runtime capability underneath these tools is also now a documented standard mechanism. Claude’s Agent SDK hook documentation describes `PreToolUse`, `PostToolUse`, and other lifecycle events; a callback receives tool name, arguments, session ID, and related data, and may allow, deny, modify input, or inject context [6]. This is exactly the substrate needed to compile one policy into multiple runtimes. Aider and OpenCode do not change the conclusion merely by not appearing in every project’s adapter matrix: once a shared core emits adapter-specific hook code or configuration, adding a new target is integration work, not a novel security primitive.

### Nearest prior art and strongest kill argument

The nearest prior art is not a generic policy language such as OPA/Rego or Cedar. It is AIES’s multi-target shared guard, Vectimus’s multi-runtime Cedar enforcement, and Yolonot’s adapter matrix. The strongest kill argument is that Candidate A’s headline—“write your agent safety policy once, enforce it everywhere”—is already the published behavior of multiple tools. A new tool would therefore compete on a long list of execution details: more targets, richer policy predicates, better UX, more adapters, or cleaner installation. Those are credible product-differentiation axes, but they are not evidence of a missing core function.

The remaining claim, “prove each compiled target actually enforces the policy,” is narrower and more defensible. Vectimus’s documentation emphasizes signed decision receipts, not adversarial conformance tests [2]; AIES documents the shared guard and failure semantics but not a reproducible red-team suite [1]. Yolonot’s diagnostics, profiles, and audits still do not establish end-to-end adversarial conformance of every emitted hook [3]. This gap is real, but it is also easy to overclaim: testing whether a hook denies a simulated probe is not proof of security, and a third party can change configuration, disable a hook, or operate outside the agent.

### Honest unoccupied space and wrapper risk

The genuine unoccupied work is an **independent, reproducible conformance suite** that compiles a policy to each target and asserts required denies/allows against the real runtime contract. This is valuable because a generator can be syntactically correct yet semantically ineffective. Yet a standalone suite is vulnerable to “thin wrapper” criticism: it still depends on upstream hook formats, must track each agent’s protocol changes, and does not itself stop malicious shell commands. It also invites configuration-space arguments—“your test passed because your policy is weak”—and adapter-coverage arguments—“you support Claude but not Aider.” The recommended decision is therefore not to build Candidate A.

## Candidate B: exact-span, extractive document extraction is not yet proven as one complete core function

### What exists

Candidate B faces substantial prior art in both clause extraction and source grounding. ToS;DR has since 2012 curated structured points and letter grades for terms of service and privacy policies through a peer-review process [5]. Commercial platforms such as Spellbook review and redline contracts, while DocuOCR explicitly claims source-clause links and confidence scores for obligations, deadlines, and renewal dates [18][19]. These systems show that obligation extraction, risk scoring, and source-linked output are established market capabilities.

On the technical side, SourceryForge is an open-source Python extraction framework that returns exact character offsets and reconciles extracted entities across chunks [20]. The ClauseLM/CUAD work fine-tunes small language models to return **verbatim spans** for 41 CUAD clause categories and reports span metrics, including 97.4% grounded spans for the cited Llama variant and 98.6% for the cited Qwen variant [21]. FinePrint Phantom explicitly asks an LLM for candidate clauses, retains only real source quotes, and exposes a labeled demo or heuristic mode [22]. Collectively, these projects cover span-level extraction, source-grounded review, and quoted clause review.

### Nearest prior art and strongest kill argument

The strongest kill argument is that Candidate B is a subset of existing contract-intelligence products plus a UI plus character offsets. A reviewer can say: “Clause extractors already link obligations to clauses; grounded extraction frameworks already return offsets; ToS;DR already summarizes policies as structured points.” That argument is serious. It rules out marketing the project as the first tool to cite sources, the first clause extractor, or the first legal-document analyzer.

The candidate nevertheless survives because the exact combination is unusually strict and unusually broad. Most contract-AI systems use generative models and summaries; CUAD models focus on 41 contract categories rather than the requested cross-document taxonomy; ToS;DR is a manual, web-facing curated database; and the cited grounded framework is a general extraction library rather than a ready-made tool for consumers to analyze a privacy policy, insurance policy, or medical bill [5][20][21]. No sourced evidence in this investigation proves that one local tool accepts all four document types, limits itself to extractive spans, exposes character offsets, classifies the requested field set, and independently re-verifies every span.

### What is genuinely unoccupied—and what can kill adoption

The defensible novelty is a **strict extractive evidence pipeline with mandatory re-verification**, not “no hallucinations.” The tool can guarantee only that an output row reproduces text at a recorded byte/character interval and that the re-runner can check this. It cannot prove that the classification label is legally correct, that an obligation is complete, or that nonstandard wording has not been missed. High false-negative risk is the main adoption threat: a strict substring contract will miss synonyms, OCR errors, tables, multi-page layouts, and conceptually implied obligations. Users may prefer a fluent summary even if it is less mechanically auditable. That trade-off must be advertised rather than hidden.

## Candidate C: prompt-to-diff attribution already works at line level for four agents

### What exists

Agent Note is direct prior art. It uses Claude Code’s hook-native prompt, response, and edit data; records pre-edit and post-edit file states; and subtracts later human edits from the final diff [4]. It supports Codex CLI through local transcripts, Cursor through edit hooks and transcripts, and Gemini CLI through `BeforeTool`/`AfterTool` and `BeforeAgent`/`AfterAgent`. For Claude Code, Codex, and Cursor, it can provide line-level attribution when the supporting evidence is sufficient; Gemini remains at file level [4]. Its most important design choice is conservative fallback: if the evidence does not align, it falls back to file level or omits uncertain data instead of inventing attribution.

### Nearest prior art and strongest kill argument

The strongest kill argument is straightforward: the proposed hunk-level review is largely a generalization of Agent Note’s line-level AI/human accounting. If line-level evidence can be aligned across the AI edit, later human edit, and final commit diff, grouping those lines into hunks is an incremental data-structure problem, not a new semantic insight. Agent Note’s file-level fallback also illustrates the unavoidable limitation: without reliable tool traces, no system can deterministically prove which author intended a hunk.

### What is genuinely unoccupied—and why it is still fragile

The unoccupied space could be a portable **prompt-to-hunk causal map** that aligns natural-language task requests with final diffs, supports additional agents, and produces a review UI for accepting or reverting individual semantic changes. Yet this remains fragile. Agent Note already documents that shell-only changes and missing transcripts reduce attribution quality [4]. Any approach that uses semantic similarity or an LLM to infer intent can misclassify coincidental edits or changes a human later amplified. A project could honestly claim “best-effort classification,” but it cannot claim ground-truth separation of requested and unrequested changes without trustworthy per-tool provenance. Candidate C therefore ranks below B: it is more obviously preempted and more dependent on upstream trace data.

## A precise novelty claim we can honestly defend

The recommended program is a local document-analysis tool that extracts a fixed set of structured fields—obligations, money amounts, deadlines, renewal, unilateral-change, arbitration, and data-sharing information—from contracts, terms of service, privacy policies, insurance policies, and medical bills. Every output field must be an exact, byte-reproducible substring of the source document; the tool must not generate, paraphrase, normalize, infer, or summarize facts; and a `--verify` mode must reopen the original document and confirm that each recorded span still matches. The tool may report only that a span was extracted and re-verified, not that a contract is “fair,” “safe,” or “free of risks.”

This claim is defensible because it combines five constraints—heterogeneous personal documents, a fixed field taxonomy, exact offsets, no generation, and mandatory re-verification—in one tool, while grounded frameworks are general extraction libraries and CUAD models are limited to 41 contract categories [20][21]. It is not defensible to claim that the tool guarantees legal completeness, catches every obligation, understands layout or scans perfectly, or eliminates hallucination. Nor should the README claim that exact-span extraction is equivalent to legal reasoning.

The README must not say:

- “Hallucination-free” or “cannot make a mistake.”
- “Reads any PDF, scan, image, or handwriting.”
- “Understands contracts” or provides legal advice.
- “Finds every obligation, deadline, or risky clause.”
- “Grounded” when the system allows inferred, normalized, or generated values.
- “Works without an OCR/text-extraction layer.”
- “Verifies legal correctness”; it verifies only substring evidence.
- “Better than lawyers” or “replaces legal review.”
- “Supports every insurance or medical-bill format.”
- “Local” if it depends on remote models, OCR APIs, or font/binaries that phone home.

## Prior-art checklist: direct attacks and honest differentiation

| Attacker’s comparison | What it actually does | Why Candidate B still differs—if at all |
|---|---|---|
| ToS;DR | Peer-reviewed points, scores, and letter grades for terms of service and privacy policies [5]. | It is a curated web knowledge base, not a local exact-offset extractor; it does not target insurance or medical bills. |
| Spellbook | AI-assisted contract review, redlining, and risk review in Word [18]. | A commercial generative review suite, not a strict extractive span tool with mandatory verification. |
| DocuOCR | Extracts obligations, deadlines, and renewals and links each to a source clause [19]. | The cited page is commercial and does not establish exact character offsets, offline-only execution, or a re-verify mode. |
| FinePrint Phantom | Analyzes ToS and privacy policies, retains source quotes, and scores risk [22]. | Focused on consumer fine-print analysis, not the full requested taxonomy, document breadth, or exact-span re-verification. |
| SourceryForge | General open-source extraction with Pydantic schemas and exact character offsets [20]. | A developer framework, not a user-facing document tool with the proposed fixed schema and `--verify`. |
| ClauseLM/CUAD | Verbatim-span contract extraction across 41 CUAD categories [21]. | Covers commercial contracts and a fixed taxonomy, not the requested heterogeneous document set or mandatory re-verification. |
| Llama/CUAD and Qwen/CUAD models | Return JSON with values copied from source and report span metrics [21]. | Evidence establishes model extraction, not a complete local CLI, broad document taxonomy, and re-verify workflow. |
| OPA/Rego or Cedar | General policy-as-code evaluation languages. | Not document extractors and not evidence that they span the requested document categories. |
| Agent Note | Attributes edits to agents and humans at line or file level [4]. | Prior art for Candidate C, not a document-extraction system. |
| AIES | One shared guard for eight agent runtimes using native hooks [1]. | Prior art for Candidate A, not a contract or document-analysis tool. |
| Vectimus | Cedar policies with local enforcement and offline-verifiable receipts [2]. | Prior art for portable agent policy enforcement, not span-cited document review. |
| Yolonot | One policy engine across 24 harnesses plus diagnostics [3]. | Shows the adapter model is established; relevant to Candidate A, not Candidate B. |

The most dangerous attack is that an existing grounded extractor plus a post-processing script could reproduce the core function. The honest defense is that Candidate B’s value lies in a single strict contract: no inferred fields, no generation, fixed schema, byte-level offsets, and an independently runnable verifier. That contract is meaningful only if the implementation enforces it mechanically and the README resists exaggeration.

## Recommended decision and adoption boundary

Build **Candidate B** only under the narrower scope above. It is the least directly preempted because the exact bundle—offline, extractive-only, fixed taxonomy, character spans, heterogeneous documents, mandatory re-check—is not verified here as one existing product. Do not market it as the first grounded document tool, the first clause extractor, or a legal-advice replacement. Make exact-span verification a technical property users can run, not a claim of legal truth.

Candidate C could be a valuable complementary feature later, particularly if it integrates Agent Note’s trace model, but it should not be the primary bet: line-level attribution for four agents already exists [4]. Candidate A should be abandoned as a standalone program unless the conformance-test suite becomes the actual product and the marketing is rewritten around independently proving compiled policies—not around compiling them.

Finally, treat this report’s coverage limit carefully. It establishes strong direct prior art through public project documentation and official material available as of 2026-11-13. It does not prove that no obscure or private repository combines Candidate B’s complete contract. A final pre-build search should target exact phrases such as “extractive only,” “exact character offsets,” “--verify,” and “medical bill,” and it should inspect closed-source CLM products, academic prototypes, and recent repositories released after this review.

## Sources

[1] https://www.ai-standards.dev/docs/handbook/native-agent-hooks
> “The AIES guard accepts --target claude|cursor|copilot|kiro|codex|gemini|devin|opencode|cli and answers in that runtime's shape, so policy lives in one file.”

[2] https://vectimus.com
> “Every policy is a plain Cedar file you can read, fork and modify. Every evaluation produces a cryptographically signed receipt you can verify offline.”

[3] https://pkg.go.dev/github.com/sezaakgun/yolonot@v1.0.0
> “One policy engine across 24 AI coding harnesses — Claude Code, Codex CLI, OpenCode, Antigravity, Cursor, GitHub Copilot CLI, Qwen, Grok, Kiro, Cline, and more.”

[4] https://wasabeef.github.io/AgentNote/agent-support
> “Agent Note records pre-edit and post-edit file states, then subtracts later human edits from the final diff.”

[5] https://edit.tosdr.org/about
> “Various Terms of Service are reviewed by ToS;DR contributors and divided into small points that can be discussed and compared.”

[6] https://platform.claude.com/docs/zh-TW/agent-sdk/hooks
> “Each matching hook’s callback function receives input about what’s happening: the tool name, its arguments, the session ID, and other event-specific details.”

[7] https://www.ai-standards.dev/docs/handbook/native-agent-hooks
> “Native hooks run outside the model, in the runtime, before the tool executes. A denial is not a suggestion; the command never runs.”

[8] https://vectimus.com
> “vectimus verify receipt.json checks the Ed25519 signature without network access.”

[9] https://pkg.go.dev/github.com/sezaakgun/yolonot@v1.0.0
> “yolonot profile codex … yolonot doctor --harness codex … yolonot audit --harness codex”

[10] https://wasabeef.github.io/AgentNote/agent-support
> “If the evidence does not line up, Agent Note falls back to file-level or skips uncertain data instead of guessing.”

[11] https://edit.tosdr.org/about
> “Ultimately, a score between 1 and 10 is assigned to each individual point.”

[12] https://platform.claude.com/docs/zh-TW/agent-sdk/hooks
> “your callback returns an output object that tells the agent what to do: allow the operation, block it, modify the input, or inject context into the conversation.”

[13] https://www.offsecblog.com/2026/10/tracekit-for-tamper-evident-auditing-of.html?m=0
> “Tracekit signs every tool and model call an AI agent makes into a hash-chained, offline-verifiable .tkb record.”

[14] https://devpost.com/software/rewind-a-flight-recorder-for-coding-agents
> “Rewind takes real Git snapshots under private refs… and records every check run as signed evidence.”

[15] https://wpnews.pro/news/agenttm-time-travel-debugging-for-ai-coding-agents
> “AgentTM… records every file change as a replayable, restorable checkpoint stored in a SQLite ledger with SHA-256 content-addressed snapshots.”

[16] https://nosaka.ai/sentient/
> “Sentient watches at the kernel level, using eBPF through Tetragon, and captures real file, process and network events as they happen.”

[17] https://www.zerostel.dev/docs/other-tools
> “Turnback… Snapshots the workspace… before every shell command and edit; undo a turn or go back to a step.”

[18] https://www.spellbook.legal
> “Spellbook uses advanced legal AI to streamline the drafting, redlining, and review of contracts directly in Word.”

[19] https://docuocr.com/obligation-extraction-software
> “Keeps each one tied to its source clause and page.”

[20] https://github.com/BlackGeorge/SourceryForge
> “Define extraction schemas with Pydantic and receive typed entities with exact source spans.”

[21] https://huggingface.co/spaces/Z-Nadjib/ClauseLM-demo
> “Every value is a verbatim span of the contract.”

[22] https://wpnews.pro/news/fineprint-phantom-summon-the-clauses-hiding-in-the-fine-print
> “Every one of those clause types is modeled on language that really appears in real consumer terms.”

[23] https://cc.bruniaux.com/guide/learning-path/06-hooks
> “A command hook is a local program launched by Claude Code. It receives one JSON object on standard input.”

[24] https://dryade.ai/de/catalog/legal_review
> “Clause extraction — pulls clauses out of a document categorised by type.”

[25] https://github.com/grandimam/wy
> “Attribution is a textual match between a hunk and a captured edit, or nothing.”
