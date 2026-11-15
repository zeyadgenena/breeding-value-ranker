#!/usr/bin/env python3
"""What the Arabian data can and cannot support.

    python qa/arabian_model.py            # print the checks
    python qa/arabian_model.py --write    # also save qa/arabian_model.json for the app

Two questions:
  1. Sale price. Can anything public about a horse predict what it sells for at
     online auction? Scored like the Quarter Horse price model: every auction is
     held out in turn.
  2. Results. Where the data has whole classes (every placing, not one barn's
     wins), do the sires that placed foals early keep placing them later?
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics as st

import price_model as pm

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data", "arabian")


def rows_of(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8", errors="replace") as fh:
        return list(csv.DictReader(fh))


def norm(s):
    return " ".join(str(s or "").upper().replace("*", " ").split())


def sales():
    points = {}
    for r in rows_of("results_classes.csv") + rows_of("results.csv"):
        if r["year"].isdigit():
            points.setdefault(norm(r["sire"]), {})
            points[norm(r["sire"])][int(r["year"])] = points[norm(r["sire"])].get(int(r["year"]), 0) + 1
    out = []
    for r in rows_of("sales.csv"):
        if r.get("lot_kind", "horse") not in ("horse", "") or r.get("sold", "Y") == "N" or not r.get("price_usd"):
            continue
        price = float(r["price_usd"])
        if price <= 0:
            continue
        year = int(r["sale_date"][:4]) if r["sale_date"][:4].isdigit() else None
        foaled = int(r["foaled"][:4]) if r.get("foaled", "")[:4].isdigit() else None
        sire = norm(r.get("sire"))
        out.append({"price": price, "auction": r["auction"], "year": year, "age": (year - foaled) if year and foaled else None, "sex": (r.get("sex") or "").upper()[:1],
                    "division": r.get("division", ""), "sire": sire, "fee": None,
                    "sire_points": sum(n for y, n in points.get(sire, {}).items() if year is None or y < year) if sire else 0})
    return out


def f_age(r, ctx):
    a = r["age"]
    return [1.0 if a is not None and a <= 1 else 0.0, 1.0 if a is not None and 2 <= a <= 3 else 0.0, 1.0 if a is None else 0.0]


def f_sex(r, ctx):
    return [1.0 if r["sex"] in ("F", "M") else 0.0, 1.0 if r["sex"] == "G" else 0.0]


def f_division(r, ctx):
    return [1.0 if r["division"] == "half-arabian" else 0.0]


def f_sire(r, ctx):
    return [math.log1p(r["sire_points"]), 0.0 if r["sire"] else 1.0]


def f_year(r, ctx):
    return [((r["year"] or 2021) - 2021) / 3.0]


NAMED = {"age": f_age, "sex": f_sex, "purebred or half-Arabian": f_division, "sire's halter placings before the sale": f_sire, "year of sale": f_year}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    S = sales()
    out = {"sales": len(S)}
    if S:
        prices = sorted(r["price"] for r in S)
        q = lambda p: prices[int(p * (len(prices) - 1))]
        young = [r["price"] for r in S if r["age"] is not None and r["age"] <= 3]
        out.update({"median": st.median(prices), "q1": q(0.25), "q3": q(0.75), "top": prices[-1], "young": len(young), "young_median": st.median(young) if young else None,
                    "with_sire": sum(1 for r in S if r["sire"]), "sires": len({r["sire"] for r in S if r["sire"]}), "auctions": len({r["auction"] for r in S}),
                    "at_opening_bid": sum(1 for r in S if r["price"] <= 1200)})
        print("%d horses sold at %d auctions. Typical price $%s (middle half $%s to $%s, top $%s). %d aged three or under, typical $%s. %d sold at $1,200 or less." % (
            len(S), out["auctions"], format(int(out["median"]), ","), format(int(out["q1"]), ","), format(int(out["q3"]), ","), format(int(out["top"]), ","),
            len(young), format(int(out["young_median"]), ",") if young else "-", out["at_opening_bid"]))
    card = []
    if len(S) >= 60 and len({r["auction"] for r in S}) >= 5:
        def fit(rows_, feats, per_sire):
            ctx = {}
            xs = [[1.0] + [v for f in feats for v in f(r, ctx)] for r in rows_]
            ys = [math.log(r["price"]) for r in rows_]
            w = pm.solve(xs, ys, ridge=1e-2)
            return {"w": w, "ctx": ctx, "sire": {}, "resid": [y - sum(p * q_ for p, q_ in zip(x, w)) for x, y in zip(xs, ys)]}
        orig = pm.fit
        pm.fit = fit
        print("\n%-58s %-13s %s" % ("version", "typical miss", "explained"))
        import itertools
        for k in range(0, len(NAMED) + 1):
            for combo in itertools.combinations(NAMED, k):
                cv = pm.cross_validate(S, [NAMED[c] for c in combo], False)
                card.append({"what": " + ".join(combo) or "one typical price for every horse", "typical_miss": cv["typical_miss"], "explained": cv["explained"],
                             "within_double_or_half": cv["within_double_or_half"]})
        pm.fit = orig
        card.sort(key=lambda c: -c["explained"])
        for c in card[:6] + [c for c in card if c["what"].startswith("one typical")]:
            print("%-58s %3.0f%%          %5.1f%%" % (c["what"][:58], 100 * c["typical_miss"], 100 * c["explained"]))
        out["price_versions"] = len(card)
        out["price_best"] = card[0]
    else:
        print("\nToo few sales for a price model (%d)." % len(S))
    out["price_scorecard"] = card[:8]

    # ---- whole-class results, if any ----
    full = [r for r in rows_of("results_classes.csv") if r.get("source_kind") == "full_class" and r["year"].isdigit() and r["sire"]]
    out["full_class_rows"] = len(full)
    if full:
        years = sorted({int(r["year"]) for r in full})
        print("\n%d placings from whole classes, %d sires, %s to %s." % (len(full), len({norm(r["sire"]) for r in full}), years[0], years[-1]))
        if len(years) >= 3:
            split = years[len(years) // 2 - 1]
            early, late = {}, {}
            for r in full:
                d = early if int(r["year"]) <= split else late
                d[norm(r["sire"])] = d.get(norm(r["sire"]), 0) + 1
            names = [s for s in early]
            order = sorted(names, key=lambda s: -early[s])
            third = max(1, len(order) // 3)
            top, rest = order[:third], order[third:]
            kept = lambda group: sum(1 for s in group if late.get(s, 0) > 0) / len(group) if group else 0.0
            out["carry_over"] = {"split": split, "sires": len(names), "top_third_kept": kept(top), "rest_kept": kept(rest),
                                 "top_third_later": st.mean(late.get(s, 0) for s in top), "rest_later": st.mean(late.get(s, 0) for s in rest) if rest else 0.0}
            print("Sires with placings up to %d: the top third went on to place foals after it %.0f%% of the time (%.1f placings each), the rest %.0f%% (%.1f)." % (
                split, 100 * kept(top), out["carry_over"]["top_third_later"], 100 * kept(rest), out["carry_over"]["rest_later"]))
    else:
        print("\nNo whole-class results yet: the placings on file are one barn's list of its own wins.")
    if a.write:
        with open(os.path.join(HERE, "arabian_model.json"), "w") as fh:
            json.dump(out, fh, indent=1)
        print("Wrote qa/arabian_model.json")


if __name__ == "__main__":
    main()
