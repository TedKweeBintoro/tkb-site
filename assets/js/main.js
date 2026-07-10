/* Ted Kwee-Bintoro — live signing + colophon interactions */
(function () {
  "use strict";

  var body = document.body;
  var sig = document.getElementById("sig");
  var face = document.getElementById("sigface");
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ── the closing line, drawn fresh each visit ────────────────────── */

  var closer = document.getElementById("bio-close");
  if (closer) {
    var closers = [
      "Sometimes I write.",
      "I don’t have a driver’s license yet, so I have to scooter everywhere.",
      "I’ve been trying to be more concise lately.",
      "Every day is a cultural revolution if you lack taste.",
      "I bought FSD for my Tesla and it ran over my foot.",
      "I was dropped on my head as a baby but not on any of the important cortexes.",
      "At the end of the day, there is night.",
      "I am an Asian-passing white man.",
      "In 2016, I was the Democratic nominee for president, becoming the first woman to win a presidential nomination by a major U.S. political party and the first woman to win the popular vote for U.S. president.",
      "Sometimes people get upset when I do “the accent.”"
    ];
    /* shuffle-bag: every sentence appears once before any repeats */
    var bag = [];
    function refillBag() {
      bag = closers.slice();
      for (var i = bag.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var t = bag[i]; bag[i] = bag[j]; bag[j] = t;
      }
    }
    var current = "";
    function nextText() {
      if (!bag.length) {
        refillBag();
        /* never repeat the sentence currently shown */
        if (bag.length > 1 && bag[bag.length - 1] === current) {
          bag[bag.length - 1] = bag[0];
          bag[0] = current;
        }
      }
      current = bag.pop();
      return current
        .replace(/\bI /g, "I\u00A0");   /* the bio never strands a lone I */
    }
    /* one span per character, so the line can erase and retype itself */
    function renderCloser(text, hidden) {
      closer.textContent = "";
      for (var i = 0; i < text.length; i++) {
        var ch = document.createElement("span");
        ch.className = "ch";
        ch.textContent = text.charAt(i);
        if (hidden) { ch.style.opacity = "0"; ch.style.display = "none"; }
        closer.appendChild(ch);
      }
    }
    var FADE = 12;   /* matches the .ch opacity transition */
    var STEP = 12;   /* each character takes 0.012s, so longer lines take longer */
    /* time-based ticker: an rAF chain paints smoothly while the tab is
       active, and a slow interval finishes the job if frames stall
       (background tabs throttle rAF); apply(t) returns true while busy */
    function drive(apply, done) {
      var start = performance.now();
      var ended = false;
      function settle() {
        ended = true;
        window.clearInterval(wd);
        done();
      }
      function frame() {
        if (ended) return;
        if (apply(performance.now() - start)) requestAnimationFrame(frame);
        else settle();
      }
      var wd = window.setInterval(function () {
        if (!ended && !apply(performance.now() - start)) settle();
      }, 120);
      requestAnimationFrame(frame);
    }
    /* erase: each character fades, then gives up its space, so the text
       after the closer walks back in step with the backspacing */
    function erase(done) {
      var chars = closer.querySelectorAll(".ch");
      var n = chars.length || 1;
      var step = STEP;
      drive(function (t) {
        var busy = false;
        for (var i = 0; i < chars.length; i++) {
          var at = (n - 1 - i) * step;   /* the last character goes first */
          var c = chars[i];
          if (t >= at + FADE) {
            if (c.style.display !== "none") c.style.display = "none";
          } else {
            busy = true;
            if (t >= at) c.style.opacity = "0";
          }
        }
        return busy;
      }, done);
    }
    /* type: each character takes its space, then fades in */
    function type(done) {
      var chars = closer.querySelectorAll(".ch");
      var step = STEP;
      drive(function (t) {
        var busy = false;
        for (var i = 0; i < chars.length; i++) {
          var c = chars[i];
          if (t < i * step) { busy = true; }
          else if (c.style.display === "none") { c.style.display = ""; busy = true; }
          else if (c.style.opacity !== "1") { c.style.opacity = "1"; busy = true; }
        }
        return busy;
      }, function () {
        window.setTimeout(done, FADE);   /* let the last fade land */
      });
    }
    /* a click backspaces the old line away, pauses, then types the new one in */
    var swapping = false;
    function swapCloser() {
      if (swapping) return;
      if (reduced) { renderCloser(nextText(), false); return; }
      swapping = true;
      erase(function () {
        window.setTimeout(function () {
          renderCloser(nextText(), true);
          type(function () { swapping = false; });
        }, 500);
      });
    }
    renderCloser(nextText(), false);
    closer.setAttribute("role", "button");
    closer.setAttribute("tabindex", "0");
    closer.setAttribute("aria-label", "Show another closing line");
    closer.addEventListener("click", swapCloser);
    closer.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); swapCloser(); }
    });
  }

  /* ── layout: face centred on the essay, essay no wider than the words ── */

  var essay = document.querySelector(".essay");
  var pageEl = document.getElementById("page");
  var colophon = document.querySelector(".colophon");
  var wordEls = Array.prototype.slice.call(document.querySelectorAll(".word"));

  function layout() {
    /* small screens: cap the essay at the width of the row of words */
    if (essay) {
      if (window.matchMedia("(max-width: 720px)").matches && wordEls.length) {
        var l = Infinity, r = -Infinity;
        wordEls.forEach(function (w) {
          var b = w.getBoundingClientRect();
          if (b.left < l) l = b.left;
          if (b.right > r) r = b.right;
        });
        if (r > l) essay.style.maxWidth = r - l + "px";
      } else {
        essay.style.maxWidth = "";
      }
    }
    /* the background face sits on the essay block's vertical centre
       (row 1 of #page; heights are transform-free layout metrics) */
    if (pageEl && colophon) {
      var y = pageEl.getBoundingClientRect().top +
        (pageEl.clientHeight - colophon.offsetHeight) / 2;
      document.documentElement.style.setProperty("--facey", y + "px");
    }
  }
  window.addEventListener("resize", layout);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(layout);
  layout();

  /* ── the signing ─────────────────────────────────────────────────── */

  var strokes = Array.prototype.slice.call(
    document.querySelectorAll("#sigstage .ms")
  );
  var done = false;

  function finish(skipFlip) {
    if (done) return;
    done = true;
    strokes.forEach(function (p) {
      p.style.strokeDashoffset = 0;
      p.style.strokeOpacity = 1;
    });
    /* drop the masks entirely: the finished signature is the plain fills */
    Array.prototype.forEach.call(document.querySelectorAll("#sigstage .sf"),
      function (f) { f.removeAttribute("mask"); });

    if (skipFlip || reduced || !sig || !face) {
      body.classList.remove("intro");
      layout();
      return;
    }
    var firstS = sig.getBoundingClientRect();
    var firstF = face.getBoundingClientRect();
    body.classList.remove("intro");
    layout();   /* place the face before measuring its landing spot */
    var lastS = sig.getBoundingClientRect();
    var lastF = face.getBoundingClientRect();

    /* the lettering flies up to the header */
    var dx = firstS.left + firstS.width / 2 - (lastS.left + lastS.width / 2);
    var dy = firstS.top + firstS.height / 2 - (lastS.top + lastS.height / 2);
    var sc = firstS.width / lastS.width;
    sig.style.transformOrigin = "center";
    sig.style.transform =
      "translate(" + dx + "px," + dy + "px) scale(" + sc + ")";

    /* the face drifts into the background and fades; its resting state
       already carries translate(-50%,-50%), so compose around it */
    var fdx = firstF.left + firstF.width / 2 - (lastF.left + lastF.width / 2);
    var fdy = firstF.top + firstF.height / 2 - (lastF.top + lastF.height / 2);
    var fsc = firstF.width / lastF.width;
    face.style.transform = "translate(calc(-50% + " + fdx + "px), calc(-50% + " +
      fdy + "px)) scale(" + fsc + ")";
    face.style.opacity = 1;

    var wrap = document.getElementById("sigwrap");
    if (wrap) wrap.classList.add("flying");   /* don't clip the flight */
    void sig.getBoundingClientRect();
    sig.classList.add("flipping");
    face.classList.add("flipping");
    sig.style.transform = "";
    face.style.transform = "";
    face.style.opacity = "";
    sig.addEventListener("transitionend", function te() {
      sig.classList.remove("flipping");
      if (wrap) wrap.classList.remove("flying");
      sig.removeEventListener("transitionend", te);
    });
    face.addEventListener("transitionend", function tf(e) {
      if (e.propertyName !== "opacity") return;
      face.classList.remove("flipping");
      face.removeEventListener("transitionend", tf);
    });
  }

  function sign() {
    if (!strokes.length || reduced) { finish(true); return; }

    var lens = strokes.map(function (p) { return p.getTotalLength(); });
    strokes.forEach(function (p, i) {
      p.style.strokeDasharray = lens[i] + " " + lens[i];
      p.style.strokeDashoffset = lens[i];
      /* round caps paint zero-length dash dots at subpath starts; keep
         strokes invisible until the pen reaches them */
      p.style.strokeOpacity = 0;
    });

    var WORD_MS = 500;   /* the signature writes in half a second */
    var FACE_MS = 1000;  /* the face takes the full second */
    var SETTLE = 500;    /* beat before the page comes in */

    /* every line starts at t0; the signature's lines complete at WORD_MS,
       the face's at FACE_MS, each drawn at its own pace */
    var durs = strokes.map(function (p) {
      return p.closest("#sigface") ? FACE_MS : WORD_MS;
    });
    var TOTAL = Math.max(WORD_MS, FACE_MS);

    var t0 = null;
    function frame(ts) {
      if (done) return;
      if (t0 === null) t0 = ts;
      var elapsed = ts - t0;

      for (var k = 0; k < strokes.length; k++) {
        var f = Math.max(0, Math.min(1, elapsed / durs[k]));
        strokes[k].style.strokeDashoffset = lens[k] * (1 - f);
        strokes[k].style.strokeOpacity = 1;
      }

      if (elapsed >= TOTAL) {
        window.setTimeout(function () { finish(false); }, SETTLE);
        return;
      }
      window.requestAnimationFrame(frame);
    }
    window.requestAnimationFrame(frame);

    /* escape hatches: click to skip, hard cap in case of jank */
    document.addEventListener("pointerdown", function () { finish(false); }, { once: true });
    window.setTimeout(function () { finish(false); }, 4000);
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
  var words = wordEls;
  var restHref = "https://tedkweebintoro.com";
  var goTimer = null;   /* touch: pending redirect */

  function cancelGo() {
    if (goTimer) { window.clearTimeout(goTimer); goTimer = null; }
  }

  function activate(word) {
    words.forEach(function (w) { w.classList.toggle("on", w === word); });
    if (!word) {
      cancelGo();
      delete hw.dataset.active;
      hw.style.removeProperty("--hc");
      hw.setAttribute("href", restHref);
      hw.setAttribute("aria-label", "tedkweebintoro");
      return;
    }
    hw.dataset.active = word.dataset.net;
    hw.style.setProperty("--hc", word.style.getPropertyValue("--c"));
    hw.setAttribute("href", word.getAttribute("href"));
    hw.setAttribute("aria-label", word.textContent.replace(/\s+/g, " ") + " — " + word.getAttribute("href"));
  }

  words.forEach(function (word) {
    word.addEventListener("mouseenter", function () {
      word.__enterAt = performance.now();
      activate(word);
    });
    word.addEventListener("focus", function () { activate(word); });
    word.addEventListener("blur", function () { activate(null); });
    word.addEventListener("click", function (e) {
      /* touch devices and phone-width windows: a tap writes the address
         out, holds it a beat, then follows the link */
      var compact = window.matchMedia("(hover: none)").matches ||
                    window.matchMedia("(max-width: 720px)").matches;
      if (!compact) return;
      /* a hover that has been open a while means the address is already
         on show — follow the link straight away (a tap's synthetic
         mouseenter lands just before its click) */
      var sameGesture = performance.now() - (word.__enterAt || 0) < 700;
      if (!sameGesture && hw.dataset.active === word.dataset.net) return;
      e.preventDefault();
      cancelGo();
      activate(word);
      var href = word.getAttribute("href");
      goTimer = window.setTimeout(function () {
        goTimer = null;
        window.location.href = href;
      }, 1450);   /* 450ms reveal + a 1s hold */
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
