#!/usr/bin/env python3
"""What young halter horses and halter mares actually sold for at public online auctions.

    python qa/sales.py

Reads qa/young_horse_sales.csv and qa/mare_sales.csv (collected 2026-11-15 from
the listing pages of internethorseauctions.com, sales from 2017 to 2025).
"""
import csv
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))


def rows(name):
    with open(os.path.join(HERE, name), newline="") as fh:
        return list(csv.DictReader(fh))


def spread(values):
    v = sorted(values)
    return "median $%s, middle half $%s to $%s, top $%s" % (
        format(int(st.median(v)), ","), format(int(v[len(v) // 4]), ","), format(int(v[3 * len(v) // 4]), ","), format(int(v[-1]), ","))


def main():
    young = rows("young_horse_sales.csv")
    price = [float(r["price"]) for r in young]
    mult = [float(r["price_over_fee"]) for r in young if r["price_over_fee"]]
    print("Young horses (weanling to two-year-old) by stallions in the workbook: %d sales" % len(young))
    print("  price: %s" % spread(price))
    print("  sold for $10,000 or more: %d | $20,000 or more: %d" % (sum(p >= 10000 for p in price), sum(p >= 20000 for p in price)))
    print("  against the stud fee paid (n=%d): median %.1fx | 3x or more: %d (%.0f%%) | 10x or more: %d | best %.1fx" % (
        len(mult), st.median(mult), sum(m >= 3 for m in mult), 100.0 * sum(m >= 3 for m in mult) / len(mult),
        sum(m >= 10 for m in mult), max(mult)))
    for age, label in (("0", "weanlings"), ("1", "yearlings"), ("2", "two-year-olds")):
        g = [r for r in young if r["age_at_sale"] == age]
        m = [float(r["price_over_fee"]) for r in g if r["price_over_fee"]]
        print("  %-14s n=%2d  median $%s%s" % (label, len(g), format(int(st.median(float(r["price"]) for r in g)), ","),
                                             "  median %.1fx the fee" % st.median(m) if m else ""))
    mares = rows("mare_sales.csv")
    print("Mares aged three and up by halter sires: %d sales" % len(mares))
    print("  price: %s" % spread([float(r["price"]) for r in mares]))


if __name__ == "__main__":
    main()
