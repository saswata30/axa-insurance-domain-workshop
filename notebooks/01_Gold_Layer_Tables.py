# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Gold Layer — certify the business-ready data 🥇
# MAGIC
# MAGIC The semantic layer is only as trustworthy as the data underneath it. Before we define KPIs or publish a
# MAGIC Genie Agent, we make the P&C tables **business-ready**: clear descriptions in business language, declared
# MAGIC keys so joins are unambiguous, an owner, and a **`Certified`** mark so consumers (and Genie) know they're trusted.
# MAGIC
# MAGIC > **Business-owner lens:** you don't rebuild the pipeline here — you *curate what already lands in Gold* so it's
# MAGIC > self-explanatory. Every comment you write becomes context Genie can use. This is the highest-leverage step.
# MAGIC
# MAGIC | Step | What | Why it matters downstream |
# MAGIC |------|------|---------------------------|
# MAGIC | 1 | Table & column **descriptions** in business terms | Genie & Discover read them as meaning; resolves jargon |
# MAGIC | 2 | **Primary / foreign keys** (`RELY`) | Genie joins the right way; no premium double-counting |
# MAGIC | 3 | **Certify** + owner | Signals "trusted" in Catalog/Discover; ranks high for Genie |

# COMMAND ----------

CATALOG = spark.sql("SELECT current_catalog()").collect()[0][0]  # workspace default catalog
SCHEMA  = "insurance"
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — Describe the tables in business language
# MAGIC A good description says *what the table is, at what grain, and how the business uses it*.

# COMMAND ----------

# MAGIC %sql
# MAGIC COMMENT ON TABLE claims    IS 'The loss run: one row per insurance claim with paid, reserved, incurred and recovery amounts. Grain: one claim. Used for claims analytics and the loss ratio numerator.';
# MAGIC COMMENT ON TABLE policies  IS 'One row per underwritten policy: written & earned premium, expenses, line of business, broker, underwriting year. Grain: one policy. Source of the loss-ratio denominator (earned premium).';
# MAGIC COMMENT ON TABLE customers IS 'Commercial insureds (policyholders): industry, segment, country, region. Grain: one insured. The customer dimension for portfolio slicing.';
# MAGIC COMMENT ON TABLE premiums  IS 'Monthly earned-premium schedule (policy x month) for period-based analysis and earned-premium time series.';

# COMMAND ----------

# MAGIC %md
# MAGIC ### Column descriptions that resolve business terminology
# MAGIC These teach the platform what analysts *say* vs. what the column is called.

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE claims   ALTER COLUMN incurred_loss    COMMENT 'Ultimate incurred loss = paid_loss + case_reserve (before recoveries). A.k.a. "ultimate loss", "loss".';
# MAGIC ALTER TABLE claims   ALTER COLUMN paid_loss        COMMENT 'Amount already paid on the claim.';
# MAGIC ALTER TABLE claims   ALTER COLUMN case_reserve     COMMENT 'Reserve held for the open portion of the claim (0 when closed). A.k.a. "outstanding", "OS".';
# MAGIC ALTER TABLE claims   ALTER COLUMN recovery_amount  COMMENT 'Salvage/subrogation recovered, reducing net loss.';
# MAGIC ALTER TABLE claims   ALTER COLUMN cause_of_loss    COMMENT 'Peril / cause: Fire, Flood, Collision, Bodily Injury, Cargo Damage, etc.';
# MAGIC ALTER TABLE policies ALTER COLUMN earned_premium   COMMENT 'Premium earned to date (pro-rata of written premium). The denominator of the loss ratio. A.k.a. "EP", "earned".';
# MAGIC ALTER TABLE policies ALTER COLUMN written_premium  COMMENT 'Total premium written for the annual policy term.';
# MAGIC ALTER TABLE policies ALTER COLUMN line_of_business COMMENT 'Product line: Property, Motor, Liability, Marine. A.k.a. "LOB", "class of business".';

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — Declare keys so joins are unambiguous
# MAGIC `RELY` tells the optimizer *and* the semantic layer the relationship is trustworthy. PK columns must be `NOT NULL`.

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE policies  ALTER COLUMN policy_id   SET NOT NULL;
# MAGIC ALTER TABLE customers ALTER COLUMN customer_id SET NOT NULL;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Idempotent: drop before (re)adding so the notebook re-runs cleanly.
# MAGIC ALTER TABLE claims    DROP CONSTRAINT IF EXISTS fk_claims_policy;
# MAGIC ALTER TABLE policies  DROP CONSTRAINT IF EXISTS fk_policy_customer;
# MAGIC ALTER TABLE policies  DROP CONSTRAINT IF EXISTS pk_policies;
# MAGIC ALTER TABLE customers DROP CONSTRAINT IF EXISTS pk_customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE policies  ADD CONSTRAINT pk_policies  PRIMARY KEY (policy_id)   RELY;
# MAGIC ALTER TABLE customers ADD CONSTRAINT pk_customers PRIMARY KEY (customer_id) RELY;
# MAGIC ALTER TABLE claims    ADD CONSTRAINT fk_claims_policy   FOREIGN KEY (policy_id)   REFERENCES policies(policy_id)   NOT ENFORCED RELY;
# MAGIC ALTER TABLE policies  ADD CONSTRAINT fk_policy_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) NOT ENFORCED RELY;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 — Mark the tables Certified (trusted) 🖱️/💻
# MAGIC Certification is the business signal that an asset is trusted. Two ways:
# MAGIC
# MAGIC **A. In the UI (business-owner path):** Catalog ▸ open each table ▸ the **⋯ / certification** control ▸ **Certify**.
# MAGIC A gold **Certified** badge appears in Catalog *and* Discover, and Genie ranks certified assets higher.
# MAGIC
# MAGIC **B. Governed tag (scriptable):** apply the account's `certified` governed tag. We do the equivalent below with a
# MAGIC lightweight property so this notebook is self-contained; use the UI **Certify** action for the real gold badge.

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE claims   SET TBLPROPERTIES ('certified' = 'true', 'certified_by' = 'AXA Analytics');
# MAGIC ALTER TABLE policies SET TBLPROPERTIES ('certified' = 'true', 'certified_by' = 'AXA Analytics');
# MAGIC ALTER TABLE customers SET TBLPROPERTIES ('certified' = 'true', 'certified_by' = 'AXA Analytics');
# MAGIC ALTER TABLE premiums SET TBLPROPERTIES ('certified' = 'true', 'certified_by' = 'AXA Analytics');

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ Verify the gold layer
# MAGIC Descriptions, keys and certification are now visible to every consumer and to Genie.

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE TABLE EXTENDED claims;

# COMMAND ----------

# MAGIC %md
# MAGIC **Done.** The P&C tables are certified, self-describing, and correctly keyed.
# MAGIC Continue to **`02_Metric_Views`** to encode the KPIs once.