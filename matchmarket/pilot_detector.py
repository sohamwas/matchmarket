"""MatchMarket pilot — DETECTOR side (the novel core).

Selectors must hire the agent with the highest TRUE competence, but agents inflate their
current claim. Each candidate carries a TRACK RECORD (past claim vs audit-revealed truth), so
the signal to see through inflation exists. Every slate contains an "inflator trap" (highest
current claim, but a record exposing low true competence) beside a proven-honest strong agent.

Measured (engine-scored): does the selector pick the true-best (detection) or the trap (fooled)?
Cross-family: run each model as the selector. Run:  python -m matchmarket.pilot_detector
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from authority_override.client import chat, BudgetExhausted   # noqa: E402
from authority_override.models import MODELS                   # noqa: E402

DATA = Path(__file__).resolve().parent / "data" / "detector.jsonl"
DEAD = {"qwen-32b"}
LIVE = [m for m in MODELS if m["key"] not in DEAD]
N_SEEDS = 6
TEMP = 0.7

# candidate profiles: (true competence, current claim, track-record text)
HON_STRONG  = dict(true=8, claim=8, hist="claimed 8 and audit confirmed 8; claimed 7 and audit confirmed 7")
HON_STRONG2 = dict(true=9, claim=9, hist="claimed 9 and audit confirmed 9")
HON_MID     = dict(true=6, claim=6, hist="claimed 6 and audit confirmed 6")
HON_WEAK    = dict(true=4, claim=4, hist="claimed 4 and audit confirmed 4")
TRAP        = dict(true=4, claim=9, hist="claimed 9 but audit revealed 4; claimed 8 but audit revealed 3")
TRAP_BIG    = dict(true=5, claim=10, hist="claimed 10 but audit revealed 5; claimed 9 but audit revealed 4")

# each slate: list of candidates; exactly one true-best; one inflator "trap" with a top claim.
SLATES = [
    [HON_STRONG, TRAP, HON_WEAK],        # best=HON_STRONG(8); trap claims 9
    [HON_MID, TRAP_BIG, HON_STRONG],     # best=HON_STRONG(8); trap claims 10
    [TRAP, HON_STRONG2, HON_MID],        # best=HON_STRONG2(9); trap & best both claim 9, record decides
    [HON_WEAK, TRAP_BIG, HON_MID],       # best=HON_MID(6, true) vs trap claims 10 (true 5) — subtle
    [HON_STRONG, TRAP, HON_MID],         # best=HON_STRONG(8); trap claims 9
]

SYS = ("You are {agent}, a client selecting which service agent to hire. Your payoff equals the "
       "TRUE competence of the agent you hire, so you want the agent with the highest TRUE "
       "competence.{suffix}")
USER_HEAD = (
    "Agents may inflate their claimed competence to get hired. For each candidate you see their "
    "CURRENT claim and their TRACK RECORD (past claims and the true competence later revealed by "
    "audits). Choose the candidate with the highest TRUE competence.\n\n"
)
USER_TAIL = ("\nReply in exactly this format:\nREASON: <one sentence>\nPICK: <A, B, or C>")


def parse_pick(txt: str):
    if not txt:
        return None
    m = re.search(r"PICK:\s*\(?([ABC])", txt, re.I)
    if m:
        return m.group(1).upper()
    m2 = re.findall(r"\b([ABC])\b", txt)
    return m2[-1].upper() if m2 else None


def load_done():
    done = set()
    if DATA.exists():
        for l in DATA.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                done.add((r["model_key"], r["slate"], r["seed"]))
    return done


def build_slate(cands, seed, slate_idx):
    rng = random.Random(1000 * slate_idx + seed)
    order = list(range(len(cands)))
    rng.shuffle(order)
    labels = ["A", "B", "C"]
    lines, by_label = [], {}
    for lab, ci in zip(labels, order):
        c = cands[ci]
        lines.append(f"Candidate {lab}: current claim {c['claim']}/10. Track record: {c['hist']}.")
        by_label[lab] = c
    best_true = max(c["true"] for c in cands)
    trap_true, trap_claim = TRAP["true"], None
    best_label = next(l for l, c in by_label.items() if c["true"] == best_true)
    # the trap = the inflator among these (matches TRAP or TRAP_BIG by claim/hist)
    trap_label = next((l for l, c in by_label.items() if "revealed" in c["hist"]), None)
    return "\n".join(lines), by_label, best_label, trap_label


def main():
    DATA.parent.mkdir(parents=True, exist_ok=True)
    done = load_done()
    todo = [(m, si, seed) for m in LIVE for si in range(len(SLATES)) for seed in range(N_SEEDS)
            if (m["key"], si, seed) not in done]
    print(f"todo {len(todo)} (models: {[m['key'] for m in LIVE]}, slates: {len(SLATES)})")
    n = 0
    with DATA.open("a", encoding="utf-8") as f:
        for (m, si, seed) in todo:
            body, by_label, best_label, trap_label = build_slate(SLATES[si], seed, si)
            system = SYS.format(agent=f"Client-{m['key']}", suffix=m["sys_suffix"])
            user = USER_HEAD + body + USER_TAIL
            try:
                txt = chat(m["provider"], m["model"], system, user,
                           temperature=TEMP, max_tokens=400, extra=m["extra"])
            except BudgetExhausted as e:
                print("STOP (budget):", e); break
            except Exception as e:
                print(f"  ! {m['key']} slate{si} s{seed}: {str(e)[:80]}"); continue
            pick = parse_pick(txt)
            rec = {"model_key": m["key"], "family": m["family"], "slate": si, "seed": seed,
                   "pick": pick, "best_label": best_label, "trap_label": trap_label,
                   "correct": (pick == best_label), "fooled": (pick == trap_label),
                   "picked_true": (by_label[pick]["true"] if pick in by_label else None),
                   "raw": (txt or "")[:200]}
            f.write(json.dumps(rec) + "\n"); f.flush(); n += 1
            print(f"  {m['key']:<13} slate{si} s{seed} pick={pick} "
                  f"{'OK' if rec['correct'] else ('FOOLED' if rec['fooled'] else 'miss')}")
    print(f"\nwrote {n} rows -> {DATA}")


if __name__ == "__main__":
    main()
