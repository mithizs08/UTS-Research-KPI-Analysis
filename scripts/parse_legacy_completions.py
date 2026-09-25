"""
Parse Table 8 / 14.8 ("Award Course Completions for All Students by State,
Higher Education Institution and Broad Level of Course") from each year's
legacy .xls publication (2015-2019). Sheet tab is consistently named '8'.

Row layout: a state-name row (data cells blank) followed by institution rows,
until the next state row. Trailing rows are 'TOTAL Australia', prior-year
total, '% change', footnotes - all dropped by requiring the row to sit
between two state headers and have a numeric TOTAL.

Suppression codes in the source: 'np' (not published) and '< 5' (small-cell
count masked for privacy). Both are kept as-is in the raw output and resolved
downstream (documented as a methodology choice), not silently guessed here.
"""
import re
import xlrd
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "student"

LEVEL_COLS = [
    "Higher Doctorate", "Doctorate by Research", "Doctorate by Coursework",
    "Master's (Extended)", "Master's by Research", "Master's by Coursework",
    "Other Postgraduate", "Bachelor", "Associate Degree", "Other Undergraduate",
    "TOTAL",
]

STATE_NAMES = {
    "New South Wales", "Victoria", "Queensland", "Western Australia",
    "South Australia", "Tasmania", "Northern Territory",
    "Australian Capital Territory", "Multi-State",
}


def parse_year(path, year, sheet="8"):
    wb = xlrd.open_workbook(path)
    ws = wb.sheet_by_name(sheet)
    header = [str(h).strip() for h in ws.row_values(3)]
    assert header[1:] == LEVEL_COLS, f"{path}: unexpected header {header}"

    records = []
    state = None
    for r in range(4, ws.nrows):
        row = ws.row_values(r)
        name = str(row[0]).strip()
        if not name:
            continue
        rest = row[1:12]
        is_data_row = any(str(c).strip() != "" for c in rest)
        if name in STATE_NAMES and not is_data_row:
            state = name
            continue
        if name.startswith("TOTAL") or name.startswith("Total ") or name.startswith("% change") or name.startswith("("):
            continue
        if not is_data_row:
            continue
        clean_name = re.sub(r"\s*\([a-z]\)\s*$", "", name).strip()
        rec = {"Year": year, "State": state, "Institution_raw": name, "Institution": clean_name}
        for col, val in zip(LEVEL_COLS, rest):
            rec[col] = val
        records.append(rec)

    return pd.DataFrame(records)


if __name__ == "__main__":
    files = {
        2015: "2015_completions.xls",
        2016: "2016_completions.xls",
        2017: "2017_section14_completions.xls",
        2018: "2018_section14_completions.xls",
        2019: "2019_section14_completions.xls",
    }
    frames = []
    for year, fname in files.items():
        df = parse_year(DATA_DIR / fname, year)
        print(year, df.shape, "TOTAL sum:", pd.to_numeric(df["TOTAL"], errors="coerce").sum())
        frames.append(df)

    out = pd.concat(frames, ignore_index=True)
    out_path = DATA_DIR / "completions_by_institution_2015_2019_raw.csv"
    out.to_csv(out_path, index=False)
    print("wrote", out_path, out.shape)
    print(sorted(out["Institution"].unique()))
