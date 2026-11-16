# Lab 02: Read the red X

The writeup is [`docs/labs/lab-02-read-the-red-x-overview.md`](../../docs/labs/lab-02-read-the-red-x-overview.md),
published at <https://uoftasic.com/ic102-d/labs/lab-02-read-the-red-x-overview.html>. It runs on
the repository you made from Tiny Tapeout's template in Lab 01, from a workbench terminal.

## How to run

```bash
L=/foss/designs/modules/ic102-d/labs/lab-02-read-the-red-x
cd /foss/designs/projects/ttsky-ic102-d
cp $L/DIAGNOSIS-template.md DIAGNOSIS.md
python3 $L/break.py --list         # the five breakages
python3 $L/break.py 1              # commit breakage 1 (doesn't push)
python3 $L/check.py --offline      # check DIAGNOSIS.md and the history
python3 $L/check.py                # ...and ask GitHub whether every fix ran green
```

## Files

| File | What it is |
|---|---|
| `break.py` | Commits one numbered breakage to your repository, with a commit message ending `IC102-Breakage: N`. Refuses to run with uncommitted changes. |
| `DIAGNOSIS-template.md` | The file you fill in: one entry per breakage, and a last section on a value no workflow catches |
| `check.py` | Checks each entry is filled in, that its fix commit comes after its breakage, and (without `--offline`) that all six jobs passed on each fix |

## The breakages

| N | What `break.py` changes | Where it comes from |
|---|---|---|
| 1 | Empties `title` in `info.yaml` | `hart-1`'s `info.yaml`, empty from Oct 18 to Nov 15, 2026 |
| 2 | Puts the template's `docs/info.md` back | `hart-1`'s `docs/info.md`, identical to the template's |
| 3 | Renames the top module in `src/project.v` and `info.yaml` to `tt_um_<username>_adder`, not in `test/tb.v` | `protocol-emulator` `b976406` |
| 4 | Makes the adder subtract, so the template's assertion fails | `protocol-emulator` `a5f1475`, which commented that assertion out |
| 5 | Sets `clock_hz: 50MHz` | Tiny Tapeout's validator, which wants an integer |

Each was checked in the course image on a copy of the template: breakages 1, 2 and 5 with
tt-support-tools' docs check at `9d13ff3`, and 3 and 4 with `make test` in `../common/tt-tools`.
