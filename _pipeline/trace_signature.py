"""Vectorize SignatureHQ.png and extract ordered pen strokes for a live-signing animation.

Outputs:
  sig_fill.txt      - SVG path data (potrace fill) of the signature
  sig_strokes.json  - ordered stroke polylines (pen traversal) + per-stroke mask widths
  preview_*.png     - visual checks
"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw
import potrace
from skimage.morphology import skeletonize
from scipy import ndimage

SCRATCH = "/private/tmp/claude-501/-Users-tehsauscabe-tkb-site/6230281c-01e0-4204-958b-bd340df3e7d1/scratchpad"

img = Image.open(f"{SCRATCH}/SignatureHQ.png").convert("RGBA")
W, H = img.size
arr = np.array(img)
alpha = arr[..., 3].astype(float) / 255.0
lum = arr[..., :3].astype(float).mean(axis=2)
# ink = dark AND visible; composite over white to handle either encoding
over_white = lum * alpha + 255.0 * (1 - alpha)
mask = over_white < 128
print("image", W, H, "ink px:", mask.sum(), f"({100*mask.mean():.1f}%)")

# ---------------- potrace fill path ----------------
bmp = potrace.Bitmap(~mask)  # potracer: 0 = black/foreground
plist = bmp.trace()

def fmt(p):
    return f"{p.x:.2f},{p.y:.2f}"

d_parts = []
for curve in plist:
    d_parts.append(f"M{fmt(curve.start_point)}")
    for seg in curve.segments:
        if seg.is_corner:
            d_parts.append(f"L{fmt(seg.c)}L{fmt(seg.end_point)}")
        else:
            d_parts.append(f"C{fmt(seg.c1)} {fmt(seg.c2)} {fmt(seg.end_point)}")
    d_parts.append("Z")
fill_d = "".join(d_parts)
open(f"{SCRATCH}/sig_fill.txt", "w").write(fill_d)
print("fill path chars:", len(fill_d), "curves:", len(plist.curves))

# ---------------- skeleton strokes ----------------
skel = skeletonize(mask)
dist = ndimage.distance_transform_edt(mask)

# label skeleton components; order left-to-right by min x (approximate signing order)
lbl, n = ndimage.label(skel, structure=np.ones((3, 3)))
comps = []
for i in range(1, n + 1):
    ys, xs = np.nonzero(lbl == i)
    comps.append((xs.min(), i, set(zip(ys.tolist(), xs.tolist()))))
comps.sort()
print("skeleton components:", n)

NBRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

def neighbors(p, pts):
    y, x = p
    return [(y + dy, x + dx) for dy, dx in NBRS if (y + dy, x + dx) in pts]

strokes = []  # list of [(x,y), ...] in pen order
for minx, ci, pts in comps:
    if len(pts) < 3:
        # tiny dot (e.g. an 'i' dot): emit as a micro stroke
        p = next(iter(pts))
        strokes.append([(p[1], p[0]), (p[1] + 0.5, p[0])])
        continue
    deg = {p: len(neighbors(p, pts)) for p in pts}
    unvisited = set(pts)
    while unvisited:
        # start at leftmost degree-1 point among unvisited, else leftmost point
        ends = [p for p in unvisited if sum(1 for q in neighbors(p, pts) if q in unvisited) <= 1]
        if ends:
            start = min(ends, key=lambda p: (p[1], p[0]))
        else:
            start = min(unvisited, key=lambda p: (p[1], p[0]))
        path = [start]
        unvisited.discard(start)
        cur = start
        prev_dir = None
        while True:
            nxt_opts = [q for q in neighbors(cur, pts) if q in unvisited]
            if not nxt_opts:
                break
            if prev_dir is not None:
                # prefer continuing in the same direction (smooth pen motion)
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

print("raw strokes:", len(strokes), "total pts:", sum(len(s) for s in strokes))

# ---- merge tiny fragments into neighbors & simplify (RDP) ----
def rdp(points, eps):
    if len(points) < 3:
        return points
    pts_np = np.array(points, dtype=float)
    keep = np.zeros(len(pts_np), dtype=bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts_np) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        seg = pts_np[b] - pts_np[a]
        L = np.hypot(*seg)
        rel = pts_np[a + 1:b] - pts_np[a]
        if L == 0:
            d = np.hypot(rel[:, 0], rel[:, 1])
        else:
            d = np.abs(seg[0] * rel[:, 1] - seg[1] * rel[:, 0]) / L
        i = np.argmax(d)
        if d[i] > eps:
            idx = a + 1 + i
            keep[idx] = True
            stack.extend([(a, idx), (idx, b)])
    return [tuple(p) for p in pts_np[keep]]

def slen(s):
    return sum(np.hypot(s[i + 1][0] - s[i][0], s[i + 1][1] - s[i][1]) for i in range(len(s) - 1))

strokes = [rdp(s, 0.75) for s in strokes]

# stroke mask width: 2 * max ink radius along the stroke + margin
out = []
for s in strokes:
    rs = []
    for (x, y) in s:
        xi, yi = int(round(x)), int(round(y))
        if 0 <= yi < H and 0 <= xi < W:
            rs.append(dist[yi, xi])
    wmax = (max(rs) if rs else 2.0) * 2.0 + 2.5
    out.append({"pts": [[round(x, 1), round(y, 1)] for x, y in s],
                "w": round(float(wmax), 1), "len": round(float(slen(s)), 1)})

json.dump({"w": W, "h": H, "strokes": out}, open(f"{SCRATCH}/sig_strokes.json", "w"))
total_len = sum(o["len"] for o in out)
print("final strokes:", len(out), "total len:", round(total_len))

# ---------------- previews ----------------
# 1. skeleton order preview: color gradient by order
prev = Image.new("RGB", (W, H), "white")
dr = ImageDraw.Draw(prev)
acc = 0.0
for o in out:
    pts = o["pts"]
    for i in range(len(pts) - 1):
        t = acc / total_len
        col = (int(255 * t), 60, int(255 * (1 - t)))
        dr.line([tuple(pts[i]), tuple(pts[i + 1])], fill=col, width=2)
        acc += float(np.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
prev.save(f"{SCRATCH}/preview_order.png")
print("previews saved")
