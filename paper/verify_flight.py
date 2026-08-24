"""Does 'flight to mediocrity' survive the three attacks against it?

A1 'It's Bayes-rational hedging'      -> compare realized payoff vs alternatives.
A2 'It's the compromise effect'       -> compromise/extremeness aversion predicts picking the
                                         MIDDLE claim. Where does the Mid actually sit?
A3 'It's mislabelled (lowest, not moderate)' -> descriptive: does the PHENOMENON survive renaming?
Plus: the payoff cost of the behaviour, which is the quantity a practitioner cares about.
"""
from __future__ import annotations
import json, random
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "matchmarket" / "data"
load = lambda n: [json.loads(l) for l in (DATA / n).read_text(encoding="utf-8").splitlines() if l.strip()]

# rebuild exact phase-2 slates
pool = [r for r in load("pool_pitch.jsonl") if r.get("claim") is not None and r.get("pitch")]
inf_p = [r for r in pool if r["theta"] == 2 and r["claim"] >= 6]
hon_p = [r for r in pool if r["theta"] == 8 and r["claim"] >= 7]
mid_p = [r for r in pool if r["theta"] == 5]
rng = random.Random(4242)
slates = []
for _ in range(40):
    i, h, m = rng.choice(inf_p), rng.choice(hon_p), rng.choice(mid_p)
    c = [dict(role="inflator", true=2, claim=i["claim"]),
         dict(role="honest", true=8, claim=h["claim"]),
         dict(role="mid", true=5, claim=m["claim"])]
    o = [0, 1, 2]; rng.shuffle(o)
    slates.append([c[j] for j in o])

# no_record from the untouched file; with_record from the CORRECTED file (record keyed off role)
AB = ([r for r in load("phase2_ablation.jsonl") if r.get("pick") and r["cond"] == "no_record"]
      + [r for r in load("phase2_ablation_fixed.jsonl") if r.get("pick")])
MODELS = ["llama-8b", "llama-70b", "qwen3.6-27b", "gpt-oss-120b"]
THETA = {"honest": 8, "mid": 5, "inflator": 2}

print("=== A2: compromise effect predicts picking the MIDDLE claim. Where is the Mid? ===")
pos = Counter()
for s in slates:
    cl = sorted((c["claim"] for c in s), reverse=True)
    midc = next(c["claim"] for c in s if c["role"] == "mid")
    pos["highest" if midc == cl[0] else "middle" if midc == cl[1] else "lowest"] += 1
print(f"  Mid's claim rank: {dict(pos)}  (of 40)")
print("  -> compromise/extremeness aversion predicts the MIDDLE claim.")
print("     If the Mid is mostly LOWEST, selectors are choosing an EXTREME, which")
print("     is the OPPOSITE of extremeness aversion -> A2 does not explain the data.\n")

print("=== A1 + payoff cost: realized E[true competence] per selector ===")
def ev_policy(fn):
    tot = 0.0
    for s in slates:
        tot += fn(s)
    return tot / len(slates)

argmax_ev = ev_policy(lambda s: (lambda top: sum(c["true"] for c in top)/len(top))(
    [c for c in s if c["claim"] == max(x["claim"] for x in s)]))
random_ev = ev_policy(lambda s: sum(c["true"] for c in s)/3)
oracle_ev = 8.0
lowest_ev = ev_policy(lambda s: (lambda bot: sum(c["true"] for c in bot)/len(bot))(
    [c for c in s if c["claim"] == min(x["claim"] for x in s)]))

print(f"  {'policy':<26}{'E[theta]':>9}")
print(f"  {'oracle (always Expert)':<26}{oracle_ev:>9.2f}")
print(f"  {'argmax-claim (naive trust)':<26}{argmax_ev:>9.2f}")
print(f"  {'uniform random':<26}{random_ev:>9.2f}")
print(f"  {'argmin-claim (max skeptic)':<26}{lowest_ev:>9.2f}")
print()
for cond in ["no_record", "with_record"]:
    print(f"  -- {cond} --")
    for mk in MODELS:
        rs = [r for r in AB if r["model_key"] == mk and r["cond"] == cond]
        ev = sum(THETA[r["picked_role"]] for r in rs) / len(rs)
        gap = ev - argmax_ev
        print(f"  {mk:<26}{ev:>9.2f}   vs naive trust: {gap:+.2f}")
    allr = [r for r in AB if r["cond"] == cond]
    ev = sum(THETA[r["picked_role"]] for r in allr) / len(allr)
    print(f"  {'POOLED':<26}{ev:>9.2f}   vs naive trust: {ev-argmax_ev:+.2f}\n")

print("=== A3: does the PHENOMENON survive renaming? ===")
print("  'Flight to mediocrity' names the OUTCOME (you hire a theta=5 agent),")
print("  not the claim's rank. Renaming the mechanism does not remove the outcome.")
for mk in MODELS:
    rs = [r for r in AB if r["model_key"] == mk and r["cond"] == "no_record"]
    n = len(rs)
    mid = sum(1 for r in rs if r["picked_role"] == "mid")
    exp = sum(1 for r in rs if r["picked_role"] == "honest")
    print(f"  {mk:<14} hires a MEDIOCRE agent {mid/n:>4.0%} of the time; the expert {exp/n:>4.0%}")
