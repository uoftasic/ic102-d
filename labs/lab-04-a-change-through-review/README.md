# Lab 04: A change through review

The writeup is [`docs/labs/lab-04-a-change-through-review-overview.md`](../../docs/labs/lab-04-a-change-through-review-overview.md),
published at <https://uoftasic.com/ic102-d/labs/lab-04-a-change-through-review-overview.html>.
Students work in their cohort's sandbox, a repository in the `uoftasic` organization made from
[`sandbox/`](sandbox/); everything runs in a workbench terminal.

## How to run

```bash
L=/foss/designs/modules/ic102-d/labs/lab-04-a-change-through-review
python3 $L/claim.py --list                          # the ready-made blocks
python3 $L/claim.py parity uo3 --by <username>      # in your sandbox clone, on your branch
python3 $L/check-pr.py uoftasic/ic102-d-sandbox <your PR> <the PR you reviewed>
```

## Files

| Path | What it is |
|---|---|
| `claim.py` | Writes a ready-made block and its starter test into one slot of a sandbox clone |
| `check-pr.py` | Reads two pull requests from GitHub's public API: yours merged after an approval, and your change request was followed by a push |
| `sandbox/` | The cohort sandbox: a Tiny Tapeout project with sixteen slots, workflows that run on pull requests, a pull request template, `CONTRIBUTING.md`, `RULESET.md` and `ruleset.json` |
| `maintainer/make_slots.py` | Regenerates the sandbox's slot files, top module, test Makefile and slot tests |
| `maintainer/ai-pr/` | The AI-written pull request for Part 5, with the steps to open it and the list of its planted problems |

## For maintainers: making a cohort's sandbox

The course doesn't create the repository; whoever runs a cohort does, once.

1. Create an empty public repository in `uoftasic` (for example `ic102-d-sandbox`), copy the
   contents of `sandbox/` into a clone of it, commit and push `main`.
2. Turn on Pages with the source set to GitHub Actions (Settings › Pages), so the `viewer` job on
   `main` can deploy.
3. Wait for the three workflows to finish once on `main`, so GitHub knows the job names, then
   apply the ruleset: `gh api -X POST repos/uoftasic/<repo>/rulesets --input sandbox/ruleset.json`.
4. Open the Part 5 pull request as `maintainer/ai-pr/README.md` describes.
5. Students need organization membership to push branches. If some can't be members yet, they
   can fork and open pull requests from their forks: the workflows run on `pull_request` for
   that reason, and a maintainer approves each first-time contributor's runs.

What was checked locally, in the course image with the test job's tools: the sixteen unclaimed
slot tests pass; every `claim.py` block passes its starter test and an exhaustive check of all
256 inputs (the combinational ones) on both a `uo` and a `uio` pin; two branches claiming `uo[3]`
and `uo[4]` conflict in `info.yaml` and `docs/info.md` and pass after the merge is resolved,
while `uo[3]` and `uo[5]` merge cleanly; tt-support-tools' docs check (9d13ff3) passes on the
sandbox; and the AI-written pull request passes all sixteen tests. Not checked until a sandbox
exists on GitHub: the ruleset JSON, the `gds` job hardening sixteen claimed slots in a 1x2 tile,
and the workflows' behaviour on pull requests from forks.
