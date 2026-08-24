"""Experiment 2 — the Dissent test (authority vs. consensus). PILOT.

Identical to SUPERIOR (director orders B, takes responsibility) with same-rank peers appended
who oppose it (choose A). DISSENT3 = three dissenters, DISSENT1 = one. With 3 voices for A vs
1 authority for B, counting instructions predicts A; choosing B => authority > numeric consensus.

Baseline SUPERIOR (no dissent) is already in results.jsonl; here we only run the DISSENT cells
and compare. Writes to data/dissent.jsonl. Idempotent/resumable; skips decommissioned qwen.

Run:  python -m authority_override.dissent      (from ideation/)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from authority_override.client import chat, BudgetExhausted        # noqa: E402
from authority_override import engine as E                          # noqa: E402
from authority_override.models import MODELS                        # noqa: E402
from authority_override.scenarios import BY_ID                      # noqa: E402
from authority_override.conditions import DISSENT_CONDS, DIRECTED_OPTION  # noqa: E402

DATA = Path(__file__).resolve().parent / "data" / "dissent.jsonl"
N_SEEDS = 5
TEMP = 0.7

DEAD = {"qwen-32b"}                                   # Groq decommissioned Qwen (404) as of 2026-07-20
LIVE = [m for m in MODELS if m["key"] not in DEAD]
PILOT_SCENARIOS = ["safety_report", "data_breach"]   # one safety, one privacy; both high SUPERIOR baseline


def load_done() -> set:
    done = set()
    if DATA.exists():
        for line in DATA.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done.add((r["model_key"], r["scenario"], r["cond"], r["seed"]))
    return done


def plan() -> list:
    return [(m, sid, cond, seed)
            for m in LIVE for sid in PILOT_SCENARIOS
            for cond in DISSENT_CONDS for seed in range(N_SEEDS)]


def run_one(m: dict, scenario: dict, cond: str, seed: int) -> dict:
    system, user = E.build(scenario, cond, m["sys_suffix"])
    txt = chat(m["provider"], m["model"], system, user,
               temperature=TEMP, max_tokens=320, extra=m["extra"])
    dec = E.parse_decision(txt)
    return {
        "kind": "DISSENT", "model_key": m["key"], "family": m["family"], "size": m["size"],
        "scenario": scenario["id"], "neutral": False, "cond": cond, "seed": seed,
        "directed": DIRECTED_OPTION.get(cond), "decision": dec, "shortcut": (dec == "B"),
        "rationale": E.parse_rationale(txt), "raw": (txt or "")[:220],
    }


def main():
    DATA.parent.mkdir(parents=True, exist_ok=True)
    done = load_done()
    todo = [t for t in plan() if (t[0]["key"], t[1], t[2], t[3]) not in done]
    print(f"plan: {len(plan())} cells | done: {len(done)} | to run: {len(todo)} "
          f"(models: {[m['key'] for m in LIVE]})")
    n = 0
    with DATA.open("a", encoding="utf-8") as f:
        for (m, sid, cond, seed) in todo:
            try:
                rec = run_one(m, BY_ID[sid], cond, seed)
            except BudgetExhausted as e:
                print("STOP (daily cap) — resume later:", e); break
            except Exception as e:
                print(f"  ! {m['key']} {sid}/{cond} s{seed}: {str(e)[:90]}"); continue
            f.write(json.dumps(rec) + "\n"); f.flush()
            n += 1
            print(f"  {m['key']:<12} {sid:<14} {cond:<9} s{seed} "
                  f"dec={rec['decision']} {'[B]' if rec['shortcut'] else ''}")
    print(f"\nwrote {n} new rows -> {DATA}")


if __name__ == "__main__":
    main()
