#!/usr/bin/env python3
"""Lab 03: put a one-line bug into your counter, or take it out again.

    python3 bug.py apply  [YOUR_REPO_DIR]    change the line, and don't commit
    python3 bug.py undo   [YOUR_REPO_DIR]    change it back, and don't commit
    python3 bug.py commit [YOUR_REPO_DIR]    change the line and commit it (Part 3)

The bug is in the line that loads a value into the counter. It looks for that line in every
.v file under src/, so it finds your counter whatever you renamed it to. The commit it makes
ends with `IC102-Bug: load`, which is how check.py finds it.
"""
import glob
import os
import subprocess
import sys

GOOD = "count <= uio_in;"
BAD = "count <= ui_in;"
TITLE = "counter: tidy up the load path"


def die(msg):
    print(f"bug.py: {msg}", file=sys.stderr)
    sys.exit(2)


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if p.returncode != 0:
        die(f"git {' '.join(args)} failed:\n{p.stderr.strip()}")
    return p.stdout


def find(repo, text):
    hits = [f for f in glob.glob(os.path.join(repo, "src", "*.v")) if text in open(f).read()]
    return hits


def swap(repo, old, new):
    hits = find(repo, old)
    if len(hits) != 1:
        if find(repo, new):
            die(f"the line already reads `{new}`")
        die(f"couldn't find `{old}` in exactly one file under src/. Is counter.v in place (Part 1)?")
    text = open(hits[0]).read()
    open(hits[0], "w").write(text.replace(old, new, 1))
    return os.path.relpath(hits[0], repo)


def main(argv):
    if not argv or argv[0] not in ("apply", "undo", "commit") or len(argv) > 2:
        die("usage: python3 bug.py apply|undo|commit [YOUR_REPO_DIR]")
    repo = git(argv[1] if len(argv) == 2 else ".", "rev-parse", "--show-toplevel").strip()
    if argv[0] == "undo":
        path = swap(repo, BAD, GOOD)
        print(f"{path}: the load line reads `{GOOD}` again (not committed)")
        return
    if argv[0] == "commit" and git(repo, "status", "--porcelain", "--untracked-files=no").strip():
        die("you have uncommitted changes. Commit your test first (Part 2), so that the bug "
            "is a commit of its own.")
    path = swap(repo, GOOD, BAD)
    if argv[0] == "apply":
        print(f"{path}: the load line now reads `{BAD}` (not committed; see it with git diff)")
        return
    git(repo, "add", path)
    git(repo, "commit", "-q", "-m", f"{TITLE}\n\nIC102-Bug: load")
    sha = git(repo, "rev-parse", "--short", "HEAD").strip()
    print(f"Committed the bug as {sha}: {TITLE}")
    print("Nothing has been pushed yet.")


if __name__ == "__main__":
    main(sys.argv[1:])
