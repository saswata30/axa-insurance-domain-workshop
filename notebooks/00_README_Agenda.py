# Databricks notebook source
# MAGIC %md
# MAGIC # 🧭 The Governed Semantic Layer — AXA, the business-user way
# MAGIC ### From certified data to trustworthy natural-language analytics — built the way a business owner would
# MAGIC
# MAGIC **Scenario:** a synthetic AXA Property & Casualty (P&C) book — the *loss run* and the *loss ratio*.
# MAGIC **Goal:** stand up the pieces a business/analytics owner curates so Genie answers underwriting & claims
# MAGIC questions reliably — and everyone discovers the same trusted assets in one place.
# MAGIC
# MAGIC ---
# MAGIC ## Who this is for
# MAGIC This is **not** a data-engineering lab. It's the workflow a **domain owner / analytics lead** follows to make
# MAGIC their business area self-serve and governed. Most of the work happens in the **UI** (Catalog, Discover, Genie),
# MAGIC with a little SQL for the governed math.
# MAGIC
# MAGIC ## ⏱️ Agenda (60 minutes)
# MAGIC
# MAGIC ### Part 1 — Why (20 min) *[slides]*
# MAGIC | Min | Topic |
# MAGIC |----|-------|
# MAGIC | 0–7 | The problem: NL analytics is only as good as the meaning you encode. Genie **interprets** meaning — it doesn't invent it. |
# MAGIC | 7–14 | The four building blocks a business owner curates: **Gold data → Metric Views → Genie Agent → Domain (pages + glossary)**. |
# MAGIC | 14–20 | The **Insurance domain** as the single governed home; how pages & the glossary ground Genie's answers. |
# MAGIC
# MAGIC ### Part 2 — Build it (40 min) *[these notebooks]*
# MAGIC | Min | Notebook | What you do |
# MAGIC |----|-----------|-------------|
# MAGIC | 0–8  | `01_Gold_Layer_Tables` | **Certify** the P&C tables as trusted Gold assets (descriptions, keys, ownership, `CERTIFIED`) |
# MAGIC | 8–18 | `02_Metric_Views` | Define the KPIs **once** — loss ratio, combined ratio, frequency, severity — as governed metric views |
# MAGIC | 18–28 | `03_Genie_Agent` | Publish the **Genie Agent** on the gold tables + metric views; curate & test it |
# MAGIC | 28–40 | `04_Insurance_Domain_and_Glossary` | Create the **Insurance domain**, add **pages**, **bulk-import the glossary**, and **tag all assets** into the domain |
# MAGIC
# MAGIC ---
# MAGIC ## The mental model — build bottom-up, discover top-down
# MAGIC ```
# MAGIC   Gold tables  →  Metric Views  →  Genie Agent           (what you BUILD, notebooks 01→03)
# MAGIC        └──────────────┴───────────────┘
# MAGIC                       ▼
# MAGIC              Insurance DOMAIN                              (how the business DISCOVERS it, notebook 04)
# MAGIC        pages · bulk glossary · every asset tagged in
# MAGIC ```
# MAGIC A **business user starts at the domain** in *Discover*, reads the plain-language **pages/glossary**, and asks the
# MAGIC **Genie Agent** — which answers using the **metric views** over the **certified gold tables**. One meaning, everywhere.
# MAGIC
# MAGIC ## 📦 What's already provisioned
# MAGIC - Catalog/schema **`serverless_stable_xhky6g_catalog.insurance`** with `customers`, `policies`, `claims`, `premiums`.
# MAGIC - A **live example built in this workspace**: the **AXA Insurance** domain (Discover) with 8 glossary pages and all
# MAGIC   assets tagged in — open it to see the finished state:
# MAGIC   [Discover ▸ AXA Insurance](https://fevm-serverless-stable-xhky6g.cloud.databricks.com/search/discover?q=domain%3A%22AXA%20Insurance%22)
# MAGIC
# MAGIC > 🔑 **The one line to remember:** *Genie interprets the meaning you encode — so encode it once, govern it,
# MAGIC > and let the whole business discover it.*

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration — the workshop dataset
# MAGIC All notebooks read from this catalog & schema. The data is **already loaded**.

# COMMAND ----------

CATALOG = "serverless_stable_xhky6g_catalog"
SCHEMA  = "insurance"
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")
print(f"Using {CATALOG}.{SCHEMA}")
display(spark.sql(f"SHOW TABLES IN {CATALOG}.{SCHEMA}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### The data model & the KPIs we will teach the business layer
# MAGIC | Table | Grain | Role |
# MAGIC |-------|-------|------|
# MAGIC | `customers` | 1 row / insured | dimension — segment, industry, country, region |
# MAGIC | `policies` | 1 row / policy | fact — written & earned premium, expenses, LOB, broker |
# MAGIC | `claims` | 1 row / claim | **the loss run** — paid, reserve, incurred, recovery |
# MAGIC | `premiums` | policy × month | earned-premium time series |
# MAGIC
# MAGIC **KPIs (defined once, in notebook 02):** Loss Ratio · Combined Ratio · Claim Frequency · Claim Severity.
# MAGIC Calibrated portfolio truth: **loss ratio ≈ 64.6%**, **combined ratio ≈ 91.8%** (5,000 policies, 2,979 claims).
