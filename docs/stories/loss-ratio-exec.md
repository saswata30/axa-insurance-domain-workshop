# User Story — Loss Ratio: what the executive should be looking at

> Part of the **AXA Insurance — Genie Ontology Workshop**. This story frames the headline
> KPI (loss ratio) from the seat of a business leader, and defines what "done" looks like
> when the governed semantic layer lets an exec self-serve the answer — and trust it.

---

## The story

**As a** P&C insurance executive (Chief Underwriting Officer / COO),
**I want to** ask, in plain language, *which parts of the book are underperforming on loss
ratio this quarter* — and see the governed definition behind every number —
**so that I** can direct underwriting, pricing, and reserving action with confidence,
without waiting on an analyst or second-guessing whose definition of "loss ratio" I'm looking at.

---

## Persona & context

- **Who:** an underwriting/finance leader who reads the book at the *portfolio* level, not the row level.
- **Reality today:** the number arrives in a slide, three weeks late, and "loss ratio" means something
  slightly different in every deck (paid vs incurred, gross vs net, written vs earned premium).
- **What changes:** Genie answers the question directly off the **governed metric views**, and the
  **glossary** shows the one approved definition — so the number on screen *is* the number of record.

---

## The questions the exec actually asks

Plain-language prompts to the **Genie Agent** (notebook `03_Genie_Agent.py`):

1. *"What's our loss ratio this year, and how does it compare to last year?"*
2. *"Which lines of business are running above target on loss ratio?"*
3. *"Break loss ratio down by region and underwriting year."*
4. *"Is the deterioration coming from more claims or bigger claims?"* (frequency vs severity)
5. *"What's the combined ratio — are we underwriting at a profit once expenses are in?"*

Each resolves to a **`MEASURE()`** on a governed metric view — one definition, computed at query time.

---

## What the exec should be looking at

Not a single number — a small, disciplined read. The governed layer makes each of these one click / one question away.

| # | What to look at | Why it matters | Where it comes from |
|---|-----------------|----------------|---------------------|
| 1 | **Loss ratio vs. target and vs. prior year** | A point value is meaningless without a bar and a trend. Book truth is **≈ 64.6%** — is a segment materially worse? | `mv_portfolio` → *Loss Ratio*, sliced by *Underwriting Year* |
| 2 | **The definition itself** | *Incurred* loss ÷ *earned* premium is the approved basis here — not paid, not written. Confirm you're comparing like with like. | Glossary page **Loss Ratio** (governed) |
| 3 | **Which segments drive it** | Portfolio 64.6% can hide a line of business at 90%+. Act on the segment, not the average. | `mv_portfolio` by *Line of Business*, *Region*, *Broker* |
| 4 | **Frequency vs. severity** | Rising loss ratio from *more* claims (frequency) vs *bigger* claims (severity) points to different fixes — terms vs pricing/cat exposure. | `mv_portfolio` → *Claim Frequency*, *Claim Severity*; `mv_claims` by *cause of loss* |
| 5 | **Attritional vs. large/cat losses** | One large loss can distort a quarter; strip it to see the underlying trend. | `mv_claims` (loss run) — incurred/paid/reserves by cause of loss |
| 6 | **Reserve development & recovery** | Incurred moves as reserves and recoveries (subrogation/salvage/reinsurance) update — is the ratio real or timing? | `mv_claims` → reserves, recovery |
| 7 | **Combined ratio, not just loss ratio** | Loss ratio ignores expenses. Underwriting profit is the combined ratio — book truth **≈ 91.8%** (< 100% = profit). | `mv_portfolio` → *Combined Ratio* (loss + expense ratio) |
| 8 | **Is the number certified & fresh?** | An exec decision needs a *trusted* asset, not an ad-hoc extract. Check certification and the domain it lives in. | Unity Catalog certification + **Insurance domain** (notebook `04`) |

**The one-line read:** *loss ratio, on the governed basis, against target and trend, decomposed to the
segment and to frequency-vs-severity, in the context of the combined ratio* — sourced from a certified asset.

---

## Why this is possible (the governed layer)

- **Metric Views** (`mv_portfolio`, `mv_claims`) define loss ratio **once** — `SUM(incurred_loss) / NULLIF(SUM(earned_premium),0)` —
  so every question, dashboard, and agent returns the same figure. No premium fan-out double-count.
- **Genie Agent** interprets the exec's language against those measures and dimensions.
- **Glossary + Insurance domain** make the definition discoverable and the assets trusted — people *and* agents share one source of truth.

> *Genie interprets the meaning you encode — so encode it once, govern it, and let the whole business discover it.*

---

## Acceptance criteria

- [ ] An exec can ask *"which lines of business are above target on loss ratio this year?"* in Genie and get a correct, ranked answer.
- [ ] The returned loss ratio matches the governed metric view (`mv_portfolio` → *Loss Ratio*), i.e. **incurred ÷ earned** — reconciles to the portfolio truth of **≈ 64.6%** at the book level.
- [ ] The exec can open the **Loss Ratio** glossary page and see the approved definition (basis, numerator, denominator) in business language.
- [ ] Loss ratio can be sliced by *Line of Business*, *Region*, *Underwriting Year*, and *Broker* without redefining the metric.
- [ ] Frequency and severity are available alongside loss ratio to explain *why* it moved.
- [ ] **Combined ratio** (**≈ 91.8%**) is available in the same view for the profitability read.
- [ ] The underlying tables/metric views are **certified** and tagged into the **Insurance domain**, so the exec knows the answer is trustworthy.

---

## Demo talk track (≈ 3 min)

1. **Ask like a human.** In Genie: *"What's our loss ratio this year vs last year?"* → ~64.6%, with the trend.
2. **Prove the definition.** Open the **Loss Ratio** glossary page — incurred ÷ earned, approved for management reporting. *"This is the number of record."*
3. **Find the driver.** *"Break loss ratio down by line of business."* → surface the segment running hot.
4. **Explain the move.** *"Is that more claims or bigger claims?"* → frequency vs severity from `mv_claims`.
5. **Land the decision.** *"And the combined ratio?"* → ~91.8%: still underwriting at a profit, but here's where to act.
6. **Trust it.** Show the certified assets inside the **Insurance domain** — self-serve, governed, discoverable.

---

## Data reference

- **Catalog / schema:** `serverless_stable_xhky6g_catalog.insurance` (`customers`, `policies`, `claims`, `premiums`)
- **Metric views:** `mv_portfolio` (policy grain — premium, loss ratio, combined ratio, frequency, severity), `mv_claims` (claim grain loss run)
- **Calibrated portfolio truth:** loss ratio **≈ 64.6%**, combined ratio **≈ 91.8%** (5,000 policies, 2,979 claims)
- **Build path:** notebooks `01_Gold_Layer_Tables` → `02_Metric_Views` → `03_Genie_Agent` → `04_Insurance_Domain_and_Glossary`
