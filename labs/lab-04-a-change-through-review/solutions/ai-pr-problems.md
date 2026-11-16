# The AI-written pull request: its planted problems

For Lab 04, Part 6 (optional). The writeup lists these in a collapsed answer, so a student sees
them only after writing their own review. All 16 tests pass on the branch with the course's
tools, which is the point: none of the three problems turns a check red.

| Where | Problem |
|---|---|
| `slot_uio7.v` | `oe` is 0, so `uio[7]` stays an input and the heartbeat never leaves the chip, while `info.yaml` calls it an output |
| `test_uio7.py` | The one assertion that checks the toggle is commented out, and the last assertion (`in (0, 1)`) can't fail; the test also never checks `uio_oe` |
| `pr-body.md` | "All 16 tests pass ... with cocotb 2.0.1" is the workbench's cocotb, not the 2.1.0 the runner and the course's `make test` use; and the period claim (512 cycles, 51.2 µs) is right, but the test never measures it |
