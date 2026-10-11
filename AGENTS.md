# Instructions for AI agents working in this repo

This is the public portfolio site for Adé Ijidakinro (ijidakinro.com).

**Before changing anything, read [`STYLE_GUIDE.md`](STYLE_GUIDE.md).** It defines the design tokens, components, voice, truth rules and the checks to run.

Short version:
- `index.html` is generated. Edit `_build/index.src.html` and `_build/build.py`, then run `python _build/build.py --release`.
- New pages: `python _build/new_page.py <slug> --title "..."`. Do not copy the legacy pages' styles.
- Every claim must trace to a confirmed source. Unknown facts get `[[CONFIRM: ...]]`, never a guess.
- Never publish the items listed in STYLE_GUIDE.md section 7. Ask Ube before pushing to `main`.
