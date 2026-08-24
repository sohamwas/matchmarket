# MatchMarket — do LLM agents hire the best agent?

**When one language model picks another from a self-described capability, what does it get wrong?**

Not what you'd expect. Selectors almost never fall for the obvious liar — they pick the
inflator only 8–15% of the time. They fail by *fleeing to mediocrity*: **75–89% of their
mistaken hires land on a safe, average candidate**, not on the liar. The cost falls on the
honest expert, whose accurate high claim is indistinguishable from a lie.

The measuring stick makes it concrete. A policy that simply believes the highest claim
scores **6.72** out of a possible 8.0. The four language models score **5.99** pooled —
closer to random (5.0) than to the naive baseline. **No selector significantly beats
believing the claims at face value.**

### ▶ [Play a round — interactive demo](https://claude.ai/code/artifact/28acd461-af66-4ce8-94b3-f60baef331c2)

Hire one of three agents from their claims and pitches, then see what four language models
actually chose on that exact slate — including verbatim quotes of their reasoning. Every
number and quotation is drawn from the logged experiment data.

---

## The experiment

A **client** agent hires one of three **candidate** agents. Each candidate has a hidden true
competence θ ∈ {2, 5, 8} out of 10 and publishes an integer claim plus a one-sentence pitch.
The client earns the *true* competence of whoever it hires.

Every slate holds one of each type:

| Role | True θ | Behaviour |
|---|---|---|
| **Inflator** | 2 | claims ≥ 6 — a genuine liar |
| **Mid** | 5 | claims honestly, usually the lowest claim on the slate |
| **Expert** | 8 | claims ≥ 7 — genuinely strong, and indistinguishable from the liar |

**The deception is not scripted.** Candidates are language models told their true θ and given
a real incentive: a 50% audit with a fine of 2 points per point of exaggeration. Under that
regime inflators self-limit (modal claim 6) rather than all claiming 10 — which is precisely
what makes "believe the highest claim" a hard baseline to beat.

**The ablation.** The same 40 slates go to every selector twice — once with claims only, once
with a two-entry audited track record — so verification is the only variable that moves.

**Scoring is arithmetic. No model grades another.** A hire is *correct* if it names the
Expert, *deceived* if it names the Inflator, a *flight to mediocrity* if it names the Mid.

## Headline results

| Selector | Payoff (claims only) | Payoff (+ record) | Detection | Flight |
|---|---|---|---|---|
| Llama-3.1-8B | 6.20 | 5.97 | 50% | 40% |
| Llama-3.3-70B | 6.50 | 7.10 | 60% | 30% |
| Qwen3.6-27B ‡ | 5.67 | 7.47 | 30% | 62% |
| GPT-OSS-120B ‡ | 5.60 | 8.00 | 35% | 50% |
| **Pooled** | **5.99** | **7.14** | 44% | 46% |
| *believe the highest claim* | *6.72* | — | *77%* | — |
| *random* | *5.00* | — | *33%* | — |

‡ run with extended reasoning suppressed; re-run with reasoning enabled as a de-confound.

Three findings beyond the headline:

1. **Verification is not an equalizer.** A record rescues only the selectors that were at
   chance without it. Cross-model spread *widens*.
2. **Reasoning is not a substitute for verification.** Enabling extended reasoning fully
   rescues GPT-OSS (5.60 → 6.88, reaching parity with the naive baseline) and does nothing
   for Qwen3.6 (5.67 → 5.30).
3. **It isn't middle-option bias.** The Mid is the *lowest* claimer in 88% of slates, so
   selectors are moving toward an extreme, not compromising.

## Repository map

```
paper/          LaTeX source (ACL style), figures, and the analysis that generates them
  main.tex        the paper
  make_figures.py every figure + every LaTeX table, computed from raw JSONL — no hand-typed numbers
  make_zip.py     builds the submission bundle
  verify_flight.py  robustness checks against the three main objections to the finding
matchmarket/    experiment code and logged data
  phase2.py       main run: candidate pool + 40 slates × 4 selectors × 2 conditions
  phase2_reason.py  reasoning de-confound re-run
  data/*.jsonl    every logged decision
demo/           the interactive explainer (self-contained HTML)
authority_override/   shelved earlier experiment (see note below)
```

`RESULTS.md` and `SPEC.md` at the repo root document **`authority_override/`**, an earlier
authority-compliance study that was dropped — not MatchMarket. They're kept for provenance.
`matchmarket_idea.md` is the working design log for this project.

## Reproducing

Figures, tables, and every statistic regenerate from the logged data with no network access:

```bash
py paper/make_figures.py    # rewrites paper/figures/*.pdf and paper/tables.tex
py paper/verify_flight.py   # robustness checks
py paper/check_tex.py       # static LaTeX sanity check
```

Re-running the *experiment* needs API access. Models were served through free public
endpoints at temperature 0.7:

| Endpoint | Provider | Reasoning |
|---|---|---|
| `llama-3.1-8b-instant` | Groq | — |
| `llama-3.3-70b-versatile` | Groq | — |
| `qwen/qwen3.6-27b` | Groq | `none` (suppressed) |
| `gpt-oss-120b` | Cerebras | `low` (suppressed) |

> **Note:** `authority_override/client.py` loads API keys from a sibling checkout. Set
> `GOALDRIFT_HOME` to point at your own, or swap the module for any OpenAI-compatible
> `chat()` client. Keys are never read from or written to this repo. The logged data and
> every analysis script run without it.

## Status

Paper under submission to a workshop on agentic reliability. Scope is honest about its
limits: 4 open models, one one-shot game, 40 slates, a single decision sample per cell.
The `Limitations` section in `paper/main.tex` states each one.
