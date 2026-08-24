# MatchMarket — Do AI agents lie to get picked, and can other agents catch them?

**Status:** has working pilot results (2026-07). This is the current lead paper candidate.
**Domain:** society-of-agents, AI-alignment. Free to test (Groq + Cerebras open models).
**Working title:** *Verification as an Equalizer: Why LLM Agent Selectors Flee to Mediocrity Without It.*
(Narrative leads with the flight-to-mediocrity HOOK; the load-bearing CLAIM stays on the robust
verification-equalizer result. Acceptance must never rest on flight being universal — see §8.7.)

---

## 1. The idea in plain words

Imagine a bunch of AI agents. One of them (the **client**) needs to hire a partner and will pick
just one. The others (the **candidates**) each want to be the one picked. Each candidate secretly has
a real skill level, but the client can't see it directly — the client only sees what each candidate
*says* about itself.

Two simple questions:
- **Do candidates lie** about how good they are to get picked? (the *deceiver* side)
- **Can the client tell** who's lying and pick the genuinely best one? (the *detector* side)

The romance/"finding a partner" framing was just the intuition. The real thing underneath is a
well-known economics problem — **"the market for lemons"** (Akerlof): when quality is hidden and lying
is easy, bad options can drive out good ones. We're asking whether *AI agent societies* fall into this
trap, and it's directly relevant to real systems where one agent picks another based on what that agent
*claims* it can do (e.g., an orchestrator choosing sub-agents by their self-described skills).

## 2. Why it matters (real-world + alignment)

- **Agent ecosystems are coming.** Agents will pick tools, collaborators, and sub-agents from
  *self-reported* abilities. If agents inflate and nobody can catch it, these markets degrade.
- **Deceptive alignment, in miniature.** "An agent claiming to be better/safer than it is, to get
  selected" is a small, measurable version of a big alignment worry.

## 3. What we tested, step by step (and what each step taught us)

We ran a series of cheap experiments, fixing problems as we found them. Here's the honest trail.

### Step 1 — First deception test (`pilot_disclosure.py`). **Result: broken game.**
Setup: an agent knows its true skill, competes to be hired, claims a skill number. Lying was
**free and unverifiable**. What happened: **every model just claimed 9 or 10**, always, regardless of
true skill. There was no interesting behavior — "claim the max" trivially wins. Lesson: *this was a
game-design problem, not a finding.* If lying has no cost, everyone lies to the ceiling.

### Step 2 — Add a cost to lying (`pilot_disclosure2.py`). **Result: the ceiling broke.**
We made over-claiming a **gamble**: if hired, you might get audited, and the bigger your lie, the
bigger the fine. Now claims spread out sensibly, and a **cross-family personality typology** appeared:
- **llama-70b = strategic liar** — inflates a lot *only when its true skill is low*, perfectly honest
  when its skill is high (it lies exactly when it has something to hide).
- **qwen3.6 = bimodal** — usually honest, occasionally an all-in reckless "claim 10."
- **llama-8b = honest**, **gpt-oss = honest**.
The models' written reasons showed they were genuinely weighing "chance of being hired vs. risk of the
fine" — real strategic thinking, not noise.

### Step 3 — Can a selector catch liars? Easy version (`pilot_detector.py`). **Result: too easy.**
We gave the client each candidate's **track record** (past claims vs. what audits later revealed). With
that evidence, detection was strong and **scaled with model size**: llama-8b 70% → llama-70b 90% →
qwen 93% → **gpt-oss 100%**. But we'd basically handed them the answer — the record spells out who
inflates. Lesson: *with clear evidence, catching liars is easy; the interesting question is what
happens without it.*

### Step 4 — Catch liars with NO track record (`pilot_matched.py`). **Result: detection collapsed
(but the test had a flaw).**
We removed the track record — the client saw only each candidate's claim and a one-sentence sales
pitch. Detection dropped to ~41% (barely better than guessing). The clients fell back on gut-feel
skepticism ("a claim of 10 is probably a lie", "those are empty buzzwords") — which sometimes
**backfires**. *Caveat:* we changed several things at once here (removed the record, added pitches,
changed wording), so it wasn't a clean comparison. Also we eased the fine per your suggestion — and
confirmed it: a gentler penalty made the most-honest model start lying, so **penalty strength really
does control how much agents lie.**

### Step 5 — The clean, controlled test (`study_ablation.py`). **Result: our main finding.**
We fixed Step 4's flaw. We built a fixed set of candidate line-ups and had each client judge **the exact
same line-ups twice — once WITH the audit record, once WITHOUT** — changing *only* that one thing. Now
the comparison is airtight.

## 4. What we found (the clean results)

**Finding 1 — Detection is "verification-dependent."**
On the *same* line-ups, giving the client an audit record changes everything:

| client (detector) | WITH record | WITHOUT record |
|---|---|---|
| llama-8b | 50% | 19% |
| llama-70b | 69% | 38% |
| qwen3.6 | 75% | 31% |
| gpt-oss | 100% | 31% |
| **average** | **73%** | **30%** |

Plain meaning: **with evidence, agents catch liars (73%, and the best model is perfect). Take the
evidence away and they drop to 30% — pure chance (there are 3 candidates, so guessing = 33%).** This
holds for *every* model family. In short: *AI agents cannot tell a real expert from a confident liar
using words alone — they need external verification.*

**Finding 2 — "Flight to mediocrity" (the mechanism behind the collapse).**
When there's no record, what do clients actually do? **62% of the time they pick the *middle* candidate
— the one with a modest claim.** Being suspicious of big claims, they avoid the loud liar *and*
accidentally avoid the genuine expert too, settling for "safe and average." So hidden information
doesn't just let liars win — it makes selectors **systematically pass over the best agents** and hire
mediocre ones. That's a fresh, quotable, and practically worrying result.

**Finding 3 — A cross-family deception typology.**
Which models lie, and how, is consistent and model-dependent: **strategic (llama-70b), unconditional
inflator (gpt-oss), moderate (llama-8b), honest (qwen3.6).** Deception here is a *personality of the
model*, not a universal.

## 5. The candidate paper claim (Phase-2 confirmed — see §9 for numbers)

> When LLM agents select partners from **self-reported** competence, unaided detection of inflated
> claims is **sharply model-dependent** — from chance (qwen 30%, gpt-oss 35%) to well above it
> (llama-70b 60%). A **verified track record equalizes** selectors: it lifts detection across **every**
> family (pooled 44% → 78%, up to 100%) and lifts it **most where it is needed most** (Δ +5/+15/+52/+65,
> largest for the weakest text-only detectors). *Secondary — verification is an equalizer against
> **mediocrity**, not just against being fooled:* the selectors that retreat most to the moderate-claim
> candidate without verification (qwen 62%, gpt-oss 50% flight-to-mid) are exactly the ones verification
> rescues most (→18%, →0%; pooled 46%→20%), while strong unaided detectors neither flee much nor gain
> much — flight-to-mediocrity and verification-benefit are two faces of one axis.

**NOTE (2026-07):** §4 above reports the *Phase-1 discovery* numbers, now SUPERSEDED by the Phase-2
confirmatory run (§9). Phase 2 falsified the "chance-floor" claim (no-record detection is 44%, above
chance) and shrank flight-to-mediocrity (62% → 46% pooled, not cross-family). The headline shifted
accordingly; §8 is the authoritative framing.

## 6. Honest status, caveats, and what's left

**What's strong:** the verification result is now a *clean, controlled, cross-family* comparison, and
"flight to mediocrity" is a crisp mechanism. Everything is **engine-scored** (deception = claimed −
true; detection = did they pick the true-best) — no unreliable "AI judge." It runs entirely on **free
open models**, and it's about behavior models *aren't* trained to suppress, so it shows up robustly.

**Honest weaknesses:**
- **Modest sample size** (16 line-ups per model per condition) — needs a bigger confirmatory run.
- **"Who-fools-whom" is weak** — because clients mostly flee to the middle rather than getting fooled
  by the loud liar, so we can't yet build a clean "model X's lies fool model Y" matrix.
- **Incremental vs. prior work.** The "markets fail without verification" idea exists (market-for-lemons
  papers). Our new angle is the *controlled cross-family detection ablation* + the *flight-to-mediocrity*
  behavior — neither of which the earlier single-model market papers have. Honest label: a **clean,
  solid workshop contribution** (good fit for REALM or the Insights workshop), not a field-shaker.

**What's left:**
1. **Phase-2 confirmatory run:** fresh seeds + more line-ups to firm up the +44% verification gap and
   the 62% flight-to-mediocrity.
2. (optional) **Enforcement sweep:** vary audit probability / fine to show how much oversight it takes
   to keep agents honest — a natural second result.
3. **Draft the paper.**

## 7. Setup details (for reference)

- **Game:** a client hires one of several candidates; candidates have a hidden true skill and state a
  claim (+ sometimes a pitch); over-claiming risks an audit fine; the client's payoff = the true skill
  of whoever it hires. All scoring is arithmetic (engine-scored), no LLM judge.
- **Models (free):** llama-3.1-8b, llama-3.3-70b, qwen3.6-27b (Groq), gpt-oss-120b (Cerebras) — 3
  families. Reuses the rate-limited client in `authority_override/`.
- **Files (all in `matchmarket/`):** `pilot_disclosure.py` (Step 1), `pilot_disclosure2.py` (Step 2),
  `pilot_detector.py` (Step 3), `pilot_matched.py` (Step 4), `study_ablation.py` (Step 5, main), plus
  an `analyze_*.py` for each and data in `matchmarket/data/`.

## 8. Framing decision — FINAL (post Phase-2 + council, 2026-07)

Decision (locked): **Headline = B "Verification as an Equalizer"; A "flight to mediocrity" = a
demoted, honestly-hedged secondary finding.** Reached via a four-voice council — all voices
unanimously against headlining A. Rationale below.

**8.0 Why B is the headline and A is secondary.**
- **A cannot carry a headline.** Flight-to-mediocrity is n-sensitive (pooled 62% → 46% between the
  discovery and confirmatory runs — the classic signature of an effect washing out with n), is
  **contradicted by llama-70b** (no flight; it picks the true expert 60% of the time), and only qwen
  clears chance cleanly. Calling a mostly-absent, 1-of-4 effect a "signature failure mode" is a
  one-row reviewer rebuttal.
- **B is the robust result.** The verification benefit Δ = +5/+15/+52/+65 is **large, monotone, and
  same-direction in every family**; with-record detection is 55/75/82/**100%**. Nothing here washes
  out. At REALM/Insights, robustness beats novelty for acceptance.
- **The concurrent theory paper flips the novelty logic (key insight).** [2606.03034] *theorizes*
  "capability advertisement = market for lemons" and *proposes* a verification trust layer with **zero
  empirics**. That makes B **more** publishable (we are the first cross-family empirical test of a live,
  citable theory) and makes A's out-novelty attempt **riskier** (fighting a published theory with our
  weakest, shrinking effect). Cite 2606.03034 as *motivation we empirically fulfil*, not as a scoop.

**8.1 What to lead with vs demote.**
- **Lead:** the **main effect** — a verified record lifts detection across *every* family (44% → 78%,
  up to 100%). Do NOT headline the 4-point inverse *gradient* either (see confound in 8.5); use it as
  the *quotable secondary hook* ("verification helps weak detectors most"), not the title claim.
- **Secondary (A′) — the verification↔mediocrity inverse relationship (REPLACES bare flight-to-
  mediocrity):** flight-to-mediocrity and verification-benefit are **two faces of one axis.** The more a
  selector flees to the moderate middle without a record, the more verification rescues it: qwen
  62%→18%, gpt-oss 50%→**0%** (pooled 46%→20%), while strong unaided detectors (llama) neither flee much
  nor gain much. This subsumes the old flight claim (flight is what happens at the *weak* end of the
  axis) and is stronger: it is **reasoning-robust** (§9.1, qwen flees even with reasoning) and shown
  **causally** by the record on/off toggle, not just correlationally. Ties A′ directly to the B
  headline — same equalizer mechanism, now on the mediocrity dimension.
- **Cut entirely from the headline:** the old "chance-floor / non-diagnostic" claim (Phase 2 falsified
  it: no-record detection is 44%, above the 33% chance line). The Phase-1 deception typology (F3) stays
  as supporting color only.

**8.2 Honest scope for the secondary (A′ — the inverse relationship).** The underlying phenomenon
(retreat to the middle under hidden quality) is Akerlof's adverse-selection *prediction*; we claim the
**behavioral instance + the equalizer mechanism**, NOT a discovery of adverse selection. State it as an
inverse relationship, backed three ways: (1) **cross-model** — flight tracks unaided detection inversely
(llama low-flight/high-detect; qwen+gpt-oss high-flight/low-detect); (2) **causal** — the record on/off
toggle collapses flight most where it is worst (qwen 62%→18%, gpt-oss 50%→0%, pooled 46%→20%); (3)
**reasoning-robust** — §9.1 shows qwen flees even with full reasoning (62%→75%), while gpt-oss's flight
was throttling. Honest caveats to include: it is a **relationship across our panel (n≈4 models + a
within-model reasoning contrast), not a statistically-powered law**; and **llama-8b is a partial
exception** (stays ~38% flight even with a record — a uniformly weak selector), so scope the claim to
"concentrated in the low-detection models," never universal. Services-market credence-goods work found
the *opposite* (polarization) — a useful contrast. Best one-liners: *"the more a selector would flee to
mediocrity, the more verification rescues it,"* and *"in qwen, reasoning does not fix the flight — it
amplifies it."*

**8.3 Must-cite-and-differentiate neighbors (name each, state the difference explicitly):**
- **Capability Advertisement as a Market for Lemons — [2606.03034](https://arxiv.org/pdf/2606.03034)
  (THE key neighbor):** theorizes capability-advertisement-as-lemons + proposes a verification "trust
  layer." *Difference:* **theoretical/protocol only, no LLM experiment, no selector-detection test, no
  cross-family, no verification on/off ablation.** We are its **first empirical, cross-family test** —
  our strongest positioning sentence.
- **Tool Registries — [2605.23916](https://arxiv.org/html/2605.23916):** agents swayed by puffery,
  disclosure labels fail cross-family. *Difference:* tools **functionally identical** (no true quality),
  so no detection, no outcome-verification ablation. They test disclosure LABELS; we test **outcome
  verification**.
- **Credence-Goods Market — [2603.08853](https://arxiv.org/html/2603.08853):** *Difference:* **single
  model (GPT-5.1)**, welfare DV, reports **"polarized, not flight to mediocrity."** We are cross-family,
  detection-accuracy DV — turn the contrast into a selling point for the A secondary.
- **Strategic Exploitation e-commerce — [2605.10059](https://arxiv.org/html/2605.10059):** one-sided
  seller→buyer, **GPT-4o only.** *Difference:* two roles, cross-family, controlled record ablation.
- **From Agent Traces to Trust — [2606.04990](https://arxiv.org/html/2606.04990v1):** verification via
  execution provenance, but **post-hoc accountability, not selection-time detection.** Cite to show
  existing "verification layers" solve a *different* problem than ours.
- **Info-asymmetry theory — [2502.12969](https://arxiv.org/abs/2502.12969)** and **principal-agent
  framing — [2601.23211](https://arxiv.org/pdf/2601.23211):** economic/theoretical framing only.
- **Deception-detection background:** DECOR [2605.19270](https://arxiv.org/pdf/2605.19270),
  Hidden-in-Plain-Sight [2506.09424](https://arxiv.org/pdf/2506.09424) — frontier models are weak
  zero-shot deception detectors; motivates *why* text-only detection is poor for some families.

**8.4 The contribution sentence (use ~verbatim in intro):**
> A concurrent theory paper argues capability advertisement is a market for lemons and proposes a
> verification trust layer; we provide the missing **empirical, cross-family** evidence — unaided
> deception detection in LLM selectors is **sharply model-dependent** (chance to well-above-chance),
> and a verified record **equalizes** them, buying **+5 to +65 points** and reaching perfect detection
> for the weakest text-only selectors. When verification is absent, weaker selectors additionally show
> a model-dependent **flight to mediocrity.**

**8.5 Honest caveats to state UP FRONT (turn weaknesses into credibility):**
- **Reasoning-suppression confound — TESTED (§9.1), and the result is a strength, not a hole.** We
  re-ran qwen + gpt-oss as detectors on the *same 40 slates* with reasoning ON (qwen none→default,
  gpt-oss low→high). The two models **dissociate**: (a) **gpt-oss's** weakness WAS throttling — with
  reasoning it detects 35%→**78%** and flight collapses 50%→**11%** (non-overlapping CIs); (b)
  **qwen's** is **genuine and reasoning-robust** — no-record detection does NOT improve (30%→18%,
  overlapping) and flight-to-mediocrity **stays high, 62%→75%**. qwen's with-record jumps to 98%, so its
  reasoning is functional; it is specifically the *no-evidence* case where reasoning drives it to
  **over-skepticism → the safe middle**. Upshot: flight-to-mediocrity is **not** an artifact of which
  models we throttled, and the inverse relationship (low text-only detect ⇒ flight) **reproduces within
  the reasoning-on data** (qwen 18%/75%, gpt-oss 78%/11%). B's main effect is untouched (with-record
  98–100% either way). Adding 2–3 non-suppressed models is now *optional polish*, not a fix for a hole.
- **Answer-key caveat:** the with-record arm states outcomes in words, so it upper-bounds "detection
  given clean evidence." The interesting variance is *how much each model still fails to use it*
  (llama-8b only 55% vs gpt-oss 100%). Reframe defensively as **gap compression** if a reviewer pushes.
- **n-sensitivity:** report BOTH Phase-1 and Phase-2 numbers transparently; directions are stable,
  magnitudes (esp. flight-to-mid) are not — which is exactly why we ran a fresh-seed confirmation.

**8.6 Positioning + method anchors.** State plainly: **clean, controlled, cross-family, engine-scored**
on **free open models** — *incremental-but-solid* workshop contribution (REALM / Insights), not a
field-shaker. Credibility anchors to foreground: engine-scored DV (no LLM judge); **controlled record
on/off ablation on identical slates** (confound-free); non-safety-gated behavior (survives cross-family).

**8.7 Narrative emphasis — front-load the flight-to-mediocrity HOOK (option A, chosen 2026-07-24).**
The plain "verification improves detection" reading is trivial; we must not let a reader stop there
before reaching the surprising content. So the *narrative* opens with the non-obvious failure (flight to
mediocrity) and presents verification as the **resolution**, while the *claim structure* keeps
verification-equalizes-detection as the load-bearing result (per the /council discipline — never phrase
the paper so acceptance depends on flight being universal).

Rules:
- **Lead the abstract + intro with the failure DIRECTION, not "verification helps":** selectors don't
  get seduced by the loudest liar (fooled 8–15% for ALL models) — the ones that can't verify from text
  overshoot *past* the expert into the mediocre middle. That is the hook.
- **Then reveal the mechanism:** unaided detection is model-dependent (chance → well-above), and a
  verified record equalizes it — and *the same verification collapses the flight* (qwen 62%→18%,
  gpt-oss 50%→0%). Flight and verification-benefit are one axis (A′).
- **Land the counterintuitive robustness:** it is not a capability artifact — reasoning does not fix it
  and in qwen amplifies it (§9.1).
- **Stay in-bounds (mandatory):** always scope flight as *concentrated in the low-detection models*
  (llama-8b is a partial exception at ~38% flight even with a record); report it as a panel-level
  relationship (n≈4 + reasoning contrast), never a universal law. The moment flight is stated
  unconditionally, the llama-70b counterexample sinks it.

**Ready-to-use abstract draft (option A):**
> When one LLM agent selects another from self-reported competence, how does it fail? Not, as one might
> expect, by being seduced by the loudest claim: across four open models from three families, selectors
> reliably avoid the obvious inflator (8–15% fooled). Instead, the models least able to verify claims
> from text alone **flee to mediocrity** — passing over the genuine expert for a safe, moderate-claim
> candidate (qwen 62%, gpt-oss 50% of the time). We situate this in a cross-family, engine-scored
> agent-selection market with a controlled verification on/off ablation, and show it is one face of a
> single mechanism. Unaided detection of inflated self-reports is sharply model-dependent — from chance
> (qwen, gpt-oss) to well above it (llama) — and a verified track record acts as an **equalizer**,
> lifting detection to 78% (up to 100%) and most for the selectors weakest without it (+5 to +65
> points). The same verification collapses the flight to mediocrity exactly where it is worst (qwen
> 62%→18%, gpt-oss 50%→0%). The failure is not a capability artifact: with full reasoning enabled it
> persists, and in one model intensifies. Our results give the first cross-family empirical evidence for
> the recently theorized "capability-advertisement market for lemons" and quantify what a verification
> layer actually buys — concentrated, we note, in the models that most need it.

## 9. Phase-2 confirmatory results (the numbers the paper uses)

Fresh-seed confirmatory run (`phase2.py` / `analyze_phase2.py`; pool seeds 8–23, 40 slates/model, new
RNG). This is the authoritative dataset; §4 is the superseded Phase-1 discovery run.

| detector | no-record detect (95% CI) | with-record detect (95% CI) | Δ (verification) | flight-to-mid (no-record) |
|---|---|---|---|---|
| llama-8b | 50% [35,65] | 55% [40,69] | +5% | 40% [26,55] |
| llama-70b | 60% [45,74] | 75% [60,86] | +15% | 30% [18,45] (no flight) |
| qwen3.6-27b | 30% [18,45] | 82% [68,91] | +52% | 62% [47,76] (strong flight) |
| gpt-oss-120b | 35% [22,50] | 100% [91,100] | +65% | 50% [35,65] |
| **POOLED** | **44% [36,51]** | **78% [71,84]** | **+34%** | **46% [38,53]** (chance = 33%) |

No-record picked-role split (avoiding the liar is universal; where they land differs): fooled/inflator
picks are 8–15% for ALL models; the split is between picking the honest expert (llama) vs the mid
(qwen/gpt-oss). Inverse pattern: worse no-record detection ⇒ more flight-to-mid. Data:
`matchmarket/data/phase2_ablation.jsonl`, `pool_pitch.jsonl`.

**Verification collapses flight-to-mediocrity where it is worst (backs secondary A′, causal):**

| flight-to-mid | llama-8b | llama-70b | qwen | gpt-oss | POOLED |
|---|---|---|---|---|---|
| NO record | 40% | 30% | 62% | 50% | 46% |
| WITH record | 38% | 25% | **18%** | **0%** | **20%** |

Verification roughly halves flight pooled (46%→20%) and *eliminates* it for the two high-flight models,
while barely touching llama (already low flight / weak selector). This is the same equalizer mechanism
as the B headline, on the mediocrity dimension.

### 9.1 Reasoning-on de-confound (`phase2_reason.py` / `analyze_phase2_reason.py`)

Same 40 slates, only reasoning toggled ON for the two previously-suppressed detectors (qwen
none→default, gpt-oss low→high). Data: `matchmarket/data/phase2_reason_ablation.jsonl`.

| metric (no-record) | qwen OFF | qwen ON | gpt-oss OFF | gpt-oss ON |
|---|---|---|---|---|
| detect | 30% [18,45] | **18% [9,32]** | 35% [22,50] | **78% [62,88]** |
| flight-to-mid | 62% [47,76] | **75% [60,86]** | 50% [35,65] | **11% [4,25]** |
| fooled (liar) | 8% | 8% | 15% | 11% |
| with-record detect | 82% | **98%** | 100% | 100% |

**Interpretation:** the two models **dissociate**. gpt-oss's Phase-2 weakness was a throttling
artifact (reasoning recovers detection, flight collapses — significant, non-overlapping CIs). qwen's is
**genuine and reasoning-robust** (detection does not improve; flight stays high/higher; yet with-record
→98%, so its reasoning works — it over-thinks itself into the safe middle when it has no evidence). The
inverse relation reproduces *within* the reasoning-on data. Nets out: **B headline untouched; A
secondary upgraded from "possible artifact" to a real, model-specific, reasoning-robust failure.**
