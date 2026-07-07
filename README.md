# tedkweebintoro.com

Personal site for Ted Kwee-Bintoro. Static — no build step.

- The signature signs itself on load (SVG mask animation over a potrace of
  `images/SignatureHQ.png`, stroke order hand-authored).
- The face doodle from the signature is the faint page background
  (`images/face.svg`, also the favicon).
- Body is set in [Redaction](https://www.redaction.us) (SIL OFL, see
  `assets/fonts/OFL.txt`), footnotes appear as tooltips.
- Footer links assemble handwritten URL fragments
  (`images/handwriting/`) around a centered "tedkweebintoro".

## Deploying to GitHub Pages

1. Push this repo to GitHub.
2. Settings → Pages → Source: **Deploy from a branch**, branch `main`, folder `/ (root)`.
3. The `CNAME` file points the site at `tedkweebintoro.com`; configure the
   domain's DNS to GitHub Pages as usual.

`.nojekyll` is included so GitHub serves the files as-is.

## Local preview

```sh
python3 -m http.server 3000
# → http://localhost:3000
```
