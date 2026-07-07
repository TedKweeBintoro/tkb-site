"""Assemble handwritten "katytechnologies" from individual letters in ink_layer.png.

Letters are cropped, deskewed by their source line's angle, trimmed, and placed
on a shared baseline with per-letter kerning. h = l+n composite, y = u+g-tail.
Output: frags/katytechnologies.png + preview.
"""
import json
import numpy as np
from PIL import Image

SCRATCH = "/private/tmp/claude-501/-Users-tehsauscabe-tkb-site/6230281c-01e0-4204-958b-bd340df3e7d1/scratchpad"
ink = np.array(Image.open(f"{SCRATCH}/ink_layer.png"))[..., 3].astype(float) / 255.0

# letter sources: box (x0,y0,x1,y1) in ink_layer coords, rot = line deskew angle
LETTERS = {
    "k":  ((368, 612, 466, 788), -5.0),   # linkedin
    "a":  ((656, 1298, 734, 1428), -4.5), # substack 'a' (below t crossbar)
    "t":  ((546, 1243, 650, 1428), -4.5), # substack 't'
    "u":  ((258, 1290, 342, 1430), -4.5), # substack 'u' (for y)
    "gt": ((572, 478, 660, 580), -5.0),   # instagram g descender tail (for y)
    "e":  ((424, 685, 470, 778), -5.0),   # linkedin 'e'
    "c":  ((292, 942, 372, 1032), -3.5),  # xcom 'c'
    "l":  ((136, 640, 220, 778), -5.0),   # linkedin 'l' (for h and l)
    "n":  ((248, 690, 336, 778), -5.0),   # linkedin 'n' (for h and n)
    "o":  ((386, 933, 452, 1008), -3.5),  # xcom 'o'
    "g":  ((563, 425, 662, 580), -5.0),   # instagram 'g'
    "i":  ((202, 632, 250, 778), -5.0),   # linkedin 'i' with dot
    "s":  ((205, 1295, 265, 1425), -4.5), # substack lead 's'
}

def crop(box, rot):
    x0, y0, x1, y1 = box
    sub = (ink[y0:y1, x0:x1] * 255).astype(np.uint8)
    im = Image.fromarray(sub, "L")
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True, fillcolor=0)
    a = np.array(im).astype(float) / 255.0
    ys, xs = np.nonzero(a > 0.1)
    if not len(ys):
        raise SystemExit(f"empty crop {box}")
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

glyphs = {k: crop(b, r) for k, (b, r) in LETTERS.items()}

# composites ------------------------------------------------------------
def canvas_paste(cv, g, x, y):
    h, w = g.shape
    H, W = cv.shape
    x, y = int(x), int(y)
    cv[y:y + h, x:x + w] = np.maximum(cv[y:y + h, x:x + w], g[:max(0, min(h, H - y)), :max(0, min(w, W - x))])

# h = l + n  (n tucked at l's right, sharing baseline)
l_g, n_g = glyphs["l"], glyphs["n"]
h_h = max(l_g.shape[0], n_g.shape[0])
h_w = l_g.shape[1] + n_g.shape[1] - 8
cv = np.zeros((h_h, h_w + 4))
canvas_paste(cv, l_g, 0, h_h - l_g.shape[0])
canvas_paste(cv, n_g, l_g.shape[1] - 8, h_h - n_g.shape[0])
glyphs["h"] = cv

# y = u + g-tail (tail hangs below-right of u)
u_g, gt = glyphs["u"], glyphs["gt"]
y_w = max(u_g.shape[1], gt.shape[1] + 6)
y_h = u_g.shape[0] + gt.shape[0] - 26
cv = np.zeros((y_h, y_w))
canvas_paste(cv, u_g, 0, 0)
canvas_paste(cv, gt, max(0, u_g.shape[1] - gt.shape[1] - 2), u_g.shape[0] - 26)
glyphs["y"] = cv

# descender depth below baseline per glyph (px in glyph space)
DESC = {"g": 62, "y": 58, "gt": 0}
# manual per-letter kern (px, applied before the letter)
KERN = {"default": -6}

WORD = "katytechnologies"
seq = list(WORD)
imgs = [glyphs[ch] for ch in seq]
baselines = [g.shape[0] - DESC.get(ch, 0) for ch, g in zip(seq, imgs)]

BL = max(baselines) + 4
depth = max(g.shape[0] - b for g, b in zip(imgs, baselines))
H = BL + depth + 4
W = sum(g.shape[1] for g in imgs) + 40
cvs = np.zeros((H, W))
x = 4
for ch, g, b in zip(seq, imgs, baselines):
    x += KERN.get(ch, KERN["default"])
    canvas_paste(cvs, g, max(0, x), BL - b)
    x += g.shape[1]

ys, xs = np.nonzero(cvs > 0.1)
t, b_, l_, r_ = ys.min(), ys.max(), xs.min(), xs.max()
final = cvs[t:b_ + 1, l_:r_ + 1]
fh, fw = final.shape
out = np.zeros((fh, fw, 4), np.uint8)
out[..., 3] = (np.clip(final, 0, 1) * 255).astype(np.uint8)
Image.fromarray(out, "RGBA").save(f"{SCRATCH}/frags/katytechnologies.png")

man = json.load(open(f"{SCRATCH}/frags/manifest.json"))
man["katytechnologies"] = {"w": fw, "h": fh, "baseline": int(BL - t)}
json.dump(man, open(f"{SCRATCH}/frags/manifest.json", "w"), indent=1)

prev = Image.new("RGB", (fw + 20, fh + 20), "white")
prev.paste(Image.new("RGB", (fw, fh), "black"), (10, 10),
           mask=Image.fromarray((final * 255).astype(np.uint8)))
prev.save(f"{SCRATCH}/frags/_katy_preview.png")
print("katytechnologies:", fw, "x", fh, "baseline", int(BL - t))
