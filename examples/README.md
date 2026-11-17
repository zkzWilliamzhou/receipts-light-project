# Attack fixtures / ten-second demo

These files are intentionally hostile. Run them from the repository root:

```bash
# 1. A lying agent: the configured test command reports failures.
python3 -m receipts check --file examples/lying-agent.md \
  --config examples/.receipts.json --html /tmp/receipts-demo.html
# expected: exit 1, tests.pass FAIL

# 2. Filtered run (claim laundering attempt): refused, not graded PASS.
python3 -m receipts check --text "All tests pass." \
  --config examples/.receipts.laundered.json
# expected: INDETERMINATE with "selection/coverage refused"

# 3. Selective omission needs an external manifest to be visible.
python3 -m receipts check --file examples/lying-agent.md \
  --config examples/.receipts.json --require examples/required-claims.json
# expected: manifest.required_claims FAIL listing missing claim ids

# 4. A forged span.
python3 -m receipts check --file examples/forged-span.json
# expected: span.matches FAIL
```

`lying-agent.md` is a PR body an agent might plausibly write. `.receipts.json` points at a command that prints a real failing summary. No network access, no install, no agent cooperation.
