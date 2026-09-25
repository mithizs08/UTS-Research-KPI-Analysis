"""
Parse the raw pivot-cache records embedded in the Department of Education's
'Perturbed Award Course Completions Pivot Table 2024' workbook.

The published sheet only shows whatever pivot view was last saved in Excel;
the actual record-level (perturbed) microdata lives in
xl/pivotCache/pivotCacheRecords1.xml, indexed against the shared-item lookup
lists in xl/pivotCache/pivotCacheDefinition1.xml. We reconstruct it here so we
can group Completions by Year x Institution x Detailed Course Level ourselves
(specifically isolating 'Postgraduate research' = HDR completions).
"""
import xml.etree.ElementTree as ET
import zipfile
import pandas as pd
from pathlib import Path

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
XLSX_PATH = Path(__file__).resolve().parent.parent / "data" / "student" / "perturbed_completions_pivot_2024.xlsx"


def load_cache(zf, defn_path, rec_path):
    tree = ET.parse(zf.open(defn_path))
    root = tree.getroot()
    cache_fields = root.find("m:cacheFields", NS).findall("m:cacheField", NS)

    field_names = []
    shared_items = []  # list of list-or-None per field
    for f in cache_fields:
        field_names.append(f.get("name"))
        si = f.find("m:sharedItems", NS)
        if si is not None and len(si) > 0:
            vals = [c.get("v") for c in si]
        else:
            vals = None
        shared_items.append(vals)

    records = []
    rec_root = ET.parse(zf.open(rec_path)).getroot()
    for r in rec_root.findall("m:r", NS):
        row = []
        for i, cell in enumerate(r):
            tag = cell.tag.split("}")[-1]
            v = cell.get("v")
            if tag == "x":  # index into shared items
                row.append(shared_items[i][int(v)])
            elif tag == "n":  # numeric literal
                row.append(float(v) if v is not None else None)
            elif tag == "m":  # missing
                row.append(None)
            else:
                row.append(v)
        records.append(row)

    df = pd.DataFrame(records, columns=field_names)
    return df


if __name__ == "__main__":
    with zipfile.ZipFile(XLSX_PATH) as zf:
        df = load_cache(
            zf,
            "xl/pivotCache/pivotCacheDefinition1.xml",
            "xl/pivotCache/pivotCacheRecords1.xml",
        )
    print(df.shape)
    print(df.dtypes)
    print(df.head())

    out = XLSX_PATH.parent / "completions_pivot_raw.csv"
    df.to_csv(out, index=False)
    print("wrote", out)
