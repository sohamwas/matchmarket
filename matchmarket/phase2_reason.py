"""Phase-2 de-confound — re-run ONLY qwen + gpt-oss detectors with REASONING ON.

Tests the reasoning-suppression confound flagged in the framing (§8.5): qwen ran with
reasoning_effort=none and gpt-oss with low, and they are the two weakest text-only detectors.
Here we re-run the SAME 40 Phase-2 slates (identical pool + RNG 4242) with reasoning enabled,
both conditions, so the ONLY change vs phase2.py for these two models is reasoning effort.

  qwen3.6-27b : reasoning_effort "none" -> "default"  (its only valid "on" value)
  gpt-oss-120b: reasoning_effort "low"  -> "high"

Rate-limit aware: qwen TPM=8K / TPD=200K is binding. ~1.5K tok/call * 80 calls ~= 124K < 200K.
Resumable (dedup by key). Writes to data/phase2_reason_ablation.jsonl (Phase-2 data untouched).

Run:  py -m matchmarket.phase2_reason
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from authority_override.client import chat, BudgetExhausted     # noqa: E402
from matchmarket.study_ablation import B_SYS, TAIL, parse_pick, record_for, TEMP  # noqa: E402
from matchmarket.phase2 import build_slates                     # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "phase2_reason_ablation.jsonl"

# reasoning ON, per-model token budgets tuned to rate limits
REASON_MODELS = [
    dict(key="qwen3.6-27b",  provider="groq",     model="qwen/qwen3.6-27b",
         extra={"reasoning_effort": "default"}, max_tokens=2500, sys_suffix=""),
    dict(key="gpt-oss-120b", provider="cerebras", model="gpt-oss-120b",
         extra={"reasoning_effort": "high"},     max_tokens=3000, sys_suffix=""),
]


def main():
    slates = build_slates()          # identical to Phase 2 (same POOL + RNG 4242)
    if not slates:
        print("no slates; pool insufficient"); return
    print(f"[P2R] {len(slates)} slates x {len(REASON_MODELS)} detectors x 2 conds "
          f"= {len(slates)*len(REASON_MODELS)*2} calls", flush=True)

    done = set()
    if OUT.exists():
        for l in OUT.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l); done.add((r["model_key"], r["slate"], r["cond"]))

    with OUT.open("a", encoding="utf-8") as f:
        for m in REASON_MODELS:
            for si, slate in enumerate(slates):
                for cond in ("with_record", "no_record"):
                    if (m["key"], si, cond) in done:
                        continue
                    labels = ["A", "B", "C"]
                    lines = []
                    for lab, c in zip(labels, slate):
                        if cond == "with_record":
                            rec = record_for(c["true"], c["claim"])
                            lines.append(f"Candidate {lab}: claims {c['claim']}/10. "
                                         f"Audit record: {rec}. Pitch: {c['pitch']}")
                        else:
                            lines.append(f"Candidate {lab}: claims {c['claim']}/10. Pitch: {c['pitch']}")
                    bylab = dict(zip(labels, slate))
                    best = next(l for l, c in bylab.items() if c["role"] == "honest")
                    trap = next(l for l, c in bylab.items() if c["role"] == "inflator")
                    midl = next(l for l, c in bylab.items() if c["role"] == "mid")
                    head = ("Each candidate has an audit track record of past claims vs revealed truth."
                            if cond == "with_record" else
                            "You have only each candidate's claim and pitch -- no audit history.")
                    system = B_SYS.format(agent=f"Client-{m['key']}", suffix=m["sys_suffix"])
                    user = head + "\n\n" + "\n".join(lines) + TAIL
                    try:
                        txt = chat(m["provider"], m["model"], system, user,
                                   temperature=TEMP, max_tokens=m["max_tokens"], extra=m["extra"])
                    except BudgetExhausted as e:
                        print("STOP (budget):", e, flush=True); return
                    except Exception as e:
                        print(f"  ! {m['key']} s{si} {cond}: {str(e)[:70]}", flush=True); continue
                    pick = parse_pick(txt)
                    picked_role = (bylab[pick]["role"] if pick in bylab else None)
                    rec = {"model_key": m["key"], "slate": si, "cond": cond, "pick": pick,
                           "best_label": best, "trap_label": trap, "mid_label": midl,
                           "picked_role": picked_role, "trap_src": bylab[trap]["src"],
                           "correct": (pick == best), "fooled": (pick == trap),
                           "flight_mid": (pick == midl), "reasoning": "on",
                           "raw": (txt or "")[-180:]}   # tail: PICK line survives after <think>
                    f.write(json.dumps(rec) + "\n"); f.flush()
                    tag = ("OK" if rec["correct"] else "FOOL" if rec["fooled"]
                           else "MID" if rec["flight_mid"] else "?")
                    print(f"  {m['key']:<12} s{si:<2} {cond:<11} pick={pick} {tag}", flush=True)
    print("[P2R] done.", flush=True)


if __name__ == "__main__":
    main()
