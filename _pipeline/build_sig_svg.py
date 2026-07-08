"""Generate the inline signature SVG as 14 per-stroke sub-paths.

The signature ink is PARTITIONED among the pen strokes: each stroke gets its
own potraced fill, revealed by its own mask. A mask stroke can therefore only
ever reveal its own stroke's ink — crossings never bleed into other strokes.

Stroke order (matches the notebook progression):
  T, ed, K-downstroke, rest-of-Kwee, hyphen, B-downstroke, rest-of-B,
  intoro, i-tittle, then the doodle: hair, head+ear, eyes, mouth, inner ear.
Fragment ids refer to sig_strokes.json; "NR" = fragment N reversed.
"""
import json
import numpy as np
import potrace
from PIL import Image, ImageDraw
from scipy import ndimage

SCRATCH = "/private/tmp/claude-501/-Users-tehsauscabe-tkb-site/6230281c-01e0-4204-958b-bd340df3e7d1/scratchpad"
SITE = "/Users/tehsauscabe/tkb-site"

meta = json.load(open(f"{SCRATCH}/sig_strokes.json"))
frags = meta["strokes"]
W, H = meta["w"], meta["h"]

# ink mask from the original scan
img = Image.open(f"{SCRATCH}/SignatureHQ.png").convert("RGBA")
arr = np.array(img)
alpha = arr[..., 3].astype(float) / 255.0
lum = arr[..., :3].astype(float).mean(axis=2)
ink = (lum * alpha + 255.0 * (1 - alpha)) < 128

# the B's downstroke: one continuous line, top of the B to its bottom-left
# foot, following the ink through the mid pinch
B_SPINE = [[476, 7], [468, 10], [464, 16], [465, 26], [471, 40], [473, 46],
           [468, 60], [461, 75], [460, 80], [468, 88], [462, 93], [455, 98],
           [447, 106]]
# the hyphen dash at its full extent, crossing the B's entry
HYPHEN = [[441, 84], [458, 66], [475, 48]]

# (name, parts, pause_ms_after)
GROUPS = [
    ("T",        [0, 1, 2],                          0),
    ("ed",       [3, 4, 5, 6, 7],                    0),
    ("Kdown",    ["8R"],                             0),
    ("Kwee",     [11, 9, 10, 12, 13, 14, 15],        0),
    ("hyphen",   ["HYPHEN"],                         0),
    ("Bdown",    ["SPINE"],                          0),
    ("Brest",    ["16R", 17],                        0),
    ("intoro",   [21, 22, 23, "24R", 25, 26, 27, 28], 0),
    ("tittle",   [29],                               260),   # beat before the drawing
    ("hair",     [30, 31],                           0),
    ("headear",  [32],                               0),
    ("eyes",     [33, 34, 35],                       0),
    ("mouth",    [36],                               0),
    ("innerear", [37, 38],                           0),
]

def frag_pts(ref):
    if ref == "SPINE":
        return [list(map(float, p)) for p in B_SPINE], 10.5
    if ref == "HYPHEN":
        return [list(map(float, p)) for p in HYPHEN], 8.0
    if isinstance(ref, str) and ref.endswith("R"):
        f = frags[int(ref[:-1])]
        return list(reversed(f["pts"])), f["w"]
    f = frags[ref]
    return f["pts"], f["w"]

# assemble each group's polyline + nominal width
groups = []
for name, parts, pause in GROUPS:
    pts_all, wmax = [], 0.0
    for ref in parts:
        pts, w = frag_pts(ref)
        wmax = max(wmax, w)
        pts_all.extend(pts)
    groups.append({"name": name, "pts": pts_all, "w": wmax, "pause": pause})

# ---- partition the ink among the strokes ---------------------------------
def polyline_dist(pts):
    """distance transform to a 1px rasterization of the polyline"""
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.line([tuple(p) for p in pts], fill=255, width=1, joint="curve")
    return ndimage.distance_transform_edt(np.array(m) < 128)

dists = [polyline_dist(g["pts"]) for g in groups]

# Exclusive assignment. penetration = distance beyond the stroke's half-width:
# - a pixel inside more than one stroke's CORE is a true crossing -> earliest
#   stroke in draw order owns it (the later pass is already inked, so its
#   reveal void there is invisible)
# - otherwise the pixel goes to the stroke it penetrates deepest
CORE, CAPTURE = 1.0, 2.5
pen = np.stack([d - g["w"] / 2 for d, g in zip(dists, groups)])
in_core = pen <= CORE
has_core = in_core.any(axis=0)
first_core = in_core.argmax(axis=0)
pen_cap = np.where(pen <= CAPTURE, pen, np.inf)
has_cap = np.isfinite(pen_cap.min(axis=0))
nearest_cap = pen_cap.argmin(axis=0)
nearest_any = pen.argmin(axis=0)   # strays: nearest stroke outright
choice = np.where(has_core, first_core,
                  np.where(has_cap, nearest_cap, nearest_any))
stray = ink & ~has_core & ~has_cap
print(f"stray px: {int(stray.sum())}")

fills = []
for k, (g, dist) in enumerate(zip(groups, dists)):
    f = ink & (choice == k)
    captured = f & ~stray
    g["svg_w"] = round(float(2 * dist[captured].max() + 2), 1)
    g["fill"] = f
    fills.append(f)

# sanity: the fills partition the signature exactly
union = np.zeros_like(ink)
for f in fills:
    assert not (union & f).any(), "fills overlap"
    union |= f
assert (ink & ~union).sum() == 0, "ink pixels lost in partition"

# ---- potrace each stroke's ink -------------------------------------------
def trace(mask):
    bmp = potrace.Bitmap(~mask)   # potracer: 0 = foreground
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

# the doodle detaches at the end: lettering flies to the header, the face
# drifts into the page background — so they are two sibling SVGs that sit
# flush during the signing
FACE_FROM = 9   # strokes[9:] = hair, head+ear, eyes, mouth, inner ear

def chunk(i, g):
    d_fill = trace(g["fill"])
    d_line = f"M{g['pts'][0][0]},{g['pts'][0][1]}" + "".join(
        f"L{x},{y}" for x, y in g["pts"][1:])
    pause_attr = f' data-pause="{g["pause"]}"' if g["pause"] else ""
    return f'''<mask id="sm{i}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
<rect width="{W}" height="{H}" fill="#000"/>
<path class="ms" data-g="{g["name"]}" d="{d_line}" stroke="#fff" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="{g["svg_w"]}"{pause_attr}/>
</mask>
<path class="sf" d="{d_fill}" fill="currentColor" fill-rule="evenodd" mask="url(#sm{i})"/>'''

letter_union = np.zeros_like(ink)
for g in groups[:FACE_FROM]:
    letter_union |= g["fill"]
face_union = np.zeros_like(ink)
for g in groups[FACE_FROM:]:
    face_union |= g["fill"]

LW = int(np.nonzero(letter_union.any(axis=0))[0].max()) + 6
fys, fxs = np.nonzero(face_union)
FX, FY = int(fxs.min()) - 4, int(fys.min()) - 4
FW, FH = int(fxs.max()) + 5 - FX, int(fys.max()) + 5 - FY

letter_chunks = [chunk(i, g) for i, g in enumerate(groups[:FACE_FROM])]
face_chunks = [chunk(FACE_FROM + i, g) for i, g in enumerate(groups[FACE_FROM:])]

svg = f'''<div id="sigstage" style="--lr:{LW/W:.4f};--fr:{FW/W:.4f};--fyr:{FY/W:.4f}">
<svg id="sig" viewBox="0 0 {LW} {H}" role="img" aria-label="Ted Kwee-Bintoro's signature" xmlns="http://www.w3.org/2000/svg">
{chr(10).join(letter_chunks)}
</svg>
<svg id="sigface" viewBox="{FX} {FY} {FW} {FH}" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
{chr(10).join(face_chunks)}
</svg>
</div>'''

html = open(f"{SITE}/index.html").read()
assert "<!--SIG_SVG-->" in html, "placeholder missing"
open(f"{SITE}/index.html", "w").write(html.replace("<!--SIG_SVG-->", svg))
print(f"injected {len(groups)} per-stroke fills, {len(svg)} chars")
print(f"lettering viewBox 0 0 {LW} {H}; face viewBox {FX} {FY} {FW} {FH}")
for g in groups:
    print(f'  {g["name"]}: mask w {g["svg_w"]}, ink px {int(g["fill"].sum())}')
