import pandas as pd
import numpy as np

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
pd.set_option("display.max_rows", 60)

m = pd.read_csv("data/clean/master_panel.csv")

print("=== National totals by year ===")
nat = m.groupby("Year")[["hdr_completions", "rbg_total", "rbg_rtp", "rbg_rsp_like", "rbg_total_covid_adj"]].sum()
nat["hdr_completions"] = nat["hdr_completions"].astype(int)
for c in ["rbg_total", "rbg_rtp", "rbg_rsp_like", "rbg_total_covid_adj"]:
    nat[c] = (nat[c] / 1e6).round(1)
print(nat)

print()
print("=== YoY growth rates (%) ===")
growth = nat.pct_change() * 100
print(growth.round(1))

print()
print("=== Panel balance check ===")
counts = m.groupby("HEP_Code")["Year"].nunique().sort_values()
print("Providers with <10 years of data:")
print(counts[counts < 10])

print()
print("=== hdr_has_suppressed_np flag prevalence by year ===")
print(m.groupby("Year")["hdr_has_suppressed_np"].sum())
