"""Opening signature v2: the lowercase footer word + the face doodle.

Composite canvas = images/handwriting/tedkweebintoro.png ink at the origin,
plus the SignatureHQ face doodle scaled FSCALE and placed to its right.
The word writes as 3 pen runs (tedk / weeb / intoro) + the i-tittle, each a
chained skeleton traversal; the face keeps its notebook stroke order.
Per-stroke ink partition + potraced fills, exactly as before.
"""
import json
import numpy as np
import potrace
from PIL import Image, ImageDraw
from scipy import ndimage

SCRATCH = "/private/tmp/claude-501/-Users-tehsauscabe-tkb-site/6230281c-01e0-4204-958b-bd340df3e7d1/scratchpad"
SITE = "/Users/tehsauscabe/tkb-site"

# ---- the word --------------------------------------------------------------
wmeta = json.load(open(f"{SCRATCH}/word_strokes.json"))
wfrags = wmeta["strokes"]
WW, WH = wmeta["w"], wmeta["h"]
word_ink = np.array(Image.open(f"{SITE}/images/handwriting/tedkweebintoro.png").convert("RGBA"))[..., 3] > 128

# ---- the face, lifted from the formal signature ----------------------------
smeta = json.load(open(f"{SCRATCH}/sig_strokes.json"))
sfrags = smeta["strokes"]
sig = np.array(Image.open(f"{SCRATCH}/SignatureHQ.png").convert("RGBA"))
salpha = sig[..., 3].astype(float) / 255.0
slum = sig[..., :3].astype(float).mean(axis=2)
sink = (slum * salpha + 255.0 * (1 - salpha)) < 128
face_src = sink[:, 716:]                     # everything right of the lettering
fys, fxs = np.nonzero(face_src)
face_src = face_src[fys.min():fys.max() + 1, fxs.min():fxs.max() + 1]
SRC_X0, SRC_Y0 = 716 + fxs.min(), fys.min()  # face origin in SignatureHQ space

FSCALE = 1.25
GAP = 26                                     # whitespace between word and face
FX0 = WW + GAP                               # face placement in the composite
FY0 = 8

fh, fw = face_src.shape
face_zoom = ndimage.zoom(face_src.astype(float), FSCALE, order=1) > 0.5
zh, zw = face_zoom.shape

W = FX0 + zw + 4
H = max(WH, FY0 + zh + 2)
ink = np.zeros((H, W), dtype=bool)
ink[:WH, :WW] = word_ink
ink[FY0:FY0 + zh, FX0:FX0 + zw] = face_zoom
print(f"composite {W}x{H}  word ink {int(word_ink.sum())}  face ink {int(face_zoom.sum())}")

def face_pts(i):
    """fragment i of the formal signature, moved into the composite"""
    return [[(x - SRC_X0) * FSCALE + FX0, (y - SRC_Y0) * FSCALE + FY0]
            for x, y in sfrags[i]["pts"]]

# ---- chain each pen run's fragments into one polyline ----------------------
wlbl, nw = ndimage.label(word_ink, structure=np.ones((3, 3)))

def frag_comp(f):
    xs = [p[0] for p in f["pts"]]; ys = [p[1] for p in f["pts"]]
    x = int(round(min(max(np.median(xs), 0), WW - 1)))
    y = int(round(min(max(np.median(ys), 0), WH - 1)))
    if wlbl[y, x]:
        return wlbl[y, x]
    yy, xx = np.nonzero(word_ink)
    j = np.argmin((xx - x) ** 2 + (yy - y) ** 2)
    return wlbl[yy[j], xx[j]]

comp_of = [frag_comp(f) for f in wfrags]

def chain(indices, start_xy):
    """greedy endpoint chain; returns ordered fragment polylines (subpaths),
    so the mask pen lifts between fragments instead of drawing jump lines"""
    todo = set(indices)
    pos = np.array(start_xy, dtype=float)
    subs = []
    while todo:
        best, bd, brev = None, None, False
        for i in todo:
            p = wfrags[i]["pts"]
            d0 = np.hypot(*(np.array(p[0]) - pos))
            d1 = np.hypot(*(np.array(p[-1]) - pos))
            d, rev = (d0, False) if d0 <= d1 else (d1, True)
            if bd is None or d < bd:
                best, bd, brev = i, d, rev
        todo.discard(best)
        pts = wfrags[best]["pts"]
        pts = list(reversed(pts)) if brev else list(pts)
        subs.append(pts)
        pos = np.array(pts[-1], dtype=float)
    return subs

comp_ids = sorted(set(comp_of))
runs = {c: [i for i, cc in enumerate(comp_of) if cc == c] for c in comp_ids}
for c in comp_ids:
    xs = [p[0] for i in runs[c] for p in wfrags[i]["pts"]]
    print(f"run comp {c}: frags {runs[c]}  x {min(xs):.0f}..{max(xs):.0f}")

# identify the runs by extent: tedk starts at x~0; weeb in the middle;
# intoro at the right; the tittle is the tiny top tick
def run_min_x(c):
    return min(p[0] for i in runs[c] for p in wfrags[i]["pts"])

def run_size(c):
    return sum(wfrags[i]["len"] for i in runs[c])

big = sorted([c for c in comp_ids if run_size(c) > 60], key=run_min_x)
tiny = [c for c in comp_ids if run_size(c) <= 60]
assert len(big) == 3 and len(tiny) == 1, (big, tiny)
c_tedk, c_weeb, c_intoro = big
c_tittle = tiny[0]

g_tedk = chain(runs[c_tedk], (0, 81))
g_weeb = chain(runs[c_weeb], tuple(g_tedk[-1][-1]))
g_intoro = chain(runs[c_intoro], tuple(g_weeb[-1][-1]))
g_tittle = chain(runs[c_tittle], tuple(g_intoro[-1][-1]))

GROUPS = [
    # the whole signature is one gesture (the dash flows through every pen
    # run; subpath hops are instant); the face draws on a parallel track
    ("word",     g_tedk + g_weeb + g_intoro + g_tittle, 0),
    ("hair",     [face_pts(30), face_pts(31)],  0),
    ("headear",  [face_pts(32)],                0),
    ("eyes",     [face_pts(33), face_pts(34), face_pts(35)], 0),
    ("mouth",    [face_pts(36)],                0),
    ("innerear", [face_pts(37), face_pts(38)],  0),
]
FACE_FROM = 1

groups = [{"name": n, "subs": p, "pause": pz} for n, p, pz in GROUPS]

# ---- partition the ink among the strokes (unchanged machinery) -------------
def polyline_dist(subs):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for pts in subs:
        if len(pts) == 1:
            pts = pts + [[pts[0][0] + 0.5, pts[0][1]]]
        d.line([tuple(p) for p in pts], fill=255, width=1, joint="curve")
    return ndimage.distance_transform_edt(np.array(m) < 128)

dists = [polyline_dist(g["subs"]) for g in groups]

# stroke half-widths: word runs are thin; face strokes carry the formal width
halfw = []
for k, g in enumerate(groups):
    on_ink = dists[k][ink]
    hw = 6.0 if k < FACE_FROM else 7.0 * FSCALE
    halfw.append(hw)

CORE, CAPTURE = 1.0, 2.5
pen = np.stack([d - hw for d, hw in zip(dists, halfw)])
in_core = pen <= CORE
has_core = in_core.any(axis=0)
first_core = in_core.argmax(axis=0)
pen_cap = np.where(pen <= CAPTURE, pen, np.inf)
has_cap = np.isfinite(pen_cap.min(axis=0))
nearest_cap = pen_cap.argmin(axis=0)
nearest_any = pen.argmin(axis=0)
choice = np.where(has_core, first_core,
                  np.where(has_cap, nearest_cap, nearest_any))
stray = ink & ~has_core & ~has_cap
print(f"stray px: {int(stray.sum())}")

fills = []
for k, (g, dist) in enumerate(zip(groups, dists)):
    f = ink & (choice == k)
    captured = f & ~stray
    g["svg_w"] = round(float(2 * dist[captured].max() + 2), 1) if captured.any() else 8.0
    g["fill"] = f
    fills.append(f)

union = np.zeros_like(ink)
for f in fills:
    assert not (union & f).any(), "fills overlap"
    union |= f
assert (ink & ~union).sum() == 0, "ink pixels lost in partition"

# ---- potrace each stroke's ink ---------------------------------------------
def trace(mask):
    bmp = potrace.Bitmap(~mask)
    plist = bmp.trace()
    def fmt(p):
        return f"{p.x:.2f},{p.y:.2f}"
    parts = []
    for c in plist.curves:
        parts.append(f"M{fmt(c.start_point)}")
        for s in c.segments:
            if s.is_corner:
                parts.append(f"L{fmt(s.c)}L{fmt(s.end_point)}")
            else:
                parts.append(f"C{fmt(s.c1)} {fmt(s.c2)} {fmt(s.end_point)}")
        parts.append("Z")
    return "".join(parts)

def chunk(i, g):
    d_fill = trace(g["fill"])
    d_line = "".join(
        f"M{s[0][0]:.1f},{s[0][1]:.1f}" + "".join(f"L{x:.1f},{y:.1f}" for x, y in s[1:])
        for s in g["subs"])
    pause_attr = f' data-pause="{g["pause"]}"' if g["pause"] else ""
    return f'''<mask id="sm{i}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
<rect width="{W}" height="{H}" fill="#000"/>
<path class="ms" data-g="{g["name"]}" d="{d_line}" stroke="#fff" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="{g["svg_w"]}"{pause_attr}/>
</mask>
<path class="sf" d="{d_fill}" fill="currentColor" fill-rule="evenodd" mask="url(#sm{i})"/>'''

face_union = np.zeros_like(ink)
for g in groups[FACE_FROM:]:
    face_union |= g["fill"]
fys2, fxs2 = np.nonzero(face_union)
FX, FY = int(fxs2.min()) - 4, int(fys2.min()) - 4
FW, FH = int(fxs2.max()) + 5 - FX, int(fys2.max()) + 5 - FY
LW = FX + 3   # lettering viewBox runs to the face box, keeping the gap

letter_chunks = [chunk(i, g) for i, g in enumerate(groups[:FACE_FROM])]
face_chunks = [chunk(FACE_FROM + i, g) for i, g in enumerate(groups[FACE_FROM:])]

svg = f'''<span id="sigstage" style="--lw:{LW};--lr:{LW/W:.4f};--fr:{FW/W:.4f};--fyr:{FY/W:.4f}">
<svg id="sig" viewBox="0 0 {LW} {H}" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
{chr(10).join(letter_chunks)}
</svg>
<svg id="sigface" viewBox="{FX} {FY} {FW} {FH}" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
{chr(10).join(face_chunks)}
</svg>
</span>'''

html = open(f"{SITE}/index.html").read()
assert "<!--SIG_SVG-->" in html, "placeholder missing"
open(f"{SITE}/index.html", "w").write(html.replace("<!--SIG_SVG-->", svg))
print(f"injected {len(groups)} per-stroke fills, {len(svg)} chars")
print(f"lettering viewBox 0 0 {LW} {H}; face viewBox {FX} {FY} {FW} {FH}")
total = 0.0
for g in groups:
    L = sum(np.hypot(s[i+1][0]-s[i][0], s[i+1][1]-s[i][1])
            for s in g["subs"] for i in range(len(s) - 1))
    total += L
    print(f'  {g["name"]}: mask w {g["svg_w"]}, {len(g["subs"])} subpaths, path len {L:.0f}, ink px {int(g["fill"].sum())}')
print(f"total path len {total:.0f} (~{total/1050:.1f}s at 1050u/s)")

# chain-order preview
prev = Image.new("RGB", (W, H), "white")
dr = ImageDraw.Draw(prev)
cols = [(220,40,40),(30,120,220),(30,160,60),(230,130,20),(150,40,200),
        (200,40,140),(20,170,170),(120,100,30),(60,60,220)]
for i, g in enumerate(groups):
    c = cols[i % len(cols)]
    for s in g["subs"]:
        P = [tuple(p) for p in s]
        for a, b in zip(P, P[1:]):
            dr.line([a, b], fill=c, width=2)
    dr.text((g["subs"][0][0][0], max(0, g["subs"][0][0][1] - 12)), g["name"], fill=c)
prev = prev.resize((W * 2, H * 2), Image.NEAREST)
prev.save(f"{SCRATCH}/word_chain.png")
