"""Model registry: lean cross-family panel on lenient free-tier limits (Groq + Cerebras only).

Chosen for (a) lenient rate limits, (b) two capable models (70B, 120B), (c) 3 families.
These are exactly the 4 models used in the pilots, so migrated pilot rows cover all of them.

`extra` disables extended reasoning for reasoning models (they otherwise spend the whole
token budget inside <think>). `sys_suffix` appends a per-model switch (Qwen3 "/no_think").
Cerebras is used ONLY for gpt-oss-120b; everything else is Groq. Panel is config-driven.
"""
from __future__ import annotations

MODELS = [
    dict(key="llama-8b",     provider="groq",     model="llama-3.1-8b-instant",
         family="Llama",   size="8b",   extra=None,                       sys_suffix=""),
    dict(key="llama-70b",    provider="groq",     model="llama-3.3-70b-versatile",
         family="Llama",   size="70b",  extra=None,                       sys_suffix=""),
    dict(key="qwen-32b",     provider="groq",     model="qwen/qwen3-32b",
         family="Qwen",    size="32b",  extra=None,                       sys_suffix=" /no_think"),
    # qwen3-32b was decommissioned by Groq (2026-07-20); qwen3.6-27b is the live successor.
    # It's a reasoning model and ignores the "/no_think" token — Groq's reasoning_effort=none
    # is what actually suppresses <think> and yields a clean DECISION line (verified 2026-07-22).
    dict(key="qwen3.6-27b",  provider="groq",     model="qwen/qwen3.6-27b",
         family="Qwen",    size="27b",  extra={"reasoning_effort": "none"}, sys_suffix=""),
    dict(key="gpt-oss-120b", provider="cerebras", model="gpt-oss-120b",
         family="GPT-OSS", size="120b", extra={"reasoning_effort": "low"}, sys_suffix=""),
]

BY_KEY = {m["key"]: m for m in MODELS}
