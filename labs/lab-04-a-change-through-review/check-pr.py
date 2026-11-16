#!/usr/bin/env python3
"""Lab 04 check: your pull request merged after an approval, and a review of yours asked for a
change that its author then made.

    python3 check-pr.py YOUR_PR THE_PR_YOU_REVIEWED [--me GITHUB_USERNAME]

Each pull request is OWNER/REPO#NUMBER or its link. In Lab 04 the first is in your partner's
review repository and the second in yours, for example:

    python3 check-pr.py PARTNER-USERNAME/ttsky-ic102-d-review#3 YOUR-USERNAME/ttsky-ic102-d-review#2

It reads both pull requests from GitHub's public API, without signing in, and checks:

  1. YOUR_PR is merged, and someone other than you approved it before it was merged;
  2. on THE_PR_YOU_REVIEWED, you submitted a review that requested changes, and its author
     pushed at least one commit after that review.

"You" are the author of YOUR_PR, unless --me says otherwise. It changes nothing on GitHub.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "common"))
import ic102  # noqa: E402


def parse(arg):
    """OWNER/REPO#N, or https://github.com/OWNER/REPO/pull/N, as (owner, repo, n)."""
    m = (re.fullmatch(r"([\w.-]+)/([\w.-]+)#(\d+)", arg)
         or re.fullmatch(r"(?:https?://)?github\.com/([\w.-]+)/([\w.-]+)/pull/(\d+)/?\S*", arg))
    if not m:
        raise ic102.CheckError(f"{arg!r} isn't OWNER/REPO#NUMBER or a pull request's link")
    return m.group(1), m.group(2), int(m.group(3))


def pr(owner, name, n):
    return (ic102.api_get(f"/repos/{owner}/{name}/pulls/{n}"),
            ic102.api_get(f"/repos/{owner}/{name}/pulls/{n}/reviews?per_page=100"),
            ic102.api_get(f"/repos/{owner}/{name}/pulls/{n}/commits?per_page=100"))


def main():
    args = sys.argv[1:]
    me = None
    if "--me" in args:
        i = args.index("--me")
        me = args[i + 1]
        args = args[:i] + args[i + 2:]
    if len(args) != 2:
        raise ic102.CheckError("usage: python3 check-pr.py OWNER/REPO#N OWNER/REPO#N "
                               "(your pull request, then the one you reviewed)")
    owner, name, mine = parse(args[0])
    o_owner, o_name, other = parse(args[1])
    problems = []

    p, reviews, _ = pr(owner, name, mine)
    me = me or p["user"]["login"]
    print(f"{owner}/{name} #{mine}: {p['title']}")
    print(f"  author        {p['user']['login']}")
    merged = p.get("merged_at")
    print(f"  merged        {merged or 'no'}")
    approvals = [r for r in reviews if r["state"] == "APPROVED" and r["user"]["login"] != me]
    before = [r for r in approvals if merged and r["submitted_at"] <= merged]
    for r in approvals:
        when = "before the merge" if r in before else "after the merge" if merged else ""
        print(f"  approved by   {r['user']['login']} at {r['submitted_at']} {when}".rstrip())
    if not approvals:
        print("  approved by   nobody yet")
    if not merged:
        problems.append(f"#{mine} isn't merged yet")
    elif not before:
        problems.append(f"#{mine} has no approval from someone else that came before the merge")

    o, reviews, commits = pr(o_owner, o_name, other)
    print(f"\n{o_owner}/{o_name} #{other}: {o['title']}")
    print(f"  author        {o['user']['login']}")
    asks = [r for r in reviews if r["user"]["login"] == me and r["state"] == "CHANGES_REQUESTED"]
    if not asks:
        print(f"  {me} hasn't requested changes on it")
        problems.append(f"request a change on #{other} (Part 4)")
    else:
        first = asks[0]["submitted_at"]
        later = [c for c in commits if c["commit"]["committer"]["date"] > first]
        print(f"  {me} requested changes at {first}")
        print(f"  commits pushed after that: {len(later)}")
        if not later:
            problems.append(f"#{other}'s author hasn't pushed a change since your review")

    print()
    for x in problems:
        print(f"todo: {x}")
    print("VERDICT: PASS" if not problems else "VERDICT: not yet")
    return not problems


if __name__ == "__main__":
    ic102.run_checker(main)
