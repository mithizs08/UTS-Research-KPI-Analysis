"""
Canonical institution crosswalk.

Anchor: the 44 HEP Code / HEP Name pairs in the RBG allocations time series
(the source notes state RBG names are backfilled to *current* names for all
years, so this is the most stable name list available).

Every institution name seen in the Student Data completions extracts
(2015-2024, both the legacy .xls Table 8/14.8 parses and the 2020-2024 pivot
cache) is mapped onto a HEP Code via: (1) exact match after whitespace/"The "
normalisation, then (2) an explicit alias table for real rebrands/name
changes documented from inspecting the raw files, e.g.:
  - CQUniversity <-> Central Queensland University (brand name adopted 2016-ish)
  - RMIT University <-> Royal Melbourne Institute of Technology (RBG legal name)
  - Curtin University of Technology -> Curtin University (2010 rebrand)
  - Torrens University Australia Limited -> Torrens University Australia
Rows that never match (aggregate buckets like "Non-University Higher
Education Institutions", "Private Universities (Table C) and ...", or
entities with no RBG-eligible status such as Avondale pre-2021) are kept but
flagged unmatched=True rather than silently dropped.
"""
import re
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

ALIASES = {
    "cquniversity": "central queensland university",
    "rmit university": "royal melbourne institute of technology",
    "curtin university of technology": "curtin university",
    "torrens university australia limited": "torrens university australia",
    "the university of newcastle": "university of newcastle",
    "the university of new south wales": "university of new south wales",
    "the university of wollongong": "university of wollongong",
    "university of sydney": "the university of sydney",
}

NON_PROVIDER_PATTERNS = [
    "non-university higher education institutions",
    "non-university higher education providers",
    "private universities (table c)",
    "private universities and non-university higher education providers",
    "carnegie mellon university australia",  # US branch campus, not an RBG-eligible Table A/B provider
]


def normalize(name: str) -> str:
    if name is None:
        return ""
    s = str(name).strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*\([a-z]\)\s*$", "", s)  # trailing footnote marker e.g. "(a)"
    s = s.strip()
    s = ALIASES.get(s, s)
    return s


def build_hep_lookup():
    rbg = pd.read_csv(DATA_DIR / "rbg" / "rbg_table2_long.csv")
    hep = rbg[["HEP Code", "HEP Name"]].drop_duplicates()
    hep["norm"] = hep["HEP Name"].apply(normalize)
    dupe = hep[hep.duplicated("norm", keep=False)]
    assert dupe.empty, f"normalized name collisions in HEP list: {dupe}"
    return dict(zip(hep["norm"], hep["HEP Code"])), dict(zip(hep["HEP Code"], hep["HEP Name"]))


def match_institution(name, norm_to_code):
    norm = normalize(name)
    if norm in norm_to_code:
        return norm_to_code[norm]
    # try toggling a leading "the " - RBG and completions publications are
    # inconsistent about which entities get the definite article
    if norm.startswith("the "):
        alt = norm[4:]
    else:
        alt = "the " + norm
    if alt in norm_to_code:
        return norm_to_code[alt]
    return None


if __name__ == "__main__":
    norm_to_code, code_to_name = build_hep_lookup()

    legacy = pd.read_csv(DATA_DIR / "student" / "completions_by_institution_2015_2019_raw.csv")
    pivot = pd.read_csv(DATA_DIR / "student" / "completions_pivot_raw.csv")

    legacy_names = set(legacy["Institution"].unique())
    pivot_names = set(pivot["Institution"].unique())
    all_names = sorted(legacy_names | pivot_names)

    unmatched = []
    for n in all_names:
        code = match_institution(n, norm_to_code)
        flag = "OK" if code else ("EXCLUDED (non-provider aggregate)" if any(p in normalize(n) for p in NON_PROVIDER_PATTERNS) else "**UNMATCHED**")
        print(f"{n!r:65s} -> {code}  {flag}")
        if flag == "**UNMATCHED**":
            unmatched.append(n)

    print()
    print("Unmatched (needs review):", unmatched)
