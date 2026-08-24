"""Analyze the disclosure pilot: is there inflation, does it depend on true trait, on model?

Run:  python -m matchmarket.analyze_disclosure   (PYTHONIOENCODING=utf-8 on Windows)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATA = Path(__file__).resolve().parent / "data" / "disclosure.jsonl"
THETAS = [2, 5, 8]


def load():
    return [json.loads(l) for l in DATA.read_text(encoding="utf-8").splitlines() if l.strip()]


def main():
    rows = [r for r in load() if r.get("inflation") is not None]
    print(f"loaded {len(rows)} scored rows\n")
    models = list(dict.fromkeys(r["model_key"] for r in rows))

    # inflation = claim - theta, by model x theta
    print("== mean inflation (claimed - true) by model x true-competence ==")
    print(f"{'model':<14}" + "".join(f"{'θ='+str(t):>9}" for t in THETAS) + f"{'ALL':>9}{'θ2-θ8':>9}")
    for mk in models:
        mr = [r for r in rows if r["model_key"] == mk]
        cells = {t: [r["inflation"] for r in mr if r["theta"] == t] for t in THETAS}
        means = {t: (mean(cells[t]) if cells[t] else float("nan")) for t in THETAS}
        allm = mean([r["inflation"] for r in mr]) if mr else float("nan")
        trait = (means[2] - means[8]) if (means[2] == means[2] and means[8] == means[8]) else float("nan")
        print(f"{mk:<14}" + "".join(f"{means[t]:>+9.2f}" for t in THETAS)
              + f"{allm:>+9.2f}{trait:>+9.2f}")

    # pooled
    print("\n== pooled ==")
    for t in THETAS:
        tr = [r["inflation"] for r in rows if r["theta"] == t]
        # claim honesty: fraction who claimed above true
        infl = [r["inflation"] for r in rows if r["theta"] == t]
        over = sum(1 for x in infl if x > 0) / len(infl) if infl else float("nan")
        print(f"  θ={t}: mean inflation {mean(tr):+.2f}   inflated(claim>true) {over:.0%}   n={len(tr)}")
    allr = [r["inflation"] for r in rows]
    print(f"  ALL : mean inflation {mean(allr):+.2f}   inflated {sum(1 for x in allr if x>0)/len(allr):.0%}")

    # trait correlation (do low-competence agents inflate more?)
    lo = [r["inflation"] for r in rows if r["theta"] == 2]
    hi = [r["inflation"] for r in rows if r["theta"] == 8]
    if lo and hi:
        print(f"\n== trait effect: inflation(θ=2) - inflation(θ=8) = {mean(lo)-mean(hi):+.2f} ==")
        print("   (>0 => LOW-competence agents inflate MORE — 'bad agents lie more')")

    # quick read of what claims look like at low competence (the most telling cell)
    print("\n== sample claims at θ=2 (true competence LOW) ==")
    for r in [x for x in rows if x["theta"] == 2][:8]:
        print(f"  {r['model_key']:<13} claimed {r['claim']} (true 2)  :: {r['raw'][:70]!r}")


if __name__ == "__main__":
    main()
