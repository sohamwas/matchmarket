"""Analyze the detector pilot: who sees through inflated claims, who gets fooled by the trap?

Run:  python -m matchmarket.analyze_detector   (PYTHONIOENCODING=utf-8 on Windows)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATA = Path(__file__).resolve().parent / "data" / "detector.jsonl"


def main():
    rows = [json.loads(l) for l in DATA.read_text(encoding="utf-8").splitlines() if l.strip()]
    scored = [r for r in rows if r.get("pick") is not None]
    print(f"loaded {len(rows)} rows ({len(scored)} with a parsed pick)\n")
    models = list(dict.fromkeys(r["model_key"] for r in scored))

    print("== detector performance by model ==")
    print(f"{'model':<14}{'n':>4}{'detect%':>9}{'fooled%':>9}{'miss%':>8}{'avg_true_hired':>16}")
    for mk in models:
        mr = [r for r in scored if r["model_key"] == mk]
        det = mean(1.0 if r["correct"] else 0.0 for r in mr)
        fool = mean(1.0 if r["fooled"] else 0.0 for r in mr)
        miss = 1.0 - det - fool
        avgt = mean(r["picked_true"] for r in mr if r["picked_true"] is not None)
        print(f"{mk:<14}{len(mr):>4}{det:>9.0%}{fool:>9.0%}{miss:>8.0%}{avgt:>16.2f}")

    # oracle baseline: always picking the true-best would score avg_true = mean of best_true per slate
    print("\n== per-slate fooled rate (pooled models) — which traps work best? ==")
    slates = sorted({r["slate"] for r in scored})
    for si in slates:
        sr = [r for r in scored if r["slate"] == si]
        fool = mean(1.0 if r["fooled"] else 0.0 for r in sr)
        det = mean(1.0 if r["correct"] else 0.0 for r in sr)
        print(f"  slate {si}: detect {det:.0%}  fooled {fool:.0%}  (n={len(sr)})")

    print("\n== sample FOOLED cases (picked the inflator despite its record) ==")
    for r in [x for x in scored if x["fooled"]][:6]:
        print(f"  {r['model_key']:<12} slate{r['slate']}: {r['raw'][:120]!r}")


if __name__ == "__main__":
    main()
