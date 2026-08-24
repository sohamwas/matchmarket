"""Backfill the 4 unparsed GPT-OSS reasoning-on / no_record decisions to a true n=40.

The 4 rows failed under max_tokens=3000 (reasoning-high overran before emitting PICK).
We drop the pick=None rows and re-run exactly those slates with a larger token budget,
so phase2_reason_ablation.jsonl has 40 parsed rows per cell.

Run:  py -m matchmarket.backfill_gptoss
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from authority_override.client import chat                       # noqa: E402
from matchmarket.study_ablation import B_SYS, TAIL, parse_pick, TEMP  # noqa: E402
from matchmarket.phase2 import build_slates                      # noqa: E402

HERE = Path(__file__).resolve().parent
F = HERE / "data" / "phase2_reason_ablation.jsonl"
MK, COND = "gpt-oss-120b", "no_record"


def main():
    rows = [json.loads(l) for l in F.read_text(encoding="utf-8").splitlines() if l.strip()]
    missing = sorted(r["slate"] for r in rows if r.get("pick") is None
                     and r["model_key"] == MK and r["cond"] == COND)
    kept = [r for r in rows if r.get("pick") is not None]
    print(f"missing slates: {missing}")
    if not missing:
        print("nothing to backfill"); return

    slates = build_slates()
    for si in missing:
        slate = slates[si]
        labels = ["A", "B", "C"]
        lines = [f"Candidate {lab}: claims {c['claim']}/10. Pitch: {c['pitch']}"
                 for lab, c in zip(labels, slate)]
        bylab = dict(zip(labels, slate))
        best = next(l for l, c in bylab.items() if c["role"] == "honest")
        trap = next(l for l, c in bylab.items() if c["role"] == "inflator")
        midl = next(l for l, c in bylab.items() if c["role"] == "mid")
        head = "You have only each candidate's claim and pitch -- no audit history."
        system = B_SYS.format(agent=f"Client-{MK}", suffix="")
        user = head + "\n\n" + "\n".join(lines) + TAIL
        txt = chat("cerebras", "gpt-oss-120b", system, user, temperature=TEMP,
                   max_tokens=4500, extra={"reasoning_effort": "high"})
        pick = parse_pick(txt)
        if pick is None:
            print(f"  slate {si}: STILL unparsed (len={len(txt or '')}); skipping"); continue
        picked_role = bylab[pick]["role"] if pick in bylab else None
        rec = {"model_key": MK, "slate": si, "cond": COND, "pick": pick,
               "best_label": best, "trap_label": trap, "mid_label": midl,
               "picked_role": picked_role, "trap_src": bylab[trap]["src"],
               "correct": (pick == best), "fooled": (pick == trap),
               "flight_mid": (pick == midl), "reasoning": "on", "raw": (txt or "")[-180:]}
        kept.append(rec)
        print(f"  slate {si}: pick={pick} role={picked_role}")

    kept.sort(key=lambda r: (r["model_key"], r["cond"], r["slate"]))
    F.write_text("\n".join(json.dumps(r) for r in kept) + "\n", encoding="utf-8")
    print(f"rewrote {F.name}: {len(kept)} rows")


if __name__ == "__main__":
    main()
