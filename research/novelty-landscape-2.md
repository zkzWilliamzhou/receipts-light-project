# `receipts` survives only as a narrow, deterministic claim-replay format—not as a general “trust AI” protocol

## Executive summary: the defensible core is replayable local evidence bindings, not semantic proof

`receipts` is not a new idea at the level of “make the agent verify its work.” That claim is already saturated by self-verifying coding agents, evidence-carrying agents, agentic evaluation, verification runtimes, and standards for build provenance and test results. OpenSquilla and Hermes already advertise evidence-backed “self-verification” for coding agents [10][14], while ECA and agentic evaluators independently check claims or trajectories before or after action [7][12]. The `receipts` idea can survive only by narrowing its novelty to one position: a deliberately **thin, offline, local, cross-agent schema and CLI that links a typed claim to exact repository evidence, then re-executes or replays that evidence under stated constraints**.

Even there, it is not unprecedented: SLSA provenance describes how artifacts were produced; TAP and JUnit-like formats report test results; SARIF reports static-analysis findings; in-toto/SLSA define how downstream consumers verify builder claims [1][3]. The candidate is nevertheless *distinct in product scope* because it targets a post-hoc contract between an LLM and a human reviewer in an ordinary source repository, rather than supply-chain signing, CI policy, or model evaluation.

The strongest attack is that `receipts verify` is reducible to a small shell wrapper around `git`, hashes, and command re-execution. The candidate partly answers this with canonical evidence bindings, a strict verifier, and HTML report rendering—but it cannot prove semantic claims whose definitions it does not own, it cannot prevent a fully malicious agent from emitting a plausible-but-false receipt, and it inherits the nondeterminism of the project it verifies. The single most dangerous reviewer attack is therefore **claim laundering**: the agent quotes a command and a real-looking span that were never authorized by the task and cannot establish the claim. `public API unchanged` is an example of an unverifiable claim unless the receipt precisely specifies the language, toolchain, API-extracting tool, baseline revision, visibility rules, and comparison algorithm.

A realistic novelty statement is: *`receipts` is an offline, zero-dependency, cross-agent CLI and JSON contract for binding a small set of precisely typed, locally replayable assertions to immutable byte spans, command outputs, repository snapshots, and rendered evidence reports. It is not a build-attestation infrastructure, semantic theorem prover, model evaluator, or standalone security guarantee.* That claim is defensible; claims of preventing lies, proving correctness, or eliminating CI cannot be defended.

## Direct prior art already covers agent self-verification and independent evidence checking

The first and most important finding is that the candidate’s headline mechanism is no longer vacant. OpenSquilla 0.4.0 was reported as introducing “self-verification” for AI coding work: an agent first runs a test that should fail, then completes the implementation so the test passes, then runs existing regression tests and produces reviewable evidence [10]. Hermes v0.18.0 similarly runs tests, checks builds, inspects files, and reports the evidence supporting completion [14]. Neither is necessarily a drop-in equivalent to `receipts`, but both show that “the agent should verify its own claims with runnable evidence” is already a deployed product concept rather than a fresh insight.

ECA—Evidence-Carrying Multimodal Agents—goes further in one direction: it uses a typed evidence lane, constrained verifiers, and certificates that gate actions before execution [7]. Its stated result is that model-only checks accepted 99.25% of unsafe actions in its test, compared with zero for its evidence-carrying certificate configuration [7]. That is stronger than a PR artifact in safety-critical interactive settings. ECA is pre-action and action-centric, while `receipts` is post-work and source-repository-centric; the difference is real, but it does not create a new category.

Other work checks explanations or trajectories rather than first-party signed claims. An ASE 2026 paper, ExplainBench, reviews agent explanations by independently running tests against patched and unpatched code and comparing results with the agent’s account [12]. Qwen’s evaluation work likewise identifies failures in review agents that read code but do not execute it, and forbids the evaluator from secretly fixing the artifact under test [13]. These are prior art for the **independent verification** intuition, even though they do not necessarily produce a portable receipt or use `receipts verify`’s local repository contract.

**The burden of novelty is therefore on the exact contract, not on the value of independent checking.** OpenWorkProof is unverified as a shipped, open-source implementation and should not be treated as confirmed prior art. Several secondary write-ups describe generic “agent receipts,” “evidence receipts,” and “proof-carrying work,” but those names and code locations could not be verified in this research pass. Their existence still demonstrates that the naming space is crowded; `receipts` should not claim to have coined “evidence receipt” or “agent receipt.”

| Prior art | What it already does | Why it challenges `receipts` | Remaining differentiation |
|---|---|---|---|
| OpenSquilla self-verification | Runs failing tests, green tests, regressions; produces evidence [10] | Claims “AI coding self-verification” first | A formal, portable cross-agent receipt and verifier CLI may still be new |
| Hermes completion contract | Runs tests, builds, and file checks; reports completion evidence [14] | Verification is integrated into the agent runtime | Offline, agent-neutral evidence replay remains a potential difference |
| ECA | Typed certificates, constrained evidence verifiers, pre-action gating [7] | Directly connects claims, evidence, and execution gates | ECA is browser/action-focused; a repository-span verifier could cover a different workflow |
| ExplainBench-style review | Runs pre/post tests and compares explanations to observed behavior [12] | Independent checking is not novel | A durable, machine-checkable artifact is a different product layer |
| SLSA | Describes artifact production; supports downstream verification [1] | Established verifiable-build framing | SLSA binds builder/artifact provenance; `receipts` would bind a repository state to an agent’s assertion |
| TAP/JUnit/SARIF | Standardize test results and analysis results | Rich ecosystems already consume machine-readable evidence | These do not intrinsically express “I claim X” and replay its evidence |

## Existing standards already provide formats and verification machinery; `receipts` must avoid reinventing them

The candidate should be positioned as a **claim-to-evidence contract layer**, not a replacement for mature standards. SLSA v1 provenance’s stated purpose is to describe how an artifact was produced so consumers can verify that it was built according to expectations and can rebuild it if desired [1]. Its predicate captures build type, external and internal parameters, resolved dependencies, builder identity, invocation metadata, and byproducts [1]. SLSA therefore already separates trusted builder internals from untrusted inputs and already requires downstream verification of relevant values [1].

That makes “signed build provenance” an indefensible uniqueness claim. Where `receipts` could still add value is at the developer-review layer: a team may not operate a SLSA-compliant builder, yet still want to ask whether an agent’s textual claim is supported by this checkout at this commit. The proper design is to embed or reference SLSA/provenance materials where available, not to imitate them.

**Test-result formats provide useful evidence types, but none is automatically a proof of an agent claim.** TAP is a deliberately simple text protocol between tests and a harness. A TAP stream begins with a test count and contains `ok`/`not ok` lines plus diagnostics [3]. TAP alone is neither authenticated nor bound to a repository snapshot. JUnit XML with hashes and SARIF would need primary-specification confirmation, so those remain unverified in this report; the safe architectural conclusion is to use them as evidence *envelopes*, not as the trust root. A receipt should reference TAP/JUnit/SARIF files by canonical path and content hash, then bind that reference to a claim, rather than declare those formats sufficient.

| Format | Verified purpose | Correct role in `receipts` |
|---|---|---|
| SLSA provenance | Artifact-build description and downstream verification [1] | Optional provenance material, not the receipt’s identity |
| TAP | Test-to-harness output protocol [3] | Evidence payload for test-execution claims |
| JUnit XML | Test reporting format | Unverified in this pass; support only as an import adapter |
| SARIF | Static-analysis results format | Unverified in this pass; support only as an import adapter |
| in-toto layouts/attestations | Step and authorization policy for supply chains | Unverified here; do not claim `receipts` replaces them |
| SCITT | Supply-chain transparency infrastructure | Unverified here; out of scope for offline local verification |

## The strongest kill argument is valid: `receipts` is a small semantic layer over hashes, spans, and re-execution

The most brutal reading of `receipts` is that it is a JSON schema plus `git diff`, `git rev-parse`, `sha256`, and a few calls to the project’s test command. Much of the core is indeed reproducible with a modest shell script. A wrapper can capture a before/after tree digest, record command output, and rerun a test. This critique is especially strong for claims that are already executable and local: tests passed, build succeeded, files changed, and no new dependencies were added.

The candidate’s answer cannot be “but we add HTML.” A rendered report is valuable UX, but it is not novel security infrastructure. The actual defense must be the **typed evidence-binding contract**: each claim identifies its claim type, subject paths, required evidence, exact byte spans, command, captured stdout/stderr digest, exit status, repository identifier, and snapshot digest. It must also record failure modes, replay policy, and the verification result. That bundle is more useful than ad hoc agent prose, but it should be presented as an engineering discipline—not as a cryptographic guarantee.

**Forgery cannot be solved by format design alone.** A malicious agent that controls receipt emission can fabricate command strings, invent output digests, record a test command that does not cover the stated claim, or edit files and then create a receipt that matches the new state. `receipts run` improves the situation only when a trustworthy harness—not the same untrusted model—captures the environment and command result. Even then, if the harness trusts the model to choose which claims to make, selective omission remains. The README must therefore state that a receipt proves only that *the recorded evidence, under the recorded constraints, supports the recorded claim*; it does not prove the agent is honest, complete, or competent.

**Nondeterminism is the second fatal-looking problem, and it cannot be fully removed.** Flaky tests, dynamic timestamps, network access, ephemeral ports, locale, CPU count, environment variables, container state, and compiler nondeterminism can all change a rerun’s exit code or digest. A strict verifier will create false failures; a lax verifier creates false assurance. The design must therefore distinguish:

| Claim family | Reasonable verification mode | Hard boundary |
|---|---|---|
| Exact spans | Byte-exact comparison | Normalization can hide a change; report the raw bytes |
| Exit-code claims | Re-execute with the same pinned command, image, and environment | Cannot promise bit-identical external behavior |
| Build/test status | Treat as a fresh observation, not a proof of an unchanging property | Record command, exit code, digest, and timestamp separately |
| Repo state | Compare canonical git tree and working-tree snapshot | Ignore-list abuse must be explicit |
| No new dependencies | Define registry lockfile, manifest, and diff algorithm | Network availability cannot establish “no dependency exists” |
| Public-API claims | Require an API extractor and explicit semantic comparator | Cannot infer language semantics from strings |
| Secret claims | Use an allow-list scanner plus human review | Absence of a pattern is not proof that no secret exists |
| Check-disabling claims | Scan configuration and exact commands | A renamed flag or future tool can defeat the check |

The correct mitigation is not to promise determinism. It is to require a declared replay contract: pinned command, shell, working directory, commit or snapshot, environment, allowed network mode, output-truncation policy, timeouts, and a machine-readable `reproducibility_class`. Fresh test execution must be labeled `OBSERVED_AT_VERIFY`, not silently treated as the same as the original evidence.

## Semantic claims are outside the verifier’s authority unless the receipt brings its own proof system

The README must restrict top-level claim types to properties the verifier can directly inspect. “I did not disable any checks” is a negative claim over unknown configuration space; it can be approximated by scanning known CI configuration files, linter configs, and exact command strings, but it cannot be complete. “Public API unchanged” similarly cannot be established by grepping for `pub` or `export`: public visibility, exported types, implicit interfaces, dynamically discovered plugins, protobuf compatibility, database migrations, HTTP contracts, and semantic behavior all require explicit domain rules.

The defensible model is **claim-type versioning**. `test:executed`, `command:exit_status`, `repository:snapshot`, and `span:matches` can be standardized. `api:public_unchanged` should be an extension with a required toolchain, baseline, extractor, visibility policy, comparator, and version. If those fields are absent, the verifier must return `INCOMPLETE_EVIDENCE` rather than `PASS`. This is less exciting than a universal trust layer, but it is the only honest design.

**Selective omission is the most realistic failure mode.** A capable agent may emit five correct receipts for trivial claims while omitting a consequential unverified claim. The verifier cannot read the agent’s private intent, so it cannot infer omission. The only useful answer is a task contract: the human or harness supplies an expected claim manifest, and `receipts verify` reports `CLAIMS_MISSING` when the bundle omits a required claim. Without that contract, “selective omission detection” is false advertising.

## The verifier itself must be treated as an attack surface, not trusted by virtue of being “independent”

A local verifier is only as trustworthy as its parsing, path handling, command execution, report rendering, and upgrade path. The following list is a minimum security backlog. It is not exhaustive, and every mitigation needs a test, fuzzer target, or adversarial fixture before a security reviewer should accept it.

| # | Attack vector | Required mitigation |
|---|---|---|
| 1 | Path traversal in span paths | Canonicalize within an explicit repo root; reject `..`, absolute paths, and non-normal forms |
| 2 | Symlink/hardlink escapes | Resolve links once; compare canonical targets; forbid bindings outside the root |
| 3 | Shell injection through rerun commands | Use an explicit argv/exec model; never invoke a shell; no string concatenation |
| 4 | TOCTOU between verify and use | Bind to a read-only snapshot; rehash the working tree before trust decisions |
| 5 | Hash-selection confusion | Specify algorithm, encoding, canonical input, and version; disallow collision-prone algorithms |
| 6 | Unicode/homoglyph path confusion | NFC-normalize only with a documented policy; compare bytes and display forms separately |
| 7 | Environment-variable leakage | Capture only an allow-listed, redacted environment; never echo secrets into HTML |
| 8 | Unbounded command output / zip bombs | Enforce size, line, depth, and runtime limits before hashing or embedding |
| 9 | YAML/JSON parser bombs | Use a memory-bounded parser; reject duplicate keys, deep nesting, and trailing garbage |
| 10 | Malicious HTML report XSS | Render from a safe template or HTML-escaped data model; no `innerHTML` or markdown execution |
| 11 | Receipt replay | Bind to repository identity and snapshot; record replay context and monotonic verification timestamp |
| 12 | Downgrade of claim types | Version every claim predicate; reject unknown or downgraded required claims |
| 13 | Clock/timestamp manipulation | Accept external time only as observed metadata; do not base trust decisions on it |
| 14 | Verifier self-modification | Distribute verifier hashes/checksums; verify binary provenance and execute from a read-only location |
| 15 | Dependency confusion | Lock dependencies; use hash-pinned installs and an allowed registry scope |
| 16 | `.git` directory writes | Treat `.git` as out of scope by default; prevent evidence capture from modifying repository history |
| 17 | Resource exhaustion / DoS | Limit parallelism, processes, wall-clock time, file descriptors, and output bytes |
| 18 | Selective claim omission | Require an externally defined claim manifest and emit a missing-claims result |
| 19 | Re-execution escape | Default to read-only mode; allow only explicitly declared, sandboxed commands |
| 20 | Forged “independent” capture | Attribute capture provenance and tool versions; do not confuse capture by a wrapper with trusted capture |

**The single most dangerous reviewer attack is claim laundering, not cryptographic forgery.** An agent supplies `command: pytest -k trivial`, a real output digest, and a span inside an irrelevant file, then claims `all_tests_pass`. The command executed, the digest matches, and the span is authentic—but none of those facts entails the claim. The verifier must therefore prove coverage: the recorded test result must be produced by the exact declared command, cover the relevant changed behavior, and be interpreted under the claim type’s definition. A claim must never be treated as proven merely because its evidence is internally consistent.

## The README must promise a bounded, replayable artifact—not universal trust or AI safety

The following prohibitions distinguish a credible repository from marketing overreach:

1. Do not claim the system prevents agents from lying.
2. Do not claim one receipt proves overall code correctness.
3. Do not claim it replaces CI, code review, or application security testing.
4. Do not claim it replaces SLSA, in-toto, Sigstore, or SBOM attestations.
5. Do not claim a PASS means the change is safe, compliant, or production-ready.
6. Do not claim it detects all secrets, vulnerabilities, or malicious code.
7. Do not claim to prove semantic properties without an explicit proof tool.
8. Do not claim outputs are deterministic when rerun in different environments.
9. Do not claim selective omission can be inferred from an agent’s chat output.
10. Do not claim HTML evidence is tamper-proof or cryptographically signed.

The most credible feature set is modest: exact-span checks, repository snapshot checks, command exit/status checks, required-claim coverage, machine-readable verdicts, and a human-readable report. The CLI should require a `claims manifest` when the caller wants assurance that nothing was omitted. `receipts run` should capture a minimal environment and produce a draft receipt; it must never imply that capture by the agent’s own tooling is a trust anchor.

**The correct security boundary is evidence binding plus explicit claim semantics.** A receipt should support three outcomes: `PASS` only when all recorded evidence satisfies the recorded claim under its declared rules; `FAIL` when evidence contradicts a claim; and `INCOMPLETE` or `INDETERMINATE` when a claim lacks a comparator, the environment differs, or re-execution is unsafe. This taxonomy is less satisfying than binary trust, but it is the one a security reviewer can audit.

## >105,000 GitHub stars is not impossible, but it is far less plausible than the “killer tool” framing suggests

`receipts` could plausibly reach a meaningful developer audience if it becomes a low-friction standard for AI coding agent PRs. Its potential advantage is small, observable, and understandable: a one-file evidence contract, an offline CLI, and a compact HTML report. By contrast, supply-chain attestation standards are heavyweight and require infrastructure investment. This is the most plausible route to adoption.

However, 105,000 stars is extraordinary. As of this report’s date, no direct comparable repository or star count has been verified, so that target is pure speculation. The threshold is not a reasonable baseline from which to infer product-market fit.

**The three biggest blockers are indifference, maintenance burden, and a missing shared convention.** First, developers who already run CI will ask why they need another local artifact. A receipt can fail in CI anyway, and CI is already the shared source of truth. Second, every repository has its own test command, shell, package manager, API contract, ignore patterns, and flaky-test culture; a “zero-dependency” verifier will still need an extensible plugin model. Third, no individual agent vendor has an incentive to emit a neutral format unless users demand it. Without cross-agent support, `receipts` is merely one more agent-specific wrapper.

The three strongest viral hooks are credible but not sufficient by themselves:

1. **`AI AGENT EVIDENCE` as a visible PR status.** Reviewers would see a compact artifact showing which claims were checked and which could not be verified. This is more compelling than a chat transcript.
2. **A five-line agent snippet that produces something immediately useful.** The snippet must record exact commands and byte spans, not ask the model to write a JSON receipt unaided.
3. **A concrete security/reproducibility demo.** A repository should ship intentional attack fixtures: a lying agent, a stale receipt, a fabricated span, a test-selection bypass, and a command-injection replay attempt. These demonstrate value faster than generic claims.

Adoption is most likely if `receipts` positions itself as “machine-checkable evidence attachments for agent-generated PRs,” remains opt-in per claim, integrates with existing test/JUnit/SARIF outputs, and supports a shared `claims manifest`. It is far less likely to succeed as “the trust layer for AI coding agents.”

## Final verdict: pursue the narrow artifact, but abandon the universal-trust story

`receipts` should not be killed as an engineering project, but its novelty claim must be surgically narrowed. The project is neither first to verify agents nor first to use evidence and attestations. Its opportunity lies in combining ordinary source-repository artifacts—byte spans, tree digests, command exit codes, and result files—into a portable, replayable, claim-specific contract with a local verifier and HTML report.

The recommended name and positioning is deliberately unromantic: **“A local evidence-binding CLI for typed agent assertions about a source repository.”** The project should expose a small schema, an opt-in claim manifest, verifier semantics, and fuzz-tested path/command/output handling. It should not claim to stop lying, prove semantic correctness, replace CI or supply-chain attestation, or make AI safe.

The two decisions that determine survival are:

- whether `receipts` can demonstrate coverage and replay correctness for a genuinely useful claim set without becoming a heavy framework; and
- whether independent agent runtimes adopt the same manifest and evidence format before the project is dismissed as yet another wrapper.

If those conditions are met, the project is publishable and potentially useful. If not, it is vulnerable to the correct and brutal criticism that it is “run the tests yourself, plus a JSON schema.”

## Sources

[1] https://slsa.dev/provenance/v1
> “Purpose: Describe how an artifact or set of artifacts was produced so that: Consumers of the provenance can verify that the artifact was built according to expectations.”

[2] https://slsa.dev/spec/v1.1/verifying_artifacts
> Page retrieval returned no usable specification content in this research pass; the URL remains unverified as a current or accessible source.

[3] https://www.sarif.org/specifications/
> Page retrieval returned no usable content in this research pass; SARIF’s role therefore remains unverified from a primary specification here.

[4] https://testanything.org/tap-specification.html
> “TAP, the Test Anything Protocol, is Perl’s simple text-based interface between testing modules such as Test::More and a test harness.”

[5] https://news.qq.com/rain/a/20260101A001GN00
> “SmartSnap provides a simple RL training method, [in which] the agent learns to actively decompose subgoals and preserve evidence.”

[6] https://www.163.com/dy/article/L3RFGARL05561FZQ_pdya11y.html
> “The core object is ActionReceipt, which binds the authorization decision, quota changes, and related evidence references together.”

[7] https://new.qq.com/rain/a/20260914A09D1Z00
> “ECA introduces an independent evidence channel, which requires this judgment to be externally verified before execution.”

[8] https://new.qq.com/rain/a/20260914A09D1Z00
> “Among the Judge variants, the Naive MLLM configuration had a UAR of 99.25, while ECA (E2E) achieved 0.00.”

[9] https://news.qq.com/rain/a/20260527A096AX00
> “AI code can pass all visible tests, yet still be full of holes in actual use.”

[10] https://new.qq.com/rain/a/20260702A03RN400
> “OpenSquilla’s coding workflow introduces a ‘red → green → regression’ self-verification mechanism.”

[11] https://www.163.com/dy/article/L0OFNGCF053469RG.html
> “Before handing back the result, [the agent] first runs tests to produce reviewable evidence proving ‘the change is correct.’”

[12] https://news.qq.com/rain/a/20260630A04WVW00
> “The evaluation agent must not secretly fix the code and then test it; discovered bugs should only be recorded.”

[13] https://news.qq.com/rain/a/20260630A04WVW00
> “Initially, the evaluation agent mostly read source code without actually executing it, resulting in plausible-looking but actually broken code being incorrectly judged as good.”

[14] https://thepaper.cn/newsDetail_forward_33538041
> “Hermes v0.18.0 added an evidence-based verification mechanism: it can run tests, check build results, and inspect file state as a basis for completion.”
