"""
Build the master analysis panel: HEP Code x Year (2015-2024) with
- HDR completions (Doctorate by Research + Master's by Research)
- Doctorate-by-Research-only completions (a robustness-check alternative,
  since it is far less affected by cell suppression - see profiling notes)
- Total award course completions (all levels), as a scale control
- RBG allocations: Total RBG, RTP-only, RSP-only, RSP with the 2021 COVID
  one-off addition removed (using Table 3's Base RSP figure for 2021 only)

Suppression handling for the 2015-2019 legacy tables (documented, not
silently guessed):
  '< 5'  -> imputed at the interval midpoint, 2.0 (bounded max error of 2-3)
  'np'   -> left as NaN; flagged in `hdr_has_suppressed_np` so downstream
            analysis can exclude or caveat affected institution-years
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_crosswalk import build_hep_lookup, match_institution, normalize

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "clean"
OUT_DIR.mkdir(exist_ok=True)


def to_numeric_suppressed(series):
    """Returns (numeric_value_with_<5_imputed_as_2, is_np_flag)."""
    s = series.astype(str).str.strip()
    is_np = (s == "np")
    is_lt5 = (s == "< 5")
    numeric = pd.to_numeric(s, errors="coerce")
    numeric = numeric.where(~is_lt5, 2.0)
    return numeric, is_np


def build_legacy_hdr():
    df = pd.read_csv(DATA_DIR / "student" / "completions_by_institution_2015_2019_raw.csv")
    doc, doc_np = to_numeric_suppressed(df["Doctorate by Research"])
    mas, mas_np = to_numeric_suppressed(df["Master's by Research"])
    tot, _ = to_numeric_suppressed(df["TOTAL"])

    out = pd.DataFrame({
        "Year": df["Year"],
        "Institution_raw": df["Institution_raw"],
        "doctorate_by_research": doc,
        "masters_by_research": mas,
        "hdr_completions": doc.fillna(0) + mas.fillna(0),
        "hdr_has_suppressed_np": doc_np | mas_np,
        "total_completions": tot,
        "source": "legacy_xls_table8",
    })
    return out


def build_pivot_hdr():
    df = pd.read_csv(DATA_DIR / "student" / "completions_pivot_raw.csv")
    hdr = df[df["Detailed Course Level"] == "Postgraduate research"].groupby(
        ["Year", "Institution"], as_index=False
    )["Completions"].sum().rename(columns={"Completions": "hdr_completions", "Institution": "Institution_raw"})

    tot = df.groupby(["Year", "Institution"], as_index=False)["Completions"].sum().rename(
        columns={"Completions": "total_completions", "Institution": "Institution_raw"}
    )
    out = hdr.merge(tot, on=["Year", "Institution_raw"], how="outer")
    out["doctorate_by_research"] = np.nan  # not separable at this granularity in the pivot cache
    out["masters_by_research"] = np.nan
    out["hdr_has_suppressed_np"] = False  # pivot is perturbed, not suppressed
    out["source"] = "perturbed_pivot_2024"
    return out


def build_completions_panel():
    norm_to_code, code_to_name = build_hep_lookup()
    legacy = build_legacy_hdr()
    pivot = build_pivot_hdr()
    panel = pd.concat([legacy, pivot], ignore_index=True)

    panel["HEP_Code"] = panel["Institution_raw"].apply(lambda n: match_institution(n, norm_to_code))
    matched = panel[panel["HEP_Code"].notna()].copy()
    unmatched = panel[panel["HEP_Code"].isna()].copy()

    matched["HEP_Code"] = matched["HEP_Code"].astype(int)
    matched["Institution_canonical"] = matched["HEP_Code"].map(code_to_name)

    dupes = matched[matched.duplicated(["Year", "HEP_Code"], keep=False)]
    if not dupes.empty:
        print("WARNING duplicate Year/HEP_Code rows after crosswalk:")
        print(dupes[["Year", "Institution_raw", "HEP_Code", "source"]])

    return matched, unmatched


def build_rbg_panel():
    rbg = pd.read_csv(DATA_DIR / "rbg" / "rbg_table2_long.csv")
    total = rbg.groupby(["HEP Code", "Year"], as_index=False)["Amount"].sum().rename(
        columns={"HEP Code": "HEP_Code", "Amount": "rbg_total"}
    )
    rtp = rbg[rbg["Program"] == "RTP"].groupby(["HEP Code", "Year"], as_index=False)["Amount"].sum().rename(
        columns={"HEP Code": "HEP_Code", "Amount": "rbg_rtp"}
    )
    rsp_programs = {"RSP", "SRE", "RIBG", "JRE"}  # pre-2017 programs folded into RSP from 2017
    rsp = rbg[rbg["Program"].isin(rsp_programs)].groupby(["HEP Code", "Year"], as_index=False)["Amount"].sum().rename(
        columns={"HEP Code": "HEP_Code", "Amount": "rbg_rsp_like"}
    )

    out = total.merge(rtp, on=["HEP_Code", "Year"], how="left").merge(rsp, on=["HEP_Code", "Year"], how="left")
    out[["rbg_rtp", "rbg_rsp_like"]] = out[["rbg_rtp", "rbg_rsp_like"]].fillna(0.0)

    # COVID-adjusted 2021 RSP: swap in Table 3's "Base RSP" for 2021 only
    import openpyxl
    wb = openpyxl.load_workbook(DATA_DIR / "rbg" / "rbg_allocations_time_series.xlsx", data_only=True)
    ws = wb["Table 3"]
    base_rsp_2021 = {}
    for row in ws.iter_rows(min_row=4, values_only=True):
        if row[0] is None or not isinstance(row[0], (int, float)) or row[2] is None:
            continue
        base_rsp_2021[int(row[0])] = float(row[2])  # HEP Code -> Base RSP

    out["rbg_total_covid_adj"] = out["rbg_total"].astype(float)
    mask_2021 = out["Year"] == 2021
    for idx in out[mask_2021].index:
        code = out.loc[idx, "HEP_Code"]
        if code in base_rsp_2021:
            actual_total_rsp = out.loc[idx, "rbg_rsp_like"]
            base = base_rsp_2021[code]
            covid_addition = actual_total_rsp - base
            out.loc[idx, "rbg_total_covid_adj"] = out.loc[idx, "rbg_total"] - covid_addition

    return out


if __name__ == "__main__":
    completions, unmatched = build_completions_panel()
    rbg_panel = build_rbg_panel()

    print("Completions panel:", completions.shape, "years:", sorted(completions["Year"].unique()))
    print("Unmatched (excluded) rows:", unmatched.shape[0], "-", sorted(unmatched["Institution_raw"].unique()))
    print()
    print("RBG panel:", rbg_panel.shape, "years:", sorted(rbg_panel["Year"].unique()))

    master = completions.merge(rbg_panel, on=["HEP_Code", "Year"], how="inner")
    print()
    print("Master merged panel (completions x RBG, inner join):", master.shape)
    print("HEP codes present:", master["HEP_Code"].nunique(), "/ years:", sorted(master["Year"].unique()))

    missing_rbg = completions.merge(rbg_panel, on=["HEP_Code", "Year"], how="left", indicator=True)
    missing_rbg = missing_rbg[missing_rbg["_merge"] == "left_only"]
    if not missing_rbg.empty:
        print()
        print("Completions rows with NO matching RBG allocation for that year (check):")
        print(missing_rbg[["Year", "Institution_canonical", "HEP_Code"]].drop_duplicates())

    completions.to_csv(OUT_DIR / "completions_panel.csv", index=False)
    rbg_panel.to_csv(OUT_DIR / "rbg_panel.csv", index=False)
    master.to_csv(OUT_DIR / "master_panel.csv", index=False)
    print()
    print("wrote data/clean/completions_panel.csv, rbg_panel.csv, master_panel.csv")
