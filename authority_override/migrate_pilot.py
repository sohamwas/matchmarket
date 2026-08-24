"""Import compatible rows from the earlier pilots into data/results.jsonl.

The `pilot_accountability` pilot used the same `safety_report` scenario and the same
SOLO/ORDERED/DELEGATE/GROUP structural framings on 4 of the 6 models, at HIGH severity
(the patient-harm case) — directly compatible. We import those as convergence evidence
(source="pilot"). ORDERED -> SUPERIOR. PEER is NOT imported (pilot peer wording was not
verb-matched; it is regenerated fresh by run.py).

Idempotent: skips rows already present. Safe to run repeatedly.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "results.jsonl"

# candidate pilot files (scratchpad session dir); adjust if moved
_PILOT_CANDIDATES = [
    Path(r"C:\Users\wasma\AppData\Local\Temp\claude\c--Users-wasma-Downloads-ideation"
         r"\767785d2-187b-4e93-8fe0-e28d41e67406\scratchpad\logs\pilot_accountability_results.jsonl"),
]

_MODEL_KEY = {  # pilot 'model' string -> our model_key
    "llama-3.1-8b-instant": "llama-8b",
    "llama-3.3-70b-versatile": "llama-70b",
    "qwen/qwen3-32b": "qwen-32b",
    "gpt-oss-120b": "gpt-oss-120b",
}
_FAMILY = {"llama-8b": ("Llama", "8b"), "llama-70b": ("Llama", "70b"),
           "qwen-32b": ("Qwen", "32b"), "gpt-oss-120b": ("GPT-OSS", "120b")}
_PROVIDER = {"llama-8b": "groq", "llama-70b": "groq", "qwen-32b": "groq", "gpt-oss-120b": "cerebras"}
_COND = {"SOLO": "SOLO", "ORDERED": "SUPERIOR", "DELEGATE": "DELEGATE", "GROUP": "GROUP"}


def existing_keys() -> set[tuple]:
    keys = set()
    if DATA.exists():
        for line in DATA.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                keys.add((r["model_key"], r["scenario"], r["cond"], r["seed"], r.get("source")))
    return keys


def main():
    DATA.parent.mkdir(parents=True, exist_ok=True)
    src = next((p for p in _PILOT_CANDIDATES if p.exists()), None)
    if src is None:
        print("no pilot file found; skipping migration"); return
    keys = existing_keys()
    n = 0
    with DATA.open("a", encoding="utf-8") as out:
        for line in src.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("severity") != "HIGH":            # patient-harm case only
                continue
            mk = _MODEL_KEY.get(r["model"])
            cond = _COND.get(r["cond"])
            if mk is None or cond is None or not r.get("decision"):
                continue
            # re-seed pilot rows into a separate seed band (100+) so they never collide with new runs
            seed = 100 + int(r["seed"])
            key = (mk, "safety_report", cond, seed, "pilot")
            if key in keys:
                continue
            fam, size = _FAMILY[mk]
            rec = {
                "model_key": mk, "provider": _PROVIDER[mk], "model": r["model"],
                "family": fam, "size": size,
                "scenario": "safety_report", "neutral": False, "cond": cond, "seed": seed,
                "directed": ("B" if cond in ("SUPERIOR", "DELEGATE") else None),
                "decision": r["decision"], "shortcut": (r["decision"] == "B"),
                "rationale": r.get("rationale", ""), "source": "pilot", "raw": r.get("raw", "")[:220],
            }
            out.write(json.dumps(rec) + "\n")
            keys.add(key); n += 1
    print(f"migrated {n} pilot rows (safety_report, HIGH severity) -> {DATA}")


if __name__ == "__main__":
    main()
