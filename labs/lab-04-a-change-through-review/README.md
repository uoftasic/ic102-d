# Lab 04: A change through review

The writeup is [`docs/labs/lab-04-a-change-through-review-overview.md`](../../docs/labs/lab-04-a-change-through-review-overview.md),
published at <https://uoftasic.com/ic102-d/labs/lab-04-a-change-through-review-overview.html>.
Students work in pairs. Each makes a review repository, `ttsky-ic102-d-review`, in their own
account from [`sandbox/`](sandbox/), and contributes to their partner's through a pull request
from a fork. Everything runs in a workbench terminal.

## How to run

```bash
L=/foss/designs/modules/ic102-d/labs/lab-04-a-change-through-review
cp -r $L/sandbox /foss/designs/projects/ttsky-ic102-d-review    # Part 1: your own repository
python3 $L/claim.py --list                                       # the ready-made blocks
python3 $L/claim.py parity uo3 --by YOUR-USERNAME                # in a clone, on your branch
python3 $L/ai-pr.py                                              # Part 6, in your fork's clone
python3 $L/check-pr.py PARTNER-USERNAME/ttsky-ic102-d-review#N YOUR-USERNAME/ttsky-ic102-d-review#N
```

## Files

| Path | What it is |
|---|---|
| `sandbox/` | The review sandbox: a Tiny Tapeout project with sixteen slots, workflows that also run on pull requests, a pull request template, `CONTRIBUTING.md`, `RULESET.md` and `ruleset.json` |
| `claim.py` | Writes a ready-made block and its starter test into one slot of a sandbox clone |
| `check-pr.py` | Reads two pull requests from GitHub's public API, and checks that yours was merged after an approval and that a push followed your change request on the other |
| `ai-pr.py`, `ai-pr/` | The AI-written pull request for the optional Part 6, and the script that commits it onto a branch of your fork |
| `solutions/ai-pr-problems.md` | The problems planted in the AI-written pull request |
| `maintainer/make_slots.py` | Regenerates the sandbox's slot files, top module, test Makefile and slot tests |

What was checked locally, in the course image with the test job's tools:

- The sixteen unclaimed slot tests pass.
- Every `claim.py` block passes its starter test, and the combinational ones pass an exhaustive
  check of all 256 inputs, on both a `uo` and a `uio` pin.
- The Lab 04 flow, with local bare repositories standing in for the owner's repository and the
  partner's fork. It ran from the first commit of the sandbox, through a claim on `uo[3]` from
  the fork and a claim on `uo[4]` merged into the owner's `main`, to the conflict that this
  leaves in `info.yaml` and `docs/info.md`. Both tests pass after the merge is resolved.
- tt-support-tools' docs check (9d13ff3) passes on the sandbox.
- The AI-written pull request, made with `ai-pr.py`, passes all sixteen tests.

Not checked until it runs on GitHub: importing `ruleset.json`, the `gds` job hardening the
sandbox in a 1x2 tile, and the workflows' behaviour on pull requests from forks.
