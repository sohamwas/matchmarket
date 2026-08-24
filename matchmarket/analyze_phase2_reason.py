"""Compare reasoning-OFF (Phase 2) vs reasoning-ON for qwen + gpt-oss.

Answers the confound question (§8.5): was their low text-only detection / high flight-to-mediocrity
an artifact of reasoning suppression? Same 40 slates, same conditions, only reasoning effort changed.

Run:  py -m matchmarket.analyze_phase2_reason
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# these reports use non-ASCII glyphs; Windows consoles default to cp1252 and would crash
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
OFF = HERE / "data" / "phase2_ablation.jsonl"          # reasoning suppressed
ON = HERE / "data" / "phase2_reason_ablation.jsonl"    # reasoning on
MODELS = ["qwen3.6-27b", "gpt-oss-120b"]


def load(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n; d = 1 + z*z/n; c = p + z*z/(2*n)
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return ((c-h)/d, (c+h)/d)


def cell(rows, key):
    n = len(rows)
    if not n:
        return "   --      "
    k = sum(1 for r in rows if r[key])
    lo, hi = wilson(k, n)
    return f"{k/n:>4.0%} [{lo:.0%},{hi:.0%}]"


def main():
    off = [r for r in load(OFF) if r.get("pick") is not None]
    on = [r for r in load(ON) if r.get("pick") is not None]
    if not on:
        print("(reasoning-on run not started yet)"); return

    def sub(rows, mk, cond):
        return [r for r in rows if r["model_key"] == mk and r["cond"] == cond]

    print("Confound check: reasoning OFF (Phase 2) vs ON (same 40 slates)\n")
    print(f"{'model':<14}{'metric':<22}{'reasoning OFF':<20}{'reasoning ON':<20}")
    print("-" * 76)
    for mk in MODELS:
        oN = sub(on, mk, "no_record")
        offN = sub(off, mk, "no_record")
        oW = sub(on, mk, "with_record")
        offW = sub(off, mk, "with_record")
        n_on = len(oN)
        print(f"{mk:<14}{'no-rec detect':<22}{cell(offN,'correct'):<20}{cell(oN,'correct'):<20}")
        print(f"{'':<14}{'no-rec flight-to-mid':<22}{cell(offN,'flight_mid'):<20}{cell(oN,'flight_mid'):<20}")
        print(f"{'':<14}{'no-rec fooled(liar)':<22}{cell(offN,'fooled'):<20}{cell(oN,'fooled'):<20}")
        print(f"{'':<14}{'with-rec detect':<22}{cell(offW,'correct'):<20}{cell(oW,'correct'):<20}")
        print(f"{'':<14}{'(on n='+str(n_on)+'/cond)':<22}")
        print("-" * 76)

    # verdict helper
    print("\nRead: if no-rec detect RISES and flight-to-mid FALLS with reasoning on,")
    print("the Phase-2 weakness WAS partly a suppression artifact (confound real -> soften §8.5).")
    print("If they barely move, the weakness is genuine (confound not the driver -> claim firms up).")


if __name__ == "__main__":
    main()
