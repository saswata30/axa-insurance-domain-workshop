# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · The Genie Agent — let the business just *ask* 🧞
# MAGIC
# MAGIC A **Genie Agent** is the conversational analytics surface your business users actually touch. You point it at
# MAGIC the **certified gold tables** and **metric views** from notebooks 01–02, curate a little context, and it answers
# MAGIC underwriting & claims questions in natural language — using the *governed* KPI definitions, not a guess.
# MAGIC
# MAGIC > This step is done in the **UI** (Genie Agents), because curating an agent is a business/steward activity, not a
# MAGIC > code task. There is no SQL for this. Below is the exact click-path plus the curation that matters.
# MAGIC
# MAGIC **Left nav ▸ Genie Agents** → [open Genie Agents](https://fevm-serverless-stable-xhky6g.cloud.databricks.com/genie)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — Create the agent (≈3 min) 🖱️
# MAGIC 1. **Genie Agents ▸ New**.
# MAGIC 2. Name it **`AXA P&C — Underwriting & Claims`**; add a one-line purpose.
# MAGIC 3. **Data**: add from `serverless_stable_xhky6g_catalog.insurance` —
# MAGIC    the metric views **`mv_portfolio`** and **`mv_claims`** *first* (they carry the governed KPIs), then the
# MAGIC    tables `claims`, `policies`, `customers`, `premiums` for detail/drill-down.
# MAGIC 4. Pick the workshop **SQL warehouse**. Save.
# MAGIC
# MAGIC > 💡 Adding the **metric views** is what makes "loss ratio" and "combined ratio" resolve to the *governed* math.
# MAGIC > Tables alone force Genie to re-derive KPIs — which is exactly how you get confident-but-wrong answers.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — Curate context, in this order (most structural first)
# MAGIC You already did most of the heavy lifting in notebooks 01–02. Add only what can't be modelled structurally:
# MAGIC
# MAGIC **A. Synonyms / value dictionaries** (map how people speak → fields & values)
# MAGIC - `incurred_loss` → *"ultimate loss", "loss", "losses"*; `earned_premium` → *"EP", "earned"*
# MAGIC - `line_of_business` → *"LOB", "class of business"*; `case_reserve` → *"reserves", "outstanding", "OS"*
# MAGIC - "UK" / "Britain" → `region = 'UK & Ireland'`; "open claims" → `claim_status = 'Open'`
# MAGIC
# MAGIC **B. Trusted example queries** (question pattern → verified SQL). Paste these MEASURE-based examples:

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Example 1: overall loss ratio (paste into the agent as a trusted example)
# MAGIC SELECT ROUND(MEASURE(`Loss Ratio`),3) AS overall_loss_ratio
# MAGIC FROM serverless_stable_xhky6g_catalog.insurance.mv_portfolio;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Example 2: combined ratio for a given underwriting year
# MAGIC SELECT `Underwriting Year`, ROUND(MEASURE(`Combined Ratio`),3) AS combined_ratio
# MAGIC FROM serverless_stable_xhky6g_catalog.insurance.mv_portfolio
# MAGIC WHERE `Underwriting Year` = 2024 GROUP BY `Underwriting Year`;

# COMMAND ----------

# MAGIC %md
# MAGIC **C. Text instructions** — only the last-mile behaviour, e.g.:
# MAGIC - *"Always express ratios as percentages to 1 decimal."*
# MAGIC - *"'This year' = the latest underwriting year present in the data."*
# MAGIC - *"'Loss run' means a claim-level listing from the claims table."*
# MAGIC
# MAGIC > **Rule of thumb:** if you're writing a 20th instruction, you probably need a metric view or a value dictionary
# MAGIC > instead. Structure beats prose.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 — Test the agent against the ground truth 🧪
# MAGIC Ask these and confirm they match the governed numbers (from notebook 02). Keep this as your mini-benchmark.
# MAGIC
# MAGIC | # | Ask the agent | What good looks like |
# MAGIC |---|----------------|----------------------|
# MAGIC | 1 | *What is our overall loss ratio?* | ≈ **64.6%** (incurred ÷ earned) |
# MAGIC | 2 | *Loss ratio by line of business* | correct join, 4 LOBs |
# MAGIC | 3 | *Combined ratio in 2024?* | loss + expense ratio |
# MAGIC | 4 | *Total incurred loss for Motor* | uses `incurred_loss`, LOB filter |
# MAGIC | 5 | *Average claim severity by cause of loss* | incurred ÷ claim count |
# MAGIC | 6 | *Which region has the highest loss ratio?* | region join across facts |
# MAGIC | 7 | *Show me the loss run for the UK* | claims filtered to region = UK & Ireland |
# MAGIC
# MAGIC ### The accuracy loop 🔁
# MAGIC Benchmark 10–20 SME questions → change **one** thing → re-ask → compare. Fix in this order:
# MAGIC `gold data / keys → metric views → example SQL → instructions`. Turn on 👍/👎 and the Monitoring tab; feed
# MAGIC recurring misses back into the **structural** layers, not more prose.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Reference: a Genie Agent already exists in this workspace
# MAGIC **"Insurance Claims and Underwriting Analytics"** is live on `claims` + `mv_portfolio` + `mv_claims` and answers
# MAGIC the loss/combined ratio correctly. Open **Genie Agents** to try it, or clone its setup for your own.
# MAGIC
# MAGIC > Programmatic note (for developers, optional): agents are reachable via the Genie API
# MAGIC > (`/api/2.0/data-rooms`, and the managed Genie MCP at `/api/2.0/mcp/genie/{space_id}`) — but **creating and
# MAGIC > curating** an agent is a UI activity. Next: **`04_Insurance_Domain_and_Glossary`** — make all of this
# MAGIC > discoverable under one governed domain.
