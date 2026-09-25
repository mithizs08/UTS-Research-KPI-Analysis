"""
v2: completions side of the panel now sourced from the Department's official
'Higher degree by research (HDR) student completions time series (1989-2024)'
file (Table 1, matrix format), instead of our own legacy-xls + pivot-cache
reconstruction.

Why the switch: cross-checking our reconstructed HDR numbers against this
official file (same HEP Code scheme as the RBG file) showed the levels
correlation is very high (r=0.993) and most institution-years match closely,
but there are material mismatches concentrated in 2021 and a handful of other
institution-years (e.g. Sydney -300, Melbourne -334, UTS -188 in 2021 alone).
Diagnosis: our own reconstructed *total* (all-level) completions for those
same institution-years matches the independently published Table 14.4 series
almost exactly (Sydney 2021: 22,376 vs 22,332 official) - so the crosswalk
and overall completions counts are correct. The gap is specific to the
"Detailed Course Level: Postgraduate research" bucket inside the 2020-2024
*pivot* file, which appears to under-classify HDR completions in COVID
backlog-clearing years. The official HDR-specific file is purpose-built and
cross-referenced against HERDC for RTP allocation purposes, so it is treated
as ground truth here; our RBG-side cleaning, crosswalk, and panel structure
are unchanged and reused as-is.
"""
import re
import pandas as pd
import numpy as np
import openpyxl
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_crosswalk import build_hep_lookup
from build_master_panel import build_rbg_panel

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR = DATA_DIR / "clean"
OUT_DIR.mkdir(exist_ok=True)


def load_official_hdr():
    wb = openpyxl.load_workbook(
        DATA_DIR / "hdr_official" / "hdr_completions_official_1989_2024.xlsx", data_only=True
    )
    ws = wb["Table 1"]
    rows = list(ws.iter_rows(min_row=3, values_only=True))
    header = [str(h).strip() for h in rows[0]][:7]
    data = [r[:7] for r in rows[1:] if r[0] is not None]
    df = pd.DataFrame(data, columns=header)
    df = df.rename(columns={"HEP Code": "HEP_Code", "Higher Education Provider": "Institution_raw"})

    def to_num(s):
        s = s.astype(str).str.strip()
        is_lt5 = s == "< 5"
        is_lt5 = is_lt5 | (s == "<5")
        num = pd.to_numeric(s, errors="coerce")
        num = num.where(~is_lt5, 2.0)  # documented midpoint imputation, consistent with v1 methodology
        return num, is_lt5

    df["doctorate_by_research"], doc_supp = to_num(df["Doctorate by Research"])
    df["masters_by_research"], mas_supp = to_num(df["Masters by Research"])
    df["hdr_completions"] = df["doctorate_by_research"].fillna(0) + df["masters_by_research"].fillna(0)
    df["hdr_has_suppressed_lt5"] = doc_supp | mas_supp
    df["Year"] = df["Year"].astype(int)
    df["HEP_Code"] = df["HEP_Code"].astype(int)
    return df[["HEP_Code", "Institution_raw", "Year", "Cohort", "doctorate_by_research",
               "masters_by_research", "hdr_completions", "hdr_has_suppressed_lt5"]]


def load_total_completions_from_pivot_and_legacy():
    """Keep our own reconstructed *total* (all-level) completions as a scale
    control - already cross-validated against Table 14.4 above."""
    legacy = pd.read_csv(DATA_DIR / "student" / "completions_by_institution_2015_2019_raw.csv")
    tot_l = pd.to_numeric(legacy["TOTAL"].astype(str).str.strip().replace({"< 5": "2", "np": np.nan}), errors="coerce")
    legacy_out = pd.DataFrame({
        "Institution_raw": legacy["Institution_raw"], "Year": legacy["Year"], "total_completions": tot_l
    })

    pivot = pd.read_csv(DATA_DIR / "student" / "completions_pivot_raw.csv")
    pivot_tot = pivot.groupby(["Year", "Institution"], as_index=False)["Completions"].sum().rename(
        columns={"Institution": "Institution_raw", "Completions": "total_completions"}
    )
    return pd.concat([legacy_out, pivot_tot], ignore_index=True)


if __name__ == "__main__":
    norm_to_code, code_to_name = build_hep_lookup()

    hdr = load_official_hdr()
    hdr["Institution_canonical"] = hdr["HEP_Code"].map(code_to_name)

    from build_crosswalk import match_institution
    total_comp = load_total_completions_from_pivot_and_legacy()
    total_comp["HEP_Code"] = total_comp["Institution_raw"].apply(lambda n: match_institution(n, norm_to_code))
    total_comp = total_comp.dropna(subset=["HEP_Code"])
    total_comp["HEP_Code"] = total_comp["HEP_Code"].astype(int)
    total_comp_g = total_comp.groupby(["HEP_Code", "Year"], as_index=False)["total_completions"].sum()

    completions = hdr.merge(total_comp_g, on=["HEP_Code", "Year"], how="left")

    rbg_panel = build_rbg_panel()
    master = completions.merge(rbg_panel, on=["HEP_Code", "Year"], how="inner")

    print("Official-HDR-based completions panel:", completions.shape,
          "years:", sorted(completions["Year"].unique()))
    print("Master merged panel (v2):", master.shape,
          "HEP codes:", master["HEP_Code"].nunique())

    completions.to_csv(OUT_DIR / "completions_panel_v2.csv", index=False)
    master.to_csv(OUT_DIR / "master_panel_v2.csv", index=False)
    print("wrote data/clean/completions_panel_v2.csv, master_panel_v2.csv")
