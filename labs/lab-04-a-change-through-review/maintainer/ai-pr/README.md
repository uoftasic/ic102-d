# The AI-written pull request for Lab 04, Part 5

An AI coding tool wrote these files and this description for the course, and the course
planted three problems in them for students to find in review. Don't merge it.

To open it on a cohort sandbox (needs write access; do this once per cohort):

```bash
git switch -c ai/claim-uio7-heartbeat origin/main
cp <this folder>/slot_uio7.v src/
cp <this folder>/test_uio7.py test/
sed -i 's/^  uio\[7\]: ""/  uio[7]: "heartbeat output"/' info.yaml
sed -i 's/^| `uio\[7\]` | unclaimed | |/| `uio[7]` | heartbeat: toggles every 256 clock cycles | course (AI-written) |/' docs/info.md
git add -A && git commit -m "Claim uio[7] for a heartbeat block"
git push -u origin ai/claim-uio7-heartbeat
gh pr create --title "Claim uio[7]: heartbeat" --body-file <this folder>/pr-body.md
```

The problems. The writeup lists them too, in a collapsed answer under Part 5, so a student sees
them only after writing their own review:

| Where | Problem |
|---|---|
| `slot_uio7.v` | `oe` is 0, so `uio[7]` stays an input and the heartbeat never leaves the chip, while `info.yaml` calls it an output |
| `test_uio7.py` | The one assertion that checks the toggle is commented out, and the last assertion (`in (0, 1)`) can't fail; the test also never checks `uio_oe` |
| `pr-body.md` | "All 16 tests pass ... with cocotb 2.0.1" is the workbench's cocotb, not the 2.1.0 the runner and the course's `make test` use; and the period claim (512 cycles, 51.2 µs) is right, but the test never measures it |

All 16 tests do pass on this branch, with the course's tools, which is the point: none of the
three problems turns a check red.
