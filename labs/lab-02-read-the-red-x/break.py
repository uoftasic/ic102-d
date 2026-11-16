#!/usr/bin/env python3
"""Lab 02: commit one numbered breakage to your Tiny Tapeout repository.

    python3 break.py N [YOUR_REPO_DIR]      N is 1 to 5
    python3 break.py --list

Each breakage is a mistake one of the team's repositories made, or one Tiny Tapeout's checks
exist to catch. The script edits your files, commits the change with a message like the ones
real commits had, and stops. It doesn't push: you do that, and then read what GitHub says.

It refuses to run on a clone with uncommitted changes, so a breakage is always one whole commit
that you can find with `git show`. The commit message ends with a line `IC102-Breakage: N`,
which is how check.py finds it later.
"""
import os
import re
import subprocess
import sys

# The digital template's docs/info.md (ttsky-verilog-template a42e666), byte for byte.
TEMPLATE_INFO_MD = """<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

Explain how your project works

## How to test

Explain how to use your project

## External hardware

List external hardware used in your project (e.g. PMOD, LED display, etc), if any
"""

TITLES = {
    1: "info.yaml: tidy up the project section",
    2: "docs: start info.md again from the template's layout",
    3: "Rename the top module so that it's unique on the shuttle",
    4: "Output the difference ui_in - uio_in instead of the sum",
    5: "info.yaml: run the design at 50 MHz",
}


def die(msg):
    print(f"break.py: {msg}", file=sys.stderr)
    sys.exit(2)


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if p.returncode != 0:
        die(f"git {' '.join(args)} failed:\n{p.stderr.strip()}")
    return p.stdout


def read(repo, path):
    with open(os.path.join(repo, path), newline="") as fh:
        return fh.read()


def write(repo, path, text):
    with open(os.path.join(repo, path), "w", newline="") as fh:
        fh.write(text)


def sub_once(text, pattern, repl, what):
    new, n = re.subn(pattern, repl, text, count=1, flags=re.M)
    if n != 1:
        die(f"couldn't find {what}. Has this file changed shape since Lab 01?")
    return new


def github_user(repo):
    url = git(repo, "remote", "get-url", "origin").strip()
    m = re.search(r"github\.com[/:]([^/]+)/", url)
    return m.group(1) if m else None


def top_module(repo):
    m = re.search(r'^\s*top_module:\s*"([^"]+)"', read(repo, "info.yaml"), re.M)
    if not m:
        die("couldn't find top_module in info.yaml")
    return m.group(1)


def break_1(repo):
    # An empty title (hart-1's info.yaml, Oct 18 to Nov 15, 2026).
    y = read(repo, "info.yaml")
    y = sub_once(y, r'^(\s*title:\s*)"[^"]*"', r'\1""', "the title line in info.yaml")
    write(repo, "info.yaml", y)
    return ["info.yaml"]


def break_2(repo):
    # The template's placeholder sentences back in docs/info.md (hart-1's info.md is the
    # template's, unchanged).
    if read(repo, "docs/info.md") == TEMPLATE_INFO_MD:
        die("docs/info.md is already the template's. Fill it in (Lab 01, Part 4) first.")
    write(repo, "docs/info.md", TEMPLATE_INFO_MD)
    return ["docs/info.md"]


def break_3(repo):
    # The module renamed in src/ and info.yaml, but not in test/tb.v (protocol-emulator
    # b976406, Oct 24, 2026).
    old = top_module(repo)
    user = (github_user(repo) or "ic102").lower()
    new = "tt_um_" + re.sub(r"[^a-z0-9_]", "_", user) + "_adder"
    if old == new:
        die(f"the top module is already {new}")
    y = sub_once(read(repo, "info.yaml"), rf'^(\s*top_module:\s*)"{re.escape(old)}"',
                 rf'\1"{new}"', "top_module in info.yaml")
    v = sub_once(read(repo, "src/project.v"), rf"^module {re.escape(old)}\b",
                 f"module {new}", f"`module {old}` in src/project.v")
    write(repo, "info.yaml", y)
    write(repo, "src/project.v", v)
    return ["info.yaml", "src/project.v"]


def break_4(repo):
    # A deliberate design change that the template's single assertion notices. The fix is a
    # new expected value, not a deleted assertion (protocol-emulator a5f1475 deleted it).
    v = sub_once(read(repo, "src/project.v"),
                 r"^(\s*)assign uo_out\s*=\s*ui_in \+ uio_in;.*$",
                 r"\1assign uo_out  = ui_in - uio_in;  // uo_out is the difference ui_in - uio_in",
                 "`assign uo_out  = ui_in + uio_in;` in src/project.v")
    write(repo, "src/project.v", v)
    return ["src/project.v"]


def break_5(repo):
    # A clock given with units. The validator wants an integer number of hertz.
    y = sub_once(read(repo, "info.yaml"), r"^(\s*clock_hz:\s*)[^\s#]+",
                 r"\g<1>50MHz", "clock_hz in info.yaml")
    write(repo, "info.yaml", y)
    return ["info.yaml"]


BREAKS = {1: break_1, 2: break_2, 3: break_3, 4: break_4, 5: break_5}


def main(argv):
    if len(argv) >= 1 and argv[0] in ("--list", "-l"):
        for n, t in TITLES.items():
            print(f"{n}  {t}")
        return
    if len(argv) not in (1, 2) or argv[0] not in {str(n) for n in BREAKS}:
        die("usage: python3 break.py N [YOUR_REPO_DIR], where N is 1 to 5")
    n = int(argv[0])
    repo = git(argv[1] if len(argv) == 2 else ".", "rev-parse", "--show-toplevel").strip()
    if not os.path.exists(os.path.join(repo, "info.yaml")):
        die(f"{repo} has no info.yaml. Point the script at your Tiny Tapeout repository.")
    if git(repo, "status", "--porcelain", "--untracked-files=no").strip():
        die("you have uncommitted changes. Commit or stash them first, so that the breakage "
            "is a commit of its own.")
    if f"IC102-Breakage: {n}" in git(repo, "log", "--format=%B", "-50"):
        print(f"note: breakage {n} is already in your recent history; applying it again.")
    files = BREAKS[n](repo)
    git(repo, "add", *files)
    git(repo, "commit", "-q", "-m", f"{TITLES[n]}\n\nIC102-Breakage: {n}")
    sha = git(repo, "rev-parse", "--short", "HEAD").strip()
    print(f"Committed breakage {n} as {sha}: {TITLES[n]}")
    print("Nothing has been pushed. Make your prediction (Part 2), then: git push")


if __name__ == "__main__":
    main(sys.argv[1:])
