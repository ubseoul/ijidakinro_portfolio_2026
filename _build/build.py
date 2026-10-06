"""Builds index.html and the brand assets for ijidakinro.com.

  python _build/build.py            # index.html + assets/octo.svg + assets/favicon.svg
  python _build/build.py --images   # also favicon PNGs and og.png (needs Chrome)
  python _build/build.py --release  # publishable: unconfirmed [[CONFIRM]] facts are left out instead of shown as notes

Every number on the page is sourced (see SOURCES at the bottom). Change a fact here, not in index.html."""
import html
import os
import re
import subprocess
import sys
import tempfile

import octo

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
ASSETS = os.path.join(SITE, "assets")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
e = html.escape

MARQUEE = ["Claude Opus", "Claude Sonnet", "Claude Code", "ChatGPT", "Codex", "Gemini", "Antigravity", "DeepSeek",
           "Python", "Streamlit", "Supabase", "GitHub", "JavaScript", "SQL", "Figma", "Agile / Scrum",
           "Articulate Rise", "Qualtrics", "Jira"]

PLATFORMS = [
    ("Judgment · rulings · merges", "Claude",
     "Best at careful judgment and clean merges, so it held the rulings and the only merge key. It also ruled from memory once, and the ruling had to be withdrawn.",
     "Cite the source before ruling. One model merges; the others propose."),
    ("Planning · long runs", "ChatGPT + Codex",
     "A tireless planner and runner. Its status reports understated problems three times, and a five-agent run burned 98% of a 5-hour window in one night.",
     "Evidence over status. One session per lane, and every run stops on the meter."),
    ("Testing · research · documents", "Gemini + Antigravity",
     "A strong second opinion. It ran the smoke tests on finished pieces, and handled research and longer documents in long solo runs.",
     "Don't let the builder test its own work. Give testing to a different model."),
    ("Wide research, low cost", "DeepSeek",
     "Fast and cheap for breadth: market scans, source checks and research briefs. It ran a full shift until it hit the meter line.",
     "Spend expensive models on judgment and cheap ones on breadth. Research arrives as a brief; another agent commits it."),
]

# Lessons (the Lab): the rule now comes first, the failure that produced it second, and the headline number is the win.
EXPERIMENTS = [
    ("L-01", "Runs stop themselves",
     "Five agents coordinating through claims and heartbeats used 98% of a 5-hour usage window in one night.",
     "−65%", "tokens on the shared board every agent reads",
     "A script reads the real usage meter and stops each run before the limit. Each platform works its own lane, with one commit per finished ticket.",
     [("before", "6.9K", 1.0, True), ("after", "2.4K", 2.4 / 6.9, False)], "tokens on the shared board"),
    ("L-02", "Evidence over status",
     "The planning agent's status reports understated problems three separate times.",
     "3", "understated reports caught by checking the work itself",
     "Reports lead with failures and attach evidence. I check the work, not the summary.", None, None),
    ("L-03", "Rule from the source",
     "A design ruling made from memory instead of the written source had to be withdrawn.",
     "1 → gate", "one withdrawn ruling led to a check-first gate",
     "A check-first gate asks “already written or already ruled?” before anything reaches the decision-maker, and rulings cite their source.", None, None),
    ("L-04", "Ask the human first",
     "Agents drafted all night while the work waited on five answers only I could give.",
     "10 min", "question list that unblocked a full night's held work",
     "The queue asks me first, and a ping budget caps interruptions at three a week.", None, None),
]

# A body is either one paragraph or a list of (label, text) rows. [[CONFIRM: ...]] marks a fact Ube still has to supply;
# it shows as a dashed "To confirm" note and the build lists it. Don't publish while any remain.
CASE = {
    "rows": [
        ("Bottleneck", "Building a course took about three weeks. [[CONFIRM: which steps took the longest before the change?]]"),
        ("My role", "I translated the existing course-production process into a structured, AI-supported workflow in Claude Code, "
                    "used across multiple instructional teams. AI speeds up scripting, voiceover and asset production."),
        ("Adoption", "I drove adoption with the instructional design team: training, plus the guides, tip sheets, FAQs and support "
                     "documentation the teams use to run the workflow. [[CONFIRM: how many designers or teams use it, and how many "
                     "courses have shipped through it?]]"),
        ("Human review", "[[CONFIRM: who reviews AI-assisted drafts, at which step, and against what standard?]]"),
        ("Result", "Course-creation time fell from about three weeks to 4–7 days, 66–80% faster, for courses reaching 200+ students."),
    ],
    "stats": [("3 weeks → 4–7 days", "Course-creation time, 66–80% faster"),
              ("200+", "Students reached by courses built this way")],
    "chips": ["Claude Code", "Instructional design", "Change management", "Guides · tip sheets · FAQs"],
}

WORK = [
    ("Build With AI", "A workshop on auditing AI-generated learning content", "Learning · Workshop",
     "I designed, facilitated and evaluated a 75-minute workshop built on one framework: Frame → Generate → Audit → Log. In a "
     "two-person pilot, both participants caught more planted flaws with the audit checklist than without it. Evaluated at "
     "Kirkpatrick levels 1–3; level 4 wasn't measurable at pilot size.",
     ["Needs analysis", "Action mapping", "Kirkpatrick evaluation", "Articulate Rise"],
     [("build-with-ai.html", "Case study"), ("assets/facilitator-guide.pdf", "Facilitator guide (PDF)"),
      ("assets/participant-workbook.pdf", "Participant workbook (PDF)"), ("assets/audit-checklist.pdf", "Audit checklist (PDF)"),
      ("assets/evaluation-report.pdf", "Evaluation report (PDF)")]),
    ("AI Assignment Stress Tester", "Three agents attempt an assignment; a fourth recommends fixes", "Independent · Multi-agent tool",
     "Built for faculty. An instructor pastes an assignment and rubric; three agents attempt it the way students commonly use AI, "
     "and an advisor agent writes a vulnerability report with specific revisions. Status: functional prototype.",
     ["Python", "Streamlit", "Claude API", "DeepSeek"], ("stress-tester.html", "Case study")),
    ("UX Feedback Analyzer", "Turns survey scores and comments into explainable churn risk", "Independent · ML tool",
     "Cleans mixed-method feedback, turns comments into signals and ranks churn risk by segment, with the reasons shown. It scrubs "
     "personal details and labels results as directional when there are fewer than 200 responses. Status: MVP.",
     ["Python", "Streamlit", "TF-IDF", "Logistic regression"], ("analyzer.html", "Case study")),
    ("Damage Shield", "Damage documentation for mobile auto detailers", "Independent · Live product",
     [("Problem", "Detailers get blamed for damage that was already on a car before the job."),
      ("Users", "Mobile auto detailers."),
      ("How it works", "Enter the client and vehicle, photograph each existing issue, have the client sign on screen, and send a "
                       "timestamped, signed PDF to both parties. Five free reports, then $20 a month."),
      ("Validation", "[[CONFIRM: any detailers using it, reports created, or feedback you can share?]]")],
     ["Supabase Edge Functions", "Resend", "Vercel"], ("https://damageshield.org", "Visit")),
    ("Break Lab", "A browser drum sampler for producers", "Independent · Live",
     "Waveform slicing, a step sequencer and a live looper in the browser. No install, no signup.",
     ["JavaScript", "Web Audio API", "Canvas"], ("https://breaklab.app", "Visit")),
]

JOBS = [
    ("2024–now", "Program Manager, AI & Learning", "Ehoro Village",
     "AI-supported course production, team training, onboarding design and documentation, cross-functional enablement "
     "workshops for 20+ internal champions, and a Python/Streamlit review tool that cut manual triage 40–60%. I use learner "
     "data to guide improvements.", None),
    ("2023–24", "Product Designer & UX Researcher", "University of Michigan · BRAID",
     "Research with 100+ stakeholders; a redesign that lifted new sign-ups 40% in four weeks. ", ("braid.html", "Case study")),
    ("2021–22", "IT Project Manager", "Procter & Gamble",
     "Coordinated 11 regional project managers on a $20M+ global initiative; drove adoption of a program-management "
     "framework across 10+ teams with training and documentation; P&G CEO Award for program impact.", None),
    ("2017–21", "Project Coordinator, Arts & Cultural Programs", "University of Michigan · Multi-Ethnic Student Affairs",
     "Nearly four years of heritage months, seminars and workshops, including anti-racism workshops for classes of 40+.", None),
]


def platforms():
    return "\n".join(f"""<article class="plat reveal" style="transition-delay:{i * 70}ms">
        <div><span class="role">{e(role)}</span><h3>{e(name)}</h3></div>
        <p class="found">{e(found)}</p>
        <p class="rule"><b>Rule now</b>{e(rule)}</p>
      </article>""" for i, (role, name, found, rule) in enumerate(PLATFORMS))


def experiments():
    out = []
    for eid, title, broke, big, small, fix, bars, bars_label in EXPERIMENTS:
        viz = ""
        if bars:
            viz = '<div class="bars" aria-label="' + e(bars_label) + '">' + "".join(
                f'<div class="bar"><span>{e(k)}</span><i class="{"old" if old else ""}" style="--w:{w:.3f}"></i><span>{e(v)}</span></div>'
                for k, v, w, old in bars) + "</div>"
        out.append(f"""<article class="exp reveal">
        <span class="id">{eid}</span>
        <div><h3>{e(title)}</h3><p class="fix">{e(fix)}</p>{viz}</div>
        <div class="big">{e(big)}<small>{e(small)}</small></div>
        <div><p class="broke">{e(broke)}</p></div>
      </article>""")
    return "\n".join(out)


CONFIRMS = []
RELEASE = "--release" in sys.argv
CONFIRM_RE = r"\s*\[\[CONFIRM: .+?\]\]"


def text(t):
    """Escape, then turn [[CONFIRM: ...]] into a visible draft note (and remember it for the build report)."""
    out = e(t)
    for m in re.findall(r"\[\[CONFIRM: (.+?)\]\]", t):
        CONFIRMS.append(m)
        out = out.replace(e(f"[[CONFIRM: {m}]]"), f'<span class="confirm">To confirm · {e(m)}</span>')
    return out


def clean(body):
    """Release builds publish only confirmed facts: confirm notes are removed, and a row that was only a question goes."""
    if not RELEASE:
        return body
    if isinstance(body, list):
        CONFIRMS.extend(m for _, v in body for m in re.findall(r"\[\[CONFIRM: (.+?)\]\]", v))
        body = [(k, re.sub(CONFIRM_RE, "", v).strip()) for k, v in body]
        return [(k, v) for k, v in body if v]
    CONFIRMS.extend(re.findall(r"\[\[CONFIRM: (.+?)\]\]", body))
    return re.sub(CONFIRM_RE, "", body).strip()


def case():
    rows = clean(CASE["rows"])
    dl = '<dl class="case">' + "".join(f"<div><dt>{e(k)}</dt><dd>{text(v)}</dd></div>" for k, v in rows) + "</dl>"
    stats = "".join(f'<div class="feature-stat"><b>{e(b)}</b><span>{e(t)}</span></div>' for b, t in CASE["stats"])
    chips = '<div class="chips">' + "".join(f'<span class="chip">{e(c)}</span>' for c in CASE["chips"]) + "</div>"
    return f'<div class="feature reveal"><div>{dl}</div><aside class="feature-side">{stats}{chips}</aside></div>'


def work():
    out = []
    for n, (name, what, tag, body, chips, link) in enumerate(WORK):
        go = ""
        for href, label in ([link] if isinstance(link, tuple) else link or []):
            ext = href.startswith("http")
            go += f'<a class="go" href="{e(href)}"{" target=_blank rel=noopener" if ext else ""}>{e(label)} <span>{"↗" if ext else "→"}</span></a>'
        if go:
            go = f'<div class="links">{go}</div>'
        body = clean(body)
        if isinstance(body, list):
            main = '<dl class="case">' + "".join(f"<div><dt>{e(k)}</dt><dd>{text(v)}</dd></div>" for k, v in body) + "</dl>"
        else:
            main = f"<p>{text(body)}</p>"
        out.append(f"""<div class="row">
        <button aria-expanded="false" aria-controls="w{n}">
          <span class="name">{e(name)}</span><span class="what">{e(what)}</span><span class="tag">{e(tag)}</span>
          <span class="plus" aria-hidden="true"><svg width="12" height="12" viewBox="0 0 12 12" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M6 1v10M1 6h10"/></svg></span>
        </button>
        <div class="more" id="w{n}" role="region"><div><div class="inner">
          {main}
          <div class="side"><div class="chips">{"".join(f'<span class="chip">{e(c)}</span>' for c in chips)}</div>{go}</div>
        </div></div></div>
      </div>""")
    return "\n".join(out)


H1 = "I help teams adopt AI and improve how work gets done."
H1_SERIF_FROM = 8   # "work gets done." in the serif


def h1():
    words = H1.split()
    spans = []
    for i, w in enumerate(words):
        cls = ' class="serif"' if i >= H1_SERIF_FROM else ""
        spans.append(f'<span class="w"><span{cls} style="--d:{i * 45}ms">{e(w)}</span></span>')
    return f'<h1 aria-label="{e(H1)}"><span aria-hidden="true">{" ".join(spans)}</span></h1>'


def jobs():
    out = []
    for when, title, org, line, link in JOBS:
        a = f' <a href="{e(link[0])}">{e(link[1])} →</a>' if link else ""
        out.append(f"""<div class="job"><span class="when">{e(when)}</span>
        <div><h3>{e(title)}</h3><p class="org">{e(org)}</p><p>{e(line.strip())}{a}</p></div></div>""")
    return "\n".join(out)


def page():
    src = open(os.path.join(HERE, "index.src.html"), encoding="utf-8").read()
    marquee = "".join(f"<span>{e(m)}</span>" for m in MARQUEE * 2)
    for key, val in {"MARK": octo.mark(), "HERO": octo.hero(), "H1": h1(), "CASE": case(), "MARQUEE": marquee, "PLATFORMS": platforms(),
                     "EXPERIMENTS": experiments(), "WORK": work(), "JOBS": jobs()}.items():
        src = src.replace("{{" + key + "}}", val)
    assert "{{" not in src, "unfilled placeholder"
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    if CONFIRMS:
        print(f"{'RELEASE: left out' if RELEASE else 'DRAFT:'} {len(CONFIRMS)} fact(s) still to confirm with Ube:")
        for c in CONFIRMS:
            print("  - " + c)


def assets():
    os.makedirs(ASSETS, exist_ok=True)
    with open(os.path.join(ASSETS, "octo.svg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="#0b0b0b">{octo.mark().replace("var(--octo-eye,#fff)", "#fff")}</svg>\n')
    with open(os.path.join(ASSETS, "favicon.svg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(octo.favicon() + "\n")


def shoot(html_text, out, w, h):
    tmp = tempfile.mkdtemp()
    src = os.path.join(tmp, "s.html")
    with open(src, "w", encoding="utf-8") as f:
        f.write(html_text)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={os.path.join(tmp, 'p')}",
                    f"--window-size={w},{h}", f"--screenshot={out}", "file:///" + src.replace("\\", "/")],
                   capture_output=True, timeout=120)


def images():
    fav = octo.favicon()
    for size, name in ((32, "favicon-32.png"), (180, "apple-touch-icon.png")):
        shoot(f'<html><body style="margin:0;background:transparent"><div style="width:{size}px;height:{size}px">{fav.replace("<svg ", f"<svg width={size} height={size} ")}</div></body></html>',
              os.path.join(ASSETS, name), size, size)
    mark = octo.mark().replace("var(--octo-eye,#fff)", "#fff")
    og = f"""<html><head><link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600&family=Instrument+Serif:ital@1&display=swap" rel="stylesheet"></head>
<body style="margin:0;width:1200px;height:630px;background:#fff;font-family:Inter,Segoe UI,sans-serif;display:flex;align-items:center;justify-content:space-between;padding:0 90px;box-sizing:border-box">
<div><div style="font-size:22px;color:#737373;letter-spacing:.02em;margin-bottom:22px">Adé Ijidakinro · AI Enablement · Program Management</div>
<div style="font-size:70px;line-height:1;letter-spacing:-.045em;font-weight:600;color:#0b0b0b">I help teams adopt AI<br>and improve how<br><span style="font-family:'Instrument Serif',serif;font-style:italic;font-weight:400;letter-spacing:-.02em">work gets done.</span></div>
<div style="font-size:22px;color:#737373;margin-top:28px">ijidakinro.com</div></div>
<svg width="330" height="330" viewBox="0 0 100 100" fill="#0b0b0b">{mark}</svg></body></html>"""
    shoot(og, os.path.join(ASSETS, "og.png"), 1200, 630)


if __name__ == "__main__":
    page()
    assets()
    if "--images" in sys.argv:
        images()
    print("built index.html" + (" + images" if "--images" in sys.argv else ""))

# SOURCES (checked Oct 5, 2026)
# 349 commits / 90 branches / Sep 21 - Oct 4: git clone of ubseoul/rich_alucard, rev-list --all, for-each-ref refs/remotes (91 incl. HEAD)
# 441 commits (354 + 87), 148 [x] tickets (126 + 22): ubseoul/ube_kitchen + ubseoul/ube_stoves, Oct 4-5
# 30+ rulings (OL-001..OL-032), R1-R8 gates, clerk gate, memory ruling withdrawn (OL-025 -> OL-029),
#   status understated 3x, Sonnet sole merger, Codex reserve builder, Gemini smoke PASS: OVERLORD HANDOFF through OL-029.md
# 259 commits / 7 h / 146 in one hour, 98% 5-hour window, 6.9K -> 2.4K board tokens, 18 drafts, 0 ready packets: 13_UBE_KITCHEN/REPORTS/2026-10-05-USAGE_STUDY.md
# 3 weeks -> 4-7 days, 66-80%, 200+ students, guides/tip sheets/FAQs, 20+ champions, 40-60% triage, P&G facts: 13_UBE_KITCHEN/resume/master.yaml (confirmed by Ube, P007)
# AI for scripting, voiceover and asset production: Ube's own About copy on the previous ijidakinro.com homepage
# Damage Shield problem/users/steps/pricing: damageshield.org (checked Oct 5 2026; no usage or testimonial data published there)
# Break Lab, Stress Tester, Analyzer, Build With AI, 24+ sessions, sushi line: Ube's own portfolio pages (ijidakinro_portfolio_2026)
