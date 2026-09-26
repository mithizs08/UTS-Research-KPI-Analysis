# Power BI Dashboard — Technical Notes

Three-page dashboard built from the extracts in `data/powerbi/` (six CSVs), reproducing the
report's two findings interactively with slicers and provider-level drill-down. Screenshots
are in `dashboard/screenshots/`; there is no live link (see README for why). These notes
document the data model, measures, and design decisions — not a click-by-click build log.

## Data model

Six flat tables, no relationships between them — each is self-contained for its visuals.

| Table | Grain | Purpose |
|---|---|---|
| `powerbi_panel` | provider × year | Base metrics: completions, funding, $/completion, cohort |
| `powerbi_growth` | provider × year | Precomputed YoY growth rates |
| `powerbi_leadlag_pairs` | provider × year | Funding growth(t) paired with completions growth(t+1), for the lead/lag scatter |
| `powerbi_robustness_checks` | one row per specification (9: 6 lead + 3 contemporaneous) | Every robustness variant tested for Finding 1 |
| `powerbi_go8_premium_results` | one row per program | Regression premiums (Total RBG / RTP / RSP) with CI and significance |
| `powerbi_go8_mechanism_validation` | one row per year | Go8's predicted vs. actual RSP share, reconstructed from HERDC income shares + the legislated formula weights |

Two columns are precomputed into the CSVs rather than built in Power Query, because Power BI
can't derive them cleanly on its own:
- **`RowKey`** (`powerbi_leadlag_pairs`): a synthetic `HEP_Code_Year` ID. Without a row-level
  key in the scatter chart's granularity field, Power BI collapses all 290 provider-years into
  a single averaged point.
- **`Go8_Label`** (`powerbi_panel`): text labels ("Go8" / "Rest of sector") for `is_go8`, so
  chart legends don't need a runtime lookup.
- **`Sort_Order`** (`powerbi_robustness_checks`): a table visual defaults to sorting
  alphabetically by whichever column it picks — here, `Specification` — which interleaves the
  lead and contemporaneous rows into a meaningless order. `Sort_Order` (1–9) is set as the
  **Sort by Column** for both `Test_Type` and `Specification`, so the intended grouping (lead
  rows first, primary spec → variants, then contemporaneous the same way) holds regardless of
  which of the two ends up as the active sort key.

Regression- and formula-derived numbers (premiums, p-values, lead/lag coefficients, predicted
RSP shares) are computed in Python and shipped as static values — Power BI can't reproduce
clustered-SE panel regressions or the from-first-principles formula reconstruction natively.

## DAX measures

```dax
-- on powerbi_panel
Total RBG = SUM(powerbi_panel[rbg_total])
Total HDR Completions = SUM(powerbi_panel[hdr_completions])
RBG per HDR Completion = DIVIDE([Total RBG], [Total HDR Completions])
Providers in Panel = DISTINCTCOUNT(powerbi_panel[HEP_Code])

HDR Completions Index Base2015 =
VAR CurrentTotal = [Total HDR Completions]
VAR BaseTotal = CALCULATE([Total HDR Completions], ALLSELECTED(powerbi_panel[Year]), powerbi_panel[Year] = 2015)
RETURN DIVIDE(CurrentTotal, BaseTotal) * 100

RBG Index Base2015 =
VAR CurrentTotal = [Total RBG]
VAR BaseTotal = CALCULATE([Total RBG], ALLSELECTED(powerbi_panel[Year]), powerbi_panel[Year] = 2015)
RETURN DIVIDE(CurrentTotal, BaseTotal) * 100

-- on powerbi_go8_premium_results
Go8 Premium Total RBG =
CALCULATE(SELECTEDVALUE(powerbi_go8_premium_results[Go8_Premium_Pct]), powerbi_go8_premium_results[Program] = "Total RBG")

Significance Label = SELECTEDVALUE(powerbi_go8_premium_results[Significant_at_5pct])
```

Notes on two of these:
- The index measures are named `Base2015`, not `Index (2015=100)` — a measure name can't
  contain `=`, since DAX reads the first `=` in whatever's typed as the name/expression
  boundary. The friendlier "2015 = 100" label is applied per-visual instead (rename the field
  display label in the Values well), not in the measure name itself.
- `Significance Label` exists because Boolean columns don't expose a `First` aggregation in a
  Tooltips well the way text columns do — dragging the raw `Significant_at_5pct` column in
  directly defaults to `Count`, which always evaluates to 1 (one row per program) regardless
  of the actual value. `SELECTEDVALUE` sidesteps the aggregation-picker issue entirely.

## Page 1 — Overview

Year (range) and Cohort (multi-select) slicers; five cards (Total HDR Completions, Total RBG,
RBG per HDR Completion, Providers in Panel, Go8 Premium Total RBG — the last previews Finding
2's headline number); a clustered column chart of Total RBG by Cohort, Go8 highlighted against
a neutral grey for the rest.

## Page 2 — Finding 1: no significant funding–completions dynamic detected

- Line chart: `HDR Completions Index Base2015` and `RBG Index Base2015` by Year — both series
  indexed to a common base (2015 = 100) rather than dual-axis, since the two measures are on
  incomparable scales and a dual-axis chart would misrepresent their relative movement.
- Scatter: funding growth(t) vs. completions growth(t+1) from `powerbi_leadlag_pairs`, one dot
  per provider-year via `RowKey`, with a trend line (near-flat, r≈0.03).
- Table: all 9 robustness-check rows (`Test_Type`, `Specification`, `N`, `Coefficient`,
  `P_Value`), sorted by `Sort_Order`, with conditional formatting flagging `P_Value` < 0.05 in
  red — surfaces the one fragile exception (contemporaneous spec, 2024 excluded, p = 0.03)
  without burying it in the middle of an alphabetically-sorted list.

## Page 3 — Finding 2: Go8's premium reflects the legislated formula, not completions

- Line chart: `RBG per HDR Completion` by Year, legend = `Go8_Label` — the $-per-completion
  gap, shown to be large and stable across the decade rather than a recent trend.
- Line chart: `Go8_RSP_Share_Actual_Pct`, `Go8_RSP_Share_Predicted_Pct` (dashed, to distinguish
  it from actual despite the two lines nearly overlapping), and `Go8_HDR_Completions_Share_Pct`
  by Year — the mechanism-validation chart, the strongest single piece of evidence in the
  report: the predicted share (reconstructed from nothing but HERDC income shares and the
  legislated formula weights) tracks the actual share almost exactly, while completions share
  sits well below both.
- Clustered column chart: Go8 premium by `Program` (RSP / Total RBG / RTP), with
  `Formula_Basis`, `CI_Low_Pct`, `CI_High_Pct`, `P_Value`, and `Significance Label` all in
  Tooltips — kept out of a separate table visual, since a fourth visual repeating the same 3
  rows the chart already shows wasn't worth the added clutter.

## Design notes carried over from the static report charts

- Both dynamic line charts on Page 2/3 are single-axis, indexed to a common base or
  share-of-total, for the same reason as above: a dual-axis chart with two different scales is
  misleading regardless of which platform renders it.
- Color pairing is consistent with the static charts (blue = Go8, orange = rest of sector /
  HDR completions share, dashed = predicted), so the dashboard and PDF read as one system.
- Wording avoids implying more certainty than the underlying statistics support — "not
  significant" and "no evidence of," not "proves" or "shows there is no" — in titles and text
  boxes alike.
