"""Render the social preview card: the face doodle, on parchment, distressed —
the site's palette and inkgrain look, baked into a 1200x630 PNG.

Rasterizes images/face.svg's vector path (evenodd fill) at supersample for
crisp edges, then applies an edge-displacement + speckle distress that
approximates the site's #inkgrain SVG filter, over the --paper parchment.
Output: images/og-card.png
"""
import re
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

SITE = "/Users/tehsauscabe/tkb-site"
W, H = 1200, 630
SS = 3                      # supersample factor for the vector fill
PAPER = (250, 246, 236)     # --paper #faf6ec
INK = (17, 17, 16)          # --ink #111110

# ---- parse the face path ---------------------------------------------------
svg = open(f"{SITE}/images/face.svg").read()
vb = re.search(r'viewBox="([\d.\- ]+)"', svg).group(1).split()
VBW, VBH = float(vb[2]), float(vb[3])
d = re.search(r'\bd="([^"]+)"', svg).group(1)

# tokenize: command letters + numbers
toks = re.findall(r"[MLCZmlcz]|-?\d*\.?\d+", d)

def bezier(p0, p1, p2, p3, n=28):
    t = np.linspace(0, 1, n)[:, None]
    mt = 1 - t
    pts = (mt**3) * p0 + 3 * (mt**2) * t * p1 + 3 * mt * (t**2) * p2 + (t**3) * p3
    return [tuple(pt) for pt in pts]

subpaths, cur, start = [], [], (0.0, 0.0)
pos = (0.0, 0.0)
i = 0
while i < len(toks):
    c = toks[i]; i += 1
    if c in "Mm":
        if cur:
            subpaths.append(cur)
        x, y = float(toks[i]), float(toks[i + 1]); i += 2
        pos = (x, y) if c == "M" else (pos[0] + x, pos[1] + y)
        start = pos; cur = [pos]
    elif c in "Ll":
        x, y = float(toks[i]), float(toks[i + 1]); i += 2
        pos = (x, y) if c == "L" else (pos[0] + x, pos[1] + y)
        cur.append(pos)
    elif c in "Cc":
        vals = list(map(float, toks[i:i + 6])); i += 6
        if c == "c":
            vals = [vals[0] + pos[0], vals[1] + pos[1], vals[2] + pos[0],
                    vals[3] + pos[1], vals[4] + pos[0], vals[5] + pos[1]]
        p1, p2, p3 = (vals[0], vals[1]), (vals[2], vals[3]), (vals[4], vals[5])
        cur.extend(bezier(np.array(pos), np.array(p1), np.array(p2), np.array(p3))[1:])
        pos = p3
    elif c in "Zz":
        cur.append(start); pos = start

if cur:
    subpaths.append(cur)
print(f"face: {len(subpaths)} subpaths, viewBox {VBW}x{VBH}")

# ---- place the face: ~60% of card width, centred -------------------------
target_w = 0.60 * W
scale = target_w / VBW
fw, fh = VBW * scale, VBH * scale
ox = (W - fw) / 2
oy = (H - fh) / 2 - 6            # a hair above centre

def to_canvas(pt):
    return ((pt[0] * scale + ox) * SS, (pt[1] * scale + oy) * SS)

# ---- evenodd rasterise at supersample ------------------------------------
cover = np.zeros((H * SS, W * SS), dtype=bool)
for sp in subpaths:
    im = Image.new("1", (W * SS, H * SS), 0)
    ImageDraw.Draw(im).polygon([to_canvas(p) for p in sp], fill=1)
    cover ^= np.array(im, dtype=bool)      # evenodd = XOR of subpath interiors

# downsample to AA coverage 0..1
cov = np.array(Image.fromarray((cover * 255).astype(np.uint8))
               .resize((W, H), Image.LANCZOS)).astype(float) / 255.0

# ---- distress: edge displacement + speckle (approximates #inkgrain) -------
rng = np.random.default_rng(11)
yy, xx = np.mgrid[0:H, 0:W].astype(float)
warp = ndimage.gaussian_filter(rng.standard_normal((H, W)), 3.0)
warp2 = ndimage.gaussian_filter(rng.standard_normal((H, W)), 3.0)
amp = 2.2
cov = ndimage.map_coordinates(cov, [yy + warp * amp, xx + warp2 * amp],
                              order=1, mode="constant")

# speckle: sparse dry-brush pinholes inside the ink
spk = rng.random((H, W))
holes = (spk < 0.05) & (cov > 0.35)
cov[holes] *= 0.12
# a touch of overall tooth
cov *= (0.90 + 0.10 * ndimage.gaussian_filter(rng.random((H, W)), 0.5))
cov = np.clip(cov, 0, 1)

# ---- parchment background: paper + grain + warm vignette ------------------
bg = np.zeros((H, W, 3), float) + np.array(PAPER, float)
grain = ndimage.gaussian_filter(rng.standard_normal((H, W)), 0.6)[..., None]
bg += grain * np.array([5.0, 4.0, 2.0])          # subtle warm tooth
mottle = ndimage.gaussian_filter(rng.standard_normal((H, W)), 40)[..., None]
bg += mottle * np.array([6.0, 5.0, 3.0])
# vignette
r = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
vig = np.clip((r - 0.55) / 0.6, 0, 1)[..., None]
bg -= vig * np.array([16.0, 15.0, 11.0])
bg = np.clip(bg, 0, 255)

# ---- composite ink over parchment ----------------------------------------
a = cov[..., None]
out = bg * (1 - a) + np.array(INK, float) * a
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB").save(
    f"{SITE}/images/og-card.png")
print(f"wrote images/og-card.png ({W}x{H}), ink px {int((cov>0.5).sum())}")
