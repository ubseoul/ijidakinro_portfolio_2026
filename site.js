/* ijidakinro.com interactions: small, smooth, and off when the visitor asks for less motion. */
(function () {
  "use strict";
  var root = document.documentElement;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var $ = function (s, el) { return (el || document).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); };

  function ready() { document.body.classList.add("ready"); }
  requestAnimationFrame(function () { requestAnimationFrame(ready); });
  setTimeout(ready, 400);   // fallback when frames are throttled

  /* theme */
  var toggle = $("[data-theme-toggle]");
  if (toggle) toggle.addEventListener("click", function () {
    var dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("theme", root.dataset.theme); } catch (e) {}
  });

  /* header + progress */
  var top = $(".top"), bar = $(".progress"), ticking = false;
  function onScroll() {
    var y = window.scrollY, h = document.documentElement.scrollHeight - innerHeight;
    top.classList.toggle("scrolled", y > 8);
    bar.style.transform = "scaleX(" + (h > 0 ? Math.min(1, y / h) : 0) + ")";
    ticking = false;
  }
  addEventListener("scroll", function () { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  onScroll();

  /* mobile menu */
  var menuBtn = $("[data-menu]"), mnav = $("#mnav");
  if (menuBtn) {
    menuBtn.addEventListener("click", function () {
      var open = mnav.hidden;
      mnav.hidden = !open;
      menuBtn.setAttribute("aria-expanded", String(open));
    });
    $$("#mnav a").forEach(function (a) { a.addEventListener("click", function () { mnav.hidden = true; menuBtn.setAttribute("aria-expanded", "false"); }); });
  }

  /* active section in nav */
  var navLinks = $$(".nav a");
  var spy = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) navLinks.forEach(function (a) { a.classList.toggle("on", a.getAttribute("href") === "#" + en.target.id); });
    });
  }, { rootMargin: "-45% 0px -50% 0px" });
  ["case", "experience", "lanes", "work", "lab"].forEach(function (id) { var el = document.getElementById(id); if (el) spy.observe(el); });

  /* reveal + count-up */
  function countUp(el) {
    var end = +el.dataset.count, t0 = null, dur = 1400;
    if (reduce) { el.textContent = end.toLocaleString(); return; }
    function step(t) {
      if (!t0) t0 = t;
      var p = Math.min(1, (t - t0) / dur), eased = 1 - Math.pow(1 - p, 4);
      el.textContent = Math.round(end * eased).toLocaleString();
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (!en.isIntersecting) return;
      en.target.classList.add("in");
      $$("[data-count]", en.target).forEach(countUp);
      io.unobserve(en.target);
    });
  }, { threshold: 0.08, rootMargin: "0px 0px -4% 0px" });
  $$(".reveal").forEach(function (el) { io.observe(el); });

  /* magnetic buttons */
  if (!reduce && matchMedia("(hover: hover)").matches) {
    $$("[data-magnetic]").forEach(function (b) {
      b.addEventListener("mousemove", function (ev) {
        var r = b.getBoundingClientRect();
        b.style.transform = "translate(" + ((ev.clientX - r.left - r.width / 2) * 0.18) + "px," + ((ev.clientY - r.top - r.height / 2) * 0.28) + "px)";
      });
      b.addEventListener("mouseleave", function () { b.style.transform = ""; });
    });
  }

  /* platform cards: soft light follows the cursor */
  $$(".plat").forEach(function (c) {
    c.addEventListener("mousemove", function (ev) {
      var r = c.getBoundingClientRect();
      c.style.setProperty("--mx", (ev.clientX - r.left) + "px");
      c.style.setProperty("--my", (ev.clientY - r.top) + "px");
    });
  });

  /* the octopus: eyes follow the cursor, the body leans a little, a click makes it wave */
  var octo = $(".octo");
  if (octo) {
    var pupils = $$(".pupil", octo), tilt = $(".tilt", octo);
    var base = pupils.map(function (p) { return { x: +p.getAttribute("cx"), y: +p.getAttribute("cy") }; });
    var raf = 0, mx = 0, my = 0;
    function look() {
      raf = 0;
      var r = octo.getBoundingClientRect();
      var cx = r.left + r.width / 2, cy = r.top + r.height * 0.35;
      var dx = mx - cx, dy = my - cy, d = Math.hypot(dx, dy) || 1, k = Math.min(1, d / 400);
      pupils.forEach(function (p) { p.style.transform = "translate(" + (dx / d * 1.25 * k) + "px," + (dy / d * 1.1 * k) + "px)"; });
      if (!reduce) tilt.style.transform = "rotate(" + Math.max(-5, Math.min(5, dx / 120)) + "deg)";
    }
    addEventListener("pointermove", function (ev) { mx = ev.clientX; my = ev.clientY; if (!raf) raf = requestAnimationFrame(look); }, { passive: true });
    function wave() {
      if (reduce) return;
      octo.classList.remove("wave"); void octo.getBoundingClientRect(); octo.classList.add("wave");
      setTimeout(function () { octo.classList.remove("wave"); }, 1500);
    }
    octo.addEventListener("click", wave);
    setTimeout(wave, 1600);
  }

  /* segmented controls: a pill slides under the active button */
  function placePill(group, btn) {
    var pill = $(".pill", group);
    if (!pill || !btn) return;
    pill.style.width = btn.offsetWidth + "px";
    pill.style.transform = "translateX(" + (btn.offsetLeft - 4) + "px)";
  }

  /* lanes (tabs) */
  var seg = $(".seg");
  if (seg) {
    var tabs = $$("[role=tab]", seg);
    function select(tab, focus) {
      tabs.forEach(function (t) {
        var on = t === tab, panel = document.getElementById(t.getAttribute("aria-controls"));
        t.setAttribute("aria-selected", String(on));
        t.tabIndex = on ? 0 : -1;
        if (on && panel.hidden) { panel.hidden = false; panel.classList.remove("enter"); void panel.offsetWidth; panel.classList.add("enter"); }
        else if (!on) panel.hidden = true;
      });
      placePill(seg, tab);
      if (focus) tab.focus();
    }
    tabs.forEach(function (t, i) {
      t.addEventListener("click", function () { select(t); });
      t.addEventListener("keydown", function (ev) {
        var d = ev.key === "ArrowRight" ? 1 : ev.key === "ArrowLeft" ? -1 : 0;
        if (d) { ev.preventDefault(); select(tabs[(i + d + tabs.length) % tabs.length], true); }
      });
    });
    placePill(seg, $("[aria-selected=true]", seg));
    addEventListener("resize", function () { placePill(seg, $("[aria-selected=true]", seg)); });
  }

  /* work rows */
  $$(".row > button").forEach(function (b) {
    b.addEventListener("click", function () {
      var row = b.parentElement, open = !row.classList.contains("open");
      row.classList.toggle("open", open);
      b.setAttribute("aria-expanded", String(open));
    });
  });

  /* ---------- the system map ---------- */
  var MAP = {
    v1: {
      caption: "v1 · the first build (the Overlord system): an interactive web app, unreleased",
      nodes: {
        me: ["Human", "Me", "Creator + approver"], brain: ["Claude Opus", "Decision-maker", "(the Overlord)"],
        gate: ["Gate", "Duplicate check", "(the Canon Clerk)"], plan: ["ChatGPT", "Planner", "(the Underlord)"],
        a1: ["Claude Sonnet", "Sole merger"], a2: ["Codex", "Builder"], a3: ["Gemini", "Smoke tests"], a4: ["DeepSeek", "Research"],
        out: ["GitHub", "Output", "the code"]
      },
      detail: {
        me: ["Human · creator and PM", "Me", "I set the intent, answered the creator questions, and carried every packet between agents by copy-paste. Each packet opened with one line telling me what I had to do, or “nothing.”", "Protect the human's attention: decisions only, never status."],
        brain: ["Claude Opus", "Decision-maker (the Overlord)", "Ruled on design, quality and the eight phase gates, from first build to release candidate: 30+ written rulings. The standing habit was to verify claims against the real repo before ruling.", "Rule from the source, never from memory. One memory-based ruling had to be withdrawn."],
        gate: ["Gate", "Duplicate check (the Canon Clerk)", "First stop for anything headed to the Overlord: is this already written, or already ruled? Duplicate questions stopped here instead of costing a ruling.", "Put cheap checks in front of expensive judgment."],
        plan: ["ChatGPT", "Planner (the Underlord)", "Turned rulings into build packets for the agents, ran the board and reported back. Its status reports understated problems three times.", "Evidence over status. Failures go in the headline."],
        a1: ["Claude Sonnet", "Sole merger", "Only one agent could merge to the trunk, so parallel work never fought over the same code.", "One merge authority beats clever conflict resolution."],
        a2: ["Codex", "Builder", "Built pieces on their own branches and stayed on call as the reserve builder when capacity ran short. It never merged.", "Keep a second builder warm; keep the merge key in one place."],
        a3: ["Gemini", "Smoke tests", "Smoke-tested finished pieces before they could move forward. The core loop passed before it was integrated.", "The tester should be a different model than the builder."],
        a4: ["DeepSeek", "Research", "Cheap, wide research and source checks that fed the planner.", "Spend expensive models on judgment, cheap ones on breadth."],
        out: ["GitHub", "Output", "349 commits across 90 branches in 14 days, with a triage ledger: every finding fixed, kept on purpose, waiting on a source, or deferred. A release candidate needs zero untriaged items.", "Every finding gets a status and a reason. Nothing ships untriaged."]
      }
    },
    v2: {
      caption: "v2 · the lean rebuild (the Kitchen): lanes, a usage meter and human approval",
      nodes: {
        me: ["Human", "Me", "≤ 3 pings a week"], brain: ["Brief + ledger", "One-page brief", "(the Executive Chef)"],
        gate: ["Board", "Ticket board", "Ranked by value ÷ size"], plan: ["Lanes + meter", "One lane per platform", "Stops at 12% left"],
        a1: ["Codex", "Runner"], a2: ["Gemini · Antigravity", "Research + documents"], a3: ["DeepSeek", "Research briefs"], a4: ["Claude", "Strategy + review"],
        out: ["Output", "Reviewed work", "One commit per ticket"]
      },
      detail: {
        me: ["Human · approver", "Me", "I answer a short question list and approve anything that leaves. Agents act on my behalf only up to a written delegation level, and they can ping me three times a week at most, bundled.", "Busy isn't done. Ask the human first, then cook."],
        brain: ["Brief + ledger", "One-page brief (the Executive Chef)", "A one-page brief and a ledger of written rulings. Every agent reads the brief, the board and one station file, instead of 58 KB of rules.", "Context is a cost. Make it one page."],
        gate: ["Board", "Ticket board", "Each ticket carries value, urgency and size; agents pull the highest value for the effort first (WSJF). One commit per finished ticket, bookkeeping once at handoff.", "The shared board went from about 6.9K to 2.4K tokens, and every agent got faster."],
        plan: ["Lanes + meter", "One lane per platform", "Each platform owns its lanes, so there's nothing to claim and nothing to collide. A script reads the real usage meter: pause when the 5-hour window runs low, stop at 12% of the week.", "A five-agent run once burned 98% of a 5-hour window in one night. Runs stop themselves now."],
        a1: ["Codex", "Runner", "Long unattended runs on my PC that stop on the meter, one session per repo.", "Even the best runner needs a stop rule."],
        a2: ["Gemini · Antigravity", "Research + documents", "Research lanes and longer documents, checked against sources and a shared fact file.", "Verify a fact once, then reuse it for 14 days."],
        a3: ["DeepSeek", "Research briefs", "Wide research briefs at low cost. Another agent reviews and commits them.", "Separate the thinking from the committing."],
        a4: ["Claude", "Strategy + review", "Strategy, reviews and high-stakes writing, including the usage study that led to v2.", "The reviewer shouldn't be the runner."],
        out: ["Output", "Reviewed work", "Finished tickets, one commit each, with bookkeeping done once at handoff. Nothing is sent, signed or bought without me.", "A ticket isn't done until it meets its written definition of done."]
      }
    }
  };

  var map = $(".map");
  if (map) {
    var card = $(".map-card"), svg = $("svg.wires", map), cols = $(".cols", map), detail = $(".detail");
    var sw = $(".switch"), swBtns = $$("button", sw), caption = $(".map-foot .caption");
    var version = "v1", active = "brain", auto = true, autoTimer = 0, visible = false;
    var order = ["me", "brain", "gate", "plan", "a1", "a2", "a3", "a4", "out"];
    var edges = [], packets = [];
    var NS = "http://www.w3.org/2000/svg";

    function fill(v) {
      var data = MAP[v];
      $$(".node", map).forEach(function (n) {
        var d = data.nodes[n.dataset.node], s = $$(".swap > span", n);
        s[0].textContent = d[0]; s[1].textContent = d[1]; if (s[2]) s[2].textContent = d[2] || "";
      });
      caption.textContent = data.caption;
    }
    function showDetail(id, animate) {
      active = id;
      $$(".node", map).forEach(function (n) { n.classList.toggle("on", n.dataset.node === id); });
      var d = MAP[version].detail[id];
      function put() {
        $(".who .k", detail).textContent = d[0]; $(".who h3", detail).textContent = d[1];
        $(".body .text", detail).textContent = d[2]; $(".body .lesson", detail).textContent = d[3];
      }
      if (animate && !reduce) { detail.classList.add("swapping"); setTimeout(function () { put(); detail.classList.remove("swapping"); }, 220); }
      else put();
      edges.forEach(function (e) { e.el.classList.toggle("hot", e.a === id || e.b === id); });
    }
    function center(el, side) {
      var r = el.getBoundingClientRect(), m = cols.getBoundingClientRect();
      var x = r.left - m.left, y = r.top - m.top;
      if (side === "r") return [x + r.width, y + r.height / 2];
      if (side === "l") return [x, y + r.height / 2];
      if (side === "b") return [x + r.width / 2, y + r.height];
      return [x + r.width / 2, y];
    }
    function draw() {
      while (svg.firstChild) svg.removeChild(svg.firstChild);
      edges = []; packets = [];
      var colEls = $$(".col", cols);
      var vertical = colEls.length > 1 && colEls[1].getBoundingClientRect().top > colEls[0].getBoundingClientRect().bottom - 2;
      var m = cols.getBoundingClientRect();
      svg.setAttribute("viewBox", "0 0 " + m.width + " " + m.height);
      for (var c = 0; c < colEls.length - 1; c++) {
        $$(".node", colEls[c]).forEach(function (a) {
          $$(".node", colEls[c + 1]).forEach(function (b) {
            var p, q, d;
            var sameRow = Math.abs(a.getBoundingClientRect().top - b.getBoundingClientRect().top) < 8;
            if (vertical && !sameRow) {
              p = center(a, "b"); q = center(b, "t");
              var my = (p[1] + q[1]) / 2;
              d = "M" + p[0] + " " + p[1] + "C" + p[0] + " " + my + " " + q[0] + " " + my + " " + q[0] + " " + q[1];
            } else {
              p = center(a, "r"); q = center(b, "l");
              if (q[0] < p[0]) { p = center(a, "b"); q = center(b, "t"); var my2 = (p[1] + q[1]) / 2; d = "M" + p[0] + " " + p[1] + "C" + p[0] + " " + my2 + " " + q[0] + " " + my2 + " " + q[0] + " " + q[1]; }
              else { var mx = (p[0] + q[0]) / 2; d = "M" + p[0] + " " + p[1] + "C" + mx + " " + p[1] + " " + mx + " " + q[1] + " " + q[0] + " " + q[1]; }
            }
            var path = document.createElementNS(NS, "path");
            path.setAttribute("d", d);
            svg.appendChild(path);
            var e = { el: path, a: a.dataset.node, b: b.dataset.node, len: 0 };
            edges.push(e);
            if (!reduce) {
              var dot = document.createElementNS(NS, "circle");
              dot.setAttribute("r", "2.6");
              svg.appendChild(dot);
              packets.push({ edge: e, dot: dot, t: Math.random(), speed: 0.0028 + Math.random() * 0.0024 });
            }
          });
        });
      }
      edges.forEach(function (e) { e.len = e.el.getTotalLength(); e.el.classList.toggle("hot", e.a === active || e.b === active); });
    }
    function tick() {
      if (visible) packets.forEach(function (p) {
        p.t += p.speed; if (p.t > 1) p.t -= 1;
        var pt = p.edge.el.getPointAtLength(p.t * p.edge.len);
        p.dot.setAttribute("cx", pt.x); p.dot.setAttribute("cy", pt.y);
        p.dot.style.opacity = Math.sin(p.t * Math.PI).toFixed(2);
      });
      requestAnimationFrame(tick);
    }
    function setVersion(v) {
      if (v === version) return;
      version = v;
      swBtns.forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.v === v)); });
      placePill(sw, $("[aria-pressed=true]", sw));
      map.classList.add("switching");
      setTimeout(function () { fill(v); map.dataset.version = v; showDetail(active, false); map.classList.remove("switching"); requestAnimationFrame(draw); }, reduce ? 0 : 260);
    }
    function stopAuto() { auto = false; clearInterval(autoTimer); }
    swBtns.forEach(function (b) { b.addEventListener("click", function () { stopAuto(); setVersion(b.dataset.v); }); });
    $$(".node", map).forEach(function (n) { n.addEventListener("click", function () { stopAuto(); showDetail(n.dataset.node, true); }); });

    fill(version);
    showDetail(active, false);
    placePill(sw, $("[aria-pressed=true]", sw));
    new IntersectionObserver(function (en) {
      visible = en[0].isIntersecting;
      if (visible && auto && !autoTimer && !reduce) {
        autoTimer = setInterval(function () {
          if (!auto) return;
          showDetail(order[(order.indexOf(active) + 1) % order.length], true);
        }, 4200);
      }
    }, { threshold: 0.25 }).observe(card);
    var rt = 0;
    addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(function () { draw(); placePill(sw, $("[aria-pressed=true]", sw)); }, 120); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { draw(); placePill(sw, $("[aria-pressed=true]", sw)); if (seg) placePill(seg, $("[aria-selected=true]", seg)); });
    draw();
    requestAnimationFrame(tick);
  }
})();
