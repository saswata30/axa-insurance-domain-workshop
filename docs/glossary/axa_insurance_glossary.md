# AXA Insurance — P&C Glossary (Discover pages)

Bulk-import source for the **AXA Insurance** domain (notebook `04_Insurance_Domain_and_Glossary`, Step 2).

**How to use:** in the domain ▸ **Create ▸ Create page** ▸ the **Genie Code** panel ▸ **"Bulk import pages"**,
either **paste this file's text** or **upload** `axa_insurance_glossary.csv`. Prompt the importer with:

> *"Create one page per term, with a Definition, Business use, and the synonyms I list; link each term to the listed asset."*

The importer proposes a review table (Name · Description · Synonyms · Status); choose **Create all**. Natural
overlaps (e.g. *Combined Ratio* references *Loss Ratio*) are expected. After creation, link each term to its
asset so the term and the math are one click apart.

---

## Loss Ratio
- **Definition:** Incurred losses ÷ earned premium; the core measure of underwriting profitability.
- **Business use:** The headline KPI leaders watch by line of business, region and underwriting year — "underperforming" means above target or worse than the peer benchmark for the period.
- **Synonyms:** LR, loss cost ratio
- **Linked asset:** `workspace.insurance.mv_portfolio` — measure *Loss Ratio*

## Combined Ratio
- **Definition:** Loss ratio + expense ratio; below 100% means the book is underwriting at a profit.
- **Business use:** The profitability read that loss ratio alone misses — it brings acquisition (commission) and operating expense into the picture.
- **Synonyms:** COR
- **Linked asset:** `workspace.insurance.mv_portfolio` — measure *Combined Ratio*

## Incurred Loss
- **Definition:** Paid loss + case reserves, before recoveries; the ultimate expected cost of a claim.
- **Business use:** The numerator of the loss ratio; the basis of record for claims cost (not "paid" alone).
- **Synonyms:** ultimate loss, incurred
- **Linked asset:** `workspace.insurance.claims` (`incurred_loss`) · `workspace.insurance.mv_claims`

## Earned Premium
- **Definition:** Written premium recognised as the policy term elapses; the loss-ratio denominator.
- **Business use:** The correct denominator for loss ratio — earned, not written — so ratios reflect exposure actually on risk.
- **Synonyms:** EP, earned
- **Linked asset:** `workspace.insurance.policies` (`earned_premium`) · `workspace.insurance.premiums`

## Loss Run
- **Definition:** Claim-level listing (paid, reserve, incurred, recovery) sourced from the claims table.
- **Business use:** The claim-by-claim source of truth for claims analytics and the loss-ratio numerator; the basis for cause-of-loss and large-loss analysis.
- **Synonyms:** claims bordereau, loss listing
- **Linked asset:** `workspace.insurance.claims` · `workspace.insurance.mv_claims`

## Claim Frequency
- **Definition:** Claim count ÷ policy count; how often claims occur.
- **Business use:** Tells you whether a rising loss ratio is driven by *more* claims (risk selection / terms) rather than bigger ones.
- **Synonyms:** frequency
- **Linked asset:** `workspace.insurance.mv_portfolio` — measure *Claim Frequency*

## Claim Severity
- **Definition:** Incurred loss ÷ claim count; the average cost per claim.
- **Business use:** Tells you whether a rising loss ratio is driven by *bigger* claims (pricing / cat exposure) rather than more of them.
- **Synonyms:** average severity
- **Linked asset:** `workspace.insurance.mv_portfolio` — measure *Claim Severity*

## Case Reserve
- **Definition:** Estimated unpaid amount on the open portion of a claim (0 when closed).
- **Business use:** The open/unpaid part of incurred loss; drives reserve development and IBNR discussions and explains why incurred moves after a claim is reported.
- **Synonyms:** outstanding, OS reserve
- **Linked asset:** `workspace.insurance.claims` (`case_reserve`) · `workspace.insurance.mv_claims` — measure *Case Reserves*
