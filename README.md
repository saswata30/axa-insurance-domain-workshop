# AXA Insurance — Genie Ontology Workshop (business-user edition)

A 60-minute, **business-user-driven** Databricks workshop that builds a **governed semantic layer** for a
synthetic AXA Property & Casualty (P&C) book — the *loss run* and the *loss ratio* — and makes it self-serve
and trustworthy through **Unity Catalog Discover**.

> **The one line to remember:** *Genie interprets the meaning you encode — so encode it once, govern it, and
> let the whole business discover it.*

## The four building blocks

Built bottom-up in the notebooks; discovered top-down at the domain.

```
  Gold tables  →  Metric Views  →  Genie Agent            (what you BUILD — notebooks 01→03)
       └───────────────┴──────────────┘
                       ▼
              Insurance DOMAIN                             (how the business DISCOVERS it — notebook 04)
       pages · bulk glossary · every asset tagged in
```

| # | Notebook | What it does |
|---|----------|--------------|
| 00 | `notebooks/00_README_Agenda.py` | Business-user journey + agenda |
| 01 | `notebooks/01_Gold_Layer_Tables.py` | **Certify** the P&C tables as trusted gold assets (descriptions, keys, certification) — *runnable SQL* |
| 02 | `notebooks/02_Metric_Views.py` | Define the KPIs **once** — loss ratio, combined ratio, frequency, severity — as governed metric views — *runnable SQL* |
| 03 | `notebooks/03_Genie_Agent.py` | Publish & curate the **Genie Agent** on the gold tables + metric views — *UI walkthrough* |
| 04 | `notebooks/04_Insurance_Domain_and_Glossary.py` | Create the **Insurance domain**, **bulk-import the glossary** as pages, and **tag every asset** into the domain — *UI walkthrough, with embedded screenshots* |

## Deck

`deck/AXA_Insurance_Domain_Workshop.html` — a self-contained dark presentation deck (14 slides, embedded
screenshots). Open it in a browser; append `?export=N` to isolate slide *N* for recording. `deck.template.html`
is the source template (screenshots are injected as base64 at build time).

## Screenshots

`screenshots/` — the real Discover UI captured while building the live example:
create domain → tag assets → bulk-import glossary → published domain with 8 glossary pages.

## The dataset & KPIs

Runs against `serverless_stable_xhky6g_catalog.insurance` (`customers`, `policies`, `claims`, `premiums`).
Calibrated portfolio truth: **loss ratio ≈ 64.6%**, **combined ratio ≈ 91.8%** (5,000 policies, 2,979 claims).

## Notes on the feature (as of Sept 2026)

- **Domains** and **Pages** live in **Catalog ▸ Discover** and are **UI features** (no REST API / SQL DDL yet;
  docs: `docs.databricks.com/uc-semantics/`). A domain is backed by a **governed tag** — *adding an asset to a
  domain = assigning that tag*, which works for tables, metric views, and Genie Agents.
- The governed-tag name is **account-unique**; this workshop uses the tag **`AXA Insurance`**.
- **Bulk glossary import** lives in the page editor's *Genie Code* panel ("Bulk import pages") and accepts pasted
  text, uploaded files (PDF/CSV), or connected sources (Confluence / GitHub / Google Drive).

*Data is synthetic. Screenshots are of the Databricks product UI in a Field Engineering demo workspace.*
