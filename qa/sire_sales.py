#!/usr/bin/env python3
"""Should a stallion's own foal sales move his sale estimate, and by how much?

    python qa/sire_sales.py            # print the test
    python qa/sire_sales.py --write    # also save qa/sire_sales.json for the app

The estimate for a stallion is the typical price for a horse of that age and
sex, moved toward what his own foals sold for. `k` sets how far: with k sold
foals he gets half of his own gap. k = "never" means his own sales are ignored.

Each k is scored on sales it has not seen: every auction is held out in turn,
so a sire cannot look good just because one seller's horses went through one
sale together.
"""
import csv
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
KS = (1, 2, 3, 5, 8, 12, 25, None)


def quarter_horse(halter_only=True):
    """Sales of young horses by halter stallions. A few pleasure-bred sires also appear on the halter lists, and their
    foals sell for more because they are a different kind of horse, so they are left out unless asked for."""
    from v2data import norm, V2
    halter = set(V2().fees) if halter_only else None
    rows = []
    with open(os.path.join(HERE, "price_training2.csv"), newline="") as fh:
        for r in csv.DictReader(fh):
            if r["sold"] == "1" and (halter is None or norm(r["sire"]) in halter):
                rows.append({"y": math.log(float(r["price"])), "sire": norm(r["sire"]), "auction": r["auction"],
                             "cell": (r["age_at_sale"], "gelding" if r["sex"].lower() == "gelding" else "other")})
    return rows


def arabian(young_only=True):
    import arabian_model as am
    rows = []
    for r in am.sales():
        if (r["year"] or 0) < 2015 or not r["sire"]:
            continue
        if young_only and (r["age"] is None or r["age"] > 3):
            continue
        rows.append({"y": math.log(r["price"]), "sire": r["sire"], "auction": r["auction"], "cell": ("all",)})
    return rows


def fit(train, k):
    cells = {}
    for r in train:
        cells.setdefault(r["cell"], []).append(r["y"])
    grand = st.mean(r["y"] for r in train)
    base = {c: st.mean(v) for c, v in cells.items()}
    gaps = {}
    for r in train:
        gaps.setdefault(r["sire"], []).append(r["y"] - base[r["cell"]])
    lift = {s: (st.mean(v) * len(v) / (len(v) + k)) if k is not None else 0.0 for s, v in gaps.items()}
    return lambda r: base.get(r["cell"], grand) + lift.get(r["sire"], 0.0)


def score(rows, k):
    sse = sst = 0.0
    errs = []
    for a in sorted({r["auction"] for r in rows}):
        train = [r for r in rows if r["auction"] != a]
        test = [r for r in rows if r["auction"] == a]
        if len(train) < 20:
            continue
        f, flat = fit(train, k), fit(train, None)
        for r in test:
            sse += (r["y"] - f(r)) ** 2
            sst += (r["y"] - flat(r)) ** 2
            errs.append(abs(r["y"] - f(r)))
    return {"gain": 1.0 - sse / sst if sst else 0.0, "typical_miss": math.exp(st.median(errs)) - 1.0 if errs else None}


def main():
    out = {}
    for name, rows in (("Quarter Horse", quarter_horse()), ("Quarter Horse with pleasure-bred sires mixed in", quarter_horse(False)), ("Arabian", arabian())):
        print("%s: %d sales, %d sires, %d auctions" % (name, len(rows), len({r["sire"] for r in rows}), len({r["auction"] for r in rows})))
        card = []
        for k in KS:
            s = score(rows, k)
            card.append({"k": k, **s})
            print("  his own sales count half after %-5s sold foals: %+5.1f%% better than ignoring them, typical miss %3.0f%%" % (k if k is not None else "never", 100 * s["gain"], 100 * s["typical_miss"]))
        best = max(card, key=lambda c: c["gain"])
        out[name] = {"sales": len(rows), "sires": len({r["sire"] for r in rows}), "scorecard": card, "best_k": best["k"] if best["gain"] > 0.005 else None, "best_gain": best["gain"]}
        print("  kept: %s\n" % ("k = %s" % best["k"] if out[name]["best_k"] is not None else "ignore his own sales (no setting beat it on unseen auctions)"))
    if "--write" in sys.argv:
        with open(os.path.join(HERE, "sire_sales.json"), "w") as fh:
            json.dump(out, fh, indent=1)
        print("Wrote qa/sire_sales.json")


if __name__ == "__main__":
    main()
