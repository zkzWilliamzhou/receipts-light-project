# Architecture Deepening Record

Method: the installed `improve-codebase-architecture` skill (from `mattpocock/skills`, vendored at `skills/mattpocock/improve-codebase-architecture/`). Its vocabulary is used exactly: **module**, **interface**, **depth**, **seam**, **adapter**, **locality**, **leverage**, and the **deletion test**.

**Hard constraint from the manager: no function of the program may change.** This was proven, not asserted: a 12-scenario golden behaviour file was captured before the refactor and compared byte-for-byte afterwards.

## Before

```
verdict.py  (393 lines)
├── result/verdict dataclasses
├── Context
├── 10 falsification procedures
├── secret/check-disable constant tables
├── an 11-branch if/elif dispatch ladder
├── manifest logic, counting, exit codes
└── (imports: hashlib, re, runner, safepath, snapshot, policy)
```

The dispatch ladder was **shallow**: `verify()` had to know every claim id, every handler name, and the mapping between them. Adding a claim type meant editing the orchestrator. The interface was almost as complex as the implementation behind it.

Friction observed while reviewing: Round 4 and Round 8 fixes had to touch `verdict.py` for both policy and mechanism; the safety constants lived next to the exit-code logic. Understanding "what does `tests.pass` actually check" required reading a 393-line file.

## Deletion test

> Imagine deleting `verify`'s dispatch ladder. Complexity vanishes (it was a pass-through table) but immediately reappears across every caller that would need to select a procedure. Now imagine deleting a `registry` module that owns the procedures **and** the table: complexity reappears in N callers. **The module earns its keep.**

## After

```
model.py      (shallow)  Result, Verdict, verdict constants, make_result()
registry.py   (deep)     10 procedures + secret/check tables + HANDLERS adapter table
                         interface: falsify(claim, ctx) -> Result
verdict.py    (thin)     Context, ordering, manifest, counting, exit_code
```

`verdict.py` shrank from 393 to 86 lines. Its **interface** is now one call: `registry.falsify(claim, ctx)`. It no longer imports `hashlib`, `re`, `runner` or `safepath` — those are hidden behind the seam. The `HANDLERS` dict is the single **adapter** table: registering a new claim type is a change to `registry.py` only.

| Property | Before | After |
|---|---|---|
| `verdict.py` lines | 393 | 86 |
| Branches in `verify` | 11 | 0 |
| Modules owning falsification procedures | 1 (mixed) | 1 (dedicated) |
| Callers that know a claim id | orchestrator + ladder | registry table only |
| New claim type requires editing | `verdict.py` | `registry.py` only |

**Locality:** everything that can change for one reason ("how this claim is falsified") now lives in one module. **Leverage:** a one-line interface hides ~290 lines of safety-sensitive behaviour.

## What changed, and what did not

Changed: file boundaries, import graph, dispatch mechanism, module docstrings.

**Not changed:** every claim id, every trigger, every falsification procedure, every reason string, every evidence key, every verdict value, every exit code, every CLI flag, every report format. This matters because reason strings and evidence keys are part of the machine-readable contract.

## Proof

```
$ python3 tools/golden.py --write     # BEFORE the refactor
golden written: docs/GOLDEN.txt (7844 bytes, 12 scenarios)

$ python3 tools/golden.py --check     # AFTER the refactor
PASS: golden byte-identical (7844 bytes, 12 scenarios)

$ python3 -m pytest -q
143 passed in 3.6s
```

The golden file covers: no-run, semantic claim, uncheckable prose, file/dependency/secret/check diff claims, span PASS and forged span, required-claim manifest, real command execution, and a multi-claim report. Volatile fields (timestamps, durations, observation ids) are stripped by a documented denylist; everything else is compared byte-for-byte.

If the golden check had failed, the refactor would have been reverted. It did not fail.

## Candidates considered and not taken

- **Splitting `claims.py` into a trigger table + compiler.** Rejected as speculative: it has one cohesive reason to change and no observed friction in eight review rounds.
- **Making `runner.py` a class hierarchy of adapters.** Rejected: `command_for()` is already a small seam, and a class tree would add speculative generality without a second real adapter.
- **A plugin system for claim types.** Rejected: YAGNI and a new security surface (third-party code execution) that would violate the stdlib-only, offline promise.
