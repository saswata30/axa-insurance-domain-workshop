"""
AXA Genie Ontology Workshop — Synthetic P&C Insurance Data Generator
====================================================================
Generates a realistic Property & Casualty insurance model into Unity Catalog,
designed to teach the Genie semantic layer (loss run + loss-ratio metrics).

Tier 1 (Polars/NumPy/Mimesis) -> Connect bridge to Unity Catalog.
Seed = 42 (reproducible).

Tables (catalog.schema = axa_workshop.insurance):
  customers  ~1,200  commercial insureds (EMEA)
  policies   ~5,000  annual policies, 4 lines of business, 2023-2025
  claims     ~7,000  THE LOSS RUN — paid/reserve/incurred/recovery, open & closed
  premiums   ~110k   monthly earned-premium schedule (time dimension for ratios)

Business logic baked in so the KPIs are real:
  loss_ratio      = incurred_loss / earned_premium
  expense_ratio   = (commission + other_expense) / earned_premium
  combined_ratio  = loss_ratio + expense_ratio
  frequency       = claim_count / policy_count
  severity        = incurred_loss / claim_count
"""
import numpy as np
import polars as pl
from datetime import date
from mimesis import Finance
from mimesis.locales import Locale

SEED = 42
rng = np.random.default_rng(SEED)
fin = Finance(locale=Locale.EN)

VALUATION_DATE = np.datetime64("2025-12-31")

# ----------------------------------------------------------------------------
# 1. CUSTOMERS (insureds)
# ----------------------------------------------------------------------------
N_CUST = 1_200
industries = np.array(["Construction", "Manufacturing", "Retail", "Logistics",
                       "Energy", "Healthcare", "Hospitality", "Real Estate",
                       "Technology", "Food & Beverage"])
ind_w = np.array([14, 16, 12, 13, 8, 7, 8, 9, 7, 6], dtype=float)

segments = np.array(["Corporate", "Mid-Market", "SME"])
seg_w = np.array([20, 35, 45], dtype=float)

# EMEA countries -> region grouping
countries = np.array(["United Kingdom", "France", "Germany", "Italy", "Spain",
                      "Netherlands", "Belgium", "Switzerland", "Ireland", "Portugal"])
country_w = np.array([22, 16, 18, 9, 8, 7, 5, 6, 5, 4], dtype=float)
region_map = {
    "United Kingdom": "UK & Ireland", "Ireland": "UK & Ireland",
    "France": "France", "Germany": "DACH", "Switzerland": "DACH",
    "Italy": "Southern Europe", "Spain": "Southern Europe", "Portugal": "Southern Europe",
    "Netherlands": "Benelux", "Belgium": "Benelux",
}

# company names via Mimesis, pooled
name_pool = np.array([fin.company() for _ in range(min(1000, N_CUST))])
cust_country = rng.choice(countries, size=N_CUST, p=country_w / country_w.sum())
customers = pl.DataFrame({
    "customer_id": np.array([f"INS-{i:06d}" for i in range(100000, 100000 + N_CUST)]),
    "customer_name": name_pool[rng.integers(0, len(name_pool), size=N_CUST)],
    "industry": rng.choice(industries, size=N_CUST, p=ind_w / ind_w.sum()),
    "segment": rng.choice(segments, size=N_CUST, p=seg_w / seg_w.sum()),
    "country": cust_country,
    "region": np.array([region_map[c] for c in cust_country]),
    "customer_since": (np.datetime64("2015-01-01")
                       + rng.integers(0, 3650, size=N_CUST).astype("timedelta64[D]")).astype("datetime64[D]"),
})
cust_ids = customers["customer_id"].to_numpy()
cust_region = dict(zip(cust_ids, customers["region"].to_numpy()))
cust_country_d = dict(zip(cust_ids, customers["country"].to_numpy()))

# ----------------------------------------------------------------------------
# 2. POLICIES
# ----------------------------------------------------------------------------
N_POL = 5_000
lobs = np.array(["Property", "Motor", "Liability", "Marine"])
lob_w = np.array([34, 30, 24, 12], dtype=float)
products = {
    "Property":  ["Commercial Property", "Industrial All-Risk", "Business Interruption"],
    "Motor":     ["Commercial Fleet", "Heavy Goods Vehicle", "Motor Trade"],
    "Liability": ["Public Liability", "Employers Liability", "Professional Indemnity"],
    "Marine":    ["Marine Cargo", "Hull & Machinery", "Marine Liability"],
}
brokers = np.array(["Marsh", "Aon", "WTW", "Gallagher", "Howden", "Direct"])
broker_w = np.array([24, 22, 18, 14, 12, 10], dtype=float)

# mean written premium (annual, EUR) by LOB — lognormal
prem_mu = {"Property": 10.6, "Motor": 10.2, "Liability": 10.4, "Marine": 10.9}
prem_sig = {"Property": 0.8, "Motor": 0.7, "Liability": 0.9, "Marine": 0.85}

pol_lob = rng.choice(lobs, size=N_POL, p=lob_w / lob_w.sum())
pol_cust = rng.choice(cust_ids, size=N_POL)
# inception dates spread across 3 underwriting years
inception = (np.datetime64("2023-01-01")
             + rng.integers(0, 1000, size=N_POL).astype("timedelta64[D]"))
expiry = inception + np.timedelta64(365, "D")
written = np.array([np.exp(rng.normal(prem_mu[l], prem_sig[l])) for l in pol_lob])
written = np.round(written, 2)

# earned premium as of valuation date (pro-rata, capped at written)
elapsed_days = np.clip((VALUATION_DATE - inception).astype("timedelta64[D]").astype(int), 0, 365)
earned = np.round(written * elapsed_days / 365.0, 2)

# status
status = np.where(expiry < VALUATION_DATE, "Expired", "Active")
cancel_mask = rng.random(N_POL) < 0.04
status = np.where(cancel_mask, "Cancelled", status)

# expenses: commission (acquisition) + other operating expense
commission_rate = np.where(np.isin(pol_lob, ["Marine", "Liability"]), 0.175, 0.15) \
    + rng.normal(0, 0.02, size=N_POL)
commission_rate = np.clip(commission_rate, 0.08, 0.25)
commission = np.round(written * commission_rate, 2)
other_expense = np.round(written * (0.11 + rng.normal(0, 0.015, size=N_POL)).clip(0.06, 0.16), 2)

policies = pl.DataFrame({
    "policy_id": np.array([f"POL-{i:07d}" for i in range(2000000, 2000000 + N_POL)]),
    "customer_id": pol_cust,
    "line_of_business": pol_lob,
    "product": np.array([rng.choice(products[l]) for l in pol_lob]),
    "underwriting_year": inception.astype("datetime64[Y]").astype(int) + 1970,
    "inception_date": inception.astype("datetime64[D]"),
    "expiry_date": expiry.astype("datetime64[D]"),
    "written_premium": written,
    "earned_premium": earned,
    "sum_insured": np.round(written * rng.uniform(15, 60, size=N_POL), 0),
    "deductible": np.round(written * rng.uniform(0.02, 0.10, size=N_POL), 0),
    "commission_amount": commission,
    "other_expense_amount": other_expense,
    "broker": rng.choice(brokers, size=N_POL, p=broker_w / broker_w.sum()),
    "country": np.array([cust_country_d[c] for c in pol_cust]),
    "region": np.array([cust_region[c] for c in pol_cust]),
    "policy_status": status,
})
pol_ids = policies["policy_id"].to_numpy()
pol_lob_d = dict(zip(pol_ids, pol_lob))
pol_incep_d = dict(zip(pol_ids, inception.astype("datetime64[D]")))
pol_region_d = dict(zip(pol_ids, policies["region"].to_numpy()))
pol_country_d = dict(zip(pol_ids, policies["country"].to_numpy()))

# ----------------------------------------------------------------------------
# 3. CLAIMS  (THE LOSS RUN)
# ----------------------------------------------------------------------------
# expected claim frequency (claims per policy per year) by LOB
freq_lambda = {"Property": 0.55, "Motor": 1.35, "Liability": 0.45, "Marine": 0.75}
# severity lognormal params (EUR incurred) by LOB
sev_mu = {"Property": 8.9, "Motor": 7.7, "Liability": 9.3, "Marine": 8.7}
sev_sig = {"Property": 1.2, "Motor": 0.9, "Liability": 1.4, "Marine": 1.15}
# report lag (days) mean by LOB — liability is long-tail
lag_mean = {"Property": 20, "Motor": 12, "Liability": 95, "Marine": 40}

causes = {
    "Property": ["Fire", "Flood", "Storm/Wind", "Water Damage", "Theft/Burglary", "Impact"],
    "Motor": ["Collision", "Theft", "Third-Party PD", "Third-Party BI", "Fire", "Weather"],
    "Liability": ["Bodily Injury", "Property Damage", "Professional Error", "Employers Liability", "Product Liability"],
    "Marine": ["Cargo Damage", "Cargo Theft", "Vessel Collision", "Grounding", "Weather/Heavy Seas"],
}
cause_w = {
    "Property": [22, 14, 20, 18, 14, 12],
    "Motor": [42, 10, 22, 12, 6, 8],
    "Liability": [30, 24, 20, 16, 10],
    "Marine": [34, 14, 18, 12, 22],
}

claim_rows = []
handlers = np.array([f"Handler-{i:02d}" for i in range(1, 31)])
month_season = {  # frequency multiplier by calendar month (winter storms etc.)
    1: 1.15, 2: 1.10, 3: 1.0, 4: 0.95, 5: 0.9, 6: 0.95,
    7: 1.0, 8: 1.05, 9: 1.0, 10: 1.05, 11: 1.2, 12: 1.25,
}

for pid in pol_ids:
    lob = pol_lob_d[pid]
    incep = pol_incep_d[pid]
    n = rng.poisson(freq_lambda[lob])
    for _ in range(n):
        # loss date uniformly within the policy year, but capped at valuation
        offset = int(rng.integers(0, 365))
        loss_dt = incep + np.timedelta64(offset, "D")
        if loss_dt > VALUATION_DATE:
            continue
        # seasonal thinning
        m = loss_dt.astype("datetime64[M]").astype(int) % 12 + 1
        if rng.random() > (month_season[m] / 1.25):
            continue
        lag = max(0, int(rng.exponential(lag_mean[lob])))
        report_dt = loss_dt + np.timedelta64(lag, "D")
        incurred = float(np.exp(rng.normal(sev_mu[lob], sev_sig[lob])))
        # rare catastrophe / large loss
        if rng.random() < 0.012:
            incurred *= rng.uniform(8, 25)
        incurred = round(incurred, 2)
        large = incurred >= 250_000
        # open vs closed: older & shorter-tail claims more likely closed
        age_days = (VALUATION_DATE - report_dt).astype("timedelta64[D]").astype(int)
        p_closed = np.clip(0.35 + age_days / 730.0 - (0.25 if lob == "Liability" else 0), 0.1, 0.95)
        is_closed = rng.random() < p_closed
        if is_closed:
            paid = incurred
            reserve = 0.0
            cstat = "Closed"
        else:
            paid_frac = rng.uniform(0.1, 0.7)
            paid = round(incurred * paid_frac, 2)
            reserve = round(incurred - paid, 2)
            cstat = "Open"
        # recovery (salvage/subrogation) on some causes
        cause = rng.choice(causes[lob], p=np.array(cause_w[lob]) / sum(cause_w[lob]))
        recovery = 0.0
        if cause in ("Theft", "Cargo Theft", "Third-Party PD", "Third-Party BI",
                     "Property Damage", "Vessel Collision") and rng.random() < 0.4:
            recovery = round(incurred * rng.uniform(0.05, 0.3), 2)
        claim_rows.append((pid, lob, str(loss_dt), str(report_dt), cause, cstat,
                           paid, reserve, incurred, recovery,
                           round(incurred - recovery, 2), large, str(rng.choice(handlers))))

claims = pl.DataFrame(
    claim_rows,
    schema=["policy_id", "line_of_business", "loss_date", "report_date",
            "cause_of_loss", "claim_status", "paid_loss", "case_reserve",
            "incurred_loss", "recovery_amount", "net_incurred_loss",
            "large_loss_flag", "claim_handler"],
    orient="row",
).with_columns([
    pl.col("loss_date").str.to_date(),
    pl.col("report_date").str.to_date(),
])
claims = claims.with_row_index("claim_seq").with_columns(
    ("CLM-" + (pl.col("claim_seq") + 3000000).cast(pl.Utf8)).alias("claim_id")
).drop("claim_seq")
# attach customer_id + region from policy
pol_cust_d = dict(zip(pol_ids, policies["customer_id"].to_numpy()))
claims = claims.with_columns([
    pl.col("policy_id").replace_strict(pol_cust_d, default=None).alias("customer_id"),
    pl.col("policy_id").replace_strict(pol_region_d, default=None).alias("region"),
    pl.col("policy_id").replace_strict(pol_country_d, default=None).alias("country"),
])

# ---- Calibrate to realistic target loss ratios per LOB ----------------------
# Scale each LOB's incurred amounts so the overall loss ratio is credible for
# commercial P&C. Claim-level distribution shape (heavy tails / large losses)
# is preserved; only the level is calibrated.
target_lr = {"Property": 0.61, "Motor": 0.72, "Liability": 0.69, "Marine": 0.58}
earned_by_lob = dict(policies.group_by("line_of_business")
                     .agg(pl.col("earned_premium").sum()).iter_rows())
incurred_by_lob = dict(claims.group_by("line_of_business")
                       .agg(pl.col("incurred_loss").sum()).iter_rows())
scale = {l: (target_lr[l] * earned_by_lob[l] / incurred_by_lob[l]) for l in target_lr}
scale_expr = pl.col("line_of_business").replace_strict(scale, default=1.0)
claims = claims.with_columns([
    (pl.col("paid_loss") * scale_expr).round(2).alias("paid_loss"),
    (pl.col("case_reserve") * scale_expr).round(2).alias("case_reserve"),
    (pl.col("incurred_loss") * scale_expr).round(2).alias("incurred_loss"),
    (pl.col("recovery_amount") * scale_expr).round(2).alias("recovery_amount"),
]).with_columns([
    (pl.col("incurred_loss") - pl.col("recovery_amount")).round(2).alias("net_incurred_loss"),
    (pl.col("incurred_loss") >= 250_000).alias("large_loss_flag"),
])

# ----------------------------------------------------------------------------
# 4. PREMIUMS  (monthly earned schedule — time dimension)
# ----------------------------------------------------------------------------
prem_rows = []
for pid, incep, wp in zip(pol_ids, inception.astype("datetime64[D]"), written):
    monthly = round(float(wp) / 12.0, 2)
    for k in range(12):
        em = (incep.astype("datetime64[M]") + np.timedelta64(k, "M"))
        first = em.astype("datetime64[D]")
        if first > VALUATION_DATE:
            break
        prem_rows.append((pid, pol_lob_d[pid], pol_region_d[pid],
                          str(first), monthly))

premiums = pl.DataFrame(
    prem_rows,
    schema=["policy_id", "line_of_business", "region", "earned_month", "earned_premium_month"],
    orient="row",
).with_columns(pl.col("earned_month").str.to_date())

# ----------------------------------------------------------------------------
# SUMMARY (printed) + write to Unity Catalog
# ----------------------------------------------------------------------------
tot_earned = policies["earned_premium"].sum()
tot_incurred = claims["incurred_loss"].sum()
tot_exp = policies["commission_amount"].sum() + policies["other_expense_amount"].sum()
print("=" * 60)
print(f"customers : {customers.height:>8,}")
print(f"policies  : {policies.height:>8,}")
print(f"claims    : {claims.height:>8,}  (the loss run)")
print(f"premiums  : {premiums.height:>8,}  (monthly)")
print("-" * 60)
print(f"Earned premium : EUR {tot_earned:>15,.0f}")
print(f"Incurred loss  : EUR {tot_incurred:>15,.0f}")
print(f"Loss ratio     : {tot_incurred / tot_earned:>8.1%}")
print(f"Expense ratio  : {tot_exp / policies['written_premium'].sum():>8.1%}")
print(f"Combined ratio : {tot_incurred / tot_earned + tot_exp / policies['written_premium'].sum():>8.1%}")
print("=" * 60)

# ---- Connect bridge to Unity Catalog ----
from databricks.connect import DatabricksSession
spark = DatabricksSession.builder.serverless().getOrCreate()

CATALOG = "axa_workshop"
SCHEMA = "insurance"
try:
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG}")
    print(f"catalog ready: {CATALOG}")
except Exception as e:
    print(f"[warn] could not create catalog {CATALOG}: {e}\n  -> falling back")
    CATALOG = "serverless_stable_xhky6g_catalog"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")

def write(df, name):
    (spark.createDataFrame(df.to_pandas())
        .write.format("delta").mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"{CATALOG}.{SCHEMA}.{name}"))
    print(f"  wrote {CATALOG}.{SCHEMA}.{name}: {df.height:,} rows")

write(customers, "customers")
write(policies, "policies")
write(claims, "claims")
write(premiums, "premiums")
print(f"\nDONE -> {CATALOG}.{SCHEMA}")
spark.stop()
