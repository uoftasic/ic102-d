# Lab 01: Your repository from the template

The writeup is [`docs/labs/lab-01-your-repo-from-the-template-overview.md`](../../docs/labs/lab-01-your-repo-from-the-template-overview.md),
published at <https://uoftasic.com/ic102-d/labs/lab-01-your-repo-from-the-template-overview.html>.
The lab works on a repository you make on GitHub from
[TinyTapeout/ttsky-verilog-template](https://github.com/TinyTapeout/ttsky-verilog-template); this
folder holds only the check. Part 1 also installs the test job's tools in
[`../common/tt-tools`](../common/tt-tools).

## How to run

```bash
cd /foss/designs/modules/<your-repo>
python3 /foss/designs/modules/ic102-d/labs/lab-01-your-repo-from-the-template/check.py
```

## Files

| File | What it is |
|---|---|
| `check.py` | Checks that `info.yaml` and `docs/info.md` are filled in, that HEAD is a commit of yours and its author address is a GitHub no-reply one, and asks GitHub's public API whether all six jobs passed on HEAD |
| `../common/check-runs.py` | Prints the jobs on any commit of a public repository: `python3 check-runs.py --repo OWNER/NAME COMMIT` |
| `../common/ic102.py` | The git and GitHub helpers every lab's check uses |
