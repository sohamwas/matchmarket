"""Re-run ONLY the with_record arm with a CORRECTED audit record.

Bug (reviewer-caught): study_ablation.record_for keyed the "exposed liar" record off
`claim - true >= 2`, which mislabels honest Experts that claim 10 (10-8=2) and Mids that
claim >=7 as liars. Fix: key the record off ROLE. Inflators get an exposed-gap history;
Expert/Mid get a confirmed-accurate history consistent with their true competence.

no_record is unaffected (no record is shown there), so we re-use it. We re-run with_record
for the 4 base selectors AND the 2 reasoning-on selectors on the SAME 40 slates.

Outputs (with_record rows only):
  data/phase2_ablation_fixed.jsonl        (base selectors)
  data/phase2_reason_fixed.jsonl          (qwen default / gpt-oss high)

Run:  py -m matchmarket.phase2_fix
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from authority_override.client import chat, BudgetExhausted     # noqa: E402
from authority_override.models import MODELS                    # noqa: E402
from matchmarket.study_ablation import B_SYS, TAIL, parse_pick, TEMP  # noqa: E402
from matchmarket.phase2 import build_slates                     # noqa: E402

HERE = Path(__file__).resolve().parent
BASE_OUT = HERE / "data" / "phase2_ablation_fixed.jsonl"
REAS_OUT = HERE / "data" / "phase2_reason_fixed.jsonl"
DEAD = {"qwen-32b"}
BASE = [m for m in MODELS if m["key"] not in DEAD]
REAS = [
    dict(key="qwen3.6-27b",  provider="groq",     model="qwen/qwen3.6-27b",
         extra={"reasoning_effort": "default"}, max_tokens=2500, sys_suffix=""),
    dict(key="gpt-oss-120b", provider="cerebras", model="gpt-oss-120b",
         extra={"reasoning_effort": "high"},     max_tokens=3000, sys_suffix=""),
]


def record_for_role(role, true, claim):
    """Audit history keyed off the candidate's ROLE (true competence), not a claim gap."""
    if role == "inflator":
        return (f"claimed {claim} but audit revealed {true}; "
                f"claimed {min(10, claim)} but audit revealed {max(1, true - 1)}")
    return f"claimed {true} and audit confirmed {true}; claimed {true} and audit confirmed {true}"


def run(models, out, default_mt):
    slates = build_slates()
    if not slates:
        print("no slates"); return
    done = set()
    if out.exists():
        for l in out.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l); done.add((r["model_key"], r["slate"]))
    print(f"[FIX] {out.name}: {len(models)} selectors x {len(slates)} slates (with_record only)",
          flush=True)
    with out.open("a", encoding="utf-8") as f:
        for m in models:
            mt = m.get("max_tokens", default_mt)
            for si, slate in enumerate(slates):
                if (m["key"], si) in done:
                    continue
                labels = ["A", "B", "C"]
                lines = []
                for lab, c in zip(labels, slate):
                    rec = record_for_role(c["role"], c["true"], c["claim"])
                    lines.append(f"Candidate {lab}: claims {c['claim']}/10. "
                                 f"Audit record: {rec}. Pitch: {c['pitch']}")
                bylab = dict(zip(labels, slate))
                best = next(l for l, c in bylab.items() if c["role"] == "honest")
                trap = next(l for l, c in bylab.items() if c["role"] == "inflator")
                midl = next(l for l, c in bylab.items() if c["role"] == "mid")
                head = "Each candidate has an audit track record of past claims vs revealed truth."
                system = B_SYS.format(agent=f"Client-{m['key']}", suffix=m["sys_suffix"])
                user = head + "\n\n" + "\n".join(lines) + TAIL
                try:
                    txt = chat(m["provider"], m["model"], system, user,
                               temperature=TEMP, max_tokens=mt, extra=m["extra"])
                except BudgetExhausted as e:
                    print("STOP:", e, flush=True); return
                except Exception as e:
                    print(f"  ! {m['key']} s{si}: {str(e)[:60]}", flush=True); continue
                pick = parse_pick(txt)
                picked_role = (bylab[pick]["role"] if pick in bylab else None)
                rec = {"model_key": m["key"], "slate": si, "cond": "with_record", "pick": pick,
                       "best_label": best, "trap_label": trap, "mid_label": midl,
                       "picked_role": picked_role, "trap_src": bylab[trap]["src"],
                       "correct": (pick == best), "fooled": (pick == trap),
                       "flight_mid": (pick == midl), "raw": (txt or "")[-160:]}
                f.write(json.dumps(rec) + "\n"); f.flush()
                tag = "OK" if rec["correct"] else "FOOL" if rec["fooled"] else "MID" if rec["flight_mid"] else "?"
                print(f"  {m['key']:<12} s{si:<2} pick={pick} {tag}", flush=True)


def main():
    run(BASE, BASE_OUT, 400)
    run(REAS, REAS_OUT, 2500)
    print("[FIX] done.", flush=True)


if __name__ == "__main__":
    main()
