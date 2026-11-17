# Vendored Agent Skills

These are upstream `SKILL.md` instruction documents fetched from public GitHub repositories during the build. They are **development workflow guidance**, not runtime dependencies of `receipts`. The program imports only the Python standard library.

| Directory | Upstream | Used for |
|---|---|---|
| `superpowers/` | `obra/superpowers` | brainstorming, TDD (red-green-refactor), verification-before-completion, systematic debugging, code review, writing/executing plans |
| `mattpocock/` | `mattpocock/skills` | `improve-codebase-architecture` (the S9 architecture pass), codebase-design vocabulary, grilling, tdd, code-review, diagnosing-bugs, writing-for-agents |
| `anthropics/` | `anthropics/skills` | skill-creator, claude-api, mcp-builder, webapp-testing |
| `vercel-labs/` | `vercel-labs/agent-skills`, `vercel-labs/skills` | writing-guidelines, react-best-practices, find-skills |
| `stop-slop/` | `hardikpandya/stop-slop` | prose quality rules (used when writing the README/docs) |

`SKILLS_MANIFEST.json` lists every vendored group, its source and file count. `../NOTICE` carries license attribution. `../research/upstream-install-manifest.json` records the fetch sizes and status of each upstream repository.

Notes:

- `improve-codebase-architecture` was requested via `smeltery/skills`, which was unavailable at fetch time. The same skill is carried by `mattpocock/skills` and was vendored from there. The architecture pass documented in `../docs/ARCHITECTURE.md` uses its vocabulary (module, interface, depth, seam, adapter, locality, leverage, deletion test).
- `superpowers/brainstorming` requires human approval before implementation; the equivalent self-grilling was recorded in `../docs/BRAINSTORM.md` and the decision was locked there before any code was written.
- Review upstream SKILL.md files before invoking them in your own agent. Some upstream skills instruct an agent to create issues, finish merges, or start local servers.
