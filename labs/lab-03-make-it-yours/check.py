#!/usr/bin/env python3
"""Lab 03 check: is the counter wired in, and did the runner see your test catch the bug?

    python3 check.py [YOUR_REPO_DIR] [--offline]

Locally, it checks that the five places that name the design agree: the module in src/, the
top_module and source_files in info.yaml, PROJECT_SOURCES in test/Makefile, and the module
test/tb.v instantiates. Then it finds the bug commit (bug.py marks it `IC102-Bug: load`) and the
first later commit that takes the bug out, and asks GitHub's public API for the jobs on both:
the test job should have failed on the bug and every job should have passed on the fix.
--offline skips the GitHub part. It changes nothing, locally or on GitHub.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "common"))
import ic102  # noqa: E402


def read(root, path):
    try:
        return open(os.path.join(root, path)).read()
    except FileNotFoundError:
        return ""


def names(root, problems):
    info = read(root, "info.yaml")
    top = re.search(r'^\s*top_module:\s*"([^"]+)"', info, re.M)
    top = top.group(1) if top else None
    block = re.search(r"^\s*source_files:\s*\n((?:\s*-\s*.*\n)+)", info, re.M)
    sources = re.findall(r'-\s*"?([^"\s#]+)"?', block.group(1)) if block else []
    mk = re.search(r"^PROJECT_SOURCES\s*=\s*(.*)$", read(root, "test/Makefile"), re.M)
    mk_sources = mk.group(1).split() if mk else []
    inst = re.search(r"^\s*(\w+)\s+user_project\b", read(root, "test/tb.v"), re.M)
    inst = inst.group(1) if inst else None
    modules = {}
    for s in sources:
        for m in re.findall(r"^\s*module\s+(\w+)", read(root, os.path.join("src", s)), re.M):
            modules[m] = s
        if not os.path.exists(os.path.join(root, "src", s)):
            problems.append(f"info.yaml lists src/{s}, which doesn't exist")
    clock = re.search(r"^\s*clock_hz:\s*([^\s#]+)", info, re.M)

    print(f"  top_module in info.yaml    {top}")
    print(f"  source_files in info.yaml  {' '.join(sources) or '-'}")
    print(f"  PROJECT_SOURCES            {' '.join(mk_sources) or '-'}")
    print(f"  module tb.v instantiates   {inst}")
    print(f"  clock_hz                   {clock.group(1) if clock else '-'}")

    if not top or not top.startswith("tt_um_"):
        problems.append("top_module must start with tt_um_")
    elif top == "tt_um_ic102_counter":
        problems.append("rename the module to tt_um_<your username>_counter (Part 1)")
    if top and top not in modules:
        problems.append(f"no file in source_files defines module {top}")
    if inst != top:
        problems.append(f"test/tb.v instantiates {inst}, but top_module is {top}")
    if sorted(sources) != sorted(mk_sources):
        problems.append("source_files in info.yaml and PROJECT_SOURCES in test/Makefile differ")
    if not clock or not clock.group(1).isdigit() or int(clock.group(1)) == 0:
        problems.append("clock_hz should be the counter's clock in hertz, a whole number above 0")
    if "count <= ui_in;" in "".join(read(root, os.path.join("src", s)) for s in sources):
        problems.append("the planted bug is still in your working copy; take it out (Part 3)")


def bug_and_fix(root):
    marks = ic102.git(root, "log", "--format=%H", "--grep=^IC102-Bug: load$").split()
    if not marks:
        return None, None
    bug = marks[0]
    later = ic102.git(root, "rev-list", "--reverse", "--ancestry-path", f"{bug}..HEAD").split()
    for c in later:
        files = ic102.git(root, "diff", "--name-only", bug, c).split()
        text = "".join(ic102.git(root, "show", f"{c}:{f}", check=False)
                       for f in files if f.startswith("src/") and f.endswith(".v"))
        if "count <= uio_in;" in text:
            return bug, c
    return bug, None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    offline = "--offline" in sys.argv
    root = ic102.repo_root(args[0] if args else ".")
    problems = []
    print(f"Checking {root}\n\nNames")
    names(root, problems)

    bug, fix = bug_and_fix(root)
    print("\nHistory")
    print(f"  bug commit  {bug[:7] if bug else 'not committed yet (Part 3)'}")
    print(f"  fix commit  {fix[:7] if fix else 'none yet (Part 3)'}")
    if not bug or not fix:
        problems.append("commit the bug with bug.py commit, push, then take it out and push again")

    if bug and fix and not offline:
        owner, name = ic102.github_slug(root)
        print(f"\nGitHub: {owner}/{name}")
        b = ic102.latest_by_name(ic102.check_runs(owner, name, bug)).get("test")
        b_state = (b or {}).get("conclusion") or (b or {}).get("status") or "no run"
        print(f"  test on the bug commit {bug[:7]}: {b_state}")
        if b_state != "failure":
            problems.append("the runner's test job should fail on the bug commit; does your "
                            "test catch the bug? (Part 2)")
        rows, ok = ic102.runs_table(ic102.check_runs(owner, name, fix))
        print(f"  every job on the fix commit {fix[:7]}:")
        ic102.print_table(rows, indent="    ")
        if not ok:
            problems.append("not every job has passed on the fix commit yet")

    print()
    for p in problems:
        print(f"todo: {p}")
    print("VERDICT: PASS" if not problems else "VERDICT: not yet")
    return not problems


if __name__ == "__main__":
    ic102.run_checker(main)
