# Power BI Dashboard — Build Guide

Written for Power BI Desktop. Steps below assume the standard ribbon/pane layout (current
Power BI Desktop as of 2026); menu names may sit one level deeper in older versions, but the
same options exist. Data extracts are in `data/powerbi/` (six CSVs, already cleaned — no
Power Query transformation needed beyond setting data types in step 2).

> **If a column named below doesn't appear in your table**: Power BI only reads a CSV at the
> moment you import it — it does not watch the file for later changes, and these extracts
> were revised more than once while this guide was being written. Two fixes, depending on
> what changed:
> - **A column is missing but the row count looks right** → add it yourself: click the table
>   in the **Data** pane → **Table tools** → **New Column** → write the DAX for it (each
>   missing-column case below gives you the exact formula).
> - **Rows are missing or counts look wrong** (a DAX column can't add new *rows*, only values
>   to rows that already exist) → right-click the table → **Delete from model** → **Home** →
>   **Get Data** → **Text/CSV** → re-select the file from `data/powerbi/` → **Load**.

| File | Grain | Key columns used below |
|---|---|---|
| `powerbi_panel.csv` | provider x year | `hdr_completions`, `rbg_total`, `rbg_per_hdr_completion`, `Cohort`, `Go8_Label`, `is_go8` |
| `powerbi_growth.csv` | provider x year | precomputed YoY growth rates (%) — not used directly below, kept for optional extra visuals |
| `powerbi_leadlag_pairs.csv` | provider x year | `g_rbg_total_pct`, `g_hdr_completions_next_year_pct`, `RowKey` |
| `powerbi_robustness_checks.csv` | one row per specification (9 rows: 6 lead + 3 contemporaneous) | `Test_Type`, `Specification`, `N`, `Coefficient`, `P_Value`, `Sort_Order` |
| `powerbi_go8_premium_results.csv` | one row per program | `Go8_Premium_Pct`, `CI_Low_Pct`, `CI_High_Pct`, `P_Value`, `Significant_at_5pct`, `Formula_Basis` |
| `powerbi_go8_mechanism_validation.csv` | one row per year | `Go8_RSP_Share_Actual_Pct`, `Go8_RSP_Share_Predicted_Pct`, `Go8_HDR_Completions_Share_Pct` |

`Go8_Label` (text: "Go8" / "Rest of sector") and `RowKey` (a unique ID per row) are already
built into the CSVs so you don't need any Power Query custom-column steps — just drag them
in where noted.

## 1. Import the data

1. **Home** ribbon → **Get Data** → **Text/CSV**.
2. Browse to `data/powerbi/`, select a file, click **Open**, then **Load** (not "Transform
   Data" — you can fix types after loading in step 2 below). Repeat for all six files.
3. In the **Data** pane (right side, the table/grid icon), confirm you now see six tables:
   `powerbi_panel`, `powerbi_growth`, `powerbi_leadlag_pairs`, `powerbi_robustness_checks`,
   `powerbi_go8_premium_results`, `powerbi_go8_mechanism_validation`.
4. Click **Model** view (left-hand vertical icon strip, second or third icon down). If Power
   BI drew any auto-detected relationship lines between tables, click the line and press
   **Delete** — none of the visuals below need them.

## 2. Set data types

For each table: click the table name in the **Data** pane → for each column, click its
header → **Column tools** ribbon tab appears → use the **Data type** dropdown.

- `Year`, `HEP_Code`, `N`, `Sort_Order` → **Whole Number**
- `Cohort`, `Institution`, `Program`, `Specification`, `Test_Type`, `Formula_Basis`,
  `Go8_Label`, `RowKey` → **Text**
- `is_go8`, `is_covid_year`, `Significant_at_5pct` → first set to **Whole Number**, click the
  dropdown again and set to **True/False** (two steps — converting straight from Text to
  True/False can misread "0"/"1" strings; see the note in the previous fix)
- Everything else (`hdr_completions`, `rbg_total`, `rbg_per_hdr_completion`, `..._pct`,
  `Coefficient`, `P_Value`, `Go8_Premium_Pct`, CI columns, `..._Share_Pct`) → **Decimal
  Number**

## 3. Create these DAX measures

Click the `powerbi_panel` table in the **Data** pane → **Table tools** ribbon tab →
**New measure**. This opens the formula bar at the bottom of the screen; type the full text
below (name and all) and press **Enter**. Repeat "New measure" for each one.

```dax
Total RBG = SUM(powerbi_panel[rbg_total])
Total HDR Completions = SUM(powerbi_panel[hdr_completions])

RBG per HDR Completion =
DIVIDE([Total RBG], [Total HDR Completions])

HDR Completions Index Base2015 =
VAR CurrentTotal = [Total HDR Completions]
VAR BaseTotal =
    CALCULATE([Total HDR Completions], ALLSELECTED(powerbi_panel[Year]), powerbi_panel[Year] = 2015)
RETURN DIVIDE(CurrentTotal, BaseTotal) * 100

RBG Index Base2015 =
VAR CurrentTotal = [Total RBG]
VAR BaseTotal =
    CALCULATE([Total RBG], ALLSELECTED(powerbi_panel[Year]), powerbi_panel[Year] = 2015)
RETURN DIVIDE(CurrentTotal, BaseTotal) * 100

Providers in Panel = DISTINCTCOUNT(powerbi_panel[HEP_Code])
```

The five measures above all go on `powerbi_panel` (select it in the Data pane before clicking
**New measure** each time). Two more go on a different table — click
`powerbi_go8_premium_results` in the Data pane first, then **New measure** for each:

```dax
Go8 Premium Total RBG =
CALCULATE(
    SELECTEDVALUE(powerbi_go8_premium_results[Go8_Premium_Pct]),
    powerbi_go8_premium_results[Program] = "Total RBG"
)

Significance Label = SELECTEDVALUE(powerbi_go8_premium_results[Significant_at_5pct])
```

`Go8 Premium Total RBG` pins the card to the "Total RBG" row's value (83.2) regardless of any
other filters on the page, rather than needing a separate visual-level filter that's easy to
accidentally remove later. `Significance Label` is for the Page 3 tooltip below — Boolean
(True/False) columns don't expose a `First` aggregation option in a Tooltips well the way Text
columns do, so a measure is the reliable fix instead of fighting with the column's default
aggregation.

**Naming note:** measure names can't contain an `=` sign — DAX reads the first `=` in
whatever you paste as the name/expression boundary, so a name like `Index (2015=100)` breaks
the parser. That's why these are named `Base2015` instead. If you want "2015 = 100" to appear
in a chart legend, rename the field *display label* inside that specific visual later (right-
click the field pill in the Values/Y-axis well → **Rename for this visual**), not the measure
itself.

After creating these, they'll appear under their respective table in the Data pane with a
calculator icon (distinguishing them from plain columns) — five under `powerbi_panel`, two
under `powerbi_go8_premium_results`.

## 4. Page 1 — "Overview"

Rename the page first: double-click the "Page 1" tab at the bottom → type `Overview`.

**Two slicers**, side by side across the top:

1. Click empty canvas (nothing selected) → **Visualizations** pane (right side) → click the
   **Slicer** icon (looks like a small filter/funnel box in the icon grid).
2. With the new empty slicer still selected, go to the **Data** pane → expand `powerbi_panel`
   → drag `Year` onto the slicer box (or drag it into the **Field** well under **Build visual**
   in the Visualizations pane).
3. Format pane (paint-roller icon, next to Visualizations) → **Slicer settings** → **Style**
   → choose **Between** — this gives a min/max range slider instead of a checklist, better
   for a 10-year range.
4. Resize/drag it to the top-left of the canvas.
5. Click empty canvas again → insert a second **Slicer** the same way → drag `Cohort` (from
   `powerbi_panel`) into its Field well.
6. Format pane → **Slicer settings** → **Style** → **Dropdown**. Under **Selection**, make
   sure **Single select** is toggled **off** so multiple cohorts can be picked at once.
7. Place it beside the Year slicer.

**Five card visuals** (the original three, plus two new ones that tie this page to the
findings):

1. Click empty canvas → Visualizations pane → click the **Card** icon (a plain rectangle with
   a big number — if your version shows both "Card" and "Card (new)", either works; steps
   below match "Card").
2. Data pane → expand `powerbi_panel` → drag the measure `Total HDR Completions` (calculator
   icon) onto the card, or into the **Fields** well under Build visual.
3. Click empty canvas → insert a second **Card** → drag `Total RBG` onto it.
4. Click empty canvas → insert a third **Card** → drag `RBG per HDR Completion` onto it.
5. Click empty canvas → insert a fourth **Card** → drag `Providers in Panel` (also under
   `powerbi_panel`) onto it — gives scale context (43).
6. Click empty canvas → insert a fifth **Card** → Data pane → expand
   `powerbi_go8_premium_results` → drag `Go8 Premium Total RBG` onto it — previews Finding
   2's headline number (83.2) right on the overview page.
7. Arrange the five cards in a row beneath the slicers (drag by their center to move, drag a
   corner handle to resize).
8. Optional formatting per card: select it → Format pane → **Callout value** → increase font
   size to ~28pt; **Category label** → toggle on if it's off, so each card shows its measure
   name underneath the number. For the Go8 premium card specifically, rename its category
   label text (same **Category label** section → there's a text field to override the
   displayed name) to "Go8 Funding Premium (%)", since the raw number (83.2) has no % sign
   baked in.

**Stacked bar chart → use a Clustered column chart instead** (a single value per category
doesn't actually stack; "stacked" needs a second dimension, which we don't have here):

1. Click empty canvas → Visualizations pane → click **Clustered column chart**.
2. Drag `Cohort` (from `powerbi_panel`) into the **X-axis** field well.
3. Drag the measure `Total RBG` into the **Y-axis** field well.
4. Sort descending: hover the visual → click the **"..."** (more options) in its top-right
   corner → **Sort by** → `Total RBG` → make sure the sort arrow shows descending.
5. Highlight Go8: Format pane → **Data colors** → each `Cohort` value gets its own color
   swatch — click the swatch next to "Go8" and set it to blue (hex `2A78D6`, matching the
   report), and set the others to a neutral grey (hex `C3C2B7`) so Go8 visually stands out.
6. Chart title: Format pane → **Title** → toggle on → type "Total RBG funding by cohort".

## 5. Page 2 — "Finding 1: No significant funding–completions dynamic detected"

New page: click the **+** tab at the bottom → rename it to match the title above (this exact
phrasing, not "no link" or "no relationship exists" — see the design note at the bottom).

**Title text box:** **Insert** ribbon → **Text box** → type the page title → drag to the top
of the canvas → Home ribbon (with text selected) set font size ~20pt bold.

**Line chart** (reproduces report Panel A):

1. Click empty canvas → Visualizations pane → **Line chart**.
2. Drag `Year` (from `powerbi_panel`) into **X-axis**.
3. Drag the measure `HDR Completions Index Base2015` into **Y-axis**. Then drag `RBG Index
   Base2015` into the *same* Y-axis well, underneath the first one — Power BI automatically
   draws it as a second line with its own legend entry (no separate Legend field needed when
   you use two measures this way).
4. Rename the series for a clean legend: in the **Y-axis** well, click the small dropdown
   arrow on the `HDR Completions Index Base2015` pill → **Rename for this visual** → type
   "HDR completions". Repeat for `RBG Index Base2015` → "RBG funding".
5. Format pane → **Y-axis** → **Axis title** → toggle on → type "Index (2015 = 100)".
6. Format pane → **Title** → type "National totals move on different paths".

**Scatter chart** (reproduces report Panel B):

1. Click empty canvas → Visualizations pane → **Scatter chart**.
2. Data pane → expand `powerbi_leadlag_pairs` → drag `g_rbg_total_pct` into **X-axis**.
3. Drag `g_hdr_completions_next_year_pct` into **Y-axis**.
4. Drag `RowKey` into the **Details** field well (some Power BI versions label this well
   **Values** instead — same purpose, use whichever one your version shows). This is the
   important step: without it, Power BI aggregates all 290 rows into a single averaged dot;
   `RowKey` is a synthetic ID (`HEP_Code` + `Year`, e.g. `1019_2016`) that's unique per
   provider-year, so it forces one dot per row instead, matching the report chart. If you
   loaded this table before this ID existed in the CSV, you don't need to re-import — click
   `powerbi_leadlag_pairs` in the Data pane → **Table tools** → **New Column** → type
   `RowKey = powerbi_leadlag_pairs[HEP_Code] & "_" & powerbi_leadlag_pairs[Year]` → Enter, and
   it'll appear as a calculated column ready to drag in.
5. Add a trend line: select the visual → Format pane → **Analytics** tab → find **Trend
   line** → toggle on. It should sit almost flat — that's the point (r≈0.03).
6. Optional reference lines at zero: same **Analytics** tab → **X-axis constant line** and
   **Y-axis constant line** → toggle on, value `0` for each, thin grey color.
7. Format pane → **X-axis** → **Axis title** → "Funding growth, year t (%)"; **Y-axis** →
   **Axis title** → "HDR completions growth, year t+1 (%)".
8. Format pane → **Title** → "No lead/lag relationship (r ≈ 0.03)".

**Table visual** (robustness checks — new evidence from the challenge round; the table now
has 9 rows, 6 testing the lead specification (funding growth → *next-year* completions
growth) and 3 testing the contemporaneous one (funding growth vs. *same-year* completions
growth) — the one fragile exception, p=0.03, is a contemporaneous-spec row, not a lead one):

1. Click empty canvas → Visualizations pane → **Table**.
2. Data pane → expand `powerbi_robustness_checks` → drag `Test_Type`, then `Specification`,
   then `N`, then `Coefficient`, then `P_Value` into the **Columns** field well, in that order
   (drag each one at a time; they'll appear left to right in the order you add them).
   `Test_Type` first makes it obvious at a glance which 6 rows are the lead spec and which 3
   are the contemporaneous spec, instead of the two groups being easy to conflate.
3. Fix the row order before doing anything else with this table — a table visual defaults to
   sorting alphabetically by whichever column it picks (here, `Specification`), which
   interleaves the Lead and Contemporaneous rows in a meaningless order. There's a
   purpose-built `Sort_Order` column (1–9) for this: go to **Data** view (the table-grid icon
   in the left-hand strip, not Report view) → select `powerbi_robustness_checks` → click the
   `Specification` column → **Column tools** ribbon → **Sort by Column** → choose
   `Sort_Order`. Repeat for the `Test_Type` column too (select it, same **Sort by Column** →
   `Sort_Order`) so the correct order holds regardless of which of the two the table ends up
   sorting by. Don't drag `Sort_Order` itself into the Columns well — it only needs to exist in
   the model for this to work, not be visible in the table.
4. Conditionally flag the one fragile result: click the dropdown arrow on `P_Value` in the
   Columns well → **Conditional formatting** → **Font color** → toggle on → **Format by**:
   Rules → set "if value is less than 0.05" → red; else → default/black → **OK**. Only the
   contemporaneous / "Excl. 2024" row (p=0.0307) should turn red, and it should now be the
   *last* row rather than buried in the middle.

   If you see 6 rows instead of 9, no `Sort_Order` column at all, or nothing ever turns red,
   you loaded this table before one of these fixes landed. Unlike `RowKey` earlier, none of
   this can be reliably patched with a New Column — the missing-rows case needs actual new
   rows (which a DAX column can't add), and `Sort_Order`'s mapping depends on a
   `Test_Type` + `Specification` combination that's fiddly to hand-write correctly as DAX.
   Simplest fix: right-click `powerbi_robustness_checks` in the Data pane → **Delete from
   model** → **Home** → **Get Data** → **Text/CSV** → re-select
   `data/powerbi/powerbi_robustness_checks.csv` → **Load**, then redo the data-type and
   Sort by Column steps.

**Text box** with the headline stat, below the table: **Insert** → **Text box** → type
*"Funding growth → next-year completions growth: p = 0.39 (not significant), provider + year
fixed effects, n = 290. Holds on an extended 2001–2024 window (n = 850, p = 0.41)."* → italics,
~10pt.

## 6. Page 3 — "Finding 2: Go8's premium is the legislated formula, not completions"

New page (**+** tab), rename it, add a title text box the same way as page 2.

**Line chart** (RBG $ per completion, Go8 vs. rest — reproduces report Panel A):

1. Click empty canvas → Visualizations pane → **Line chart**.
2. Data pane → expand `powerbi_panel` → drag `Year` into **X-axis**.
3. Drag the measure `RBG per HDR Completion` into **Y-axis**.
4. Drag `Go8_Label` into **Legend** — this splits the single line into two ("Go8" / "Rest of
   sector"), already correctly labeled (that's what the pre-built `Go8_Label` column is for).
   Not there? Same fix as `RowKey` earlier — click `powerbi_panel` → **Table tools** →
   **New Column** → `Go8_Label = IF(powerbi_panel[is_go8], "Go8", "Rest of sector")`.
5. Format pane → **Data colors** → set "Go8" to blue (`2A78D6`), "Rest of sector" to orange
   (`EB6834`), matching the report and Page 1's bar chart.
6. Format pane → **Y-axis** → **Axis title** → "RBG $ per HDR completion".
7. Format pane → **Title** → "The funding-per-completion gap is large and stable".

**Mechanism-validation line chart** (the strongest evidence — reproduces report Panel B):

1. Click empty canvas → Visualizations pane → **Line chart**.
2. Data pane → expand `powerbi_go8_mechanism_validation` → drag `Year` into **X-axis**.
3. Drag `Go8_RSP_Share_Actual_Pct` into **Y-axis**. Then drag `Go8_RSP_Share_Predicted_Pct`
   into the same Y-axis well underneath it. Then drag `Go8_HDR_Completions_Share_Pct` into
   the same well — you'll now have three lines.
4. Rename each for the legend (dropdown arrow on each pill in the Y-axis well → **Rename for
   this visual**): "Go8 share of RSP $ (actual)", "Go8 share of RSP $ (predicted)", "Go8 share
   of HDR completions".
5. Make "predicted" visually distinct: select the visual → Format pane → **Lines** (or
   **Shapes**, depending on version) → find the per-series style control → set the predicted
   series' **Line style** to **Dashed**. (If your version doesn't expose per-series line
   style, skip this — the legend labels alone still make the three series clear.)
6. Format pane → **Y-axis** → **Axis title** → "Go8 share of national total (%)".
7. Format pane → **Title** → "The formula predicts the outcome; completions don't".

**Clustered column chart** (Go8 premium by program):

1. Click empty canvas → Visualizations pane → **Clustered column chart**.
2. Data pane → expand `powerbi_go8_premium_results` → drag `Program` into **X-axis**.
3. Drag `Go8_Premium_Pct` into **Y-axis**.
4. Drag `Formula_Basis` into the **Tooltips** field well — hovering a bar now shows exactly
   what that program's formula weights ("Blend of RTP + RSP" / "50% HDR completions + 50%
   R&D income" / "100% R&D income, 0% completions"). Not there? Click
   `powerbi_go8_premium_results` → **Table tools** → **New Column**:
   ```
   Formula_Basis =
   SWITCH(
       powerbi_go8_premium_results[Program],
       "Total RBG", "Blend of RTP + RSP",
       "RTP", "50% HDR completions + 50% R&D income",
       "RSP", "100% R&D income, 0% completions"
   )
   ```
   (If you already loaded this table with the longer version of this text, you don't need to
   delete/reimport the table this time — the column and row count haven't changed, only the
   text inside it, so a plain **Refresh** (Home ribbon → **Refresh**, or right-click the table
   in the Data pane → **Refresh**) is enough to pull in the shorter wording. If you built the
   column yourself with **New Column** using the old long text, delete that column and redo
   it with the SWITCH formula above instead — a manually-typed DAX column won't update from a
   refresh of the CSV.)
5. Drag `CI_Low_Pct`, `CI_High_Pct`, and `P_Value` into the same **Tooltips** well, one at a
   time, underneath `Formula_Basis`. Then drag the measure `Significance Label` (created in
   step 3, under `powerbi_go8_premium_results`) into the Tooltips well too — use this measure,
   not the raw `Significant_at_5pct` column: Boolean columns don't offer a `First` aggregation
   option in a Tooltips well the way Text columns do, so the raw column defaults to **Count**
   (always shows 1, since every `Program` has exactly one row, regardless of the actual True/
   False value) with no reliable way to fix it from the field-well dropdown. `SELECTEDVALUE` in
   the measure sidesteps that entirely. This tooltip approach is the reliable way to surface
   CI/significance detail overall: built-in chart error bars in Power BI are version-dependent
   and don't accept custom CI columns directly, and a separate table visual next to this chart
   would just repeat the same 3 rows it already shows — not worth a fourth visual on this page
   for that.
6. Format pane → **Title** → "The premium lives in RSP, not RTP".

**Text box**: *"RSP is legally 47% competitive R&D income + 53% engagement income — zero HDR
completions weighting. RTP is 25%+25% income + 50% weighted HDR completions. Go8 holds ~68.5%
of competitive income and ~64.2% of engagement income, vs. ~48% of HDR completions."*

## 7. Publish and link

1. **Home** ribbon → **Publish** → choose a workspace → wait for the upload to finish → click
   the link it gives you to open the report in the browser.
2. In the browser: **File** → **Embed report** → **Publish to web (public)** *only if* you're
   comfortable making it public. Otherwise use **Share** (top-right) → set to "People with the
   link can view" — works fine for an appendix reference without making it fully public.
3. Copy that link into the report's Appendix in place of `[DASHBOARD_URL]`.

## Design notes carried over from the static charts

- Both dynamic line charts are **single-axis, indexed to a common base or share-of-total**
  rather than dual-axis — dual-axis charts with two different scales are misleading and were
  avoided in the static report charts for the same reason.
- Keep the Go8 / non-Go8 color pairing consistent with the static charts (blue = Go8, orange
  = rest of sector / HDR completions share, dashed = predicted) so the dashboard and PDF read
  as one system.
- Don't let the dashboard's Finding 1 page imply more certainty than the PDF does — "not
  significant" and "no evidence of" are the correct phrasings; avoid "proves," "shows there is
  no," or similar absolute language anywhere in text boxes or titles.
