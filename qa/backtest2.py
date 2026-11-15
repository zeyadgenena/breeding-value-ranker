#!/usr/bin/env python3
"""Second test of the "chance of a prize winner" ranking, on a wider pool.

    python qa/backtest2.py            # compare the rules
    python qa/backtest2.py --write    # also save the honest track record for the app

What changed from qa/backtest.py: 87 stallions with a known fee instead of 52,
eight breeding seasons instead of seven (2018 to 2025), and every stallion on the
leaderboards counted, not only the ones in the workbook.

Two scores per rule:
  picks   of the top 3 picks in a budget each season, how many sired a top-50 foal
  sorting how well the rule sorts ALL stallions in a season into those that did
          and did not (1.0 = perfect, 0.5 = coin toss). It uses every stallion,
          so it is steadier than counting 3 picks.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as st

from v2data import V2, HERE

BUDGETS = (1000, 1500, 2000, None)
K = 3


def trend(a, b, lo=0.5, hi=2.0):
    if b <= 0:
        return hi if a > 0 else 1.0
    return max(lo, min(hi, a / b))


def r_final(v, s, d):                 # the rule the app has used so far
    last = v.e(s, d)
    return last * trend(last, v.e(s, d - 1)) if last > 0 else 0.2 * v.e(s, d - 1)


def r_last(v, s, d):
    return v.e(s, d)


def r_earners(v, s, d):               # how many of his foals earned money last year
    return v.n(s, d) + v.e(s, d) / 1e7


def r_smooth(v, s, d):                # three years, the latest counting most
    return 0.6 * v.e(s, d) + 0.3 * v.e(s, d - 1) + 0.1 * v.e(s, d - 2)


def r_smooth_trend(v, s, d):
    return r_smooth(v, s, d) * trend(v.e(s, d), v.e(s, d - 1), 0.7, 1.5)


def r_per_earner(v, s, d):            # winnings per earning foal, held back when he has few
    n = v.n(s, d)
    return (v.e(s, d) / n) * min(1.0, n / 8.0) if n else 0.0


def r_hits(v, s, d):                  # top-50 foals he already had on the last two lists
    h = sum(c for (nm, crop, y), (c, _) in v.hits.items() if nm == s and y in (d, d - 1))
    return h + v.e(s, d) / 1e7


def r_hits1(v, s, d):                 # top-50 foals he had on last year's list, winnings to break ties
    h = sum(c for (nm, crop, y), (c, _) in v.hits.items() if nm == s and y == d)
    return h + v.e(s, d) / 1e7


def r_hits_trend(v, s, d):            # top-50 foals last year, moved by the winnings trend
    h = sum(c for (nm, crop, y), (c, _) in v.hits.items() if nm == s and y == d)
    return (h + 0.25) * trend(v.e(s, d), v.e(s, d - 1)) * (1.0 if v.e(s, d) > 0 else 0.0) + v.e(s, d) / 1e7


def r_young_hits(v, s, d):            # top-50 foals from his two youngest crops: are his NEW foals winning?
    h = sum(c for (nm, crop, y), (c, _) in v.hits.items() if nm == s and y == d and crop >= d - 1)
    return h + v.e(s, d) / 1e7


def r_blend(v, s, d):                 # winnings, breadth and young winners together
    return (v.e(s, d) / 100000.0) + 0.05 * v.n(s, d) + 1.0 * r_young_hits(v, s, d)


def r_fee(v, s, d):                   # no judgement: the dearest you can afford
    return v.fee(s, d) or 0.0


RULES = {"final (in use)": r_final, "last year's winnings": r_last, "number of earners": r_earners, "three-year smooth": r_smooth,
         "smooth x trend": r_smooth_trend, "winnings per earner": r_per_earner, "top-50 foals, two years": r_hits, "top-50 foals last year": r_hits1,
         "top-50 foals x trend": r_hits_trend, "young top-50 foals": r_young_hits, "blend": r_blend, "dearest": r_fee}


def auc(scores, labels):
    pos = [s for s, l in zip(scores, labels) if l]
    neg = [s for s, l in zip(scores, labels) if not l]
    if not pos or not neg:
        return None
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def season(v, rule, d, budget, k=K):
    pool = [s for s in v.universe(d) if budget is None or v.fee(s, d) <= budget]
    if len(pool) < k:
        return None
    ranked = sorted(pool, key=lambda s: (-rule(v, s, d), v.fee(s, d), s))
    hit = [1 if v.crop_hits(s, d) > 0 else 0 for s in ranked]
    return {"picks": ranked[:k], "hits": sum(hit[:k]), "base": st.mean(hit), "auc": auc([rule(v, s, d) for s in pool], [v.crop_hits(s, d) > 0 for s in pool]),
            "money": sum(v.crop_money(s, d) for s in ranked[:k]), "pool": len(pool)}


def evaluate(v, rule, years, budget):
    rows = [(d, season(v, rule, d, budget)) for d in years]
    rows = [(d, r) for d, r in rows if r]
    aucs = [r["auc"] for _, r in rows if r["auc"] is not None]
    return {"picks": K * len(rows), "hit": sum(r["hits"] for _, r in rows), "base": st.mean(r["base"] for _, r in rows) if rows else 0.0,
            "auc": st.mean(aucs) if aucs else None, "money": sum(r["money"] for _, r in rows), "rows": rows}


def honest(v, years, budget):
    """Score each season with the rule that did best on the other seasons."""
    hit = n = 0
    base = []
    for d in years:
        others = [y for y in years if y != d]
        best = max((nm for nm in RULES if nm != "dearest"), key=lambda nm: (evaluate(v, RULES[nm], others, budget)["hit"], evaluate(v, RULES[nm], others, None)["auc"] or 0))
        r = season(v, RULES[best], d, budget)
        if r:
            hit += r["hits"]
            n += K
            base.append(r["base"])
    return {"budget": budget, "picks": n, "hit": hit, "share": hit / n if n else 0.0, "base": st.mean(base) if base else 0.0}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--rule", default="", help="show one rule's picks season by season")
    a = ap.parse_args()
    v = V2()
    years = [d for d in v.years if d + 2 <= v.years[-1]]          # the crop must have reached a leaderboard
    print("Decision years %d to %d (breeding seasons %d to %d), %d stallions with a fee in at least one of them.\n" % (
        years[0], years[-1], years[0] + 1, years[-1] + 1, len({s for d in years for s in v.universe(d)})))
    print("%-26s %s   %s" % ("rule", "   ".join("%-14s" % ("$%d" % b if b else "any budget") for b in BUDGETS), "sorting"))
    table = {}
    for name, rule in RULES.items():
        cells = [evaluate(v, rule, years, b) for b in BUDGETS]
        table[name] = cells
        print("%-26s %s   %.2f" % (name, "   ".join("%2d of %2d (%2.0f%%)" % (c["hit"], c["picks"], 100.0 * c["hit"] / c["picks"]) for c in cells), cells[-1]["auc"] or 0))
    print("%-26s %s" % ("average stallion", "   ".join("%-14s" % ("%.0f%%" % (100 * table["final (in use)"][i]["base"])) for i in range(len(BUDGETS)))))
    hon = [honest(v, years, b) for b in BUDGETS]
    print("\nHonest record (each season scored with the rule that did best on the other seasons):")
    for h in hon:
        print("  %-11s %2d of %2d (%2.0f%%) against %2.0f%% for the average stallion" % ("$%d" % h["budget"] if h["budget"] else "any budget", h["hit"], h["picks"], 100 * h["share"], 100 * h["base"]))
    if a.rule:
        for d, r in table[a.rule][BUDGETS.index(2000)]["rows"]:
            print(d + 1, [(s, int(v.fee(s, d)), v.crop_hits(s, d)) for s in r["picks"]], "pool", r["pool"])
    if a.write:
        out = {"first_season": years[0] + 1, "last_season": years[-1] + 1, "k": K, "stallions": len({s for d in years for s in v.universe(d)}),
               "by_budget": hon, "rules": {nm: {"auc": c[-1]["auc"], "hits": [x["hit"] for x in c], "picks": [x["picks"] for x in c]} for nm, c in table.items()}}
        with open(os.path.join(HERE, "track_record2.json"), "w") as fh:
            json.dump(out, fh, indent=1)
        print("Wrote qa/track_record2.json")


if __name__ == "__main__":
    main()
