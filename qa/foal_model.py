#!/usr/bin/env python3
"""Foal by foal: what is the chance a weanling or yearling finishes in the top three of its futurity class?

    python qa/foal_model.py            # train every round, print the scorecard
    python qa/foal_model.py --write    # also save the kept model to qa/foal_model.json

Data: qa/futurity_foals.csv (every horse shown, 2024 to 2026) joined to what was
public about its sire and its dam BEFORE the mare was bred. A weanling shown in
2026 was foaled in 2026 and bred in 2025, so the model may only use lists up to
2024. That is the position a breeder is in.

Each round adds one idea. Rounds are scored two ways, both on foals the model
has not seen:
  forward    trained on 2024 and 2025, scored on 2026
  each year  every year held out in turn
The score is "sorting": the chance the model ranks a random top-three foal above
a random other foal. 0.50 is a coin toss, 1.00 is perfect.

Everything here is about foals that were shown. Foals that never reached the
ring are not in the data.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics as st

from v2data import V2, HERE, norm, _csv

AGES = ("weanling", "yearling")


def build(v):
    lead, top50 = {}, {}
    for r in _csv("leaders", "dams.csv"):
        if r["period"].isdigit():
            lead.setdefault(int(r["period"]), set()).add(norm(r["dam"]))
    dam_sire = {}                                                   # dam -> (her sire, first year that was public)
    def learn(dam, sire, year):
        if dam and sire and (dam not in dam_sire or year < dam_sire[dam][1]):
            dam_sire[dam] = (sire, year)
    for r in _csv("leaders", "earners.csv"):
        if r["period"].isdigit():
            learn(norm(r["dam"]), norm(r["dam_sire"]), int(r["period"]))
    for r in _csv("leaders", "dams.csv"):
        if r["period"].isdigit():
            learn(norm(r["dam"]), norm(r["sire"]), int(r["period"]))
    F = [f for f in v.futurity if f["sire"]]
    for f in F:
        learn(f["horse"], f["sire"], f["year"])                     # a dam that was shown herself tells us her sire
    was_earner = {}                                                 # a mare that was a top-50 earner or a futurity top-three herself
    for r in v.top50:
        was_earner[norm(r["horse"])] = min(int(r["period"]), was_earner.get(norm(r["horse"]), 9999))
    for f in F:
        if int(f["top3"] or 0) > 0:
            was_earner[f["horse"]] = min(f["year"], was_earner.get(f["horse"], 9999))
    earlier = {}                                                    # dam -> [(year, horse, pct)]
    for f in F:
        earlier.setdefault(f["dam"], []).append((f["year"], f["horse"], f["pct"]))
    sire_prev = {}                                                  # (sire, year) -> his foals' average finish that year
    for f in F:
        sire_prev.setdefault((f["sire"], f["year"]), []).append(f["pct"])
    earner = {(norm(r["horse"]), int(r["period"])) for r in v.top50}      # among the year's top 50 halter money earners
    rows = []
    for f in F:
        if f["age_class"] not in AGES:
            continue
        y = f["year"]
        foaled = y if f["age_class"] == "weanling" else y - 1
        k = foaled - 2                      # the last full year on record when the mare was bred (she is bred the year before the foal is born)
        b = v.board.get((f["sire"], k))
        sibs = [p for (yy, h, p) in earlier.get(f["dam"], []) if yy <= k and h != f["horse"]]
        prev = sire_prev.get((f["sire"], k), [])
        known = dam_sire.get(f["dam"])
        ds = known[0] if known and known[1] <= k else None          # only if it was public before the mare was bred
        bm = v.bm_sires.get((ds, k)) if ds else None
        rows.append({"year": y, "horse": f["horse"], "sire": f["sire"], "dam": f["dam"], "age": f["age_class"],
                     "top3": 1 if int(f["top3"] or 0) > 0 else 0, "win": 1 if int(f["wins"] or 0) > 0 else 0, "pct": f["pct"],
                     "money": 1 if (f["horse"], y) in earner else 0,
                     "sire_rank": b["rank"] if b else 99, "sire_win": b["earnings"] if b else 0.0, "sire_n": b["earners"] if b else 0,
                     "dam_proven": 1 if any(f["dam"] in lead.get(yy, ()) for yy in range(2017, k + 1)) else 0,
                     "sib": st.mean(sibs) if sibs else None,
                     "sire_fut": (st.mean(prev), len(prev)) if prev else None,
                     "bm_listed": 1 if bm else 0, "bm_known": 1 if ds else 0,
                     "dam_self": 1 if f["dam"] in was_earner and was_earner[f["dam"]] <= k else 0,
                     "sire_prev_win": v.e(f["sire"], k - 1),
                     "sire_hits": sum(c for (nm, crop, yy), (c, _) in v.hits.items() if nm == f["sire"] and yy == k)})
    return rows


# ---- features: each returns a list of numbers for one foal ----
def f_tier(r): return [1.0 if r["sire_rank"] <= 5 else 0.0, 1.0 if 5 < r["sire_rank"] <= 20 else 0.0]
def f_top20(r): return [1.0 if r["sire_rank"] <= 20 else 0.0]
def f_win(r): return [math.log1p(r["sire_win"] / 10000.0)]
def f_breadth(r): return [math.log1p(r["sire_n"])]
def f_dam(r): return [float(r["dam_proven"])]
def f_sib(r): return [((r["sib"] - 50.0) / 50.0) if r["sib"] is not None else 0.0, 1.0 if r["sib"] is not None else 0.0]
def f_bm(r): return [float(r["bm_listed"])]
def f_bm_known(r): return [float(r["bm_known"])]
def f_age(r): return [1.0 if r["age"] == "yearling" else 0.0]
def f_sire_fut(r):
    if not r["sire_fut"]:
        return [0.0]
    m, n = r["sire_fut"]
    return [((n * m + 4.0 * 50.0) / (n + 4.0) - 50.0) / 50.0]
def f_dam_self(r): return [float(r["dam_self"])]
def f_momentum(r):
    a_, b_ = r["sire_win"], r["sire_prev_win"]
    return [math.log(max(0.5, min(2.0, a_ / b_))) if a_ > 0 and b_ > 0 else 0.0]
def f_hits(r): return [math.log1p(r["sire_hits"])]
def f_tier_x_dam(r): return [float(r["dam_proven"]) * (1.0 if r["sire_rank"] <= 20 else 0.0)]


ROUNDS = [
    ("0 The same chance for every foal", []),
    ("1 Sire's leaderboard tier (top 5, 6 to 20, other)", [f_tier]),
    ("2 Sire's winnings, as a number", [f_win]),
    ("3 Sire's tier and how many earners he had", [f_tier, f_breadth]),
    ("4 Sire's tier and whether the dam has produced an earner", [f_tier, f_dam]),
    ("5 Round 4 and the finish of the dam's earlier foal", [f_tier, f_dam, f_sib]),
    ("6 Round 5 and whether the dam's sire is a listed broodmare sire", [f_tier, f_dam, f_sib, f_bm, f_bm_known]),
    ("7 Round 5 and the sire's own futurity average last year", [f_tier, f_dam, f_sib, f_sire_fut]),
    ("8 Round 5 and age class", [f_tier, f_dam, f_sib, f_age]),
    ("9 Round 4 with tier and dam working together", [f_tier, f_dam, f_tier_x_dam]),
    ("10 Sire's winnings and the dam's record", [f_win, f_dam, f_sib]),
    ("11 Round 4 and whether the dam was a winner herself", [f_tier, f_dam, f_dam_self]),
    ("12 Round 4 and whether the sire's winnings are rising or falling", [f_tier, f_dam, f_momentum]),
    ("13 Round 4 and how many top-50 foals the sire had last year", [f_tier, f_dam, f_hits]),
    ("14 The dam's record and the sire's top-50 foals", [f_dam, f_hits]),
    ("15 Sire's tier, his number of earners and the dam's record", [f_tier, f_breadth, f_dam]),
    ("16 Sire in the top 20 or not, and the dam's record (the one kept)", [f_top20, f_dam]),
]
KEPT = 16
NAMED = {"sire in the top 20": f_top20, "sire tier": f_tier, "sire winnings": f_win, "sire earners": f_breadth, "dam produced an earner": f_dam, "dam's earlier foal": f_sib,
         "age class": f_age, "sire's futurity average": f_sire_fut, "dam a winner herself": f_dam_self, "sire trend": f_momentum, "sire's top-50 foals": f_hits}


def logistic(xs, ys, ridge=1.0, steps=15):
    """Plain logistic regression by Newton steps, with a little shrinkage so small samples do not overreach."""
    n = len(xs[0])
    w = [0.0] * n
    for _ in range(steps):
        g = [0.0] * n
        h = [[0.0] * n for _ in range(n)]
        for x, y in zip(xs, ys):
            z = sum(a * b for a, b in zip(x, w))
            p = 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))
            for i in range(n):
                g[i] += (y - p) * x[i]
                for j in range(n):
                    h[i][j] += p * (1 - p) * x[i] * x[j]
        for i in range(1, n):                         # do not shrink the intercept
            g[i] -= ridge * w[i]
            h[i][i] += ridge
        for i in range(n):
            h[i][i] += 1e-9
        step = gauss(h, g)
        w = [a + b for a, b in zip(w, step)]
        if max(abs(s) for s in step) < 1e-8:
            break
    return w


def gauss(a, b):
    n = len(b)
    a = [row[:] for row in a]
    b = b[:]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(a[r][i]))
        a[i], a[p] = a[p], a[i]
        b[i], b[p] = b[p], b[i]
        for r in range(i + 1, n):
            f = a[r][i] / a[i][i]
            for c in range(i, n):
                a[r][c] -= f * a[i][c]
            b[r] -= f * b[i]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (b[i] - sum(a[i][c] * x[c] for c in range(i + 1, n))) / a[i][i]
    return x


def X(rows, feats):
    return [[1.0] + [val for f in feats for val in f(r)] for r in rows]


def prob(w, x):
    return 1.0 / (1.0 + math.exp(-max(-30, min(30, sum(a * b for a, b in zip(x, w))))))


def auc(scores, labels):
    pos = [s for s, l in zip(scores, labels) if l]
    neg = [s for s, l in zip(scores, labels) if not l]
    if not pos or not neg:
        return None
    return sum((p > q) + 0.5 * (p == q) for p in pos for q in neg) / (len(pos) * len(neg))


def score(rows, feats, target="top3"):
    years = sorted({r["year"] for r in rows})
    train = [r for r in rows if r["year"] < years[-1]]
    test = [r for r in rows if r["year"] == years[-1]]
    w = logistic(X(train, feats), [r[target] for r in train])
    fwd = auc([prob(w, x) for x in X(test, feats)], [r[target] for r in test]) if feats else 0.5
    each, pooled_s, pooled_l = [], [], []
    for y in years:
        tr = [r for r in rows if r["year"] != y]
        te = [r for r in rows if r["year"] == y]
        w = logistic(X(tr, feats), [r[target] for r in tr])
        s = [prob(w, x) for x in X(te, feats)]
        a = auc(s, [r[target] for r in te]) if feats else 0.5
        each.append(a)
        pooled_s += s
        pooled_l += [r[target] for r in te]
    brier = st.mean((s - l) ** 2 for s, l in zip(pooled_s, pooled_l))
    return {"forward": fwd, "each_year": st.mean(each), "brier": brier}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--search", action="store_true", help="try every combination of up to four factors")
    a = ap.parse_args()
    v = V2()
    rows = build(v)
    base = st.mean(r["top3"] for r in rows)
    print("%d weanlings and yearlings shown, %d sires, %d dams. %.0f%% finished in the top three of an open class; %.0f%% won one.\n" % (
        len(rows), len({r["sire"] for r in rows}), len({r["dam"] for r in rows}), 100 * base, 100 * st.mean(r["win"] for r in rows)))
    print("%-66s %-9s %-9s" % ("round", "forward", "each year"))
    card = []
    for name, feats in ROUNDS:
        s = score(rows, feats)
        card.append({"round": name, **s})
        print("%-66s %.2f      %.2f" % (name, s["forward"], s["each_year"]))
    best = max(range(len(ROUNDS)), key=lambda i: card[i]["forward"] + card[i]["each_year"])
    print("\nBest on unseen foals: round %s. Kept: round %s." % (ROUNDS[best][0].split()[0], ROUNDS[KEPT][0].split()[0]))

    searched = None
    if a.search or a.write:
        import itertools
        tried = []
        for k in range(1, 5):
            for combo in itertools.combinations(NAMED, k):
                sc = score(rows, [NAMED[c] for c in combo])
                tried.append(((sc["forward"] + sc["each_year"]) / 2.0, sc["forward"], sc["each_year"], " + ".join(combo)))
        tried.sort(reverse=True)
        searched = {"combinations": len(tried), "best": [{"what": t[3], "forward": t[1], "each_year": t[2]} for t in tried[:5]]}
        print("\nSearched %d combinations of up to four factors. Best on unseen foals:" % len(tried))
        for t in tried[:6]:
            print("  forward %.2f, each year %.2f: %s" % (t[1], t[2], t[3]))
    name, feats = ROUNDS[KEPT]
    w = logistic(X(rows, feats), [r["top3"] for r in rows])
    ww = logistic(X(rows, feats), [r["win"] for r in rows])
    wm = logistic(X(rows, feats), [r["money"] for r in rows])
    money_score = score(rows, feats, target="money")
    cut = min(float(r["earnings"]) for r in v.top50 if int(r["period"]) >= min(r2["year"] for r2 in rows))
    print("\nSame model, different question: will the foal be one of the year's top 50 money earners (about $%s or more)? %.0f%% of shown foals were. Sorting on unseen foals: forward %.2f, each year %.2f." % (
        format(int(round(cut, -3)), ","), 100 * st.mean(r["money"] for r in rows), money_score["forward"], money_score["each_year"]))
    print("\nWhat the kept model says (chance of a top-three finish, for a foal that is shown):")
    grid = []
    for tier, rank in (("sire in the top 20", 10), ("other sire", 99)):
        for dam, proven in (("dam has produced an earner", 1), ("no record for the dam", 0)):
            r = {"sire_rank": rank, "dam_proven": proven}
            x = [1.0] + [val for f in feats for val in f(r)]
            p, pw, pmn = prob(w, x), prob(ww, x), prob(wm, x)
            cell = [q for q in rows if f_top20(q) == f_top20(r) and q["dam_proven"] == proven]
            grid.append({"sire": tier, "dam": dam, "proven": proven, "top3": p, "win": pw, "money": pmn, "foals": len(cell),
                         "seen_top3": st.mean(q["top3"] for q in cell) if cell else None, "seen_money": st.mean(q["money"] for q in cell) if cell else None})
            print("  %-20s %-28s top three %2.0f%%   win %2.0f%%   top-50 earner %2.0f%%   (%d foals; what happened: %2.0f%% and %2.0f%%)" % (
                tier, dam, 100 * p, 100 * pw, 100 * pmn, len(cell), 100 * grid[-1]["seen_top3"], 100 * grid[-1]["seen_money"]))
    # how the real foals split when sorted by the model, forward test
    years = sorted({r["year"] for r in rows})
    train = [r for r in rows if r["year"] < years[-1]]
    test = [r for r in rows if r["year"] == years[-1]]
    wf = logistic(X(train, feats), [r["top3"] for r in train])
    ranked = sorted(zip([prob(wf, x) for x in X(test, feats)], test), key=lambda t: -t[0])
    third = len(ranked) // 3
    hi, lo = ranked[:third], ranked[-third:]
    split = {"year": years[-1], "foals": len(test), "top_third_rate": st.mean(t[1]["top3"] for t in hi), "bottom_third_rate": st.mean(t[1]["top3"] for t in lo),
             "top_third_said": st.mean(t[0] for t in hi), "bottom_third_said": st.mean(t[0] for t in lo)}
    print("\nForward check on %d: of the %d foals the model liked most, %.0f%% made a top three (it said %.0f%%); of the %d it liked least, %.0f%% (it said %.0f%%)." % (
        years[-1], third, 100 * split["top_third_rate"], 100 * split["top_third_said"], third, 100 * split["bottom_third_rate"], 100 * split["bottom_third_said"]))
    if a.write:
        out = {"kept": name, "target": "top-three finish in an open futurity class, weanlings and yearlings that were shown",
               "weights_top3": w, "weights_win": ww, "weights_money": wm, "money_score": money_score, "money_cutoff": cut, "money_rate": st.mean(r["money"] for r in rows), "features": ["intercept", "sire_in_top_20", "dam_proven"], "search": searched,
               "base_rate": base, "foals": len(rows), "sires": len({r["sire"] for r in rows}), "dams": len({r["dam"] for r in rows}), "years": years,
               "scorecard": card, "kept_round": card[KEPT], "grid": grid, "forward_split": split, "typical_class_size": 21,
               "dam_rates": {"proven": st.mean(r["top3"] for r in rows if r["dam_proven"]), "other": st.mean(r["top3"] for r in rows if not r["dam_proven"]),
                             "proven_foals": sum(1 for r in rows if r["dam_proven"]), "other_foals": sum(1 for r in rows if not r["dam_proven"]),
                             "meaning": "the dam was among the year's top 50 dams by foal winnings in an earlier year (about $10,000 or more won by her foals in one year)"}}
        with open(os.path.join(HERE, "foal_model.json"), "w") as fh:
            json.dump(out, fh, indent=1)
        print("Wrote qa/foal_model.json")


if __name__ == "__main__":
    main()
