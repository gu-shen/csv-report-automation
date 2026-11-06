#!/usr/bin/env python3
"""Generate messy sample sales data for the report tool demo.

Creates 3 CSV files in ./sample_input with common real-world problems:
- inconsistent column names and order
- duplicate rows
- dirty values (extra spaces, mixed date formats, currency symbols)
"""
import csv
import os
import random

random.seed(42)

OUT_DIR = "sample_input"
os.makedirs(OUT_DIR, exist_ok=True)

PRODUCTS = ["Widget A", "Widget B", "Gadget C", "Gadget D"]
REGIONS = ["North", "South", "East", "West"]


def dirty_money(v):
    """Return a messy currency string, e.g. ' $1,250 ' or '$980'."""
    return f"  ${v:,} " if random.random() < 0.6 else f"${v:,}"


# --- File 1: April, "Sales" style headers, some duplicates ---
with open(f"{OUT_DIR}/april_sales.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Order ID", "Product", "Region", "Date", "Amount"])
    for i in range(1, 13):
        w.writerow([f"A-{1000+i}", random.choice(PRODUCTS), random.choice(REGIONS),
                    f"2026-04-{random.randint(1, 28):02d}", dirty_money(random.randint(200, 2000))])
    # duplicate rows + one blank row on purpose
    w.writerow(["A-1003", "Widget A", "North", "2026-04-05", " $1,050 "])
    w.writerow([])

# --- File 2: May, lowercase reversed columns, different date format ---
with open(f"{OUT_DIR}/may_report.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["amount", "date", "region", "product", "order_id"])
    for i in range(1, 11):
        d = f"05/{random.randint(1, 28):02d}/2026"  # MM/DD/YYYY
        w.writerow([dirty_money(random.randint(150, 1800)), d, random.choice(REGIONS),
                    random.choice(PRODUCTS), f"M-{2000+i}"])

# --- File 3: June, headers with units, one row with missing amount ---
with open(f"{OUT_DIR}/june_data.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Order #", "Item Name", "Region Name", "Order Date", "Total (USD)"])
    for i in range(1, 10):
        w.writerow([f"J-{3000+i}", random.choice(PRODUCTS), random.choice(REGIONS),
                    f"2026-06-{random.randint(1, 28):02d}", dirty_money(random.randint(300, 2500))])
    w.writerow(["J-3007", "Gadget C", "East", "2026-06-15", ""])  # missing amount

print(f"Sample files written to ./{OUT_DIR}/")
