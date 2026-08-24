"""Analyze the Phase-2 confirmatory ablation, framed around the REFRAMED headline.

Reports, with Wilson 95% CIs and per-family breakdowns:
  1. no_record: flight-to-mediocrity = P(pick == mid); + full picked_role split.
  2. no_record detection vs chance (1/3): are self-reports non-diagnostic?
  3. with_record: CONTROL -- models act on explicit audit evidence.
  4. verification gap (with - no) kept as a secondary/control contrast, not headline.

Run:  py -m matchmarket.analyze_phase2
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from statistics import mean

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# these reports use non-ASCII glyphs; Windows consoles default to cp1252 and would crash
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
P2_ABL = HERE / "data" / "phase2_ablation.jsonl"


def load(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def rate(rows, key):
    return mean(1.0 if r[key] else 0.0 for r in rows) if rows else float("nan")


def wilson(k, n, z=1.96):
    """Wilson score 95% CI for a proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def ci_str(rows, key):
    n = len(rows)
    k = sum(1 for r in rows if r[key])
    lo, hi = wilson(k, n)
    return f"{k/n:>6.0%} [{lo:.0%},{hi:.0%}] n={n}" if n else "  n/a"


def main():
    ab = [r for r in load(P2_ABL) if r.get("pick") is not None]
    if not ab:
        print("(phase2 ablation not complete yet)"); return

    o = [r for r in ab if r["cond"] == "no_record"]
    w = [r for r in ab if r["cond"] == "with_record"]
    models = list(dict.fromkeys(r["model_key"] for r in ab))

    print("=" * 68)
    print("HEADLINE 1 — FLIGHT TO MEDIOCRITY (no_record): P(pick == mid)")
    print("=" * 68)
    print(f"{'detector':<14}{'flight-to-mid (95% CI)':<28}")
    for mk in models:
        mr = [r for r in o if r["model_key"] == mk]
        print(f"{mk:<14}{ci_str(mr,'flight_mid')}")
    print(f"{'POOLED':<14}{ci_str(o,'flight_mid')}   (chance baseline = 33%)")

    print("\n-- full picked_role split (no_record) --")
    print(f"{'detector':<14}{'honest(correct)':>16}{'mid(flight)':>13}{'inflator(fooled)':>18}{'unparsed':>10}")
    for mk in models:
        mr = [r for r in o if r["model_key"] == mk]
        n = len(mr)
        hon = sum(1 for r in mr if r["picked_role"] == "honest")
        mid = sum(1 for r in mr if r["picked_role"] == "mid")
        inf = sum(1 for r in mr if r["picked_role"] == "inflator")
        bad = n - hon - mid - inf
        print(f"{mk:<14}{hon/n:>16.0%}{mid/n:>13.0%}{inf/n:>18.0%}{bad/n:>10.0%}")

    print("\n" + "=" * 68)
    print("HEADLINE 2 — SELF-REPORTS NON-DIAGNOSTIC (no_record detection vs 33%)")
    print("=" * 68)
    print(f"{'detector':<14}{'detect (95% CI)':<28}")
    for mk in models:
        mr = [r for r in o if r["model_key"] == mk]
        print(f"{mk:<14}{ci_str(mr,'correct')}")
    print(f"{'POOLED':<14}{ci_str(o,'correct')}   (chance = 33%)")

    print("\n" + "=" * 68)
    print("CONTROL — WITH_RECORD (models CAN use explicit audit evidence)")
    print("=" * 68)
    print(f"{'detector':<14}{'detect (95% CI)':<28}")
    for mk in models:
        mr = [r for r in w if r["model_key"] == mk]
        print(f"{mk:<14}{ci_str(mr,'correct')}")
    print(f"{'POOLED':<14}{ci_str(w,'correct')}")

    print("\n-- secondary: verification gap (with - no), per family --")
    print(f"{'detector':<14}{'WITH':>8}{'NO':>8}{'Δ':>8}")
    for mk in models:
        wr = [r for r in w if r["model_key"] == mk]
        orr = [r for r in o if r["model_key"] == mk]
        wd, od = rate(wr, "correct"), rate(orr, "correct")
        print(f"{mk:<14}{wd:>8.0%}{od:>8.0%}{wd-od:>+8.0%}")
    print(f"{'POOLED':<14}{rate(w,'correct'):>8.0%}{rate(o,'correct'):>8.0%}"
          f"{rate(w,'correct')-rate(o,'correct'):>+8.0%}")


if __name__ == "__main__":
    main()
