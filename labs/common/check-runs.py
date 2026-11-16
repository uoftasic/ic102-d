#!/usr/bin/env python3
"""Print the result of every job GitHub ran on one commit of a public repository.

    python3 check-runs.py [REPO_DIR] [COMMIT]
    python3 check-runs.py --repo OWNER/NAME COMMIT

With no arguments it reads the clone you're in: the repository `origin` points at, and HEAD.
The six jobs of Tiny Tapeout's digital template (docs, test, gds, precheck, gl_test, viewer)
come first; any other jobs follow. Exit status 0 when all six finished with success.

It reads GitHub's public API without signing in, so the repository has to be public, and the
commit has to have been pushed. Nothing on GitHub is changed.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ic102  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("repo_dir", nargs="?", default=".", help="your clone (default: here)")
    ap.add_argument("commit", nargs="?", default="HEAD", help="commit to look up (default: HEAD)")
    ap.add_argument("--repo", metavar="OWNER/NAME", help="look up a repository without a clone")
    a = ap.parse_args()

    if a.repo:
        owner, name = a.repo.split("/", 1)
        # With --repo, the one positional argument is the commit.
        sha = a.commit if a.commit != "HEAD" else a.repo_dir
        if sha == ".":
            raise ic102.CheckError("give the commit to look up: --repo OWNER/NAME COMMIT")
    else:
        root = ic102.repo_root(a.repo_dir)
        owner, name = ic102.github_slug(root)
        sha = ic102.git(root, "rev-parse", a.commit)

    print(f"{owner}/{name} at {sha[:7]}")
    runs = ic102.check_runs(owner, name, sha)
    if not runs:
        print("  GitHub has no runs for this commit yet. If you pushed it a moment ago, wait a")
        print("  minute; if you haven't pushed it, push it first.")
        return False
    rows, ok = ic102.runs_table(runs)
    ic102.print_table(rows)
    print()
    print("All six jobs passed." if ok else "Not all six jobs have passed yet.")
    return ok


if __name__ == "__main__":
    ic102.run_checker(main)
