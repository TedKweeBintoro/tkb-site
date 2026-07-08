"""Skeleton-trace the lowercase tedkweebintoro handwriting into ordered fragments.

Same walker as trace_signature.py, pointed at the footer word PNG
(black ink on alpha). Emits word_strokes.json + an annotated preview.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from skimage.morphology import skeletonize
from scipy import ndimage

SCRATCH = "/private/tmp/claude-501/-Users-tehsauscabe-tkb-site/6230281c-01e0-4204-958b-bd340df3e7d1/scratchpad"
SITE = "/Users/tehsauscabe/tkb-site"

img = Image.open(f"{SITE}/images/handwriting/tedkweebintoro.png").convert("RGBA")
W, H = img.size
mask = np.array(img)[..., 3] > 128
print("word", W, H, "ink px:", int(mask.sum()), f"({100*mask.mean():.1f}%)")

lbl, ncomp = ndimage.label(mask, structure=np.ones((3, 3)))
print("ink components:", ncomp)
for i in range(1, ncomp + 1):
    ys, xs = np.nonzero(lbl == i)
    print(f"  comp {i}: x {xs.min()}..{xs.max()}  y {ys.min()}..{ys.max()}  px {len(xs)}")

skel = skeletonize(mask)
dist = ndimage.distance_transform_edt(mask)

slbl, n = ndimage.label(skel, structure=np.ones((3, 3)))
comps = []
for i in range(1, n + 1):
    ys, xs = np.nonzero(slbl == i)
    comps.append((xs.min(), i, set(zip(ys.tolist(), xs.tolist()))))
comps.sort()

NBRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

def neighbors(p, pts):
    y, x = p
    return [(y + dy, x + dx) for dy, dx in NBRS if (y + dy, x + dx) in pts]

strokes = []
for minx, ci, pts in comps:
    if len(pts) < 3:
        p = next(iter(pts))
        strokes.append([(p[1], p[0]), (p[1] + 0.5, p[0])])
        continue
    unvisited = set(pts)
    while unvisited:
        ends = [p for p in unvisited if sum(1 for q in neighbors(p, pts) if q in unvisited) <= 1]
        start = min(ends, key=lambda p: (p[1], p[0])) if ends else min(unvisited, key=lambda p: (p[1], p[0]))
        path = [start]
        unvisited.discard(start)
        cur = start
        prev_dir = None
        while True:
            nxt_opts = [q for q in neighbors(cur, pts) if q in unvisited]
            if not nxt_opts:
                break
            if prev_dir is not None:
                def turn_cost(q):
                    d = (q[0] - cur[0], q[1] - cur[1])
                    return -(d[0] * prev_dir[0] + d[1] * prev_dir[1])
                nxt = min(nxt_opts, key=turn_cost)
            else:
                nxt = nxt_opts[0]
            prev_dir = (nxt[0] - cur[0], nxt[1] - cur[1])
            path.append(nxt)
            unvisited.discard(nxt)
            cur = nxt
        if len(path) >= 2:
            strokes.append([(x, y) for (y, x) in path])
        elif len(path) == 1:
            x, y = path[0][1], path[0][0]
            strokes.append([(x, y), (x + 0.5, y)])

def rdp(points, eps):
    if len(points) < 3:
        return points
    P = np.array(points, dtype=float)
    keep = np.zeros(len(P), dtype=bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(P) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        seg = P[b] - P[a]
        L = np.hypot(*seg)
        rel = P[a + 1:b] - P[a]
        d = np.hypot(rel[:, 0], rel[:, 1]) if L == 0 else np.abs(seg[0] * rel[:, 1] - seg[1] * rel[:, 0]) / L
        i = np.argmax(d)
        if d[i] > eps:
            idx = a + 1 + i
            keep[idx] = True
            stack.extend([(a, idx), (idx, b)])
    return [tuple(p) for p in P[keep]]

def slen(s):
    return sum(np.hypot(s[i + 1][0] - s[i][0], s[i + 1][1] - s[i][1]) for i in range(len(s) - 1))

strokes = [rdp(s, 0.75) for s in strokes]

out = []
for s in strokes:
    rs = [dist[int(round(y)), int(round(x))] for (x, y) in s
          if 0 <= int(round(y)) < H and 0 <= int(round(x)) < W]
    wmax = (max(rs) if rs else 2.0) * 2.0 + 2.5
    out.append({"pts": [[round(x, 1), round(y, 1)] for x, y in s],
                "w": round(float(wmax), 1), "len": round(float(slen(s)), 1)})

json.dump({"w": W, "h": H, "strokes": out}, open(f"{SCRATCH}/word_strokes.json", "w"))
print("fragments:", len(out))
for i, o in enumerate(out):
    xs = [p[0] for p in o["pts"]]; ys = [p[1] for p in o["pts"]]
    print(f"  f{i}: len {o['len']:7.1f}  w {o['w']:4.1f}  "
          f"start ({o['pts'][0][0]:.0f},{o['pts'][0][1]:.0f}) end ({o['pts'][-1][0]:.0f},{o['pts'][-1][1]:.0f})  "
          f"x {min(xs):.0f}..{max(xs):.0f} y {min(ys):.0f}..{max(ys):.0f}")

# annotated preview at 2x: ink grey, fragments coloured, numbered at start point
prev = Image.new("RGB", (W * 2, H * 2), "white")
base = (np.array(img)[..., 3][:, :, None] * np.array([0.82, 0.82, 0.82])).astype(np.uint8)
ghost = Image.fromarray(255 - base).resize((W * 2, H * 2), Image.NEAREST)
prev.paste(ghost, (0, 0))
dr = ImageDraw.Draw(prev)
cols = [(220, 40, 40), (30, 120, 220), (30, 160, 60), (230, 130, 20), (150, 40, 200),
        (200, 40, 140), (20, 170, 170), (120, 100, 30), (60, 60, 220), (240, 80, 80)]
for i, o in enumerate(out):
    c = cols[i % len(cols)]
    P = [(x * 2, y * 2) for x, y in o["pts"]]
    for a, b in zip(P, P[1:]):
        dr.line([a, b], fill=c, width=2)
    dr.ellipse([P[0][0] - 4, P[0][1] - 4, P[0][0] + 4, P[0][1] + 4], outline=c, width=2)
    dr.text((P[0][0] + 5, P[0][1] - 14), f"f{i}", fill=c)
prev.save(f"{SCRATCH}/word_order.png")
print("preview saved")
