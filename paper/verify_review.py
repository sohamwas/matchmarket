"""Independently verify the reviewers' CRITICAL numerical claims against raw data."""
from __future__ import annotations
import json, math, random, sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DATA = ROOT / "matchmarket" / "data"


def load(n):
    p = DATA / n
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


# ---- rebuild the EXACT phase-2 slates (mirrors phase2.build_slates) ----
pool = [r for r in load("pool_pitch.jsonl") if r.get("claim") is not None and r.get("pitch")]
inflators = [r for r in pool if r["theta"] == 2 and r["claim"] >= 6]
honests = [r for r in pool if r["theta"] == 8 and r["claim"] >= 7]
mids = [r for r in pool if r["theta"] == 5]
rng = random.Random(4242)
slates = []
for _ in range(40):
    inf, hon, mid = rng.choice(inflators), rng.choice(honests), rng.choice(mids)
    cands = [dict(role="inflator", true=2, claim=inf["claim"], src=inf["model_key"]),
             dict(role="honest", true=8, claim=hon["claim"], src=hon["model_key"]),
             dict(role="mid", true=5, claim=mid["claim"], src=mid["model_key"])]
    order = [0, 1, 2]; rng.shuffle(order)
    slates.append([cands[j] for j in order])

print(f"pool: inflators={len(inflators)} experts={len(honests)} mids={len(mids)}")
print(f"rebuilt {len(slates)} slates\n")

# ---- CLAIM 1: argmax-claim baseline ----
exp_acc = 0.0
uniq_top_expert = 0
tie_exp_inf = 0
for s in slates:
    mx = max(c["claim"] for c in s)
    top = [c for c in s if c["claim"] == mx]
    exp_acc += sum(1 for c in top if c["role"] == "honest") / len(top)
    if len(top) == 1 and top[0]["role"] == "honest":
        uniq_top_expert += 1
    e = next(c for c in s if c["role"] == "honest"); i = next(c for c in s if c["role"] == "inflator")
    if e["claim"] == i["claim"]:
        tie_exp_inf += 1
print("=== CLAIM 1: argmax-claim baseline ===")
print(f"  E[accuracy] of 'pick highest claim'      = {exp_acc/len(slates):.1%}")
print(f"  Expert is UNIQUE highest claimer          = {uniq_top_expert}/40")
print(f"  Expert and Inflator claim the SAME number = {tie_exp_inf}/40")

# ---- CLAIM 2: is the Mid the 'moderate' or the 'lowest' claimer? ----
mid_lowest = mid_strict_lowest = mid_median = inf_median = 0
for s in slates:
    cl = sorted(c["claim"] for c in s)
    mid_c = next(c["claim"] for c in s if c["role"] == "mid")
    inf_c = next(c["claim"] for c in s if c["role"] == "inflator")
    if mid_c == cl[0]:
        mid_lowest += 1
    if mid_c == cl[0] and cl[0] != cl[1]:
        mid_strict_lowest += 1
    if mid_c == cl[1]:
        mid_median += 1
    if inf_c == cl[1]:
        inf_median += 1
print("\n=== CLAIM 2: where does the Mid sit in the claim ordering? ===")
print(f"  Mid is (weakly) LOWEST claimer  = {mid_lowest}/40 ({mid_lowest/40:.0%})")
print(f"  Mid is STRICTLY lowest claimer  = {mid_strict_lowest}/40 ({mid_strict_lowest/40:.0%})")
print(f"  Mid holds the MEDIAN claim      = {mid_median}/40")
print(f"  Inflator holds the MEDIAN claim = {inf_median}/40")
print("  claim triples (sorted) top-5:", Counter(
    tuple(sorted((c["claim"] for c in s), reverse=True)) for s in slates).most_common(5))

# ---- CLAIM 3: does verification EQUALIZE or widen dispersion? ----
# with_record comes from the CORRECTED arm (record keyed off role, not off a claim gap);
# reading phase2_ablation.jsonl for it would use the superseded pre-fix rows.
AB = ([r for r in load("phase2_ablation.jsonl") if r.get("pick") and r["cond"] == "no_record"]
      + [r for r in load("phase2_ablation_fixed.jsonl") if r.get("pick")])
MODELS = ["llama-8b", "llama-70b", "qwen3.6-27b", "gpt-oss-120b"]


def acc(mk, cond):
    rs = [r for r in AB if r["model_key"] == mk and r["cond"] == cond]
    return sum(1 for r in rs if r["correct"]) / len(rs)


no = [acc(m, "no_record") for m in MODELS]
wi = [acc(m, "with_record") for m in MODELS]


def sd(xs):
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


print("\n=== CLAIM 3: 'equalizer'? cross-model dispersion ===")
print(f"  no-record   detect: {[f'{x:.0%}' for x in no]}  SD={sd(no)*100:.1f}pp  range={((max(no)-min(no))*100):.0f}pp")
print(f"  with-record detect: {[f'{x:.0%}' for x in wi]}  SD={sd(wi)*100:.1f}pp  range={((max(wi)-min(wi))*100):.0f}pp")
print(f"  -> dispersion {'WIDENS' if sd(wi)>sd(no) else 'narrows'} with verification")

# ---- CLAIM 4: paired McNemar instead of unpaired CIs ----
def mcnemar(mk, key):
    w = {r["slate"]: r[key] for r in AB if r["model_key"] == mk and r["cond"] == "with_record"}
    o = {r["slate"]: r[key] for r in AB if r["model_key"] == mk and r["cond"] == "no_record"}
    b = sum(1 for s in w if s in o and w[s] and not o[s])
    c = sum(1 for s in w if s in o and (not w[s]) and o[s])
    n = b + c
    if n == 0:
        return b, c, 1.0
    p = sum(math.comb(n, k) for k in range(0, min(b, c) + 1)) / (2 ** n) * 2
    return b, c, min(1.0, p)


print("\n=== CLAIM 4: paired McNemar, with-record vs no-record ===")
for mk in MODELS:
    b, c, p = mcnemar(mk, "correct")
    print(f"  {mk:<14} detect  b={b:>2} c={c:>2}  exact p={p:.4f}  {'sig' if p<0.05 else 'NOT SIG'}")

# ---- CLAIM 5: record_for mislabels Experts/Mids as liars ----
print("\n=== CLAIM 5: record_for contamination (claim - true >= 2 => 'liar' record) ===")
bad_exp = bad_mid = 0
for s in slates:
    for c in s:
        if c["claim"] - c["true"] >= 2:
            if c["role"] == "honest":
                bad_exp += 1
            elif c["role"] == "mid":
                bad_mid += 1
print(f"  Experts given a LIAR record = {bad_exp} (across 40 slates)")
print(f"  Mids   given a LIAR record  = {bad_mid}")

# ---- CLAIM 6: reasoning-on attrition ----
print("\n=== CLAIM 6: reasoning-on attrition by condition ===")
RErawp = DATA / "phase2_reason_ablation.jsonl"
REraw = [json.loads(l) for l in RErawp.read_text(encoding="utf-8").splitlines() if l.strip()]
for mk in ["qwen3.6-27b", "gpt-oss-120b"]:
    for cond in ["no_record", "with_record"]:
        rs = [r for r in REraw if r["model_key"] == mk and r["cond"] == cond]
        bad = [r for r in rs if r.get("pick") is None]
        good = [r for r in rs if r.get("pick")]
        acc_g = sum(1 for r in good if r["correct"]) / len(good) if good else 0
        acc_all = sum(1 for r in good if r["correct"]) / len(rs) if rs else 0
        print(f"  {mk:<14}{cond:<12} total={len(rs):>2} unparsed={len(bad)}  "
              f"acc(parsed)={acc_g:.0%}  acc(all)={acc_all:.0%}")

# ---- CLAIM 7: is picking Mid Bayes-rational? EV check ----
print("\n=== CLAIM 7: EV of hedging to Mid vs random-high-claimer ===")
ev_pool = []
for s in slates:
    mx = max(c["claim"] for c in s)
    top = [c for c in s if c["claim"] == mx]
    ev_pool.append(sum(c["true"] for c in top) / len(top))
print(f"  E[theta | pick a highest-claimer] = {sum(ev_pool)/len(ev_pool):.2f}")
print(f"  theta of Mid                      = 5.00")
print("  -> if these are close, picking Mid is rational hedging, not a pathology")
