"""What one push starts in a Tiny Tapeout repository: three workflows, and the job graph inside gds."""
import schemdraw.elements as elm
import schemdraw.flow as flow

from circuit_style import drawing, save

TEXT_DROP = 0.11    # schemdraw puts the baseline on y; this centres the letters on it instead
NOTE = 11           # font size for the notes
JOB_W, JOB_H = 2.6, 0.9


def text(d, xy, s, halign="center", size=None):
    """Text at xy. right() stops it inheriting the last element's direction."""
    d.add(elm.Label().right().at((xy[0], xy[1] - TEXT_DROP))
          .label(s, halign=halign, fontsize=size))


def job(d, x, y, name, w=JOB_W):
    return d.add(flow.Box(w=w, h=JOB_H).anchor("center").at((x, y)).label(name))


def dashed_rect(d, x0, y0, x1, y1):
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        d.add(elm.Line().at(a).to(b).linestyle("--"))


d = drawing()
d.config(margin=0.3)     # a little white around the edge, so no text touches it

push = d.add(flow.Box(w=1.9, h=1.0).anchor("center").at((0, 1.4)).label("git push"))

# The three workflows a push starts, each with its own run.
JX = 4.4                 # centre of the first column of jobs
docs = job(d, JX, 4.6, "docs")
test = job(d, JX, 3.3, "test *")
gds = job(d, JX, 0.0, "gds")
text(d, (docs.E[0] + 0.35, 4.6), "docs workflow: checks info.yaml and docs/info.md, builds the datasheet PDF",
     halign="left", size=NOTE)
text(d, (test.E[0] + 0.35, 3.3), "test workflow: runs the cocotb test of your RTL", halign="left", size=NOTE)

BUS = 1.75
d.add(elm.Line().at(push.E).to((BUS, 1.4)))
d.add(elm.Line().at((BUS, 4.6)).to((BUS, 0.0)))
for box in (docs, test, gds):
    d.add(elm.Arrow().at((BUS, box.W[1])).to(box.W))

# Inside the gds workflow: one job, then three that each say needs: gds.
dashed_rect(d, 2.55, 2.35, 17.9, -2.0)
text(d, (2.75, 2.0), "gds workflow", halign="left", size=NOTE)
text(d, (2.85, -0.75), "digital: LibreLane builds the layout", halign="left", size=NOTE)
text(d, (2.85, -1.15), "analog: copies the GDS you drew", halign="left", size=NOTE)
text(d, (2.85, -1.55), "then uploads the artifacts", halign="left", size=NOTE)

KX = 11.4                # centre of the second column of jobs
pre = job(d, KX, 1.2, "precheck")
gl = job(d, KX, 0.0, "gl_test *")
view = job(d, KX, -1.2, "viewer")
NEEDS = 8.7
d.add(elm.Line().at(gds.E).to((NEEDS, 0.0)))
d.add(elm.Line().at((NEEDS, 1.2)).to((NEEDS, -1.2)))
for box in (pre, gl, view):
    d.add(elm.Arrow().at((NEEDS, box.W[1])).to(box.W))
text(d, (NEEDS, 1.75), "needs: gds", size=NOTE)

text(d, (pre.E[0] + 0.3, 1.2), "DRC and other checks", halign="left", size=NOTE)
text(d, (gl.E[0] + 0.3, 0.0), "simulates the netlist", halign="left", size=NOTE)
text(d, (view.E[0] + 0.3, -1.2), "publishes the viewer", halign="left", size=NOTE)

pages = d.add(flow.Box(w=2.9, h=JOB_H).anchor("center").at((KX, -3.1)).label("GitHub Pages"))
d.add(elm.Arrow().at(view.S).to(pages.N))
text(d, (KX + 0.25, -2.25), "deploy", halign="left", size=NOTE)
text(d, (pages.E[0] + 0.3, -3.1), "only if Pages is turned on", halign="left", size=NOTE)

text(d, (2.75, -4.15), "* digital template only; the analog template has no test workflow and no gl_test job",
     halign="left", size=NOTE)

print(save(d, "ic102-push-workflows"))
