"""Helpers shared by IC102-D's lab checkers.

Standard library only, so the checkers run with the workbench's python3 or with any Python 3.8+
on a laptop. Two things live here:

  - reading your clone with git (which repository on GitHub it belongs to, which commit is HEAD);
  - reading GitHub's public REST API, which answers for public repositories without signing in.
    It allows 60 requests an hour from one address, and each checker makes only a few.

The API calls are read-only. Nothing here pushes, comments or changes anything on GitHub.
"""
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"

# The jobs the digital template's three active workflows run, in the order a push starts them.
# docs.yaml has `docs`, test.yaml has `test`, and gds.yaml has `gds`, then `precheck`, `gl_test`
# and `viewer`, which each need `gds`.
TEMPLATE_JOBS = ["docs", "test", "gds", "precheck", "gl_test", "viewer"]


class CheckError(Exception):
    """A problem the student can fix; printed without a traceback."""


def git(repo, *args, check=True):
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if check and p.returncode != 0:
        raise CheckError(f"git {' '.join(args)} failed in {repo}:\n{p.stderr.strip()}")
    return p.stdout.strip()


def repo_root(path):
    try:
        return git(path, "rev-parse", "--show-toplevel")
    except CheckError:
        raise CheckError(f"{os.path.abspath(path)} is not inside a git clone")


def github_slug(repo):
    """(owner, name) of the GitHub repository that `origin` points at."""
    url = git(repo, "remote", "get-url", "origin", check=False)
    m = re.match(r"^(?:https://(?:[^@/]+@)?github\.com/|git@github\.com:|ssh://git@github\.com/)"
                 r"([^/]+)/([^/]+?)(?:\.git)?/?$", url)
    if not m:
        raise CheckError(f"origin is {url or 'not set'}, which isn't a github.com repository")
    return m.group(1), m.group(2)


def api_get(path):
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "uoftasic-ic102-checker",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise CheckError(f"GitHub says 404 for {path}. Is the repository public, "
                             "and has the commit been pushed?")
        if e.code in (403, 429):
            raise CheckError("GitHub's rate limit for unauthenticated requests (60 an hour) "
                             "is used up. Wait a few minutes and try again.")
        raise CheckError(f"GitHub answered {e.code} for {path}")
    except urllib.error.URLError as e:
        raise CheckError(f"couldn't reach api.github.com ({e.reason}). Check your connection.")


def check_runs(owner, name, sha):
    """Every check run (one per job) GitHub has recorded for this commit."""
    data = api_get(f"/repos/{owner}/{name}/commits/{sha}/check-runs?per_page=100")
    return data["check_runs"]


def latest_by_name(runs):
    """A re-run or a new run of the same workflow adds a second check run with the same job
    name; keep the most recent one of each."""
    best = {}
    for r in runs:
        key = r["name"]
        when = r.get("started_at") or ""
        if key not in best or when > (best[key].get("started_at") or ""):
            best[key] = r
    return best


def runs_table(runs, wanted=TEMPLATE_JOBS):
    """Rows of (job, status) for the wanted jobs first, then any others, and whether every
    wanted job finished with success."""
    best = latest_by_name(runs)
    rows, ok = [], True
    for job in wanted:
        r = best.get(job)
        if r is None:
            rows.append((job, "no run yet"))
            ok = False
        elif r["status"] != "completed":
            rows.append((job, r["status"]))
            ok = False
        else:
            rows.append((job, r["conclusion"]))
            ok = ok and r["conclusion"] == "success"
    for job in sorted(set(best) - set(wanted)):
        r = best[job]
        rows.append((job, r["conclusion"] if r["status"] == "completed" else r["status"]))
    return rows, ok


def print_table(rows, indent="  "):
    width = max(len(job) for job, _ in rows)
    for job, status in rows:
        print(f"{indent}{job:<{width}}  {status}")


def run_checker(main):
    """Run a checker's main(), printing CheckErrors plainly. Exit 0 on PASS, 1 otherwise."""
    try:
        ok = main()
    except CheckError as e:
        print(f"\nCan't check yet: {e}")
        ok = False
    except KeyboardInterrupt:
        ok = False
    sys.exit(0 if ok else 1)
