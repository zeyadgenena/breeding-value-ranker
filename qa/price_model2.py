#!/usr/bin/env python3
"""Second attempt at the sale-price model, with what each lot's own page says about the horse.

    python qa/price_model2.py            # train every round and search combinations
    python qa/price_model2.py --write    # also save the result to qa/price_model2.json

Data: qa/price_training2.csv, young halter-bred horses sold at public online
auction, now with height, futurity eligibility, the horse's own record, the
dam's sire and the dam's produce record, read from each lot page.

Scored exactly as qa/price_model.py: every auction is held out in turn.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import os
import statistics as st

import price_model as pm

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    rows = []
    with open(os.path.join(HERE, "price_training2.csv"), newline="") as fh:
        for r in csv.DictReader(fh):
            if r["sold"] != "1":
                continue
            r["price"] = float(r["price"])
            r["fee"] = None
            r["year"] = int(r["sale_date"][:4])
            r["win_bred"] = float(r["sire_winnings_when_bred"]) if r["sire_winnings_when_bred"] != "" else None
            r["win_prev"] = float(r["sire_winnings_before_sale"]) if r["sire_winnings_before_sale"] != "" else None
            r["hits"] = float(r["sire_top50_when_bred"]) if r["sire_top50_when_bred"] != "" else None
            r["h"] = float(r["hands"]) if r["hands"] else None
            rows.append(r)
    return rows


flag = lambda key: (lambda r, ctx: [float(r[key])])
def f_hits(r, ctx): return [math.log1p(r["hits"] or 0.0), 1.0 if r["hits"] is None else 0.0]
def f_height(r, ctx): return [(r["h"] - 15.0) if r["h"] else 0.0, 0.0 if r["h"] else 1.0]
def f_words(r, ctx): return [math.log1p(float(r["notes_words"])) - 4.0]
def f_dam_foals(r, ctx): return [math.log1p(float(r["dam_foals"])) if r["dam_foals"] != "" else 0.0, 0.0 if r["dam_foals"] != "" else 1.0]


BASE = [pm.f_age, pm.f_sex]
NAMED = {"sire's winnings when bred": pm.f_record_bred, "sire's top-50 foals when bred": f_hits, "dam had produced an earner": flag("dam_proven_before"),
         "futurity eligible": flag("futurity_eligible"), "height": f_height, "own show record in the text": flag("own_record"),
         "dam described as a producer": flag("dam_producer_text"), "dam's sire a listed broodmare sire": flag("dam_sire_listed"),
         "year of sale": pm.f_year, "length of the description": f_words, "dam's number of foals": f_dam_foals, "ready to show": flag("ready_to_show")}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    rows = load()
    for r in rows:
        r["fee"] = None
    # price_model.fit wants a median fee; these rows carry none, so give it a constant
    orig_fit = pm.fit
    def fit(rows_, feats, per_sire):
        for r in rows_:
            r.setdefault("fee", None)
        ctx_rows = rows_ if any(r["fee"] for r in rows_) else rows_ + [{"fee": 1500.0}]
        import statistics
        ctx = {"median_fee": 1500.0}
        xs = [[1.0] + [v for f in feats for v in f(r, ctx)] for r in rows_]
        ys = [math.log(r["price"]) for r in rows_]
        w = pm.solve(xs, ys, ridge=1e-3)
        resid = [y - sum(p * q for p, q in zip(x, w)) for x, y in zip(xs, ys)]
        return {"w": w, "ctx": ctx, "sire": {}, "resid": resid}
    pm.fit = fit
    print("%d sales by %d sires at %d auctions, %d to %d. Typical price $%s.\n" % (len(rows), len({r["sire"] for r in rows}), len({r["auction"] for r in rows}),
          min(r["year"] for r in rows), max(r["year"] for r in rows), format(int(st.median(r["price"] for r in rows)), ",")))
    print("%-56s %-13s %s" % ("round", "typical miss", "explained"))
    card = []
    def run(name, feats):
        cv = pm.cross_validate(rows, feats, False)
        card.append({"round": name, "typical_miss": cv["typical_miss"], "explained": cv["explained"], "within_double_or_half": cv["within_double_or_half"]})
        print("%-56s %3.0f%%          %5.1f%%" % (name, 100 * cv["typical_miss"], 100 * cv["explained"]))
        return cv
    run("0 One typical price for every horse", [])
    run("1 Age and sex", BASE)
    for i, (name, f) in enumerate(NAMED.items(), start=2):
        run("%d Age, sex and %s" % (i, name), BASE + [f])
    tried = []
    for k in range(0, 5):
        for combo in itertools.combinations(NAMED, k):
            cv = pm.cross_validate(rows, BASE + [NAMED[c] for c in combo], False)
            tried.append((cv["explained"], cv["typical_miss"], cv["within_double_or_half"], " + ".join(("age", "sex") + combo)))
    tried.sort(reverse=True)
    print("\nSearched %d combinations of up to four extra factors. Best on unseen auctions:" % len(tried))
    for e, m, w2, name in tried[:6]:
        print("  %5.1f%% explained, typical miss %3.0f%%, %2.0f%% within half or double: %s" % (100 * e, 100 * m, 100 * w2, name))
    pm.fit = orig_fit
    if a.write:
        out = {"sales": len(rows), "sires": len({r["sire"] for r in rows}), "auctions": len({r["auction"] for r in rows}), "scorecard": card,
               "combinations_tried": len(tried), "best": [{"explained": t[0], "typical_miss": t[1], "within_double_or_half": t[2], "what": t[3]} for t in tried[:6]]}
        with open(os.path.join(HERE, "price_model2.json"), "w") as fh:
            json.dump(out, fh, indent=1)
        print("Wrote qa/price_model2.json")


if __name__ == "__main__":
    main()
