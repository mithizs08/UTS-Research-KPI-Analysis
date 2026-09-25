"""
Finding 2, challenge round: does the legislated RSP formula (47% competitive
R&D income share + 53% engagement income share, per the Other Grants
Guidelines (Research) 2017 - see data/methodology/rsp_calculation.pdf)
mechanically explain Go8's RSP funding share, independent of HDR completions?

Reconstructs Go8's *predicted* RSP share from nothing but the Department's
own HERDC R&D income time series (data/herdc_income/) and the legislated
formula weights, then compares it against Go8's *actual* observed RSP share
from the RBG panel. Also carries Go8's HDR completions share for contrast.
"""
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main():
    income = pd.read_csv(DATA_DIR / "herdc_income" / "herdc_income_long.csv")
    income = income[(income["Year"] >= 2015) & (income["Year"] <= 2024)].copy()

    rbg = pd.read_csv(DATA_DIR / "rbg" / "rbg_table2_long.csv")
    cohort_map = rbg[["HEP Code", "Cohort"]].drop_duplicates().groupby("HEP Code")["Cohort"].agg(
        lambda s: s.mode().iat[0]
    )
    income["Cohort"] = income["HEP Code"].map(cohort_map)
    income["is_go8"] = income["Cohort"] == "Go8"
    income["is_competitive"] = income["Category"] == 1  # HERDC Category 1 = competitive; 2-4 = engagement

    comp = income[income["is_competitive"]].groupby(["Year", "is_go8"])["Amount"].sum().unstack()
    comp_share_go8 = comp[True] / (comp[True] + comp[False]) * 100
    eng = income[~income["is_competitive"]].groupby(["Year", "is_go8"])["Amount"].sum().unstack()
    eng_share_go8 = eng[True] / (eng[True] + eng[False]) * 100

    # legislated RSP weights: 47% competitive + 53% engagement (rsp_calculation.pdf, p.5)
    predicted_rsp = 0.47 * comp_share_go8 + 0.53 * eng_share_go8

    m = pd.read_csv(DATA_DIR / "clean" / "master_panel_v2.csv")
    m = m[(m["Year"] >= 2015) & (m["Year"] <= 2024)].copy()
    rspg = m.groupby(["Year", "Cohort"])["rbg_rsp_like"].sum().unstack()
    actual_rsp_go8_share = rspg["Go8"] / rspg.sum(axis=1) * 100
    hdrg = m.groupby(["Year", "Cohort"])["hdr_completions"].sum().unstack()
    hdr_go8_share = hdrg["Go8"] / hdrg.sum(axis=1) * 100

    out = pd.DataFrame({
        "comp_income_go8_share": comp_share_go8,
        "eng_income_go8_share": eng_share_go8,
        "predicted_rsp_go8_share": predicted_rsp,
        "actual_rsp_go8_share": actual_rsp_go8_share,
        "hdr_completions_go8_share": hdr_go8_share,
    })
    out_path = DATA_DIR / "clean" / "go8_mechanism_validation.csv"
    out.to_csv(out_path)
    print("wrote", out_path)
    print(out.round(1))
    print()
    print("mean abs error, predicted vs actual RSP share (pp):",
          round((predicted_rsp - actual_rsp_go8_share).abs().mean(), 2))


if __name__ == "__main__":
    main()
