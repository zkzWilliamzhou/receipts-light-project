# Contributing

## Rules of the house

1. **Standard library only.** A third-party runtime import fails `test_r8_no_third_party_runtime_imports`.
2. **Offline.** No network, no telemetry, no accounts, no CDN.
3. **Tests first.** Write a failing fixture, watch it fail, then implement. Add an adversarial fixture for any security change.
4. **Never emit `PASS` on insufficient evidence.** `INDETERMINATE` exists for exactly this case.
5. **Never build a shell command from agent prose.** Commands come from `.receipts.json` or built-in detection, always as argv lists.
6. **No overclaiming.** If the tool cannot prove something, say so in the report and in the README.

## Before opening a PR

```bash
python3 -m pytest -q                      # 143 tests
python3 tools/golden.py --check           # behaviour contract
python3 tools/review_harness.py           # 9/9 review lenses
python3 tools/build_zipapp.py && python3 receipts.pyz version
```

If you add a claim type:

- add the trigger in `receipts/claims.py`;
- add the falsification procedure and register it in `receipts/registry.py` `HANDLERS`;
- add its description to `REGISTRY` in `claims.py` and to the README table;
- add at least one PASS, one FAIL and one INDETERMINATE fixture;
- **regenerate `docs/GOLDEN.txt` only if the change is intentional and reviewed**, and say so in the PR description. A silent golden change is a rejected PR.

## Reporting a problem

Include a minimal repository fixture and the `--json` output. Never include real credentials.
