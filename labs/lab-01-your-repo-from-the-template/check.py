#!/usr/bin/env python3
"""Lab 01 check: is your repository filled in, pushed, and green on a commit you made?

    python3 check.py [YOUR_REPO_DIR]

It reads your clone (default: the folder you're in) and then asks GitHub's public API which
jobs ran on HEAD. It changes nothing, locally or on GitHub.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "common"))
import ic102  # noqa: E402

# The two sentences tt-support-tools' docs check looks for (project_checks.py at 9d13ff3).
PLACEHOLDERS = [
    ("How it works", "# How it works\n\nExplain how your project works"),
    ("How to test", "# How to test\n\nExplain how to use your project"),
]


def yaml_value(text, key):
    """The quoted value of `key:` in info.yaml's project section, without a YAML library."""
    m = re.search(rf'^\s*{key}:\s*"(.*?)"', text, re.M)
    return m.group(1) if m else None


def main():
    root = ic102.repo_root(sys.argv[1] if len(sys.argv) > 1 else ".")
    problems, notes = [], []
    print(f"Checking {root}\n")

    # 1. Files: the placeholders the docs workflow rejects.
    try:
        info = open(os.path.join(root, "info.yaml")).read()
    except FileNotFoundError:
        raise ic102.CheckError("no info.yaml here. Run this from your repository's top folder.")
    for key in ("title", "author", "description"):
        if not yaml_value(info, key):
            problems.append(f"info.yaml: `{key}` is empty")
    pins = re.findall(r'^\s*u(?:i|o|io)\[\d\]:\s*"(.*?)"', info, re.M)
    if not any(pins):
        problems.append("info.yaml: every pin in `pinout` is still blank")
    md = open(os.path.join(root, "docs", "info.md")).read()
    for section, text in PLACEHOLDERS:
        if text in md:
            problems.append(f"docs/info.md: '{section}' still holds the template's sentence")

    # 2. History: a commit of yours on top of the template's single first commit.
    if not ic102.git(root, "rev-list", "--max-parents=0", "HEAD").strip():
        raise ic102.CheckError("this clone has no commits")
    if ic102.git(root, "rev-list", "--count", "HEAD") == "1":
        problems.append("HEAD is still the template's first commit; commit and push your changes")
    email = ic102.git(root, "log", "-1", "--format=%ae", "HEAD")
    if not email.endswith("@users.noreply.github.com"):
        notes.append(f"HEAD's author email is {email}, not your GitHub no-reply address "
                     "(Part 2). Set it before your next commit.")
    if ic102.git(root, "status", "--porcelain", "--untracked-files=no"):
        notes.append("you have uncommitted changes; the check below is about HEAD as pushed")

    # 3. GitHub: every job of the three workflows, on HEAD.
    owner, name = ic102.github_slug(root)
    sha = ic102.git(root, "rev-parse", "HEAD")
    print(f"GitHub: {owner}/{name} at {sha[:7]}")
    runs = ic102.check_runs(owner, name, sha)
    if not runs:
        problems.append("GitHub has no runs for HEAD. Push it, or wait a minute if you just did")
    else:
        rows, ok = ic102.runs_table(runs)
        ic102.print_table(rows)
        if not ok:
            problems.append("not every job on HEAD has passed yet")
    print()

    for n in notes:
        print(f"note: {n}")
    for p in problems:
        print(f"todo: {p}")
    print("VERDICT: PASS" if not problems else "VERDICT: not yet")
    return not problems


if __name__ == "__main__":
    ic102.run_checker(main)
