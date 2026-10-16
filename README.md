# tedkweebinto.ro

Personal site for Ted Kwee-Bintoro. Static — no build step.

- The opening signs the handwritten name stroke by stroke, completes `k` before
  `w`, dots the `i` last, then draws the face. Native Web Animations reveal SVG
  masks in pen order. The lettering comes from `images/handwriting/tedkweebintoro.png`;
  the face comes from `images/SignatureHQ.png`. Reduced motion skips the intro.
- The face doodle from the signature is the faint page background
  (`images/face.svg`, also the favicon).
- Body is set in [Redaction](https://www.redaction.us) (SIL OFL, see
  `assets/fonts/OFL.txt`), footnotes appear as tooltips.
- The footer assembles handwritten URL fragments (`images/handwriting/`) around
  a centered "tedkweebintoro"; hover or focus reveals each social/email link,
  while the center link returns to the canonical site URL.
- Personal email links to `ted@tedkweebinto.ro`. Its handwritten preview reuses
  `images/handwriting/period.png`, sized to match the `i` tittle's visual weight.
  The dot fades in beneath the `o`/`r` ligature, left of the `r` downstroke,
  without adding space or replacing the signature.

## Deploying to GitHub Pages

1. Push this repo to GitHub.
2. Settings → Pages → Source: **Deploy from a branch**, branch `main`, folder `/ (root)`.
3. The `CNAME` file points the site at `tedkweebinto.ro`. Configure the
   domain's DNS to GitHub Pages as usual.

`.nojekyll` is included so GitHub serves the files as-is.

## Local preview

```sh
python3 -m http.server 3000
# → http://localhost:3000
```
