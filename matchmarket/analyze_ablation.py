"""Analyze the verification ablation study — the controlled record on/off contrast.

Run:  python -m matchmarket.analyze_ablation   (PYTHONIOENCODING=utf-8 on Windows)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

HERE = Path(__file__).resolve().parent
POOL = HERE / "data" / "pool_pitch.jsonl"
ABL = HERE / "data" / "ablation.jsonl"


def load(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def rate(rows, key):
    return mean(1.0 if r[key] else 0.0 for r in rows) if rows else float("nan")


def main():
    pool = [r for r in load(POOL) if r.get("claim") is not None]
    print("== Stage A': deception (over-claim) by model x theta, consistent framing ==")
    print(f"{'model':<14}{'θ=2':>8}{'θ=5':>8}{'θ=8':>8}")
    for mk in dict.fromkeys(r["model_key"] for r in pool):
        mr = [r for r in pool if r["model_key"] == mk]
        cells = {t: [r["over_claim"] for r in mr if r["theta"] == t] for t in (2, 5, 8)}
        print(f"{mk:<14}" + "".join(f"{(mean(cells[t]) if cells[t] else float('nan')):>+8.1f}" for t in (2, 5, 8)))

    ab = [r for r in load(ABL) if r.get("pick") is not None]
    if not ab:
        print("\n(ablation not complete yet)"); return

    print("\n== Stage C: CONTROLLED record on/off (same slates), detect% / fooled% ==")
    print(f"{'detector':<14}{'WITH detect':>13}{'NO detect':>11}{'Δ detect':>10}"
          f"{'WITH fool':>11}{'NO fool':>9}")
    for mk in dict.fromkeys(r["model_key"] for r in ab):
        mr = [r for r in ab if r["model_key"] == mk]
        w = [r for r in mr if r["cond"] == "with_record"]
        o = [r for r in mr if r["cond"] == "no_record"]
        wd, od = rate(w, "correct"), rate(o, "correct")
        print(f"{mk:<14}{wd:>13.0%}{od:>11.0%}{wd-od:>+10.0%}"
              f"{rate(w,'fooled'):>11.0%}{rate(o,'fooled'):>9.0%}")

    w = [r for r in ab if r["cond"] == "with_record"]
    o = [r for r in ab if r["cond"] == "no_record"]
    print(f"\n  POOLED  with-record detect {rate(w,'correct'):.0%} (fooled {rate(w,'fooled'):.0%})  "
          f"|  no-record detect {rate(o,'correct'):.0%} (fooled {rate(o,'fooled'):.0%})")
    print(f"  >>> verification effect (Δ detect) = {rate(w,'correct')-rate(o,'correct'):+.0%}")

    # backfiring skepticism: in no-record, how often did they reject the honest-strong (miss = neither)?
    o_miss = mean(1.0 if (not r["correct"] and not r["fooled"]) else 0.0 for r in o)
    print(f"\n== backfiring skepticism: no-record 'miss' rate (rejected the honest expert too) = {o_miss:.0%} ==")

    # who-fools-whom (no-record): fooled% by trap source
    print("\n== who-fools-whom (no-record): fooled% by trap-source model ==")
    for src in dict.fromkeys(r["trap_src"] for r in o):
        sr = [r for r in o if r["trap_src"] == src]
        print(f"  trap from {src:<13} fooled {rate(sr,'fooled'):.0%}  (n={len(sr)})")


if __name__ == "__main__":
    main()
