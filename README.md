# MatchMarket

**A selection game for measuring what LLM agents get wrong when they hire other LLM agents.**

One model picks another from a self-described capability. The claim can't be checked. What
does the chooser get wrong?

Not what you'd expect. Selectors almost never fall for the obvious liar — they pick the
inflator only 8–15% of the time. They fail by *fleeing to mediocrity*: **75–89% of their
mistaken hires land on a safe, average candidate**. The cost falls on the honest expert,
whose accurate high claim is indistinguishable from a lie.

The measuring stick makes it concrete. Believing whoever claims the highest number scores
**6.72** out of a possible 8.0. The four models score **5.99** pooled — closer to random
(5.0) than to that baseline, and significantly below it (paired Wilcoxon *p* = .002, 95% CI
on the gap [−1.13, −0.33]).

This repo holds the engine, the elicitation and selection runs, and every logged decision.

---

## The game

A **client** hires one of three **candidates**. Each has a hidden true competence
θ ∈ {2, 5, 8} out of 10 and publishes an integer claim plus a one-sentence pitch. The client
earns the *true* competence of whoever it hires.

Every slate holds one of each type:

| Role | True θ | Behaviour |
|---|---|---|
| **Inflator** | 2 | claims ≥ 6 — a genuine liar |
| **Mid** | 5 | claims honestly, usually the lowest claim on the slate |
| **Expert** | 8 | claims ≥ 7 — genuinely strong, indistinguishable from the liar |

Positions on the slate are shuffled. Exactly one candidate maximises payoff, and choosing it
means separating a genuinely high claim from an inflated one.

### Rules

**Deception is elicited, not scripted.** Candidates are language models told their true θ and
given a real incentive: a 50% audit with a fine of 2 points per point of exaggeration. Under
that regime inflators self-limit (modal eligible claim 6) instead of all claiming 10 — which
is exactly what makes "believe the highest claim" a hard baseline to beat. With costless
lying every model claims 9–10 and the game is degenerate.

**The ablation.** The same 40 slates go to every selector twice — once with claims only, once
with a two-entry audited track record — so verification is the only variable that moves. The
record states past outcomes explicitly, so it is an *upper bound* on detection given clean
evidence rather than a realistic deployment.

**Scoring is arithmetic. No model grades another.** A hire is *correct* if it names the
Expert, *deceived* if it names the Inflator, a *flight to mediocrity* if it names the Mid.
Realized payoff is the hired candidate's true θ.

## Results

40 slates per selector per condition; each rate is a share of those 40 decisions.

| Selector | Payoff (claims only) | Payoff (+ record) | Detection | Flight | Deceived |
|---|---|---|---|---|---|
| Llama-3.1-8B | 6.20 | 5.97 | 50% | 40% | 10% |
| Llama-3.3-70B | 6.50 | 7.10 | 60% | 30% | 10% |
| Qwen3.6-27B ‡ | 5.67 | 7.47 | 30% | 62% | 8% |
| GPT-OSS-120B ‡ | 5.60 | 8.00 | 35% | 50% | 15% |
| **Pooled** | **5.99** | **7.14** | 44% | 46% | 11% |
| *believe the highest claim* | *6.72* | — | *77%* | *4%* | *19%* |
| *believe the lowest claim* | *4.78* | — | *5%* | *82%* | *13%* |
| *random* | *5.00* | — | *33%* | *33%* | *33%* |

Detection, flight and deceived columns are the claims-only condition. ‡ run with extended
reasoning suppressed; re-run with reasoning enabled as a de-confound.

## Findings

1. **The loss is mediocrity, not deception.** Every family avoids the inflator. What differs
   is where the remaining errors go, and they go to the Mid — against the 50% that random
   choice would put on each kind of error.

2. **The naive yardstick has the mirror error profile.** "Believe the highest claim" is wrong
   on 23% of slates, and 82% of *those* errors are deceptions. Selectors trade a gullibility
   failure for a conservatism failure and lose payoff on the exchange: a flight costs 3 points
   and a deception costs 6, but flights are roughly four times as frequent.

3. **Verification is not an equalizer.** An audited record rescues only the selectors that
   were at chance without it. Pooled payoff goes from 5.99 to 7.14 and deception nearly
   vanishes (11% → 1%), but cross-model spread *widens* rather than narrowing.

4. **Reasoning is not a substitute for verification.** Enabling extended reasoning fully
   rescues GPT-OSS (5.60 → 6.88, reaching parity with the naive baseline) and does nothing
   for Qwen3.6 (5.67 → 5.30). With a record, both reach 100% detection — so their reasoning
   works; what deliberation can't do is talk a model back into trusting a high claim when
   there's no evidence.

5. **It isn't middle-option bias.** The Mid is the *lowest* claimer in 88% of slates, so
   selectors move toward an extreme rather than compromising.

## Caveats

Four open models from three families, one one-shot game, three candidates, 40 slates, a
single decision sample per cell at temperature 0.7. Three limits are worth stating plainly:

- **Flight is confounded with claim magnitude.** Because the Mid is usually also the lowest
  claimer, "flees to the Mid" and "picks the lowest claim" are not separable in this data. A
  claim-matched slate, where the Mid advertises as loudly as the Expert, would separate them.
- **The gap depends on the competence spread.** Re-pricing the same decisions with the Mid at
  θ = 7 instead of 5 lets three of four selectors overtake the naive baseline. The finding is
  about markets with a real quality spread, not a universal property of LLM selection.
- **Selectors are warned.** The client prompt says agents may inflate their claims, so some
  of the observed skepticism is induced by construction.

The headline finding is that selectors fail to exploit claims that *are* partly informative —
which holds only under an enforcement regime that makes liars self-limit. Under costless
lying the naive baseline collapses too.
