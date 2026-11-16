#!/usr/bin/env python3
"""Copy IC102's shared guide pages from this repo (ic102-d) into another course repo (ic102-a).

IC102 comes in two versions, each in its own repository. Eight guide pages are the same in both,
and they're written here, in ic102-d. This script copies them into the other repository's
docs/guide/, together with everything they need:

  - the images they reference, from docs/assets/img/;
  - for each SVG figure, the script in scripts/figures/ that draws it, plus the shared style
    module and requirements.txt, so the figure can be redrawn in the other repository too.

It reports every file as one of: same (nothing to do), new (not in the target yet), or differs
(the target's copy is different, and is overwritten unless you pass --dry-run). For text files
that differ it prints a unified diff, so an edit somebody made directly in the target is shown
before it's replaced; port such edits back to ic102-d, since that's where the shared pages live.

It also lists links from the shared pages to other pages that don't exist in the target. A link
to a lab that hasn't been written yet is expected; a link to a page that only ic102-d has means a
shared page is pointing at something version-specific, and should be fixed here.

Usage, from the root of this repository:

    python3 scripts/sync_shared_pages.py ../ic102-a --dry-run    # report only, change nothing
    python3 scripts/sync_shared_pages.py ../ic102-a              # copy, then report

Run it on a target worktree with no uncommitted changes, so `git diff` there shows exactly what
the copy changed. Exit status: 0 if the target is (now) in step, 1 if --dry-run found anything
new or different, 2 for a usage error.
"""
import argparse
import difflib
import re
import shutil
import sys
from pathlib import Path

SHARED_PAGES = [
    "git-in-one-page.md",
    "templates-forks-and-clones.md",
    "what-a-cloud-runner-is.md",
    "reading-a-workflow-file.md",
    "pull-requests-and-review.md",
    "branch-rules.md",
    "how-open-source-projects-work.md",
    "history-as-evidence.md",
]

# Files every figure script needs, copied whenever any figure script is.
FIGURE_SUPPORT = ["scripts/figures/circuit_style.py", "scripts/figures/requirements.txt"]

TEXT_SUFFIXES = {".md", ".py", ".txt", ".yml", ".yaml"}

# ![alt](path){attrs} and raw HTML src="..." / poster="..."
IMAGE_MD = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")
IMAGE_HTML = re.compile(r'(?:src|poster)="([^"]+)"')
# [text](path.md#anchor), but not images
PAGE_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s#]+\.md)(#[^)\s]*)?\)")
# save(d, "ic102-git-places") in a figure script
FIGURE_SAVE = re.compile(r"""save\(\s*\w+\s*,\s*["']([^"']+)["']\s*\)""")


def repo_root():
    return Path(__file__).resolve().parent.parent


def images_used(page_path):
    """Repo-relative paths of the local images a page references."""
    text = page_path.read_text(encoding="utf-8")
    found = []
    for ref in IMAGE_MD.findall(text) + IMAGE_HTML.findall(text):
        if ref.startswith(("http:", "https:", "data:")):
            continue
        target = (page_path.parent / ref).resolve()
        found.append(target)
    return found


def figure_scripts(src_root):
    """Map each figure name a script saves (without .svg) to that script."""
    scripts = {}
    for script in sorted((src_root / "scripts" / "figures").glob("*.py")):
        for name in FIGURE_SAVE.findall(script.read_text(encoding="utf-8")):
            scripts[name] = script
    return scripts


def page_links(page_path):
    """Relative .md links in a page, as written (so relative to docs/guide/)."""
    text = page_path.read_text(encoding="utf-8")
    return [m.group(1) for m in PAGE_LINK.finditer(text) if not m.group(1).startswith(("http:", "https:"))]


def files_to_copy(src_root):
    """Repo-relative paths of everything the shared pages need, in a stable order."""
    guide = src_root / "docs" / "guide"
    wanted = []
    missing = []
    svgs = set()
    for page in SHARED_PAGES:
        path = guide / page
        if not path.is_file():
            missing.append(f"docs/guide/{page}")
            continue
        wanted.append(path)
        for image in images_used(path):
            if not image.is_file():
                missing.append(str(image.relative_to(src_root)))
                continue
            wanted.append(image)
            if image.suffix == ".svg":
                svgs.add(image.stem)
    scripts = figure_scripts(src_root)
    used_scripts = set()
    for stem in sorted(svgs):
        if stem in scripts:
            used_scripts.add(scripts[stem])
        else:
            missing.append(f"scripts/figures/<script that saves {stem}>")
    wanted.extend(sorted(used_scripts))
    if used_scripts:
        wanted.extend(src_root / rel for rel in FIGURE_SUPPORT)
    seen = set()
    unique = []
    for path in wanted:
        rel = path.relative_to(src_root)
        if rel not in seen:
            seen.add(rel)
            unique.append(rel)
    return unique, missing


def describe_difference(src, dst, show_diff):
    """Print a unified diff of a text file, or a size line for anything else."""
    if src.suffix in TEXT_SUFFIXES:
        old = dst.read_text(encoding="utf-8").splitlines(keepends=True)
        new = src.read_text(encoding="utf-8").splitlines(keepends=True)
        diff = list(difflib.unified_diff(old, new, f"target/{dst.name}", f"ic102-d/{src.name}"))
        changed = sum(1 for line in diff if line[:1] in "+-" and line[:3] not in ("+++", "---"))
        print(f"      {changed} changed lines")
        if show_diff:
            for line in diff:
                print("      " + line.rstrip("\n"))
    else:
        print(f"      {dst.stat().st_size} bytes in the target, {src.stat().st_size} in ic102-d")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("target", type=Path, help="root of the target course repo, e.g. ../ic102-a")
    parser.add_argument("--dry-run", action="store_true", help="report only; change nothing")
    parser.add_argument("--no-diff", action="store_true", help="count changed lines instead of printing diffs")
    args = parser.parse_args()

    src_root = repo_root()
    dst_root = args.target.resolve()
    if dst_root == src_root:
        print("The target is this repository; give the path of the other course repo.", file=sys.stderr)
        return 2
    if not (dst_root / "docs" / "guide").is_dir():
        print(f"{dst_root} has no docs/guide/; is it a course repo?", file=sys.stderr)
        return 2

    files, missing = files_to_copy(src_root)
    if missing:
        print("Missing in ic102-d (fix these before syncing):")
        for item in missing:
            print(f"  {item}")
        return 2

    counts = {"same": 0, "new": 0, "differs": 0}
    for rel in files:
        src = src_root / rel
        dst = dst_root / rel
        if not dst.exists():
            state = "new"
        elif dst.read_bytes() == src.read_bytes():
            state = "same"
        else:
            state = "differs"
        counts[state] += 1
        if state == "same":
            continue
        print(f"  {state:8} {rel}")
        if state == "differs":
            describe_difference(src, dst, show_diff=not args.no_diff)
        if not args.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    # Links from the shared pages to pages the target doesn't have.
    # The shared pages themselves are being copied, so links between them don't count.
    dangling = []
    for page in SHARED_PAGES:
        for link in page_links(src_root / "docs" / "guide" / page):
            if link in SHARED_PAGES:
                continue
            if not (dst_root / "docs" / "guide" / link).resolve().is_file():
                dangling.append((page, link))
    if dangling:
        print("\nLinks from the shared pages to pages the target doesn't have yet:")
        for page, link in sorted(set(dangling)):
            print(f"  {page} -> {link}")

    verb = "would copy" if args.dry_run else "copied"
    print(f"\n{len(files)} files: {counts['same']} same, {counts['new']} new, "
          f"{counts['differs']} different ({verb} {counts['new'] + counts['differs']}).")
    if args.dry_run and (counts["new"] or counts["differs"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
