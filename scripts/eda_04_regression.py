import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

pd.set_option("display.width", 220)

m = pd.read_csv("data/clean/master_panel.csv")
rbg_raw = pd.read_csv("data/rbg/rbg_table2_long.csv")
cohort = rbg_raw[["HEP Code", "Cohort"]].drop_duplicates().rename(columns={"HEP Code": "HEP_Code"})
cohort_mode = cohort.groupby("HEP_Code")["Cohort"].agg(lambda s: s.mode().iat[0])
m = m.merge(cohort_mode.rename("Cohort"), on="HEP_Code", how="left")
m["is_go8"] = (m["Cohort"] == "Go8").astype(int)
m["log_hdr"] = np.log(m["hdr_completions"].clip(lower=1))
m["log_rbg_total"] = np.log(m["rbg_total"].clip(lower=1))
m["log_rbg_rtp"] = np.log(m["rbg_rtp"].clip(lower=1))
m["log_rbg_rsp"] = np.log(m["rbg_rsp_like"].clip(lower=1))
m["Year_c"] = m["Year"].astype(str)

print("=== Does Go8 get a funding premium beyond what completions volume predicts? ===")
print("Model: log(RBG $) ~ log(HDR completions) + is_Go8 + year FE, clustered SE by provider")
print()

for dep, label in [("log_rbg_total", "Total RBG"), ("log_rbg_rtp", "RTP"), ("log_rbg_rsp", "RSP-like")]:
    model = smf.ols(f"{dep} ~ log_hdr + is_go8 + C(Year_c)", data=m).fit(
        cov_type="cluster", cov_kwds={"groups": m["HEP_Code"]}
    )
    b_hdr = model.params["log_hdr"]
    b_go8 = model.params["is_go8"]
    se_go8 = model.bse["is_go8"]
    p_go8 = model.pvalues["is_go8"]
    pct_premium = (np.exp(b_go8) - 1) * 100
    print(f"{label:10s}: log_hdr coef={b_hdr:.3f}  |  is_go8 coef={b_go8:.3f} (se={se_go8:.3f}, p={p_go8:.4f})  ->  Go8 premium ~ {pct_premium:.1f}% at same completions volume, R2={model.rsquared:.3f}")

print()
print("=== Robustness: same regression dropping 2021 (COVID) ===")
m2 = m[m["Year"] != 2021]
for dep, label in [("log_rbg_total", "Total RBG"), ("log_rbg_rtp", "RTP"), ("log_rbg_rsp", "RSP-like")]:
    model = smf.ols(f"{dep} ~ log_hdr + is_go8 + C(Year_c)", data=m2).fit(
        cov_type="cluster", cov_kwds={"groups": m2["HEP_Code"]}
    )
    b_go8 = model.params["is_go8"]
    p_go8 = model.pvalues["is_go8"]
    pct_premium = (np.exp(b_go8) - 1) * 100
    print(f"{label:10s}: is_go8 premium ~ {pct_premium:.1f}%  (p={p_go8:.4f})")

print()
print("=== Robustness: adding log(total_completions) as a scale control, to isolate HDR-specific effect ===")
m["log_total_comp"] = np.log(m["total_completions"].clip(lower=1))
model = smf.ols("log_rbg_total ~ log_hdr + log_total_comp + is_go8 + C(Year_c)", data=m).fit(
    cov_type="cluster", cov_kwds={"groups": m["HEP_Code"]}
)
print(model.params[["log_hdr", "log_total_comp", "is_go8"]])
print("p-values:", model.pvalues[["log_hdr", "log_total_comp", "is_go8"]].values)

print()
print("=== Growth-rate regression: does g_rbg_total predict g_hdr_completions(t+1) controlling for provider & year FE? ===")
m = m.sort_values(["HEP_Code", "Year"])
m["g_rbg_total"] = m.groupby("HEP_Code")["log_rbg_total"].diff()
m["g_hdr"] = m.groupby("HEP_Code")["log_hdr"].diff()
m["g_hdr_lead1"] = m.groupby("HEP_Code")["g_hdr"].shift(-1)
gm = m[m["Year"] != 2021].dropna(subset=["g_rbg_total", "g_hdr_lead1"])
model = smf.ols("g_hdr_lead1 ~ g_rbg_total + C(HEP_Code) + C(Year_c)", data=gm).fit(
    cov_type="cluster", cov_kwds={"groups": gm["HEP_Code"]}
)
print(f"n={len(gm)}  coef on g_rbg_total (funding growth -> next-yr completions growth) = {model.params['g_rbg_total']:.3f}  p={model.pvalues['g_rbg_total']:.4f}  R2={model.rsquared:.3f}")
