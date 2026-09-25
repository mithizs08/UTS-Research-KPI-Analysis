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

print("=== Go8 share of national totals, by year ===")
shares = m.groupby(["Year", "Cohort"])[["hdr_completions", "rbg_total"]].sum().reset_index()
tot = m.groupby("Year")[["hdr_completions", "rbg_total"]].sum().rename(
    columns={"hdr_completions": "tot_hdr", "rbg_total": "tot_rbg"})
shares = shares.merge(tot, on="Year")
shares["hdr_share"] = (shares["hdr_completions"] / shares["tot_hdr"] * 100).round(1)
shares["rbg_share"] = (shares["rbg_total"] / shares["tot_rbg"] * 100).round(1)
go8 = shares[shares["Cohort"] == "Go8"][["Year", "hdr_share", "rbg_share"]]
print(go8.to_string(index=False))

print()
print("=== Concentration (HHI-style): top-5 and top-8 providers' share of national totals, 2024 vs 2015 ===")
for yr in [2015, 2024]:
    d = m[m["Year"] == yr].sort_values("hdr_completions", ascending=False)
    tot_hdr = d["hdr_completions"].sum()
    tot_rbg = d["rbg_total"].sum()
    top5_hdr = d.head(5)["hdr_completions"].sum() / tot_hdr * 100
    top8_hdr = d.head(8)["hdr_completions"].sum() / tot_hdr * 100
    d2 = m[m["Year"] == yr].sort_values("rbg_total", ascending=False)
    top5_rbg = d2.head(5)["rbg_total"].sum() / tot_rbg * 100
    top8_rbg = d2.head(8)["rbg_total"].sum() / tot_rbg * 100
    print(f"{yr}: top-5 share of HDR completions = {top5_hdr:.1f}%, of RBG $ = {top5_rbg:.1f}%  |  top-8: HDR {top8_hdr:.1f}%, RBG {top8_rbg:.1f}%")

print()
print("=== Does the levels correlation (r=0.94) survive removing Go8? ===")
for excl in [None, "Go8"]:
    d = m if excl is None else m[m["Cohort"] != excl]
    r = d["hdr_completions"].corr(d["rbg_total"])
    print(f"excl={excl}: n={len(d)}, corr(levels)={r:.3f}")

print()
print("=== Rank stability: Spearman rank corr of provider HDR-completions rank vs RBG-$ rank, per year ===")
for yr in sorted(m["Year"].unique()):
    d = m[m["Year"] == yr]
    rho = d["hdr_completions"].rank().corr(d["rbg_total"].rank(), method="pearson")
    print(f"{yr}: spearman-style rank corr = {rho:.3f}  (n={len(d)})")

print()
print("=== Year-over-year rank persistence: does the SAME top-8 list repeat? ===")
top8_by_year = {}
for yr in sorted(m["Year"].unique()):
    d = m[m["Year"] == yr].sort_values("hdr_completions", ascending=False)
    top8_by_year[yr] = set(d.head(8)["HEP_Code"])
years = sorted(top8_by_year.keys())
for y1, y2 in zip(years[:-1], years[1:]):
    overlap = len(top8_by_year[y1] & top8_by_year[y2])
    print(f"{y1}->{y2}: {overlap}/8 providers stayed in the top-8 HDR completions list")

print()
print("=== Which providers are in the 2015 top-8 AND the 2024 top-8? ===")
names = m[["HEP_Code", "Institution_canonical"]].drop_duplicates().set_index("HEP_Code")["Institution_canonical"]
both = top8_by_year[2015] & top8_by_year[2024]
print([names[c] for c in both])
only_2024 = top8_by_year[2024] - top8_by_year[2015]
print("New to top-8 by 2024:", [names[c] for c in only_2024])
