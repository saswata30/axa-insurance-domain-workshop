# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # 02 · Metric Views — define the KPIs once 📐
# MAGIC
# MAGIC A **metric view** is a first-class Unity Catalog object that captures **dimensions** and **measures** as governed
# MAGIC code. The aggregation is resolved at *query time* via `MEASURE()`, so there is exactly **one** definition of
# MAGIC "loss ratio" — and Genie, dashboards and SQL all consume the same one. No more three teams, three numbers.
# MAGIC
# MAGIC > **Business-owner lens:** this is where you pin down the math that matters — loss ratio, combined ratio,
# MAGIC > frequency, severity — so nobody re-derives it (wrongly) in a spreadsheet. Metric views show up in **Discover**
# MAGIC > under *Featured metric views* and can be tagged into your domain (notebook 04).
# MAGIC
# MAGIC We build two:
# MAGIC - **`mv_portfolio`** — underwriting economics at policy grain (premium, loss ratio, combined ratio, frequency, severity)
# MAGIC - **`mv_claims`** — the loss run at claim grain (incurred, paid, reserves, recovery, severity by cause of loss)
# MAGIC
# MAGIC Loss ratio spans two facts at different grains, so `mv_portfolio` builds on a policy-grain source with claims
# MAGIC **pre-aggregated** — this avoids premium fan-out (the classic double-count bug).

# COMMAND ----------

CATALOG = "serverless_stable_xhky6g_catalog"
SCHEMA  = "insurance"
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Portfolio metric view — the underwriting economics

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW mv_portfolio
# MAGIC WITH METRICS
# MAGIC LANGUAGE YAML
# MAGIC COMMENT 'Portfolio underwriting metrics: premium, loss ratio, combined ratio, frequency, severity at policy grain.'
# MAGIC AS $$
# MAGIC version: 0.1
# MAGIC source: |
# MAGIC   SELECT p.policy_id, p.line_of_business, p.product, p.region, p.country,
# MAGIC          p.broker, p.underwriting_year, p.policy_status,
# MAGIC          p.written_premium, p.earned_premium,
# MAGIC          p.commission_amount, p.other_expense_amount,
# MAGIC          COALESCE(c.incurred_loss,0)   AS incurred_loss,
# MAGIC          COALESCE(c.paid_loss,0)       AS paid_loss,
# MAGIC          COALESCE(c.case_reserve,0)    AS case_reserve,
# MAGIC          COALESCE(c.recovery_amount,0) AS recovery_amount,
# MAGIC          COALESCE(c.claim_count,0)     AS claim_count
# MAGIC   FROM serverless_stable_xhky6g_catalog.insurance.policies p
# MAGIC   LEFT JOIN (
# MAGIC      SELECT policy_id, SUM(incurred_loss) incurred_loss, SUM(paid_loss) paid_loss,
# MAGIC             SUM(case_reserve) case_reserve, SUM(recovery_amount) recovery_amount,
# MAGIC             COUNT(*) claim_count
# MAGIC      FROM serverless_stable_xhky6g_catalog.insurance.claims GROUP BY policy_id
# MAGIC   ) c ON p.policy_id = c.policy_id
# MAGIC dimensions:
# MAGIC   - name: Line of Business
# MAGIC     expr: line_of_business
# MAGIC   - name: Region
# MAGIC     expr: region
# MAGIC   - name: Underwriting Year
# MAGIC     expr: underwriting_year
# MAGIC   - name: Broker
# MAGIC     expr: broker
# MAGIC   - name: Policy Status
# MAGIC     expr: policy_status
# MAGIC measures:
# MAGIC   - name: Earned Premium
# MAGIC     expr: SUM(earned_premium)
# MAGIC   - name: Written Premium
# MAGIC     expr: SUM(written_premium)
# MAGIC   - name: Incurred Loss
# MAGIC     expr: SUM(incurred_loss)
# MAGIC   - name: Policy Count
# MAGIC     expr: COUNT(DISTINCT policy_id)
# MAGIC   - name: Claim Count
# MAGIC     expr: SUM(claim_count)
# MAGIC   - name: Loss Ratio
# MAGIC     expr: SUM(incurred_loss) / NULLIF(SUM(earned_premium),0)
# MAGIC   - name: Expense Ratio
# MAGIC     expr: (SUM(commission_amount)+SUM(other_expense_amount)) / NULLIF(SUM(written_premium),0)
# MAGIC   - name: Combined Ratio
# MAGIC     expr: SUM(incurred_loss)/NULLIF(SUM(earned_premium),0) + (SUM(commission_amount)+SUM(other_expense_amount))/NULLIF(SUM(written_premium),0)
# MAGIC   - name: Claim Frequency
# MAGIC     expr: SUM(claim_count) / NULLIF(COUNT(DISTINCT policy_id),0)
# MAGIC   - name: Claim Severity
# MAGIC     expr: SUM(incurred_loss) / NULLIF(SUM(claim_count),0)
# MAGIC $$;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Claims (loss run) metric view

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW mv_claims
# MAGIC WITH METRICS
# MAGIC LANGUAGE YAML
# MAGIC COMMENT 'Claim-level (loss run) metrics: incurred, paid, reserves, recovery, frequency and severity by cause of loss.'
# MAGIC AS $$
# MAGIC version: 0.1
# MAGIC source: serverless_stable_xhky6g_catalog.insurance.claims
# MAGIC dimensions:
# MAGIC   - name: Line of Business
# MAGIC     expr: line_of_business
# MAGIC   - name: Region
# MAGIC     expr: region
# MAGIC   - name: Cause of Loss
# MAGIC     expr: cause_of_loss
# MAGIC   - name: Claim Status
# MAGIC     expr: claim_status
# MAGIC   - name: Large Loss
# MAGIC     expr: large_loss_flag
# MAGIC   - name: Loss Year
# MAGIC     expr: YEAR(loss_date)
# MAGIC   - name: Loss Month
# MAGIC     expr: DATE_TRUNC('MONTH', loss_date)
# MAGIC measures:
# MAGIC   - name: Incurred Loss
# MAGIC     expr: SUM(incurred_loss)
# MAGIC   - name: Paid Loss
# MAGIC     expr: SUM(paid_loss)
# MAGIC   - name: Case Reserves
# MAGIC     expr: SUM(case_reserve)
# MAGIC   - name: Recovery Amount
# MAGIC     expr: SUM(recovery_amount)
# MAGIC   - name: Net Incurred Loss
# MAGIC     expr: SUM(net_incurred_loss)
# MAGIC   - name: Claim Count
# MAGIC     expr: COUNT(claim_id)
# MAGIC   - name: Large Loss Count
# MAGIC     expr: SUM(CASE WHEN large_loss_flag THEN 1 ELSE 0 END)
# MAGIC   - name: Average Severity
# MAGIC     expr: SUM(incurred_loss) / NULLIF(COUNT(claim_id),0)
# MAGIC   - name: Open Reserve Ratio
# MAGIC     expr: SUM(case_reserve) / NULLIF(SUM(incurred_loss),0)
# MAGIC $$;

# COMMAND ----------

# MAGIC %md
# MAGIC ### Query with `MEASURE()` — one definition, reused everywhere
# MAGIC The governed loss ratio by line of business. This is the *exact* number Genie will return.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT `Line of Business`,
# MAGIC        ROUND(MEASURE(`Loss Ratio`),3)      AS loss_ratio,
# MAGIC        ROUND(MEASURE(`Combined Ratio`),3)  AS combined_ratio,
# MAGIC        ROUND(MEASURE(`Claim Frequency`),3) AS frequency,
# MAGIC        ROUND(MEASURE(`Claim Severity`),0)  AS severity
# MAGIC FROM mv_portfolio
# MAGIC GROUP BY `Line of Business`
# MAGIC ORDER BY loss_ratio DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Portfolio truth: loss ratio ~0.646, combined ratio ~0.918
# MAGIC SELECT ROUND(MEASURE(`Loss Ratio`),4)     AS loss_ratio,
# MAGIC        ROUND(MEASURE(`Combined Ratio`),4) AS combined_ratio,
# MAGIC        MEASURE(`Policy Count`)            AS policies,
# MAGIC        MEASURE(`Claim Count`)             AS claims
# MAGIC FROM mv_portfolio;

# COMMAND ----------

# MAGIC %md
# MAGIC **Done.** The KPIs are governed and reusable. In **`03_Genie_Agent`** we put a conversational agent on top of
# MAGIC these metric views so business users can just *ask*.
