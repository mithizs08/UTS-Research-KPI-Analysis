import pandas as pd
import numpy as np

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 20)
pd.set_option("display.max_rows", 80)

m = pd.read_csv("data/clean/master_panel.csv")
rbg_raw = pd.read_csv("data/rbg/rbg_table2_long.csv")

cohort = rbg_raw[["HEP Code", "Cohort"]].drop_duplicates().rename(columns={"HEP Code": "HEP_Code"})
cohort_mode = cohort.groupby("HEP_Code")["Cohort"].agg(lambda s: s.mode().iat[0])
m = m.merge(cohort_mode.rename("Cohort"), on="HEP_Code", how="left")

m = m.sort_values(["HEP_Code", "Year"])

for col in ["hdr_completions", "rbg_total", "rbg_rtp", "rbg_rsp_like", "rbg_total_covid_adj"]:
    m[f"log_{col}"] = np.log(m[col].clip(lower=1))
    m[f"g_{col}"] = m.groupby("HEP_Code")[f"log_{col}"] .diff()  # log growth ~ pct change

panel = m[m["Year"] != 2021].copy()  # 2021 dropped as primary spec: COVID hit both sides (RSP one-off + HDR completion delays)
panel_incl2021 = m.copy()

print("Providers x years in growth panel (2021 excluded):", panel["g_hdr_completions"].notna().sum())

def pooled_and_fe_corr(df, xcol, ycol, lag, min_obs=30):
    """corr(x_t, y_{t+lag}) pooled, and within-provider (fixed-effects, i.e.
    demeaned by HEP_Code) - the FE version removes any pure cross-sectional
    size confound (big unis have both more funding and more completions)."""
    d = df[["HEP_Code", "Year", xcol, ycol]].dropna().copy()
    d["Year_shifted"] = d["Year"] - lag
    merged = d.merge(
        df[["HEP_Code", "Year", ycol]].rename(columns={"Year": "Year_shifted", ycol: "y_lead"}),
        on=["HEP_Code", "Year_shifted"], how="inner"
    )
    merged = merged.dropna(subset=[xcol, "y_lead"])
    if len(merged) < min_obs:
        return len(merged), np.nan, np.nan
    pooled_r = merged[xcol].corr(merged["y_lead"])
    x_dm = merged[xcol] - merged.groupby("HEP_Code")[xcol].transform("mean")
    y_dm = merged["y_lead"] - merged.groupby("HEP_Code")["y_lead"].transform("mean")
    fe_r = x_dm.corr(y_dm)
    return len(merged), pooled_r, fe_r


print()
print("=== Growth-rate cross-correlation: g_rbg_total(t) vs g_hdr_completions(t+lag) ===")
print("lag>0 means funding growth LEADS completions growth by `lag` years; lag<0 means funding growth LAGS (follows) completions growth")
for lag in range(-3, 4):
    n, pooled_r, fe_r = pooled_and_fe_corr(panel, "g_rbg_total", "g_hdr_completions", lag)
    print(f"lag={lag:+d}  n={n:4d}  pooled_r={pooled_r if pd.isna(pooled_r) else round(pooled_r,3):>7}  within_provider_r={fe_r if pd.isna(fe_r) else round(fe_r,3):>7}")

print()
print("=== Same, using RTP only (the explicitly performance-formula-driven program) ===")
for lag in range(-3, 4):
    n, pooled_r, fe_r = pooled_and_fe_corr(panel, "g_rbg_rtp", "g_hdr_completions", lag)
    print(f"lag={lag:+d}  n={n:4d}  pooled_r={pooled_r if pd.isna(pooled_r) else round(pooled_r,3):>7}  within_provider_r={fe_r if pd.isna(fe_r) else round(fe_r,3):>7}")

print()
print("=== Same, using RSP-like only (income/publication-driven, NOT completions-formula-driven) ===")
for lag in range(-3, 4):
    n, pooled_r, fe_r = pooled_and_fe_corr(panel, "g_rbg_rsp_like", "g_hdr_completions", lag)
    print(f"lag={lag:+d}  n={n:4d}  pooled_r={pooled_r if pd.isna(pooled_r) else round(pooled_r,3):>7}  within_provider_r={fe_r if pd.isna(fe_r) else round(fe_r,3):>7}")

print()
print("=== Levels (not growth) pooled correlation, for reference - expect inflated by size ===")
lvl = panel[["hdr_completions", "rbg_total"]].dropna()
print("corr(levels):", lvl["hdr_completions"].corr(lvl["rbg_total"]).round(3))

print()
print("=== By Cohort: within-provider growth correlation, rbg_total(t) vs hdr_completions(t+1) [funding leads] ===")
for coh, g in panel.groupby("Cohort"):
    n, pooled_r, fe_r = pooled_and_fe_corr(g, "g_rbg_total", "g_hdr_completions", 1, min_obs=10)
    print(f"{coh:15s} n={n:4d}  pooled_r={pooled_r if pd.isna(pooled_r) else round(pooled_r,3):>7}  within_r={fe_r if pd.isna(fe_r) else round(fe_r,3):>7}")

print()
print("=== By Cohort: within-provider growth correlation, hdr_completions(t) vs rbg_total(t+1) [completions leads / funding lags] ===")
for coh, g in panel.groupby("Cohort"):
    n, pooled_r, fe_r = pooled_and_fe_corr(g, "g_hdr_completions", "g_rbg_total", 1, min_obs=10)
    print(f"{coh:15s} n={n:4d}  pooled_r={pooled_r if pd.isna(pooled_r) else round(pooled_r,3):>7}  within_r={fe_r if pd.isna(fe_r) else round(fe_r,3):>7}")
