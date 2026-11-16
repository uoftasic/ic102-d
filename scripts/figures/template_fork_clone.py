"""Templates, forks and clones: what each kind of copy takes from the repository it starts from."""
import schemdraw.elements as elm
import schemdraw.flow as flow

from circuit_style import drawing, save

TEXT_DROP = 0.11    # schemdraw puts the baseline on y; this centres the letters on it instead
NOTE = 11           # font size for the notes
BOX_W, BOX_H = 5.6, 1.9
ROW = 3.3           # distance between the rows
SRC_X = BOX_W / 2   # centre of the source boxes
DST_X = SRC_X + BOX_W + 4.4
NOTE_X = DST_X + BOX_W / 2 + 0.5
STEP = 0.7          # distance between commits in a chain


def text(d, xy, s, halign="center", size=None):
    """Text at xy. right() stops it inheriting the last element's direction."""
    d.add(elm.Label().right().at((xy[0], xy[1] - TEXT_DROP))
          .label(s, halign=halign, fontsize=size))


def repo(d, x, y, title):
    """A box with the repository's name along its top edge."""
    box = d.add(flow.Box(w=BOX_W, h=BOX_H).anchor("center").at((x, y)))
    text(d, (x, y + BOX_H / 2 - 0.4), title, size=NOTE)
    return box


def chain(d, x, y, n):
    """n commits in a row, oldest on the left, centred on (x, y)."""
    x0 = x - STEP * (n - 1) / 2
    for k in range(n - 1):
        d.add(elm.Line().at((x0 + STEP * k, y)).to((x0 + STEP * (k + 1), y)))
    for k in range(n):
        d.add(elm.Dot(open=True, radius=0.13).at((x0 + STEP * k, y)))


def row(d, y, src, verb, dst, n_dst, notes, back=None):
    s = repo(d, SRC_X, y, src)
    chain(d, SRC_X, y - 0.25, 5)
    t = repo(d, DST_X, y, dst)
    chain(d, DST_X, y - 0.25, n_dst)
    d.add(elm.Arrow().at((s.E[0], y + 0.25)).to((t.W[0], y + 0.25)))
    text(d, ((s.E[0] + t.W[0]) / 2, y + 0.6), verb)
    if back:
        d.add(elm.Arrow().at((t.W[0], y - 0.35)).to((s.E[0], y - 0.35)).linestyle("--"))
        text(d, ((s.E[0] + t.W[0]) / 2, y - 0.7), back, size=NOTE)
    for k, line in enumerate(notes):
        text(d, (NOTE_X, y + 0.45 - 0.45 * k), line, halign="left", size=NOTE)


d = drawing()
d.config(margin=0.3)     # a little white around the edge, so no text touches it

row(d, 0, "TinyTapeout/ttsky-verilog-template", "Use this template",
    "you/my-project, on GitHub", 1,
    ["the files of the default branch",
     "one new commit, its own history",
     "no link back to the template",
     "settings such as Pages: not copied"])
row(d, -ROW, "TinyTapeout/ttsky-verilog-template", "Fork",
    "you/ttsky-verilog-template", 5,
    ["the full history,",
     "linked to the original, so",
     "pull requests can go back to it",
     "workflows off until you enable them"],
    back="pull request")
row(d, -2 * ROW, "you/my-project, on GitHub", "git clone",
    "my-project, on your machine", 5,
    ["every commit and branch",
     "the original becomes the",
     "remote called origin",
     "you push and pull to keep in step"],
    back="git push")

print(save(d, "ic102-template-fork-clone"))
