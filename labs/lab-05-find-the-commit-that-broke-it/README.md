# Lab 05: Find the commit that broke it

The writeup is [`docs/labs/lab-05-find-the-commit-that-broke-it-overview.md`](../../docs/labs/lab-05-find-the-commit-that-broke-it-overview.md),
published at <https://uoftasic.com/ic102-d/labs/lab-05-find-the-commit-that-broke-it-overview.html>.
Everything runs in a workbench terminal, after `make install` in [`../common/tt-tools`](../common/tt-tools).

## How to run

```bash
L=/foss/designs/modules/ic102-d/labs/lab-05-find-the-commit-that-broke-it
mkdir -p /foss/designs/projects && cd /foss/designs/projects
git clone $L/data/history.bundle ttsky-ic102-d-bisect
cd ttsky-ic102-d-bisect
cp $L/bisect-template.sh bisect.sh
# edit bisect.sh (Part 2), then:
git bisect start main v1.0
git bisect run ./bisect.sh
python3 $L/check.py [--offline]
```

## Files

| Path | What it is |
|---|---|
| `data/history.bundle` | The dimmer project's history: 36 commits on `main` and the tag `v1.0`, as a git bundle you can clone |
| `bisect-template.sh` | The starting point for your `bisect.sh`: runs the test job's steps and leaves the exit status to you |
| `check.py` | Runs your `bisect.sh` at three commits with known answers, checks that your branch reverts the right commit, and reads the branch's jobs from GitHub (`--offline` skips that) |
| `solutions/bisect.sh` | A finished script |
| `maintainer/build_history.py` | Builds `data/history.bundle` from Tiny Tapeout's template, with fixed authors and dates so the hashes are the same on every machine |
| `maintainer/verify.sh` | Tests every commit, runs three bisect scripts and the revert; run it after rebuilding the bundle |

## For maintainers

`maintainer/verify.sh` prints, among other things, which commit each bisect script names. On the
bundle as committed: a script that exits with `make`'s status, and one that calls a commit with no
`results.xml` bad, both name `85133d6`; `solutions/bisect.sh` names the planted commit. If you
rebuild the bundle, the hashes in the writeup, in `check.py` (`GOOD`, `NO_BUILD`, `LAST` and
`BROKE_SHA256`) and in this file change with it.
