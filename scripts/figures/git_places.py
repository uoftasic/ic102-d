"""Git in one page: the four places a change passes through, and the commands that move it."""
import schemdraw.elements as elm
import schemdraw.flow as flow

from circuit_style import drawing, save

TEXT_DROP = 0.11    # schemdraw puts the baseline on y; this centres the letters on it instead
NOTE = 11           # font size for the notes under the boxes
BOX_W, BOX_H = 3.4, 1.5
GAP = 2.0           # space between boxes, where the commands go
GAP_OUT = 3.0       # the wider gap between your machine and GitHub


def text(d, xy, s, halign="center", size=None):
    """Text at xy. right() stops it inheriting the last element's direction."""
    d.add(elm.Label().right().at((xy[0], xy[1] - TEXT_DROP))
          .label(s, halign=halign, fontsize=size))


def place(d, x, name, sub):
    box = d.add(flow.Box(w=BOX_W, h=BOX_H).anchor("center").at((x, 0)))
    text(d, (x, 0.25), name)
    text(d, (x, -0.3), sub, size=NOTE)
    return box


d = drawing()
d.config(margin=0.3)     # a little white around the edge, so no text touches it

xs = [BOX_W / 2 + k * (BOX_W + GAP) for k in range(3)]
xs.append(xs[2] + BOX_W + GAP_OUT)
work = place(d, xs[0], "working tree", "files you edit")
stage = place(d, xs[1], "staging area", "the next commit")
repo = place(d, xs[2], "local repository", "all commits, in .git")
gh = place(d, xs[3], "GitHub", "remote: origin")

# Forward: add, commit, push, above the middle line.
UP = 0.35
EDGE = repo.E[0] + 0.4       # the right edge of "your machine"
for a, b, cmd in ((work, stage, "git add"), (stage, repo, "git commit"), (repo, gh, "git push")):
    d.add(elm.Arrow().at((a.E[0], UP)).to((b.W[0], UP)))
    mid = (EDGE + b.W[0]) / 2 if b is gh else (a.E[0] + b.W[0]) / 2
    text(d, (mid, UP + 0.35), cmd, size=NOTE)

# Back: fetch from GitHub, then switch or merge into the working tree.
DOWN = -0.35
d.add(elm.Arrow().at((gh.W[0], DOWN)).to((repo.E[0], DOWN)))
text(d, ((EDGE + gh.W[0]) / 2, DOWN - 0.35), "git fetch", size=NOTE)
LOW = -BOX_H / 2 - 0.55
d.add(elm.Line().at((repo.S[0], repo.S[1])).to((repo.S[0], LOW)))
d.add(elm.Line().at((repo.S[0], LOW)).to((work.S[0], LOW)))
d.add(elm.Arrow().at((work.S[0], LOW)).to((work.S[0], work.S[1])))
text(d, ((work.S[0] + repo.S[0]) / 2, LOW - 0.35), "git switch, git merge", size=NOTE)

# The laptop boundary: the first three places are on your machine.
left = work.W[0] - 0.35
right = EDGE
top = BOX_H / 2 + 1.05
bottom = LOW - 0.85
d.add(elm.Line().at((left, top)).to((right, top)).linestyle("--"))
d.add(elm.Line().at((right, top)).to((right, bottom)).linestyle("--"))
d.add(elm.Line().at((right, bottom)).to((left, bottom)).linestyle("--"))
d.add(elm.Line().at((left, bottom)).to((left, top)).linestyle("--"))
text(d, (left + 0.15, top - 0.3), "your machine", halign="left", size=NOTE)
text(d, (gh.S[0], LOW - 0.35), "git pull = fetch + merge", size=NOTE)

print(save(d, "ic102-git-places"))
