"""Analysis: shortcut rates, the key contrasts, and the three instruction-following ablations.

Run:  python -m authority_override.analyze     (use PYTHONIOENCODING=utf-8 on Windows)
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from statistics import mean

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from authority_override.scenarios import HARMFUL, NEUTRAL   # noqa: E402
from authority_override.models import MODELS                 # noqa: E402

DATA = Path(__file__).resolve().parent / "data" / "results.jsonl"
CONDS = ["SOLO", "PEER", "SUPERIOR", "DELEGATE", "GROUP"]


def load():
    return [json.loads(l) for l in DATA.read_text(encoding="utf-8").splitlines() if l.strip()]


def rate(rows):
    rows = [r for r in rows if r.get("decision")]
    return (mean(1.0 if r["shortcut"] else 0.0 for r in rows), len(rows)) if rows else (float("nan"), 0)


def boot_ci(rows, n=2000):
    vals = [1.0 if r["shortcut"] else 0.0 for r in rows if r.get("decision")]
    if len(vals) < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(0)
    ms = []
    for _ in range(n):
        s = [vals[rng.randrange(len(vals))] for _ in vals]
        ms.append(sum(s) / len(s))
    ms.sort()
    return (ms[int(0.025 * n)], ms[int(0.975 * n)])


def main():
    rows = load()
    harmful = [r for r in rows if not r["neutral"]]
    print(f"loaded {len(rows)} rows ({len(harmful)} harmful)\n")

    # ---- 1. shortcut rate by condition, pooled over harmful scenarios, per model ----
    print("== shortcut rate P(choose B) by condition — harmful scenarios, per model ==")
    print(f"{'model':<14}" + "".join(f"{c:>10}" for c in CONDS) + f"{'SUP-SOLO':>10}{'SUP-PEER':>10}")
    fam_rows = {}
    for m in MODELS:
        mr = [r for r in harmful if r["model_key"] == m["key"]]
        rr = {c: rate([r for r in mr if r["cond"] == c])[0] for c in CONDS}
        supsolo = rr["SUPERIOR"] - rr["SOLO"]
        suppeer = rr["SUPERIOR"] - rr["PEER"]
        print(f"{m['key']:<14}" + "".join(f"{rr[c]:>10.2f}" for c in CONDS)
              + f"{supsolo:>+10.2f}{suppeer:>+10.2f}")
        fam_rows[m["key"]] = rr

    # ---- 2. pooled contrasts with bootstrap CIs ----
    print("\n== pooled contrasts (all harmful scenarios x models) ==")
    for c in CONDS:
        r, n = rate([x for x in harmful if x["cond"] == c])
        lo, hi = boot_ci([x for x in harmful if x["cond"] == c])
        print(f"  {c:<9} P(B)={r:.2f}  95%CI[{lo:.2f},{hi:.2f}]  n={n}")

    # ---- 3. per-scenario SUPERIOR vs SOLO/PEER ----
    print("\n== SUPERIOR vs SOLO / PEER, per harmful scenario (pooled models) ==")
    for sid in HARMFUL:
        sr = [r for r in harmful if r["scenario"] == sid]
        solo = rate([r for r in sr if r["cond"] == "SOLO"])[0]
        peer = rate([r for r in sr if r["cond"] == "PEER"])[0]
        sup = rate([r for r in sr if r["cond"] == "SUPERIOR"])[0]
        print(f"  {sid:<14} SOLO={solo:.2f} PEER={peer:.2f} SUPERIOR={sup:.2f}"
              f"  (SUP-SOLO={sup-solo:+.2f}, SUP-PEER={sup-peer:+.2f})")

    # ---- A1: verb-matched peer vs superior (already in the contrasts above) ----
    p_peer = rate([r for r in harmful if r["cond"] == "PEER"])[0]
    p_sup = rate([r for r in harmful if r["cond"] == "SUPERIOR"])[0]
    print(f"\n== A1 (source, verb-matched): PEER={p_peer:.2f} vs SUPERIOR={p_sup:.2f}"
          f"  diff={p_sup-p_peer:+.2f} ==")

    # ---- A2: content x source interaction ----
    print("\n== A2 (content x source interaction) — is rank a GENERIC compliance amplifier? ==")
    if NEUTRAL:
        nid = NEUTRAL[0]
        neu = [r for r in rows if r["scenario"] == nid]
        n_peer = rate([r for r in neu if r["cond"] == "PEER"])[0]
        n_sup = rate([r for r in neu if r["cond"] == "SUPERIOR"])[0]
        h_peer, h_sup = p_peer, p_sup
        print(f"  neutral : PEER complies={n_peer:.2f}  SUPERIOR complies={n_sup:.2f}  (SUP-PEER={n_sup-n_peer:+.2f})")
        print(f"  harmful : PEER complies={h_peer:.2f}  SUPERIOR complies={h_sup:.2f}  (SUP-PEER={h_sup-h_peer:+.2f})")
        interaction = (h_sup - h_peer) - (n_sup - n_peer)
        print(f"  INTERACTION (harmful[SUP-PEER] - neutral[SUP-PEER]) = {interaction:+.2f}")
        print("  -> if ~0 on neutral but large on harmful, rank unlocks HARMFUL compliance "
              "specifically (not instruction-following).")
    else:
        print("  (no neutral scenario data yet)")

    # ---- A3: belief-action gap ----
    print("\n== A3 (belief-action gap) — obeyed against its own stated judgment? ==")
    sup_h = [r for r in harmful if r["cond"] == "SUPERIOR" and "belief_A_correct" in r]
    if sup_h:
        complied = [r for r in sup_h if r["shortcut"]]
        gap = [r for r in complied if r.get("belief_A_correct") == "YES"]
        print(f"  SUPERIOR/harmful with belief probe: n={len(sup_h)}")
        if complied:
            print(f"  of those that took the harmful action (n={len(complied)}), "
                  f"{len(gap)} ({len(gap)/len(complied):.0%}) still said the HONEST action was ethically correct")
            print("  -> a high gap = obedience overriding the agent's own judgment (Milgram 'agentic state').")
    else:
        print("  (no belief-probe rows yet)")

    # ---- asymmetry summary ----
    print("\n== asymmetry: obeys down-chain orders but won't originate/delegate/diffuse ==")
    for c in ("SOLO", "SUPERIOR", "DELEGATE", "GROUP"):
        print(f"  {c:<9} P(B)={rate([x for x in harmful if x['cond']==c])[0]:.2f}")


if __name__ == "__main__":
    main()
