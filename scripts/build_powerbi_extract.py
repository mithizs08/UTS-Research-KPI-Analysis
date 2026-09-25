"""Build clean, Power-BI-ready extracts from the master panel.

Two flat tables (no relationships needed - small enough to keep denormalised):
  powerbi_panel.csv  - one row per provider-year, base metrics + $/completion
  powerbi_growth.csv - one row per provider-year, YoY growth rates precomputed
                        in Python (avoids fiddly DAX time-intelligence over a
                        non-contiguous panel), with the COVID year flagged
                        rather than dropped so the dashboard user can toggle it.
"""
import pandas as pd
import numpy as np
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "powerbi"
OUT.mkdir(exist_ok=True)

m = pd.read_csv("data/clean/master_panel_v2.csv")
m = m[(m["Year"] >= 2015) & (m["Year"] <= 2024)].copy()

panel = m[["HEP_Code", "Institution_canonical", "Cohort", "Year",
           "hdr_completions", "total_completions", "rbg_total", "rbg_rtp", "rbg_rsp_like"]].copy()
panel = panel.rename(columns={"Institution_canonical": "Institution", "rbg_rsp_like": "rbg_rsp"})
panel["is_go8"] = (panel["Cohort"] == "Go8").astype(int)
panel["Go8_Label"] = panel["is_go8"].map({1: "Go8", 0: "Rest of sector"})  # ready-made Legend field
# guard against divide-by-zero (e.g. Batchelor Institute, 2022: 0 HDR completions that
# year) - leave the ratio blank rather than writing out "inf", which Power BI/Excel
# can't read as a number.
panel["rbg_per_hdr_completion"] = (panel["rbg_total"] / panel["hdr_completions"]).replace(
    [np.inf, -np.inf], np.nan
)
panel["is_covid_year"] = (panel["Year"] == 2021).astype(int)
panel.to_csv(OUT / "powerbi_panel.csv", index=False)

g = panel.sort_values(["HEP_Code", "Year"]).copy()
for col in ["hdr_completions", "rbg_total", "rbg_rtp", "rbg_rsp"]:
    g[f"log_{col}"] = np.log(g[col].clip(lower=1))
    g[f"growth_{col}_pct"] = g.groupby("HEP_Code")[f"log_{col}"].diff() * 100  # log-growth, ~pct for small moves
growth_cols = ["HEP_Code", "Institution", "Cohort", "Year", "is_go8", "is_covid_year"] + \
              [f"growth_{c}_pct" for c in ["hdr_completions", "rbg_total", "rbg_rtp", "rbg_rsp"]]
growth = g[growth_cols].dropna(subset=["growth_hdr_completions_pct"], how="all")
growth.to_csv(OUT / "powerbi_growth.csv", index=False)

print("wrote", OUT / "powerbi_panel.csv", panel.shape)
print("wrote", OUT / "powerbi_growth.csv", growth.shape)
print()
print(panel.head())
