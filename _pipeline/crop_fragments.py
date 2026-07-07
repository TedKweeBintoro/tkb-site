"""Crop handwriting fragments from ink_layer.png.

Components are claimed exclusively by the first fragment (in priority order)
whose box contains the component centroid. Fragments marked dup=True claim
non-exclusively. Each fragment is rotated to level the baseline, trimmed,
saved as black-ink+alpha PNG. Writes manifest.json and a contact sheet.
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

SCRATCH = "/private/tmp/claude-501/-Users-tehsauscabe-tkb-site/6230281c-01e0-4204-958b-bd340df3e7d1/scratchpad"

ink = np.array(Image.open(f"{SCRATCH}/ink_layer.png"))[..., 3].astype(float) / 255.0

# name: (x0, y0, x1, y1, rot_deg, dup)
FRAGS = [
    ("period",         (250, 992,  298, 1040), -3.5, True),
    ("dotcom",         (150, 290,  580, 400), -4.0, False),   # y<=400: leaves the lower dot to instagram (i tittle)
    ("at",             (540,  55,  735, 295), -4.0, True),
    ("ted-at",         (100,  40,  720, 300), -4.0, False),
    ("tedkweebintoro", (690,  30, 1820, 300), -4.0, False),
    ("xcom",           (100, 830,  760, 1150), -3.5, False),
    ("linkedin",       (100, 600, 1400, 850), -5.0, False),
    ("instagram",      (130, 360, 1490, 660), -5.0, False),
    ("substack",       (130, 1220, 1270, 1480), -4.5, False),
]

solid = ink > 0.4
lbl, n = ndimage.label(solid, structure=np.ones((3, 3)))
cents = ndimage.center_of_mass(solid, lbl, range(1, n + 1))  # (y, x) per label
claimed = set()
manifest = {}

os.makedirs(f"{SCRATCH}/frags", exist_ok=True)

for name, (x0, y0, x1, y1), rot, dup in FRAGS:
    ids = []
    for i, (cy, cx) in enumerate(cents):
        if i + 1 in claimed and not dup:
            continue
        if x0 <= cx <= x1 and y0 <= cy <= y1:
            ids.append(i + 1)
    if not dup:
        claimed.update(ids)
    keep = np.isin(lbl, ids)
    sub_alpha = (ink * keep)[y0:y1, x0:x1]
    im = Image.fromarray((sub_alpha * 255).astype(np.uint8), "L")
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True, fillcolor=0)
    a = np.array(im).astype(float) / 255.0
    ys, xs = np.nonzero(a > 0.1)
    if len(ys) == 0:
        print(f"!! {name}: empty")
        continue
    t, b, l, r = ys.min(), ys.max(), xs.min(), xs.max()
    a = a[t:b + 1, l:r + 1]
    h, w = a.shape
    out = np.zeros((h, w, 4), np.uint8)
    out[..., 3] = (a * 255).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(f"{SCRATCH}/frags/{name}.png")
    lows = []
    for c in range(w):
        col = np.nonzero(a[:, c] > 0.3)[0]
        if len(col):
            lows.append(int(col.max()))
    lows.sort()
    core = lows[int(len(lows) * 0.15):int(len(lows) * 0.75)] or lows
    baseline = int(np.median(core))
    manifest[name] = {"w": w, "h": h, "baseline": baseline}
    print(f"{name}: {w}x{h} baseline={baseline} comps={len(ids)}")

json.dump(manifest, open(f"{SCRATCH}/frags/manifest.json", "w"), indent=1)

pad = 14
tot_h = sum(m["h"] + pad for m in manifest.values()) + pad
max_w = max(m["w"] for m in manifest.values()) + 2 * pad
sheet = Image.new("RGB", (max_w, tot_h), "white")
dr = ImageDraw.Draw(sheet)
y = pad
for name, m in manifest.items():
    fim = Image.open(f"{SCRATCH}/frags/{name}.png")
    sheet.paste(Image.new("RGB", fim.size, "black"), (pad, y), mask=fim.split()[3])
    dr.line([(0, y + m["baseline"]), (max_w, y + m["baseline"])], fill=(255, 0, 0), width=2)
    dr.text((2, y + 2), name, fill=(0, 120, 255))
    y += m["h"] + pad
sheet.save(f"{SCRATCH}/frags/_sheet.png")
print("sheet saved")
