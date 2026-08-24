"""Analyze the two-sided matched pilot.

Stage A: over-claim by model x theta under the GENTLE penalty (did easing free up deception?).
Stage B: detection vs fooled under HARD detection (claim+pitch, no record), by detector model
         and by trap-source model (whose lies fool whom).

Run:  python -m matchmarket.analyze_matched   (PYTHONIOENCODING=utf-8 on Windows)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

HERE = Path(__file__).resolve().parent
POOL = HERE / "data" / "deceiver_pool.jsonl"
MATCHED = HERE / "data" / "matched.jsonl"


def load(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def main():
    pool = [r for r in load(POOL) if r.get("claim") is not None]
    print("== Stage A: over-claim under GENTLE penalty (fine 1 @ 40% audit) ==")
    print(f"{'model':<14}{'θ=2':>8}{'θ=5':>8}{'θ=8':>8}{'θ2-θ8':>9}")
    for mk in dict.fromkeys(r["model_key"] for r in pool):
        mr = [r for r in pool if r["model_key"] == mk]
        cells = {t: [r["over_claim"] for r in mr if r["theta"] == t] for t in (2, 5, 8)}
        means = {t: (mean(cells[t]) if cells[t] else float("nan")) for t in (2, 5, 8)}
        gap = means[2] - means[8] if means[2] == means[2] and means[8] == means[8] else float("nan")
        print(f"{mk:<14}{means[2]:>+8.1f}{means[5]:>+8.1f}{means[8]:>+8.1f}{gap:>+9.1f}")

    mm = [r for r in load(MATCHED) if r.get("pick") is not None]
    if not mm:
        print("\n(Stage B not complete yet)"); return
    print("\n== Stage B: HARD detection (claim+pitch only, no record), by DETECTOR model ==")
    print(f"{'detector':<14}{'n':>4}{'detect%':>9}{'fooled%':>9}{'miss%':>8}")
    for mk in dict.fromkeys(r["model_key"] for r in mm):
        mr = [r for r in mm if r["model_key"] == mk]
        det = mean(1.0 if r["correct"] else 0.0 for r in mr)
        fool = mean(1.0 if r["fooled"] else 0.0 for r in mr)
        print(f"{mk:<14}{len(mr):>4}{det:>9.0%}{fool:>9.0%}{1-det-fool:>8.0%}")

    print("\n== who-fools-whom: fooled% by TRAP-SOURCE model (whose inflated pitch got through) ==")
    for src in dict.fromkeys(r["trap_src"] for r in mm):
        sr = [r for r in mm if r["trap_src"] == src]
        fool = mean(1.0 if r["fooled"] else 0.0 for r in sr)
        print(f"  trap from {src:<13} fooled the detector {fool:.0%} of the time (n={len(sr)})")

    print("\n== pooled ==")
    det = mean(1.0 if r['correct'] else 0.0 for r in mm)
    fool = mean(1.0 if r['fooled'] else 0.0 for r in mm)
    print(f"  overall detect {det:.0%} | fooled {fool:.0%} | n={len(mm)}")
    print("  (contrast with the EASY pilot's ~90% detect: does removing the record collapse detection?)")

    print("\n== sample fooled reasons ==")
    for r in [x for x in mm if x["fooled"]][:6]:
        print(f"  {r['model_key']:<12} (trap {r['trap_src']}): {r['raw'][:120]!r}")


if __name__ == "__main__":
    main()
