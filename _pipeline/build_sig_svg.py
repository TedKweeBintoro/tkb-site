"""Generate the inline signature SVG with hand-authored stroke order.

Groups (one <path> each, drawn continuously; pen lifts between groups):
  T, ed, K-downstroke, rest-of-Kwee, hyphen, B-downstroke,
  rest-of-Bintoro (from top-left of B, through intoro),
  i-tittle, then the doodle: hair, head+ear, eyes, mouth, inner ear.
Fragment ids refer to sig_strokes.json; "NR" = fragment N reversed.
"""
import json

SCRATCH = "/private/tmp/claude-501/-Users-tehsauscabe-tkb-site/6230281c-01e0-4204-958b-bd340df3e7d1/scratchpad"
SITE = "/Users/tehsauscabe/tkb-site"

fill = open(f"{SCRATCH}/sig_fill.txt").read()
meta = json.load(open(f"{SCRATCH}/sig_strokes.json"))
frags = meta["strokes"]

# the B's spine, top to bottom (skeleton walk fragmented it; drawn by hand
# along the ink — the wide mask stroke absorbs the small offsets)
B_SPINE = [[476, 7], [468, 10], [464, 16], [465, 26], [471, 40], [473, 46],
           [468, 60], [461, 75], [454, 90], [449, 101], [447, 106]]

GROUPS = [
    ("T",        [0, 1, 2],                          0),
    ("ed",       [3, 4, 5, 6, 7],                    0),
    ("Kdown",    ["8R"],                             0),
    ("Kwee",     [11, 9, 10, 12, 13, 14, 15],        0),
    ("hyphen",   [19, 20, 18],                       0),
    ("Bdown",    ["SPINE"],                          0),
    ("Bintoro",  ["16R", 17, 21, 22, 23, "24R", 25, 26, 27, 28], 0),
    ("tittle",   [29],                               260),   # beat before the drawing
    ("hair",     [30, 31],                           0),
    ("headear",  [32],                               0),
    ("eyes",     [33, 34, 35],                       0),
    ("mouth",    [36],                               0),
    ("innerear", [37, 38],                           0),
]

def frag_pts(ref):
    if ref == "SPINE":
        return [list(map(float, p)) for p in B_SPINE], 13.0
    if isinstance(ref, str) and ref.endswith("R"):
        f = frags[int(ref[:-1])]
        return list(reversed(f["pts"])), f["w"]
    f = frags[ref]
    return f["pts"], f["w"]

paths = []
for name, parts, pause in GROUPS:
    pts_all, wmax = [], 0.0
    for ref in parts:
        pts, w = frag_pts(ref)
        wmax = max(wmax, w)
        pts_all.extend(pts)
    d = f"M{pts_all[0][0]},{pts_all[0][1]}" + "".join(
        f"L{x},{y}" for x, y in pts_all[1:])
    pause_attr = f' data-pause="{pause}"' if pause else ""
    paths.append(
        f'<path class="ms" data-g="{name}" d="{d}" stroke-width="{wmax}"{pause_attr}/>')

svg = f'''<svg id="sig" viewBox="0 0 {meta["w"]} {meta["h"]}" role="img" aria-label="Ted Kwee-Bintoro's signature, ending in a small self-portrait doodle" xmlns="http://www.w3.org/2000/svg">
<defs>
<mask id="sigmask" maskUnits="userSpaceOnUse" x="0" y="0" width="{meta["w"]}" height="{meta["h"]}">
<rect width="{meta["w"]}" height="{meta["h"]}" fill="#000"/>
<g stroke="#fff" fill="none" stroke-linecap="round" stroke-linejoin="round">
{chr(10).join(paths)}
</g>
</mask>
</defs>
<path id="sigfill" d="{fill}" fill="currentColor" fill-rule="evenodd" mask="url(#sigmask)"/>
</svg>'''

html = open(f"{SITE}/index.html").read()
assert "<!--SIG_SVG-->" in html, "placeholder missing"
open(f"{SITE}/index.html", "w").write(html.replace("<!--SIG_SVG-->", svg))
print("injected", len(paths), "grouped strokes,", len(svg), "chars")
