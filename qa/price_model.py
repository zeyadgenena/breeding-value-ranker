#!/usr/bin/env python3
"""Train and check a model of what a young halter horse sells for at public auction.

    python qa/price_model.py            # train every round, print the scorecard
    python qa/price_model.py --write    # also save the chosen model to qa/price_model.json

Data: qa/price_training.csv, one row per young horse sold (weanling to
two-year-old) by a stallion whose stud fee and foal results we know.

The model predicts the logarithm of the price, because prices are skewed: a few
horses sell for several times the typical one. Each round adds one idea. A round
is only kept if it predicts sales it has NOT seen better than the round before:
every auction is held out in turn, the model is trained on the others, and it is
scored on the one held out.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
AGES = ("0", "1", "2")


def load(path=None):
    rows = []
    with open(path or os.path.join(HERE, "price_training.csv"), newline="") as fh:
        for r in csv.DictReader(fh):
            r["price"] = float(r["price"])
            r["fee"] = float(r["fee"]) if r["fee"] else None
            r["win_prev"] = float(r["sire_winnings_year_before_sale"]) if r["sire_winnings_year_before_sale"] != "" else None
            r["win_bred"] = float(r["sire_winnings_when_bred"]) if r["sire_winnings_when_bred"] != "" else None
            r["year"] = int(r["sale_date"][:4])
            rows.append(r)
    return rows


# --------------------------------------------------------------------------
# a small least-squares solver (no third-party libraries)
# --------------------------------------------------------------------------
def solve(xs, ys, ridge=1e-6):
    n = len(xs[0])
    a = [[sum(x[i] * x[j] for x in xs) + (ridge if i == j else 0.0) for j in range(n)] for i in range(n)]
    b = [sum(x[i] * y for x, y in zip(xs, ys)) for i in range(n)]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(a[r][i]))
        a[i], a[p] = a[p], a[i]
        b[i], b[p] = b[p], b[i]
        for r in range(i + 1, n):
            f = a[r][i] / a[i][i]
            for c in range(i, n):
                a[r][c] -= f * a[i][c]
            b[r] -= f * b[i]
    w = [0.0] * n
    for i in range(n - 1, -1, -1):
        w[i] = (b[i] - sum(a[i][c] * w[c] for c in range(i + 1, n))) / a[i][i]
    return w


# --------------------------------------------------------------------------
# features, one idea per round
# --------------------------------------------------------------------------
def f_age(r, ctx):
    return [1.0 if r["age_at_sale"] == a else 0.0 for a in AGES[1:]]


def f_fee(r, ctx):
    fee = r["fee"] if r["fee"] else ctx["median_fee"]
    return [math.log(fee / 1000.0), 0.0 if r["fee"] else 1.0]


def f_record_sale(r, ctx):
    w = r["win_prev"]
    return [math.log1p((w or 0.0) / 10000.0), 1.0 if w is None else 0.0]


def f_record_bred(r, ctx):
    w = r["win_bred"]
    return [math.log1p((w or 0.0) / 10000.0), 1.0 if w is None else 0.0]


def f_sex(r, ctx):
    s = r["sex"].lower()
    return [1.0 if s in ("filly", "mare") else 0.0, 1.0 if s == "gelding" else 0.0]


def f_year(r, ctx):
    return [(r["year"] - 2021) / 4.0]


ROUNDS = [
    ("0 One typical price for every horse", [], False),
    ("1 Age at sale", [f_age], False),
    ("2 Age and stud fee", [f_age, f_fee], False),
    ("3 Age, stud fee and the sire's foal winnings the year before the sale", [f_age, f_fee, f_record_sale], False),
    ("4 Age, stud fee and the sire's foal winnings when the mare was bred", [f_age, f_fee, f_record_bred], False),
    ("5 Age and stud fee, plus each sire's own price level", [f_age, f_fee], True),
    ("6 Age, stud fee and sex, plus each sire's own price level", [f_age, f_fee, f_sex], True),
    ("7 Age, stud fee and year of sale, plus each sire's own price level", [f_age, f_fee, f_year], True),
    ("8 Age, plus each sire's own price level", [f_age], True),
    ("9 Age, sex and the sire's foal winnings when the mare was bred (the one kept)", [f_age, f_record_bred, f_sex], False),
]
KEPT = 9


def fit(rows, feats, per_sire):
    ctx = {"median_fee": st.median(r["fee"] for r in rows if r["fee"])}
    xs = [[1.0] + [v for f in feats for v in f(r, ctx)] for r in rows]
    ys = [math.log(r["price"]) for r in rows]
    w = solve(xs, ys)
    resid = [y - sum(a * b for a, b in zip(x, w)) for x, y in zip(xs, ys)]
    sire = {}
    if per_sire:
        groups = {}
        for r, e in zip(rows, resid):
            groups.setdefault(r["sire"], []).append(e)
        within = st.mean([st.pvariance(v) for v in groups.values() if len(v) > 1] or [0.25])
        means = [st.mean(v) for v in groups.values() if len(v) >= 2]
        avg_n = st.mean(len(v) for v in groups.values())
        between = max(0.0, (st.pvariance(means) if len(means) > 1 else 0.0) - within / avg_n)
        k = within / between if between > 1e-9 else 1e9       # sales a sire needs before half his gap is believed
        sire = {s: st.mean(v) * len(v) / (len(v) + k) for s, v in groups.items()}
        resid = [e - sire.get(r["sire"], 0.0) for r, e in zip(rows, resid)]
        ctx["k"] = k
    return {"w": w, "ctx": ctx, "sire": sire, "resid": resid}


def predict(model, feats, r):
    x = [1.0] + [v for f in feats for v in f(r, model["ctx"])]
    return sum(a * b for a, b in zip(x, model["w"])) + model["sire"].get(r["sire"], 0.0)


def cross_validate(rows, feats, per_sire, group="auction"):
    """Hold each auction (or each sire) out in turn. Returns errors on the held-out sales."""
    errs, sse, sst = [], 0.0, 0.0
    for g in sorted({r[group] for r in rows}):
        train = [r for r in rows if r[group] != g]
        test = [r for r in rows if r[group] == g]
        if len(train) < 20:
            continue
        m = fit(train, feats, per_sire)
        base = st.mean(math.log(r["price"]) for r in train)
        for r in test:
            y = math.log(r["price"])
            p = predict(m, feats, r)
            errs.append(abs(y - p))
            sse += (y - p) ** 2
            sst += (y - base) ** 2
    miss = math.exp(st.median(errs)) - 1.0           # typical miss, as a share of the price
    within2 = sum(1 for e in errs if e <= math.log(2)) / len(errs)
    return {"typical_miss": miss, "within_double_or_half": within2, "explained": 1.0 - sse / sst if sst else 0.0, "n": len(errs)}


def quantile(v, q):
    v = sorted(v)
    pos = q * (len(v) - 1)
    lo, hi = int(math.floor(pos)), int(math.ceil(pos))
    return v[lo] + (v[hi] - v[lo]) * (pos - lo)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="save the kept model to qa/price_model.json for the app")
    ap.add_argument("--search", action="store_true", help="also try every combination of factors")
    a = ap.parse_args()
    rows = load()
    print("%d sales by %d stallions at %d auctions, %d to %d. Typical price $%s." % (
        len(rows), len({r["sire"] for r in rows}), len({r["auction"] for r in rows}), min(r["year"] for r in rows),
        max(r["year"] for r in rows), format(int(st.median(r["price"] for r in rows)), ",")))
    print("\n%-80s %-22s %-22s %s" % ("round", "typical miss", "within half or double", "variation explained"))
    card = []
    for name, feats, per_sire in ROUNDS:
        cv = cross_validate(rows, feats, per_sire)
        new_sire = cross_validate(rows, feats, False, group="sire")
        card.append({"round": name, **cv, "typical_miss_new_sire": new_sire["typical_miss"]})
        print("%-80s %3.0f%% (new sire %3.0f%%)   %3.0f%%                    %5.1f%%" % (
            name, 100 * cv["typical_miss"], 100 * new_sire["typical_miss"], 100 * cv["within_double_or_half"], 100 * cv["explained"]))
    best = min(range(len(ROUNDS)), key=lambda i: (round(card[i]["typical_miss"], 3), -card[i]["explained"]))
    explained = max(range(len(ROUNDS)), key=lambda i: card[i]["explained"])
    print("\nLowest typical miss: round %s. Most variation explained: round %s." % (ROUNDS[best][0][:1], ROUNDS[explained][0][:1]))
    if a.search or a.write:
        import itertools
        named = {"age": f_age, "fee": f_fee, "winnings before sale": f_record_sale, "winnings when bred": f_record_bred,
                 "sex": f_sex, "year": f_year}
        tried = []
        for k in range(len(named) + 1):
            for combo in itertools.combinations(named, k):
                for ps in (False, True):
                    cv = cross_validate(rows, [named[c] for c in combo], ps)
                    tried.append((cv["explained"], cv["typical_miss"], " + ".join(combo) + (" + sire level" if ps else "")))
        tried.sort(reverse=True)
        print("\nSearched %d combinations. Best by variation explained on unseen auctions:" % len(tried))
        for e, m, name in tried[:5]:
            print("  %5.1f%% explained, typical miss %3.0f%%: %s" % (100 * e, 100 * m, name or "(nothing)"))
    if a.write:
        name, feats, per_sire = ROUNDS[KEPT]
        m = fit(rows, feats, per_sire)
        w = m["w"]
        fees = [r["fee"] for r in rows if r["fee"]]
        out = {"kept": name, "target": "natural log of sale price in US dollars",
               "intercept": w[0], "yearling": w[1], "two_year_old": w[2], "winnings_log": w[3], "winnings_unknown": w[4],
               "filly": w[5], "gelding": w[6],
               "winnings_term": "log(1 + winnings / 10000)",
               "residuals": sorted(round(e, 4) for e in m["resid"]),
               "sales": len(rows), "sires": len({r["sire"] for r in rows}), "auctions": len({r["auction"] for r in rows}),
               "fee_range_in_sales": [min(fees), max(fees)],
               "scorecard": card, "kept_round": card[KEPT],
               "combinations_tried": len(tried), "best_combination": {"explained": tried[0][0], "typical_miss": tried[0][1], "what": tried[0][2]}}
        with open(os.path.join(HERE, "price_model.json"), "w") as fh:
            json.dump(out, fh, indent=1)
        print("Wrote qa/price_model.json (%s)" % name)


if __name__ == "__main__":
    main()
