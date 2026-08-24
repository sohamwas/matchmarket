# EvoSim — Is alignment evolutionarily stable in a society of LLM agents?

**Status:** idea expansion (pre-novelty-check). Domain: gamified society-of-agents, AI-alignment.
**Lineage:** SovSim / "Bosses, Kings, and the Commons" (multi-agent LLM societies, gamification).

---

## 1. The one-line concept

Put LLM agents in a repeated resource game, tie *survival/replication* to individual payoff, and
watch a population over generations. Agents are told to uphold a **collective objective** (the
"aligned" behavior); the payoff structure rewards **deviating** from it. The open question:

> When an agent society is placed under optimization pressure, does alignment (following the stated
> collective objective) **persist**, or does it get **competed away** by self-interested strategies —
> and under what conditions?

This reframes a classic evolutionary-commons setup as an **alignment-stability** question:
*is "do the aligned thing" a fixed point, or an unstable strategy that selection erodes?*

## 2. Methodology philosophy (why no pre-registered hypothesis — and the guardrail)

We deliberately do **not** fix a research question up front. The sandbox is rich enough to produce
several qualitatively different outcomes (Section 7); we run it, observe which **robust** phenomenon
emerges, and let *that* become the paper's claim.

**Guardrail against fishing / HARKing (non-negotiable):** two-phase.
- **Phase 1 — discovery.** Exploratory runs with full logging. We look at the data and identify the
  strongest, most robust regularity.
- **Phase 2 — confirmation.** We *freeze* that observation as a claim, then run a **fresh,
  pre-registered** replication (new seeds, held-out models/scenarios) to confirm it survives.
  Only Phase-2-surviving observations go in the paper.

What we DO pre-commit before Phase 1: the environment mechanics, the measurements/logging, and the
model panel. That keeps the design honest without pre-deciding the finding.

## 3. Environment (engine-scored, no LLM judge)

A **renewable commons** played by `N` agents over rounds (a shared resource pool):

- Each round, every agent privately chooses an **extraction amount** `e_i ∈ [0, cap]` (a number).
- Pool dynamics: `pool_{t+1} = regrow(pool_t − Σ e_i)`, where `regrow` is logistic (fast regrowth
  when healthy, collapse if over-harvested). Standard tragedy-of-the-commons tension.
- Payoff to agent `i` this round = `e_i` **if** the pool stays solvent; if the pool collapses,
  everyone earns ~0 for the remaining rounds of that block. Individual greed vs collective survival.
- All quantities are numbers → the dependent variables are **engine-computed**, not LLM-judged.

Why commons: there is **no safe/neutral escape** (the lesson from prior nulls) — doing well for
yourself and sustaining the group genuinely conflict — and defecting is **not a refusable/harmful
act**, so it shows up robustly across safety-tuned models (the lesson from the dropped idea).

## 4. Agents: what "aligned" vs "misaligned" means (behavioral, not a label)

Every agent is given the **same explicit collective objective** in its brief, e.g. *"the shared
resource must remain healthy for all agents across all rounds; act to sustain it."* That is the
**alignment target** — it is stated, intended, and identical for everyone.

- **Aligned behavior** = restraint consistent with the stated objective (sustainable extraction).
- **Misaligned behavior** = extracting for individual payoff at the collective's expense.

Alignment is thus measured **behaviorally** (how far an agent's actions track the stated objective),
never assigned as a persona. No agent is told to be greedy; greed, if it appears, is emergent.

## 5. The evolutionary / selection mechanism (the novel core)

After each **block** of rounds (a "generation"):

1. **Selection:** rank agents by accumulated payoff. Remove the bottom `k`.
2. **Replication:** the top `k` agents are copied into the vacated slots. An offspring inherits its
   parent's evolving **strategy memory** — a short natural-language summary of "what worked for me"
   that the parent maintains and passes down (cultural, not weight-level, evolution).
3. **Mutation (optional):** small perturbation of the inherited strategy text, to allow drift.

Over generations we watch whether the **population's aligned behavior** (mean restraint / objective-
adherence) rises, holds, or decays — i.e., whether alignment is selected for or against.

Selection strength `k` is a knob: it is literally the **optimization pressure** dial. A central
question the sandbox can answer: *how much optimization pressure does alignment survive?*

## 6. Levers we can vary (to make outcomes rich, not to pre-commit)

- **Initial composition:** fraction of initially-aligned vs already-exploitative agents.
- **Selection strength `k`:** weak → strong optimization pressure.
- **Reputation/visibility:** do agents see others' past extractions? (enables reciprocity/punishment)
- **Sanctioning:** is a costly-punishment action available?
- **Model panel / heterogeneity:** homogeneous vs mixed-model societies (our free panel).
- **Objective framing strength:** how strongly the collective objective is stated.

## 7. Candidate emergent phenomena (a menu, NOT commitments)

The sandbox is designed so any of these *could* emerge; Phase 1 tells us which actually does:

- **Alignment erosion under pressure** — mean objective-adherence decays as selection strengthens
  ("optimization competes alignment away"; an evolutionary Goodhart).
- **Invasion / instability** — a single exploitative strategy takes over an aligned population
  (alignment is not evolutionarily stable).
- **Tipping points / bistability** — small committed minorities flip the society (cf. norm-tipping).
- **Model-dependent stability** — some models sustain aligned equilibria, others always collapse
  (an "alignment robustness" axis across our panel).
- **Rescue mechanisms** — reputation or punishment spontaneously stabilizes alignment.
- **Inequality/monopoly** — a few agents capture the commons (ties back to SovSim inequality).

Every one of these is a viable paper framing; we pick the one the data supports most strongly.

## 8. What we log (so post-hoc observation is rich and defensible)

Per round: each agent's extraction, pool level, payoff, and short rationale. Per generation:
population mean/variance of extraction, objective-adherence score, survivor composition, inherited
strategy texts, collapse/recovery events, inequality (Gini). Full traces retained for qualitative
reads of *why* strategies win.

## 9. Free-infra mapping

Panel: `llama-3.1-8b`, `llama-3.3-70b`, `qwen3.6-27b`, `gpt-oss-120b` (Groq + Cerebras).
Small societies (`N ≈ 6–12`), tens of generations, one numeric decision per agent per round →
cheap and rate-limit-friendly. Cross-model robustness is built in from day one. Reuses the proven
rate-limited/resumable client already in `authority_override/`.

## 10. Open design questions (to resolve before Phase 1)

1. Cultural (strategy-text inheritance) vs compositional (model-mix selection) evolution — or both?
2. Payoff→survival mapping: hard cutoff (bottom-k die) vs soft (fitness-proportional replication)?
3. Do offspring know they inherited a strategy, or just receive it as context?
4. Society size vs generations trade-off under the token budget.
5. How to score "objective-adherence" purely from numbers (e.g., distance from the sustainable-yield
   extraction) so it stays engine-scored.

## 11. Next gate

**Novelty check before any building** (the discipline we're now enforcing): deep-read the closest
prior work — cultural-evolution-of-cooperation among LLM agents (arXiv 2412.10270), evolutionary /
selection dynamics in LLM societies, and reward-hacking/Goodhart-in-agents — to confirm the
*alignment-stability-under-selection* framing is open. Only then do we build Phase 1.
