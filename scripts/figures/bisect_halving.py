"""History as evidence: how git bisect halves the suspect range with each test."""
import schemdraw.elements as elm

from circuit_style import drawing, save

TEXT_DROP = 0.11    # schemdraw puts the baseline on y; this centres the letters on it instead
NOTE = 11           # font size for the notes
STEP = 0.9          # distance between commits
N = 16              # commits in the history, 1 is known good and 16 known bad
FIRST_BAD = 11
TESTS = [8, 12, 10, 11]   # the commit each test checks out, in order


def text(d, xy, s, halign="center", size=None):
    """Text at xy. right() stops it inheriting the last element's direction."""
    d.add(elm.Label().right().at((xy[0], xy[1] - TEXT_DROP))
          .label(s, halign=halign, fontsize=size))


def x(k):
    return STEP * (k - 1)


d = drawing()
d.config(margin=0.3)     # a little white around the edge, so no text touches it

# The history, oldest on the left.
d.add(elm.Line().at((x(1), 0)).to((x(N), 0)))
for k in range(1, N + 1):
    if k in (1, N) or k in TESTS:
        bad = k >= FIRST_BAD
        d.add(elm.Dot(open=not bad, radius=0.17).at((x(k), 0)))
    else:
        d.add(elm.Dot(radius=0.06).at((x(k), 0)))

text(d, (x(1), 0.6), "good", size=NOTE)
text(d, (x(N), 0.6), "bad", size=NOTE)
for n, k in enumerate(TESTS, start=1):
    text(d, (x(k), 0.6), str(n), size=NOTE)
text(d, (x(FIRST_BAD), 1.15), "first bad commit", size=NOTE)
text(d, (x(N) + 0.6, 0), "16 commits", halign="left", size=NOTE)

# The suspects after each test: every commit after the last good one, up to
# and including the earliest bad one.
ranges = [(2, 16), (9, 16), (9, 12), (11, 12), (11, 11)]
labels = ["before: 15 suspects", "after test 1 (good): 8", "after test 2 (bad): 4",
          "after test 3 (good): 2", "after test 4 (bad): 1, commit 11"]
for row, ((lo, hi), label) in enumerate(zip(ranges, labels), start=1):
    y = -0.75 * row
    d.add(elm.Line().at((x(lo) - 0.2, y)).to((x(hi) + 0.2, y)).linewidth(3))
    text(d, (x(N) + 0.6, y), label, halign="left", size=NOTE)

# Legend.
y = -0.75 * (len(ranges) + 1) - 0.1
d.add(elm.Dot(open=True, radius=0.17).at((x(1), y)))
text(d, (x(1) + 0.35, y), "tested, passed", halign="left", size=NOTE)
d.add(elm.Dot(radius=0.17).at((x(5), y)))
text(d, (x(5) + 0.35, y), "tested, failed", halign="left", size=NOTE)
d.add(elm.Dot(radius=0.06).at((x(9), y)))
text(d, (x(9) + 0.35, y), "never tested", halign="left", size=NOTE)
text(d, (x(13), y), "1 to 4: the order of the tests", halign="left", size=NOTE)

print(save(d, "ic102-bisect-halving"))
