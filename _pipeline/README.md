# Asset pipeline

Scripts that generated the site's assets (run with a venv containing
pillow, numpy, scipy, scikit-image, potracer):

- trace_signature.py — vectorizes images/SignatureHQ.png, extracts stroke skeletons (sig_fill.txt + sig_strokes.json)
- build_sig_svg.py — the FORMAL signature builder (superseded as the opening, kept for reference)
- trace_word.py — skeleton-traces images/handwriting/tedkweebintoro.png into fragments (word_strokes.json)
- build_word_svg.py — the CURRENT opening: lowercase word (3 pen runs + tittle) composed with the
  SignatureHQ face doodle (scaled 1.25); injects at the <!--SIG_SVG--> placeholder (restore it first)
- crop_fragments.py — cuts the handwritten link fragments out of handwriting.jpg into images/handwriting/ (BW ink on alpha)
- assemble_katy.py — assembles 'katytechnologies' letter-by-letter from the same page (h = l+n, y = u+g-tail)
- katytechnologies.png — the assembled word (w:1273 h:182 baseline:120), NOT yet wired into the site (deferred)
- manifest.json — per-fragment width/height/baseline used for the CSS --fw/--fh/--fb values
