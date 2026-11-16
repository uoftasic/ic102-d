#!/usr/bin/env python3
"""Lab 02 check: five diagnoses, each followed by a fix that GitHub ran green.

    python3 check.py [YOUR_REPO_DIR] [--offline]

It reads DIAGNOSIS.md at the top of your repository and, for each breakage:

  - checks that every field of the entry is filled in;
  - finds the breakage commit (break.py marks it with `IC102-Breakage: N`) and checks that the
    fix commit you named comes after it in your history;
  - asks GitHub's public API whether all six jobs passed on the fix commit (skipped with
    --offline, for example before you've pushed).

It changes nothing, locally or on GitHub.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "common"))
import ic102  # noqa: E402

FIELDS = ["Prediction", "Job that failed first", "Step", "First error line", "Fix", "Fix commit"]


def sections(text):
    """{heading: body} for each `## heading` in the file."""
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m:
            cur = m.group(1)
            out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def field(body, name):
    m = re.search(rf"^\s*-\s*{re.escape(name)}:[ \t]*(.*)$", body, re.M)
    return m.group(1).strip().strip("`").strip() if m else ""


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    offline = "--offline" in sys.argv
    root = ic102.repo_root(args[0] if args else ".")
    path = os.path.join(root, "DIAGNOSIS.md")
    if not os.path.exists(path):
        raise ic102.CheckError(f"no DIAGNOSIS.md in {root}. Copy DIAGNOSIS-template.md there "
                               "(Part 1).")
    secs = sections(open(path).read())
    slug = None if offline else ic102.github_slug(root)
    passed = 0

    for n in range(1, 6):
        print(f"Breakage {n}")
        body = secs.get(f"Breakage {n}")
        if body is None:
            print(f"  no '## Breakage {n}' section in DIAGNOSIS.md\n")
            continue
        empty = [f for f in FIELDS if not field(body, f)]
        if empty:
            print(f"  still to fill in: {', '.join(empty)}\n")
            continue
        marks = ic102.git(root, "log", "--format=%H", f"--grep=^IC102-Breakage: {n}$").split()
        if not marks:
            print(f"  break.py hasn't committed breakage {n} in this clone\n")
            continue
        broke = marks[0]          # the most recent, if it was applied more than once
        fixed = ic102.git(root, "rev-parse", "--verify", "--quiet",
                          field(body, "Fix commit") + "^{commit}", check=False)
        if not fixed:
            print(f"  Fix commit '{field(body, 'Fix commit')}' isn't a commit in this clone\n")
            continue
        if fixed == broke or not _is_ancestor(root, broke, fixed):
            print(f"  fix {fixed[:7]} doesn't come after the breakage commit {broke[:7]}\n")
            continue
        print(f"  entry filled in; fix {fixed[:7]} comes after breakage {broke[:7]}")
        if offline:
            print("  GitHub: not checked (--offline)\n")
            passed += 1
            continue
        runs = ic102.check_runs(*slug, fixed)
        rows, ok = ic102.runs_table(runs)
        if ok:
            print("  GitHub: all six jobs passed on the fix\n")
            passed += 1
        else:
            print("  GitHub, on the fix commit:")
            ic102.print_table(rows, indent="    ")
            print()

    extra = secs.get("A value no workflow catches", "")
    has_extra = bool(field(extra, "Value")) and bool(field(extra, "Why every workflow passes with it"))
    print("A value no workflow catches: " + ("filled in" if has_extra else "still to fill in"))
    ok = passed == 5 and has_extra
    print(f"\n{passed} of 5 breakages diagnosed and fixed" + (" (GitHub not checked)" if offline else ""))
    print("VERDICT: PASS" if ok else "VERDICT: not yet")
    return ok


def _is_ancestor(root, a, b):
    import subprocess
    return subprocess.run(["git", "-C", root, "merge-base", "--is-ancestor", a, b]).returncode == 0


if __name__ == "__main__":
    ic102.run_checker(main)
