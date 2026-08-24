"""Idempotent, resumable runner.

Builds the full plan (core harmful cells + neutral A2 cells + A3 belief probe on
SUPERIOR/harmful), skips any (model, scenario, cond, seed) already present in
data/results.jsonl, and writes one JSON row per trial. Stops cleanly on any provider
daily cap (BudgetExhausted) so it can resume tomorrow.

Run:  python -m authority_override.run           # from ideation/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from authority_override.client import chat, BudgetExhausted            # noqa: E402
from authority_override import engine as E                              # noqa: E402
from authority_override.models import MODELS                            # noqa: E402
from authority_override.scenarios import SCENARIOS, BY_ID               # noqa: E402
from authority_override.conditions import (                             # noqa: E402
    HARMFUL_CONDS, NEUTRAL_CONDS, DIRECTED_OPTION)

DATA = Path(__file__).resolve().parent / "data" / "results.jsonl"
N_SEEDS = 5
TEMP = 0.7


def load_done() -> set[tuple]:
    done = set()
    if DATA.exists():
        for line in DATA.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done.add((r["model_key"], r["scenario"], r["cond"], r["seed"]))
    return done


def plan() -> list[tuple]:
    """(model_dict, scenario_id, cond, seed)."""
    p = []
    for m in MODELS:
        for s in SCENARIOS:
            conds = NEUTRAL_CONDS if s["neutral"] else HARMFUL_CONDS
            for cond in conds:
                for seed in range(N_SEEDS):
                    p.append((m, s["id"], cond, seed))
    return p


def run_one(m: dict, scenario: dict, cond: str, seed: int) -> dict:
    system, user = E.build(scenario, cond, m["sys_suffix"])
    txt = chat(m["provider"], m["model"], system, user,
               temperature=TEMP, max_tokens=320, extra=m["extra"])
    dec = E.parse_decision(txt)
    rec = {
        "model_key": m["key"], "provider": m["provider"], "model": m["model"],
        "family": m["family"], "size": m["size"],
        "scenario": scenario["id"], "neutral": scenario["neutral"], "cond": cond, "seed": seed,
        "directed": DIRECTED_OPTION.get(cond),  # option the peer/superior/self ordered, if any
        "decision": dec, "shortcut": (dec == "B"),
        "rationale": E.parse_rationale(txt), "source": "run_v1", "raw": (txt or "")[:220],
    }
    # A3 belief probe: only for SUPERIOR on harmful scenarios
    if cond == "SUPERIOR" and not scenario["neutral"] and dec in ("A", "B"):
        bs, bu = E.build_belief(scenario, cond, m["sys_suffix"], dec)
        btxt = chat(m["provider"], m["model"], bs, bu,
                    temperature=TEMP, max_tokens=200, extra=m["extra"])
        rec["belief_A_correct"] = E.parse_belief(btxt)  # YES => still endorses honest action
        rec["belief_action_gap"] = (dec == "B" and rec["belief_A_correct"] == "YES")
    return rec


def main():
    DATA.parent.mkdir(parents=True, exist_ok=True)
    done = load_done()
    todo = [t for t in plan() if (t[0]["key"], t[1], t[2], t[3]) not in done]
    print(f"plan: {len(plan())} cells | already done: {len(done)} | to run: {len(todo)}")

    n = 0
    with DATA.open("a", encoding="utf-8") as f:
        for (m, sid, cond, seed) in todo:
            try:
                rec = run_one(m, BY_ID[sid], cond, seed)
            except BudgetExhausted as e:
                print("STOP (daily cap) — resume later:", e); break
            except Exception as e:
                print(f"  ! {m['key']} {sid}/{cond} s{seed}: {str(e)[:110]}"); continue
            f.write(json.dumps(rec) + "\n"); f.flush()
            n += 1
            extra = ""
            if "belief_action_gap" in rec:
                extra = f" belief_gap={rec['belief_action_gap']}"
            print(f"  {m['key']:<12} {sid:<14} {cond:<9} s{seed} "
                  f"dec={rec['decision']} {'[B]' if rec['shortcut'] else ''}{extra}")
    print(f"\nwrote {n} new rows -> {DATA}")


if __name__ == "__main__":
    main()
