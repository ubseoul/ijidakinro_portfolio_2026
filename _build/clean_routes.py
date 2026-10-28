"""Keep the clean portfolio routes in sync with their .html aliases.

Run from the repository root: python _build/clean_routes.py
The root .html files stay available for links already shared. Both copies use
root-relative local assets and links, so they work from either URL depth.
"""

from pathlib import Path
import re


SITE = Path(__file__).resolve().parent.parent
SLUGS = ("thoughts", "concepts", "figma-make-protected-edits", "roblox-startup-diagnostics", "north-star")
LINKS = {
    "north-star.html": "/north-star/",
    "roblox-startup-diagnostics.html": "/roblox-startup-diagnostics/",
    "index.html": "/",
    "thoughts.html": "/thoughts/",
    "concepts.html": "/concepts/",
    "figma-make-protected-edits.html": "/figma-make-protected-edits/",
}
ATTRIBUTE = re.compile(r'\b(href|src)="([^"]*)"')


def root_relative(match):
    attr, value = match.groups()
    base, separator, fragment = value.partition("#")
    if base in LINKS:
        return f'{attr}="{LINKS[base]}{separator}{fragment}"'
    if value.startswith(("/", "#", "http:", "https:", "mailto:", "data:")):
        return match.group(0)
    return f'{attr}="/{value}"'


for slug in SLUGS:
    alias = SITE / f"{slug}.html"
    page = alias.read_text(encoding="utf-8")
    page = page.replace(
        f"https://ijidakinro.com/{slug}.html",
        f"https://ijidakinro.com/{slug}/",
    )
    page = ATTRIBUTE.sub(root_relative, page)
    alias.write_text(page, encoding="utf-8", newline="")

    destination = SITE / slug / "index.html"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(page, encoding="utf-8", newline="")
    print(f"{slug}/index.html <= {slug}.html")
