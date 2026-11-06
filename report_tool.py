#!/usr/bin/env python3
"""CSV/Excel Sales Report Tool

Merges multiple messy CSV/Excel files into one clean, deduplicated dataset
and produces a summary report (per-region and per-product totals).

Usage:
    python report_tool.py <input_folder> <output_folder>

Input:  a folder of .csv or .xlsx files (see make_sample_data.py for examples)
Output: clean_merged.csv, report.xlsx, summary_chart.png, log of all fixes

Author: Zeforge Studio
"""
import os
import re
import sys
from datetime import datetime

import pandas as pd
import matplotlib

matplotlib.use("Agg")  # headless: no window needed
import matplotlib.pyplot as plt

# --- Column mapping: every known alias -> canonical name -------------------
COLUMN_MAP = {
    "order id": "order_id", "order_id": "order_id", "order #": "order_id",
    "order no": "order_id", "id": "order_id",
    "product": "product", "item name": "product", "item": "product",
    "region": "region", "region name": "region",
    "date": "date", "order date": "date",
    "amount": "amount", "total": "amount", "total (usd)": "amount",
    "revenue": "amount", "price": "amount",
}

FIX_LOG = []  # human-readable record of every cleanup action


def log(msg):
    print(f"  [fix] {msg}")
    FIX_LOG.append(msg)


def normalize_columns(df, filename):
    """Rename columns to canonical names using COLUMN_MAP aliases."""
    rename = {}
    for col in df.columns:
        key = str(col).strip().lower()
        if key in COLUMN_MAP:
            rename[col] = COLUMN_MAP[key]
        else:
            raise ValueError(f"{filename}: unknown column '{col}' — add an alias to COLUMN_MAP")
    return df.rename(columns=rename)


def clean_amount(series):
    """' $1,250 ' -> 1250.0 ; empty/invalid -> NaN (row kept, flagged)."""
    cleaned = series.astype(str).str.replace(r"[$,\s]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def clean_date(series):
    """Accept YYYY-MM-DD and MM/DD/YYYY; unparseable -> NaT (row kept, flagged)."""
    return pd.to_datetime(series, format="mixed", errors="coerce")


def load_and_clean(path):
    """Load one CSV or Excel file and return a cleaned DataFrame."""
    filename = os.path.basename(path)
    if path.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    df = normalize_columns(df, filename)
    # drop fully-empty rows
    before = len(df)
    df = df.dropna(how="all")
    if len(df) < before:
        log(f"{filename}: removed {before - len(df)} empty row(s)")

    df["amount"] = clean_amount(df["amount"])
    df["date"] = clean_date(df["date"])
    df["product"] = df["product"].astype(str).str.strip()
    df["region"] = df["region"].astype(str).str.strip().str.title()

    # report rows with missing critical values instead of silently dropping
    bad = df[df["amount"].isna()]
    for oid in bad["order_id"]:
        log(f"{filename}: order '{oid}' has a missing/invalid amount — kept as blank")

    return df


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python report_tool.py <input_folder> <output_folder>")

    in_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    files = [f for f in sorted(os.listdir(in_dir))
             if f.lower().endswith((".csv", ".xlsx", ".xls"))]
    if not files:
        sys.exit(f"No CSV/Excel files found in '{in_dir}'")

    print(f"Processing {len(files)} file(s) from {in_dir}/ ...")
    frames = [load_and_clean(os.path.join(in_dir, f)) for f in files]
    merged = pd.concat(frames, ignore_index=True)

    # deduplicate by order_id
    before = len(merged)
    merged = merged.drop_duplicates(subset="order_id", keep="first")
    if len(merged) < before:
        log(f"removed {before - len(merged)} duplicate order(s) by Order ID")

    # outputs
    merged.to_csv(f"{out_dir}/clean_merged.csv", index=False)
    by_region = merged.groupby("region", dropna=False)["amount"].sum().round(2)
    by_product = merged.groupby("product", dropna=False)["amount"].sum().round(2)

    with pd.ExcelWriter(f"{out_dir}/report.xlsx") as xw:
        merged.to_excel(xw, sheet_name="Clean Data", index=False)
        by_region.to_frame("Total").to_excel(xw, sheet_name="By Region")
        by_product.to_frame("Total").to_excel(xw, sheet_name="By Product")

    ax = by_region.sort_values().plot(kind="barh", figsize=(7, 4),
                                      color="#F59E0B", title="Total Sales by Region")
    ax.set_xlabel("USD")
    plt.tight_layout()
    plt.savefig(f"{out_dir}/summary_chart.png", dpi=150)
    plt.close()

    with open(f"{out_dir}/cleanup_log.txt", "w") as f:
        f.write("Cleanup actions performed:\n" + "\n".join(f"- {m}" for m in FIX_LOG) + "\n")

    print(f"\nDone. {len(merged)} clean rows -> {out_dir}/")
    print(f"  - clean_merged.csv, report.xlsx, summary_chart.png, cleanup_log.txt")
    print("\nBy region:\n", by_region.to_string())


if __name__ == "__main__":
    main()
