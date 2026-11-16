#!/usr/bin/env python3
"""Lab 04, Part 6: put the course's AI-written pull request on a branch of your fork.

    python3 ai-pr.py [REPO_DIR]

Run it in your clone of your fork of your partner's review repository. It makes a branch called
ai-claim-uio7-heartbeat from upstream/main (your partner's main), copies the AI-written block and
test from ai-pr/ into slot uio[7], names the pin in info.yaml and docs/info.md, and commits all
four files as one commit. It doesn't push: you push the branch and open the pull request, with
ai-pr/pr-body.md as its description.

It refuses to run with uncommitted changes, or when uio[7] is already claimed on upstream/main.
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "ai-pr")
BRANCH = "ai-claim-uio7-heartbeat"
MESSAGE = """Claim uio[7] for a heartbeat block

Written by an AI coding tool for IC102-D Lab 04, Part 6. It contains
problems on purpose: review it, and don't merge it."""


def die(msg):
    print(f"ai-pr.py: {msg}", file=sys.stderr)
    sys.exit(2)


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if p.returncode != 0:
        die(f"git {' '.join(args)} failed:\n{p.stderr.strip()}")
    return p.stdout


def main(argv):
    if len(argv) > 1 or argv[:1] in (["-h"], ["--help"]):
        print(__doc__.strip())
        return
    start = argv[0] if argv else "."
    repo = subprocess.run(["git", "-C", start, "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True).stdout.strip()
    if not repo or not os.path.exists(os.path.join(repo, "src", "slot_uio7.v")):
        die("run this in your clone of your fork of your partner's review repository")
    if git(repo, "status", "--porcelain", "--untracked-files=no").strip():
        die("you have uncommitted changes. Commit or stash them first.")
    if "upstream" not in git(repo, "remote").split():
        die("this clone has no remote called upstream (Lab 04, Part 2 adds it)")
    git(repo, "fetch", "-q", "upstream")
    slot = git(repo, "show", "upstream/main:src/slot_uio7.v")
    if not any(l.startswith("// Slot") and "unclaimed" in l for l in slot.splitlines()[:12]):
        die("uio[7] is already claimed on upstream/main")
    if git(repo, "branch", "--list", BRANCH).strip():
        die(f"a branch called {BRANCH} already exists in this clone; it has the pull request already")
    git(repo, "switch", "-q", "-c", BRANCH, "upstream/main")

    shutil.copyfile(os.path.join(SRC, "slot_uio7.v"), os.path.join(repo, "src", "slot_uio7.v"))
    shutil.copyfile(os.path.join(SRC, "test_uio7.py"), os.path.join(repo, "test", "test_uio7.py"))
    edits = [("info.yaml", r'^  uio\[7\]: ""$', '  uio[7]: "heartbeat output"'),
             ("docs/info.md", r"^\| `uio\[7\]` \| unclaimed \| \|$",
              "| `uio[7]` | heartbeat: toggles every 256 clock cycles | course (AI-written) |")]
    for path, pattern, line in edits:
        full = os.path.join(repo, path)
        text = open(full).read()
        new, n = re.subn(pattern, line, text, count=1, flags=re.M)
        if n != 1:
            die(f"couldn't find the uio[7] line in {path}")
        open(full, "w").write(new)

    git(repo, "add", "src/slot_uio7.v", "test/test_uio7.py", "info.yaml", "docs/info.md")
    git(repo, "commit", "-q", "-m", MESSAGE)
    head = git(repo, "rev-parse", "--short", "HEAD").strip()
    print(f"Committed the AI-written pull request as {head} on branch {BRANCH}.")
    print(f"Now: git push -u origin {BRANCH}, and open the pull request into your partner's main")
    print(f"with the text of {os.path.join(SRC, 'pr-body.md')} as its description.")


if __name__ == "__main__":
    main(sys.argv[1:])
