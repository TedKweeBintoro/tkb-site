"""Round-2 fragment surgery:
- dotcom: remove bottom tick of the leading period (+1px speck)
- substack: erase the pen-rest nub at the lead-in tail start
- instagram: raise the trailing slash to sit with the text
- linkedin: raise the sagging "/in/" cluster
- katytechnologies: downscale to match notebook-page x-height
Re-trims each image, recomputes manifest, writes preview sheet + HTML vars.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

SCRATCH = "/private/tmp/claude-501/-Users-tehsauscabe-tkb-site/6230281c-01e0-4204-958b-bd340df3e7d1/scratchpad"
F = f"{SCRATCH}/frags"

def load(name):
    return np.array(Image.open(f"{F}/{name}.png"))[..., 3].astype(float) / 255.0

def comps(a):
    lbl, n = ndimage.label(a > 0.04, structure=np.ones((3, 3)))
    return lbl, n

def shift_xy(a, mask, dx, dy):
    """move pixels under mask by (dx, dy) in image coords, erase original."""
    src = a * mask
    a = a * (~mask)
    moved = np.roll(np.roll(src, dy, axis=0), dx, axis=1)
    if dy > 0: moved[:dy, :] = 0
    elif dy < 0: moved[dy:, :] = 0
    if dx > 0: moved[:, :dx] = 0
    elif dx < 0: moved[:, dx:] = 0
    return np.maximum(a, moved)

def trim(a):
    ys, xs = np.nonzero(a > 0.06)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

def save(name, a, baseline_row):
    a = np.clip(a, 0, 1)
    h, w = a.shape
    out = np.zeros((h, w, 4), np.uint8)
    out[..., 3] = (a * 255).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(f"{F}/{name}.png")
    return {"w": int(w), "h": int(h), "baseline": int(baseline_row)}

def auto_baseline(a, x0f=0.15, x1f=0.75):
    h, w = a.shape
    lows = []
    for c in range(int(w * x0f), int(w * x1f)):
        col = np.nonzero(a[:, c] > 0.3)[0]
        if len(col):
            lows.append(int(col.max()))
    lows.sort()
    core = lows[int(len(lows) * 0.15):int(len(lows) * 0.75)] or lows
    return int(np.median(core))

man = json.load(open(f"{F}/manifest.json"))

# ---- dotcom: drop bottom tick (bottom-left comp) + specks ----
a = load("dotcom")
lbl, n = comps(a)
for i, sl in enumerate(ndimage.find_objects(lbl)):
    ys, xs = sl
    sz = (lbl[sl] == i + 1).sum()
    if sz < 5 or (xs.start < 25 and ys.start > 70):   # speck / bottom tick
        a[lbl == i + 1] = 0
old_top = np.nonzero((a > 0.06).any(axis=1))[0].min()
a = trim(a)
man["dotcom"] = save("dotcom", a, man["dotcom"]["baseline"] - old_top)

# ---- substack: erase pen-rest nub at tail start ----
a = load("substack")
a[112:, :22] = 0
a = trim(a)   # trim shouldn't change origin (word body remains)
man["substack"] = save("substack", a, man["substack"]["baseline"])

# ---- instagram: raise slash (rightmost tall comp) ----
a = load("instagram")
lbl, n = comps(a)
RAISE_SLASH = 62
for i, sl in enumerate(ndimage.find_objects(lbl)):
    ys, xs = sl
    if xs.start >= 1000 and (ys.stop - ys.start) > 120:   # the slash
        a = shift_xy(a, lbl == i + 1, 0, -RAISE_SLASH)
        break
old_top = np.nonzero((a > 0.06).any(axis=1))[0].min()
a = trim(a)
man["instagram"] = save("instagram", a, man["instagram"]["baseline"] - old_top)

# ---- linkedin: raise /in/, lift the word, drop .com down-left (centered) ----
a = load("linkedin")
lbl, n = comps(a)
m_word = np.zeros_like(a, dtype=bool)
m_com = np.zeros_like(a, dtype=bool)
m_in = np.zeros_like(a, dtype=bool)
for i, sl in enumerate(ndimage.find_objects(lbl)):
    ys, xs = sl
    if xs.start < 550:
        m_word |= (lbl == i + 1)
    elif xs.start < 745:
        m_com |= (lbl == i + 1)
    else:
        m_in |= (lbl == i + 1)
a = shift_xy(a, m_word, 0, -8)
a = shift_xy(a, m_com, -20, 9)
a = shift_xy(a, m_in, 0, -46)
old_top = np.nonzero((a > 0.06).any(axis=1))[0].min()
a = trim(a)
man["linkedin"] = save("linkedin", a, man["linkedin"]["baseline"] - 8 - old_top)

# ---- katytechnologies: downscale to notebook x-height ----
SCALE = 0.70
im = Image.open(f"{F}/katytechnologies.png")
assert im.height > 300, "katy already scaled — re-extract first"
nw, nh = int(im.width * SCALE), int(im.height * SCALE)
im = im.resize((nw, nh), Image.LANCZOS)
a = np.array(im)[..., 3].astype(float) / 255.0
a = trim(a)
kb = auto_baseline(a, 0.30, 0.55)
man["katytechnologies"] = save("katytechnologies", a, kb)

json.dump(man, open(f"{F}/manifest.json", "w"), indent=1)

# ---- preview sheet with baselines ----
names = ["dotcom", "substack", "instagram", "linkedin", "katytechnologies"]
pad = 14
tot_h = sum(man[n]["h"] + pad for n in names) + pad
max_w = max(man[n]["w"] for n in names) + 2 * pad
sheet = Image.new("RGB", (max_w, tot_h), "white")
dr = ImageDraw.Draw(sheet)
y = pad
for n in names:
    m = man[n]
    fim = Image.open(f"{F}/{n}.png")
    sheet.paste(Image.new("RGB", fim.size, "black"), (pad, y), mask=fim.split()[3])
    dr.line([(0, y + m["baseline"]), (max_w, y + m["baseline"])], fill=(255, 0, 0), width=2)
    dr.text((2, y + 2), n, fill=(0, 120, 255))
    y += m["h"] + pad
sheet.save(f"{F}/_fix_sheet.png")

for n in names:
    m = man[n]
    print(f'{n}: --fw:{m["w"]};--fh:{m["h"]};--fb:{m["h"] - m["baseline"]}')
