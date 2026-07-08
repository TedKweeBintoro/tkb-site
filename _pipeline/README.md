# Asset pipeline

Scripts that generated the site's assets (run with a venv containing
pillow, numpy, scipy, scikit-image, potracer):

- trace_signature.py — vectorizes images/SignatureHQ.png, extracts stroke skeletons (sig_fill.txt + sig_strokes.json)
- build_sig_svg.py — hand-authored stroke order; injects the animated SVG into index.html at the <!--SIG_SVG--> placeholder
- crop_fragments.py — cuts the handwritten link fragments out of handwriting.jpg into images/handwriting/ (BW ink on alpha)
- assemble_katy.py — assembles 'katytechnologies' letter-by-letter from the same page (h = l+n, y = u+g-tail)
- make_ted_cut.py — derives images/handwriting/ted-cut.png from tedkweebintoro.png (k-descender erased inside the business "ted" crop window)
- katytechnologies.png — the assembled word (w:1273 h:182 baseline:120), NOT yet wired into the site (deferred)
- manifest.json — per-fragment width/height/baseline used for the CSS --fw/--fh/--fb values
