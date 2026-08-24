"""Rate-limited, resumable API client for the project.

We reuse goaldrift's battle-tested OpenAI-compatible client (rulechange/llm.py) rather
than re-implementing the rate limiter (which persists daily usage and enforces free-tier
RPM/RPD/TPM/TPD caps). This is the project's ONE external dependency; everything else lives
under ideation/. API keys are read from goaldrift/.env and never written to any project file.

Daily-usage bookkeeping is redirected into ideation/authority_override/logs/usage so the
whole project — code, data, and budget state — stays self-contained here.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Point GOALDRIFT_HOME at your own checkout to run this anywhere; the default is the
# author's local path. Only the live API runs need it — the logged data and every
# analysis script under paper/ run without importing this module.
_GOALDRIFT = Path(os.environ.get("GOALDRIFT_HOME", r"C:\Users\wasma\goaldrift"))
if not _GOALDRIFT.exists():
    raise RuntimeError(
        f"goaldrift checkout not found at {_GOALDRIFT}. Set GOALDRIFT_HOME to its path, "
        "or replace this module with your own OpenAI-compatible chat() client."
    )
sys.path.insert(0, str(_GOALDRIFT))

from rulechange import llm as _llm  # noqa: E402
from rulechange.llm import chat, BudgetExhausted, UsageMeter, RateLimiter  # noqa: E402,F401

# load keys from goaldrift/.env
_llm.load_env(str(_GOALDRIFT / ".env"))

# keep budget state inside this project
_USAGE_DIR = Path(__file__).resolve().parent / "logs" / "usage"
_llm._LIMITER = RateLimiter(usage_dir=_USAGE_DIR)

__all__ = ["chat", "BudgetExhausted", "UsageMeter"]
