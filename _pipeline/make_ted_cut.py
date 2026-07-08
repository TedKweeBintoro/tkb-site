"""ted-cut.png — tedkweebintoro.png with the k-downstroke remnant erased.

The business-email hover crops the centre word to its first --fcut (348) px
("ted"). The k's big descender re-enters that window below the d (x 300-348,
y > 86) and dangles there as a stray line, so this variant blanks it. The
erase box runs past the cut edge (x 361) so the chop lands in the hidden
region, not mid-stroke.
"""
from PIL import Image
import numpy as np

SITE = "/Users/tehsauscabe/tkb-site"

im = Image.open(f"{SITE}/images/handwriting/tedkweebintoro.png").convert("RGBA")
a = np.array(im)
before = int((a[..., 3] > 10).sum())
a[86:, 295:361, 3] = 0
after = int((a[..., 3] > 10).sum())
Image.fromarray(a).save(f"{SITE}/images/handwriting/ted-cut.png")
print(f"erased {before - after} ink px -> images/handwriting/ted-cut.png")

# render a check image of the visible window (x < 348) over white
alpha = a[:, :348, 3:4].astype(float) / 255
rgb = a[:, :348, :3].astype(float) * alpha + 255 * (1 - alpha)
chk = Image.fromarray(rgb.astype(np.uint8))
chk = chk.resize((chk.width * 2, chk.height * 2), Image.NEAREST)
chk.save("/private/tmp/claude-501/-Users-tehsauscabe-tkb-site/6230281c-01e0-4204-958b-bd340df3e7d1/scratchpad/ted_cut_check.png")
