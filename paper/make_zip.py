"""Bundle the submission zip for Overleaf / START upload.

Collects exactly the files the paper needs to compile — nothing else, so the bundle
never carries stale figures or local build products.

Run:  py paper/make_zip.py
"""
from __future__ import annotations

import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "overleaf_paper.zip"

MEMBERS = [
    ("main.tex", "main.tex"),
    ("custom.bib", "custom.bib"),
    ("tables.tex", "tables.tex"),
    ("acl-style-files/acl.sty", "acl.sty"),
    ("acl-style-files/acl_natbib.bst", "acl_natbib.bst"),
    ("figures/fig1_task.pdf", "figures/fig1_task.pdf"),
    ("figures/fig2_payoff.pdf", "figures/fig2_payoff.pdf"),
    ("figures/fig3_errors.pdf", "figures/fig3_errors.pdf"),
    ("figures/fig4_reasoning.pdf", "figures/fig4_reasoning.pdf"),
]


def main() -> None:
    missing = [src for src, _ in MEMBERS if not (HERE / src).exists()]
    if missing:
        raise SystemExit("missing input(s):\n  " + "\n  ".join(missing))

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in MEMBERS:
            z.write(HERE / src, arc)

    print(f"wrote {OUT.name}  ({OUT.stat().st_size:,} bytes, {len(MEMBERS)} files)")
    print("note: run `py paper/make_figures.py` first if data or figures changed.")


if __name__ == "__main__":
    main()
