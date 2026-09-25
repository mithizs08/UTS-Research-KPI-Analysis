"""
Build powerbi_leadlag_pairs.csv - one row per provider-year transition,
pairing funding growth in year t with HDR completions growth in year t+1
(the pairing Finding 1's Panel B scatter needs). 2021 excluded, matching the
report's primary specification.

Includes a precomputed RowKey (HEP_Code + "_" + Year) so the Power BI
scatter chart can use it directly in the Details field well to force one
point per row, instead of needing a Power Query custom column.
"""
import pandas as pd
import numpy as np
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "powerbi"
OUT.mkdir(exist_ok=True)

m = pd.read_csv("data/clean/master_panel_v2.csv")
m = m[(m["Year"] >= 2015) & (m["Year"] <= 2024)].copy().sort_values(["HEP_Code", "Year"])
m["log_hdr"] = np.log(m["hdr_completions"].clip(lower=1))
m["log_rbg"] = np.log(m["rbg_total"].clip(lower=1))
m["g_hdr"] = m.groupby("HEP_Code")["log_hdr"].diff()
m["g_rbg"] = m.groupby("HEP_Code")["log_rbg"].diff()

gm = m[m["Year"] != 2021].copy()
gm["g_hdr_lead1"] = gm.groupby("HEP_Code")["g_hdr"].shift(-1)
d = gm.dropna(subset=["g_rbg", "g_hdr_lead1"])[
    ["HEP_Code", "Institution_canonical", "Cohort", "Year", "g_rbg", "g_hdr_lead1"]
].copy()
d["g_rbg_total_pct"] = d["g_rbg"] * 100
d["g_hdr_completions_next_year_pct"] = d["g_hdr_lead1"] * 100
d = d.rename(columns={"Institution_canonical": "Institution"})
d["RowKey"] = d["HEP_Code"].astype(str) + "_" + d["Year"].astype(str)

out = d[["RowKey", "HEP_Code", "Institution", "Cohort", "Year",
         "g_rbg_total_pct", "g_hdr_completions_next_year_pct"]]
out_path = OUT / "powerbi_leadlag_pairs.csv"
out.to_csv(out_path, index=False)
print("wrote", out_path, out.shape)
print(out.head())
