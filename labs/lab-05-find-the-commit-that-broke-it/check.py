#!/usr/bin/env python3
"""Lab 05 check: does your bisect script answer correctly, and does your revert pass?

    python3 check.py [YOUR_DIMMER_CLONE] [--offline]

Run it in the workbench, because it runs your bisect.sh, which needs the test job's tools.

  1. It runs your bisect.sh at three commits of the prepared history, each in a temporary
     worktree so that your own checkout isn't touched: v1.0, where the test passes (your script
     should exit 0); the first commit of the preset work, which doesn't compile (125); and the
     history's last commit, where a test fails (anything from 1 to 127 except 125).
  2. It looks on your current branch for the commit that `git revert` made, and checks that it
     reverts the commit that broke the test. (It knows that commit only by a hash of its hash,
     so reading this file won't tell you which one it is.)
  3. Unless you pass --offline, it asks GitHub's public API whether all six jobs passed on your
     branch's latest commit, which is the commit your pull request shows.

It changes nothing in your clone or on GitHub.
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "common"))
import ic102  # noqa: E402

GOOD = "4e04d775e153a5c2526f9687f9ef83a185f62b7d"       # v1.0
NO_BUILD = "cbba6a3831a677c6552cf449fd3ae56728bf2565"   # WIP: preset brightness levels
LAST = "00c3d87894d0c8bce7a127e029cd9f6cbbb36da2"       # the history's last commit
BROKE_SHA256 = "52dc7fd9ccdabecaa2064687149f06c34db0a18cfca534c815b4afbeaabe226a"


def run_script(root, script, commit):
    tmp = tempfile.mkdtemp(prefix="ic102-lab05-")
    wt = os.path.join(tmp, "wt")
    try:
        ic102.git(root, "worktree", "add", "-q", "--detach", wt, commit)
        shutil.copy(script, os.path.join(wt, "bisect.sh"))
        p = subprocess.run(["bash", "bisect.sh"], cwd=wt, capture_output=True, text=True,
                           timeout=600)
        return p.returncode
    finally:
        ic102.git(root, "worktree", "remove", "--force", wt, check=False)
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    offline = "--offline" in sys.argv
    root = ic102.repo_root(args[0] if args else ".")
    problems = []
    if ic102.git(root, "cat-file", "-t", LAST, check=False) != "commit":
        raise ic102.CheckError(f"{root} isn't a clone of Lab 05's history (Part 1)")

    script = os.path.join(root, "bisect.sh")
    print(f"Checking {root}\n\nYour bisect.sh, run at three commits")
    if not os.path.exists(script):
        problems.append("no bisect.sh at the top of your clone (Part 2)")
    else:
        cases = [(GOOD, "v1.0, test passes", lambda s: s == 0, "0"),
                 (NO_BUILD, "preset WIP, doesn't compile", lambda s: s == 125, "125"),
                 (LAST, "last commit, test fails", lambda s: 1 <= s <= 127 and s != 125,
                  "1 to 127, not 125")]
        for commit, what, ok, want in cases:
            status = run_script(root, script, commit)
            mark = "ok" if ok(status) else f"expected {want}"
            print(f"  {commit[:7]}  {what:<28} exit {status:<4} {mark}")
            if not ok(status):
                problems.append(f"bisect.sh exits {status} at {commit[:7]} ({what}); "
                                f"git bisect needs {want} there")

    print("\nYour revert")
    reverted = re.findall(r"This reverts commit ([0-9a-f]{40})",
                          ic102.git(root, "log", "--format=%B", f"{LAST}..HEAD"))
    right = [c for c in reverted if hashlib.sha256(c.encode()).hexdigest() == BROKE_SHA256]
    if right:
        print(f"  reverts {right[0][:7]}, the commit that broke the test")
    elif reverted:
        print(f"  reverts {', '.join(c[:7] for c in reverted)}, which isn't the commit that "
              "broke the test")
        problems.append("revert the first bad commit (Part 3)")
    else:
        print("  no commit made by git revert on this branch yet")
        problems.append("revert the first bad commit on a branch (Part 4)")

    if right and not offline:
        owner, name = ic102.github_slug(root)
        sha = ic102.git(root, "rev-parse", "HEAD")
        print(f"\nGitHub: {owner}/{name} at {sha[:7]}")
        runs = ic102.check_runs(owner, name, sha)
        if not runs:
            problems.append("GitHub has no runs for your branch's latest commit; push it")
        else:
            rows, ok = ic102.runs_table(runs)
            ic102.print_table(rows)
            if not ok:
                problems.append("not every job has passed on your branch's latest commit")

    print()
    for p in problems:
        print(f"todo: {p}")
    print("VERDICT: PASS" if not problems else "VERDICT: not yet")
    return not problems


if __name__ == "__main__":
    ic102.run_checker(main)
