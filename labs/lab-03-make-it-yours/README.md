# Lab 03: Make it yours

The writeup is [`docs/labs/lab-03-make-it-yours-overview.md`](../../docs/labs/lab-03-make-it-yours-overview.md),
published at <https://uoftasic.com/ic102-d/labs/lab-03-make-it-yours-overview.html>. It runs on
your repository from Lab 01, in a workbench terminal, with the test job's tools from
[`../common/tt-tools`](../common/tt-tools).

## How to run

```bash
L=/foss/designs/modules/ic102-d/labs/lab-03-make-it-yours
TT=/foss/designs/modules/ic102-d/labs/common/tt-tools
cd /foss/designs/projects/ttsky-ic102-d
cp $L/counter.v src/counter.v && git rm -q src/project.v
cp $L/test_counter.py test/test.py
# rename the module and update info.yaml, test/Makefile and test/tb.v (Part 1), then:
python3 $L/check.py --offline
make -C "$TT" test PROJECT="$PWD"
python3 $L/bug.py apply | undo | commit
```

## Files

| File | What it is |
|---|---|
| `counter.v` | An 8-bit counter with enable, load and count-down, in plain Verilog that Icarus 12.0 accepts. The comment at the top is its specification. |
| `test_counter.py` | The starter test: reset and counting up, using only the pins and sampling on the falling edge, so it runs unchanged at gate level |
| `bug.py` | Puts a one-line bug in the load path (`apply`), takes it out (`undo`), or commits it with the marker `IC102-Bug: load` (`commit`) |
| `check.py` | Checks that the five names agree, finds the bug commit and its fix, and (without `--offline`) asks GitHub for the test job on the bug and every job on the fix |
| `solutions/test_load.py` | A test that catches the bug |

What was checked locally, in the course image:

- The counter and its starter test pass under Icarus 12.0, 13.0 and 14.0, with the same
  simulated times.
- The starter tests pass with the bug in, and `solutions/test_load.py` fails on it.
- Under Icarus 13.0, the three tests pass on a gate-level netlist that Yosys made from
  `counter.v` with the sky130 cells (not LibreLane's netlist). A version with an `initial`
  statement in place of the reset passes at RTL and fails two tests at gate level.

Hardening on the runner hasn't been tried yet.
