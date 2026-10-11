"""Start a new page in the house style.

  python _build/new_page.py my-case-study --title "Plain words, then serif words" --label "Case study" --description "One sentence."

Writes my-case-study.html in the repo root from _build/page.template.html, with the octopus mark inlined.
Fill every {{...}} (the script refuses to finish the job if you leave any when you pass --check).
Then read STYLE_GUIDE.md section 9 for the checks to run before publishing."""
import argparse
import os
import re
import sys

import octo

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug", nargs="?", help="file name without .html")
    ap.add_argument("--title", default="Page title")
    ap.add_argument("--label", default="Case study")
    ap.add_argument("--description", default="One sentence that says what this page is.")
    ap.add_argument("--check", metavar="FILE", help="fail if the page still has {{placeholders}}")
    a = ap.parse_args()
    if a.check:
        left = re.findall(r"\{\{[^}]*\}\}", open(os.path.join(SITE, a.check), encoding="utf-8").read())
        print(f"{len(left)} placeholder(s) left" + ("" if not left else ": " + "; ".join(x[:50] for x in left[:6])))
        sys.exit(1 if left else 0)
    if not a.slug:
        ap.error("slug is required")
    words = a.title.split()
    plain, serif = (" ".join(words[:-2]), " ".join(words[-2:])) if len(words) > 3 else (a.title, "")
    html = open(os.path.join(HERE, "page.template.html"), encoding="utf-8").read()
    for key, val in {"MARK": octo.mark(), "FILE": a.slug + ".html", "TITLE_PLAIN": plain, "TITLE_SERIF": serif,
                     "DESCRIPTION": a.description, "LABEL": a.label}.items():
        html = html.replace("{{" + key + "}}", val)
    html = html.replace("{{TITLE}}", a.title)
    out = os.path.join(SITE, a.slug + ".html")
    if os.path.exists(out):
        sys.exit(f"{a.slug}.html already exists; pick another slug.")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(f"Wrote {a.slug}.html. Fill the remaining {{{{...}}}} blocks, then run the checks in STYLE_GUIDE.md.")


if __name__ == "__main__":
    main()
