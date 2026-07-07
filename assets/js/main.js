/* Ted Kwee-Bintoro — live signing + colophon interactions */
(function () {
  "use strict";

  var body = document.body;
  var sig = document.getElementById("sig");
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ── the signing ─────────────────────────────────────────────────── */

  var strokes = Array.prototype.slice.call(
    document.querySelectorAll("#sigmask .ms")
  );
  var done = false;

  function finish(skipFlip) {
    if (done) return;
    done = true;
    strokes.forEach(function (p) { p.style.strokeDashoffset = 0; });

    if (skipFlip || reduced || !sig) {
      body.classList.remove("intro");
      return;
    }
    var first = sig.getBoundingClientRect();
    body.classList.remove("intro");
    var last = sig.getBoundingClientRect();
    var dx = first.left + first.width / 2 - (last.left + last.width / 2);
    var dy = first.top + first.height / 2 - (last.top + last.height / 2);
    var sc = first.width / last.width;
    sig.style.transformOrigin = "center";
    sig.style.transform =
      "translate(" + dx + "px," + dy + "px) scale(" + sc + ")";
    void sig.getBoundingClientRect();
    sig.classList.add("flipping");
    sig.style.transform = "";
    sig.addEventListener("transitionend", function te() {
      sig.classList.remove("flipping");
      sig.removeEventListener("transitionend", te);
    });
  }

  function sign() {
    if (!strokes.length || reduced) { finish(true); return; }

    var lens = strokes.map(function (p) { return p.getTotalLength(); });
    var pauses = strokes.map(function (p) {
      return Number(p.getAttribute("data-pause")) || 0;
    });
    strokes.forEach(function (p, i) {
      p.style.strokeDasharray = lens[i] + " " + lens[i];
      p.style.strokeDashoffset = lens[i];
    });

    var SPEED = 1050;      /* px of ink per second */
    var LIFT = 90;         /* ms pen-lift between strokes */
    var t0 = null;

    function frame(ts) {
      if (done) return;
      if (t0 === null) t0 = ts;
      var elapsed = ts - t0;
      var travelled = 0;
      var i = 0;

      while (i < strokes.length) {
        var need = (lens[i] / SPEED) * 1000 + LIFT + pauses[i];
        if (elapsed < travelled + need) break;
        travelled += need;
        i++;
      }

      if (i >= strokes.length) {
        window.setTimeout(function () { finish(false); }, 180);
        return;
      }

      var local = Math.max(0, elapsed - travelled);
      var dist = Math.min(lens[i], (local / 1000) * SPEED);

      for (var k = 0; k < strokes.length; k++) {
        strokes[k].style.strokeDashoffset =
          k < i ? 0 : k === i ? lens[k] - dist : lens[k];
      }
      window.requestAnimationFrame(frame);
    }
    window.requestAnimationFrame(frame);

    /* escape hatches: click to skip, hard cap in case of jank */
    document.addEventListener("pointerdown", function () { finish(false); }, { once: true });
    window.setTimeout(function () { finish(false); }, 8000);
  }

  function start() {
    if (!document.hidden) { sign(); return; }
    /* background tab: hold the signing until it's actually watched */
    document.addEventListener("visibilitychange", function once() {
      if (!document.hidden) {
        document.removeEventListener("visibilitychange", once);
        sign();
      }
    });
  }
  if (document.readyState === "complete") start();
  else window.addEventListener("load", start);

  /* ── footnote tooltips ───────────────────────────────────────────── */

  var refs = Array.prototype.slice.call(document.querySelectorAll(".snref"));

  function closeTips(except) {
    refs.forEach(function (r) { if (r !== except) r.classList.remove("open"); });
  }
  refs.forEach(function (ref) {
    ref.addEventListener("click", function (e) {
      e.preventDefault();
      var was = ref.classList.contains("open");
      closeTips(null);
      ref.classList.toggle("open", !was);
    });
    /* keep tooltips on screen: nudge horizontally if they'd overflow */
    ref.addEventListener("mouseenter", nudge(ref));
    ref.addEventListener("focus", nudge(ref));
  });
  function nudge(ref) {
    return function () {
      var tip = ref.querySelector(".tip");
      if (!tip) return;
      tip.style.setProperty("--shift", "0px");
      var r = tip.getBoundingClientRect();
      var pad = 10;
      var shift = 0;
      if (r.left < pad) shift = pad - r.left;
      else if (r.right > window.innerWidth - pad) shift = window.innerWidth - pad - r.right;
      if (shift) tip.style.setProperty("--shift", shift + "px");
    };
  }
  document.addEventListener("pointerdown", function (e) {
    if (!e.target.closest(".snref")) closeTips(null);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeTips(null);
  });

  /* ── colophon: reveal the handwritten address ────────────────────── */

  var hw = document.getElementById("hw");
  var words = Array.prototype.slice.call(document.querySelectorAll(".word"));
  var restHref = "https://tedkweebintoro.com";

  function activate(word) {
    words.forEach(function (w) { w.classList.toggle("on", w === word); });
    if (!word) {
      delete hw.dataset.active;
      hw.setAttribute("href", restHref);
      hw.setAttribute("aria-label", "tedkweebintoro");
      return;
    }
    hw.dataset.active = word.dataset.net;
    hw.setAttribute("href", word.getAttribute("href"));
    hw.setAttribute("aria-label", word.textContent.replace(/\s+/g, " ") + " — " + word.getAttribute("href"));
  }

  words.forEach(function (word) {
    word.addEventListener("mouseenter", function () { activate(word); });
    word.addEventListener("focus", function () { activate(word); });
    word.addEventListener("blur", function () { activate(null); });
    word.addEventListener("click", function (e) {
      /* first tap on touch devices previews; second follows the link */
      if (!word.classList.contains("on") && window.matchMedia("(hover: none)").matches) {
        e.preventDefault();
        activate(word);
      }
    });
  });

  var wordsRow = document.querySelector(".words");
  if (wordsRow) {
    wordsRow.addEventListener("mouseleave", function () { activate(null); });
  }
  document.addEventListener("pointerdown", function (e) {
    if (!e.target.closest(".words") && !e.target.closest(".hw")) activate(null);
  });
})();
