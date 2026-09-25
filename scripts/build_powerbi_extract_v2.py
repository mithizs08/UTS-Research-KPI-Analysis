"""
Power BI extract update (post-challenge-round). Adds two tables the dashboard
needs to reflect the confirmed, strengthened findings - the base panel/growth/
leadlag tables from build_powerbi_extract.py are unchanged (the underlying
2015-2024 data didn't change, only the interpretation and evidence around it):

  powerbi_go8_mechanism_validation.csv - Go8's predicted vs actual RSP share,
    reconstructed from HERDC income shares + the legislated 47%/53% formula
    weights (see data/methodology/rsp_calculation.pdf), for Finding 2's
    updated Panel B.

  powerbi_robustness_checks.csv - the Finding 1 specification results (n,
    coefficient, p-value) across the primary spec, the extended 2001-2024
    window, and the individual 2021/2024 exclusions, run in Python since
    Power BI can't reproduce clustered-SE panel regressions natively.

Also refreshes powerbi_go8_premium_results.csv with a Formula_Basis column
naming what each program's legislated formula actually weights, so a table
visual next to the premium bar chart can carry that context without prose.
"""
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT = DATA_DIR / "powerbi"
OUT.mkdir(exist_ok=True)


def build_mechanism_validation():
    src = DATA_DIR / "clean" / "go8_mechanism_validation.csv"
    df = pd.read_csv(src)
    df = df.rename(columns={
        "comp_income_go8_share": "Go8_Competitive_Income_Share_Pct",
        "eng_income_go8_share": "Go8_Engagement_Income_Share_Pct",
        "predicted_rsp_go8_share": "Go8_RSP_Share_Predicted_Pct",
        "actual_rsp_go8_share": "Go8_RSP_Share_Actual_Pct",
        "hdr_completions_go8_share": "Go8_HDR_Completions_Share_Pct",
    })
    df["Prediction_Error_Pct_Points"] = (
        df["Go8_RSP_Share_Predicted_Pct"] - df["Go8_RSP_Share_Actual_Pct"]
    ).round(2)
    out_path = OUT / "powerbi_go8_mechanism_validation.csv"
    df.to_csv(out_path, index=False)
    print("wrote", out_path, df.shape)
    print("mean abs prediction error (pp):", df["Prediction_Error_Pct_Points"].abs().mean().round(2))


def build_robustness_checks():
    m = pd.read_csv(DATA_DIR / "clean" / "master_panel_v2.csv")
    m = m[(m["Year"] >= 2015) & (m["Year"] <= 2024)].copy().sort_values(["HEP_Code", "Year"])
    m["log_hdr"] = np.log(m["hdr_completions"].clip(lower=1))
    m["log_rbg"] = np.log(m["rbg_total"].clip(lower=1))
    m["g_hdr"] = m.groupby("HEP_Code")["log_hdr"].diff()
    m["g_rbg"] = m.groupby("HEP_Code")["log_rbg"].diff()
    m["Year_c"] = m["Year"].astype(str)

    def lead_test(df):
        d = df.copy()
        d["g_hdr_lead1"] = d.groupby("HEP_Code")["g_hdr"].shift(-1)
        dd = d.dropna(subset=["g_rbg", "g_hdr_lead1"])
        mod = smf.ols("g_hdr_lead1 ~ g_rbg + C(HEP_Code) + C(Year_c)", data=dd).fit(
            cov_type="cluster", cov_kwds={"groups": dd["HEP_Code"]}
        )
        return len(dd), mod.params["g_rbg"], mod.pvalues["g_rbg"]

    def contemporaneous_test(df):
        dd = df.dropna(subset=["g_rbg", "g_hdr"])
        mod = smf.ols("g_hdr ~ g_rbg + C(HEP_Code) + C(Year_c)", data=dd).fit(
            cov_type="cluster", cov_kwds={"groups": dd["HEP_Code"]}
        )
        return len(dd), mod.params["g_rbg"], mod.pvalues["g_rbg"]

    # official HDR file extended back to 2001 (first RBG year)
    hdr_off = pd.read_csv(DATA_DIR / "hdr_official" / "hdr_official_table1.csv")
    hdr_off["doc"] = pd.to_numeric(hdr_off["Doctorate by Research"].astype(str).str.strip(), errors="coerce").fillna(2)
    hdr_off["mas"] = pd.to_numeric(hdr_off["Masters by Research"].astype(str).str.strip(), errors="coerce").fillna(2)
    hdr_off["hdr_completions"] = hdr_off["doc"] + hdr_off["mas"]
    hdr_off = hdr_off.rename(columns={"HEP Code": "HEP_Code"})
    rbg = pd.read_csv(DATA_DIR / "rbg" / "rbg_table2_long.csv")
    rbg_tot = rbg.groupby(["HEP Code", "Year"], as_index=False)["Amount"].sum().rename(
        columns={"HEP Code": "HEP_Code", "Amount": "rbg_total"}
    )
    ext = hdr_off[["HEP_Code", "Year", "hdr_completions"]].merge(rbg_tot, on=["HEP_Code", "Year"], how="inner")
    ext = ext[(ext["Year"] >= 2001) & (ext["Year"] <= 2024)].sort_values(["HEP_Code", "Year"])
    ext["log_hdr"] = np.log(ext["hdr_completions"].clip(lower=1))
    ext["log_rbg"] = np.log(ext["rbg_total"].clip(lower=1))
    ext["g_hdr"] = ext.groupby("HEP_Code")["log_hdr"].diff()
    ext["g_rbg"] = ext.groupby("HEP_Code")["log_rbg"].diff()
    ext["Year_c"] = ext["Year"].astype(str)

    rows = []
    lead_specs = [
        ("Primary: 2015-2024, excl. 2021", m[m["Year"] != 2021]),
        ("2015-2024, incl. 2021", m),
        ("Excl. 2024 (Adelaide merger year)", m[m["Year"] != 2024]),
        ("Excl. both 2021 and 2024", m[(m["Year"] != 2021) & (m["Year"] != 2024)]),
        ("Extended window 2001-2024, excl. 2021", ext[ext["Year"] != 2021]),
        ("Extended window 2001-2024, incl. 2021", ext),
    ]
    for i, (label, df) in enumerate(lead_specs, start=1):
        n, coef, p = lead_test(df)
        rows.append({
            "Sort_Order": i,
            "Test_Type": "Lead: funding growth(t) -> completions growth(t+1)",
            "Specification": label,
            "N": n,
            "Coefficient": round(coef, 3),
            "P_Value": round(p, 4),
            "Significant_at_5pct": p < 0.05,
        })

    # contemporaneous (same-year) specification - this is where the one fragile
    # exception noted in the report and challenge-round verdict actually comes from
    # (excl. 2024: p=0.03), not the lead specification above.
    contemp_specs = [
        ("2015-2024, incl. 2021", m),
        ("Excl. 2021 (COVID)", m[m["Year"] != 2021]),
        ("Excl. 2024 (Adelaide merger year)", m[m["Year"] != 2024]),
    ]
    for i, (label, df) in enumerate(contemp_specs, start=len(lead_specs) + 1):
        n, coef, p = contemporaneous_test(df)
        rows.append({
            "Sort_Order": i,
            "Test_Type": "Contemporaneous: funding growth(t) vs completions growth(t)",
            "Specification": label,
            "N": n,
            "Coefficient": round(coef, 3),
            "P_Value": round(p, 4),
            "Significant_at_5pct": p < 0.05,
        })

    out = pd.DataFrame(rows)
    out_path = OUT / "powerbi_robustness_checks.csv"
    out.to_csv(out_path, index=False)
    print("wrote", out_path)
    print(out)


def refresh_premium_results():
    path = OUT / "powerbi_go8_premium_results.csv"
    df = pd.read_csv(path)
    formula_basis = {
        "Total RBG": "Blend of RTP + RSP",
        "RTP": "50% HDR completions + 50% R&D income",
        "RSP": "100% R&D income, 0% completions",
    }
    df["Formula_Basis"] = df["Program"].map(formula_basis)
    df.to_csv(path, index=False)
    print("updated", path)
    print(df)


if __name__ == "__main__":
    build_mechanism_validation()
    print()
    build_robustness_checks()
    print()
    refresh_premium_results()
