#!/usr/bin/env python3
"""What the futurity results say about each stallion, foal by foal.

    python qa/futurity.py            # print the tests
    python qa/futurity.py --write    # also save qa/sire_model.json for the app

Data: qa/futurity_foals.csv, every horse shown in the WCHA, Big Money and
Breeders Halter Futurity classes at the Halter Million, 2024 to 2026, with its
sire, dam and finishing place. This is the first data in the project that counts
the foals that did NOT win as well as the ones that did.

A foal's score is its finish as a percentile of its class: 100 = won, 50 =
middle, 0 = last. A stallion's score is the average over his foals, pulled
toward 50 when he has few (so one lucky foal does not make a sire).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics as st

from v2data import V2, HERE


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = st.mean(xs), st.mean(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy) if sx > 0 and sy > 0 else None


def ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2.0
        i = j + 1
    return r


def spearman(xs, ys):
    return pearson(ranks(xs), ranks(ys))


def by_sire(foals):
    out = {}
    for f in foals:
        out.setdefault(f["sire"], []).append(f)
    return out


def shrink_k(groups):
    """How many foals a sire needs before half of his gap from average is believed."""
    within = st.mean([st.pvariance([f["pct"] for f in v]) for v in groups.values() if len(v) > 1] or [833.0])
    means = [st.mean(f["pct"] for f in v) for v in groups.values() if len(v) >= 3]
    avg_n = st.mean(len(v) for v in groups.values() if len(v) >= 3) if means else 1.0
    between = max(1e-9, (st.pvariance(means) if len(means) > 1 else 0.0) - within / avg_n)
    return within / between


def sire_scores(foals, k=None):
    g = by_sire(foals)
    k = shrink_k(g) if k is None else k
    out = {}
    for s, v in g.items():
        n = len(v)
        mean = st.mean(f["pct"] for f in v)
        out[s] = {"n": n, "mean": mean, "score": (n * mean + k * 50.0) / (n + k), "top3": sum(1 for f in v if int(f["top3"] or 0) > 0),
                  "wins": sum(1 for f in v if int(f["wins"] or 0) > 0), "top_half": sum(1 for f in v if f["pct"] >= 50)}
    return out, k


def thirds(pairs):
    """pairs = (predictor, outcome foal). Average outcome in the top and bottom third by predictor."""
    pairs = sorted(pairs, key=lambda p: p[0])
    n = len(pairs) // 3
    lo, hi = pairs[:n], pairs[-n:]
    f = lambda part: {"foals": len(part), "avg": st.mean(p[1]["pct"] for p in part), "top3": st.mean(1.0 if int(p[1]["top3"] or 0) > 0 else 0.0 for p in part)}
    return f(lo), f(hi)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    v = V2()
    F = [f for f in v.futurity if f["sire"]]
    years = sorted({f["year"] for f in F})
    print("%d horse-years, %d horses, %d sires, %d dams, years %s" % (len(F), len({f["horse"] for f in F}), len({f["sire"] for f in F}), len({f["dam"] for f in F}), years))
    for y in years:
        fy = [f for f in F if f["year"] == y]
        print("  %d: %d horses shown by %d sires; sires with 5 or more shown: %d" % (y, len(fy), len({f["sire"] for f in fy}), sum(1 for s, g in by_sire(fy).items() if len(g) >= 5)))

    report = {"years": years, "horse_years": len(F), "tests": {}}

    # ---- 1. does a sire's score in one year carry to his foals the next year? ----
    print("\n1. Does a stallion's futurity score carry over to the next year's foals?")
    carry = []
    for y in years[:-1]:
        prev, k = sire_scores([f for f in F if f["year"] == y])
        nxt = [f for f in F if f["year"] == y + 1]
        prev_horses = {f["horse"] for f in F if f["year"] == y}
        fresh = [f for f in nxt if f["horse"] not in prev_horses]            # different foals, not the same horse a year older
        pairs = [(prev[f["sire"]]["score"], f) for f in fresh if f["sire"] in prev]
        if len(pairs) < 30:
            continue
        r = pearson([p[0] for p in pairs], [p[1]["pct"] for p in pairs])
        lo, hi = thirds(pairs)
        carry.append({"from": y, "to": y + 1, "foals": len(pairs), "r": r, "low": lo, "high": hi, "k": k})
        print("  %d -> %d: %d new foals. Link %.2f. Foals of the top third of sires averaged %.0f and %.0f%% made a top three; bottom third %.0f and %.0f%%. (k=%.1f)" % (
            y, y + 1, len(pairs), r, hi["avg"], 100 * hi["top3"], lo["avg"], 100 * lo["top3"], k))
    report["tests"]["carry_over"] = carry

    # ---- 2. which sire measure predicts a new foal's finish best? ----
    print("\n2. Which measure of the sire, known the year before, best predicts a new foal's finish?")
    measures = {"futurity score": lambda s, y, prev: prev.get(s, {}).get("score"),
                "foals he had shown": lambda s, y, prev: prev.get(s, {}).get("n"),
                "leaderboard winnings": lambda s, y, prev: v.e(s, y),
                "leaderboard earners": lambda s, y, prev: float(v.n(s, y)),
                "winnings per earner": lambda s, y, prev: (v.e(s, y) / v.n(s, y)) if v.n(s, y) else 0.0,
                "stud fee": lambda s, y, prev: v.fee(s, y)}
    compare = {}
    for name, fn in measures.items():
        xs, ys = [], []
        for y in years[:-1]:
            prev, _ = sire_scores([f for f in F if f["year"] == y])
            prev_horses = {f["horse"] for f in F if f["year"] == y}
            for f in F:
                if f["year"] == y + 1 and f["horse"] not in prev_horses:
                    x = fn(f["sire"], y, prev)
                    if x is not None:
                        xs.append(float(x))
                        ys.append(f["pct"])
        r = spearman(xs, ys) if len(xs) >= 30 else None
        compare[name] = {"foals": len(xs), "link": r}
        print("  %-22s %4d foals   link %s" % (name, len(xs), "%.2f" % r if r is not None else "n/a"))
    report["tests"]["measures"] = compare

    # ---- 3. the mare: does a dam's earlier foal predict her next one? ----
    print("\n3. Does the mare matter? A dam's earlier foal against her later, different foal.")
    by_dam = {}
    for f in F:
        if f["dam"]:
            by_dam.setdefault(f["dam"], {}).setdefault(f["horse"], []).append(f)
    sib = []
    for dam, horses in by_dam.items():
        hs = sorted(horses.items(), key=lambda kv: min(x["year"] for x in kv[1]))
        for i in range(len(hs)):
            for j in range(i + 1, len(hs)):
                a1 = st.mean(x["pct"] for x in hs[i][1])
                b1 = st.mean(x["pct"] for x in hs[j][1])
                sib.append((a1, b1, hs[i][1][0]["sire"] == hs[j][1][0]["sire"]))
    r_sib = pearson([s[0] for s in sib], [s[1] for s in sib]) if len(sib) >= 10 else None
    print("  %d pairs of different foals out of the same mare. Link between them: %s" % (len(sib), "%.2f" % r_sib if r_sib is not None else "too few"))
    full = [s for s in sib if s[2]]
    half = [s for s in sib if not s[2]]
    for label, part in (("same sire", full), ("different sire", half)):
        r = pearson([s[0] for s in part], [s[1] for s in part]) if len(part) >= 10 else None
        print("    %-15s %3d pairs, link %s" % (label, len(part), "%.2f" % r if r is not None else "too few"))
    report["tests"]["siblings"] = {"pairs": len(sib), "link": r_sib, "same_sire_pairs": len(full), "different_sire_pairs": len(half)}

    # ---- 4. the same horse a year later: does an early finish last? ----
    print("\n4. Does a horse's finish one year predict its finish the next year?")
    by_horse = {}
    for f in F:
        by_horse.setdefault(f["horse"], {})[f["year"]] = f
    again = [(h[y]["pct"], h[y + 1]["pct"]) for h in by_horse.values() for y in years[:-1] if y in h and y + 1 in h]
    r_again = pearson([p[0] for p in again], [p[1] for p in again]) if len(again) >= 10 else None
    back = sum(1 for h in by_horse.values() for y in years[:-1] if y in h and y + 1 in h)
    first = sum(1 for h in by_horse.values() for y in years[:-1] if y in h)
    print("  %d of %d horses shown one year came back the next (%.0f%%). Link between the two finishes: %s" % (
        back, first, 100.0 * back / first if first else 0, "%.2f" % r_again if r_again is not None else "too few"))
    report["tests"]["same_horse"] = {"pairs": len(again), "link": r_again, "came_back": back, "shown_first_year": first}

    # ---- the table for the app: all years together ----
    scores, k = sire_scores(F)
    horses = {}
    for f in F:
        horses.setdefault(f["sire"], set()).add(f["horse"])
    table = {s: {"shown": len(horses[s]), "starts": x["n"], "avg": round(x["mean"], 1), "score": round(x["score"], 1), "top3": x["top3"], "wins": x["wins"], "top_half": x["top_half"]}
             for s, x in scores.items()}
    report["k"] = k
    report["sires"] = table
    top = sorted(table.items(), key=lambda kv: -kv[1]["score"])
    print("\nSires by futurity score (all years, k=%.1f). starts = foal-years shown." % k)
    for s, x in top[:14]:
        print("  %-26s score %4.1f   starts %3d   top three %3d (%2.0f%%)   wins %2d   fee %s" % (s, x["score"], x["starts"], x["top3"], 100.0 * x["top3"] / x["starts"], x["wins"], v.fee(s, v.years[-1], stale=4)))
    # ---- what a futurity finish is worth: matched to the year's top-50 money earners ----
    from v2data import norm
    earn = {(norm(r["horse"]), int(r["period"])): float(r["earnings"]) for r in v.top50}      # one spelling per horse, as everywhere else
    worth = {}
    young = [f for f in F if f["age_class"] in ("weanling", "yearling")]
    for label, test in (("won an open class", lambda f: int(f["wins"] or 0) > 0), ("top three, no win", lambda f: int(f["top3"] or 0) > 0 and int(f["wins"] or 0) == 0),
                        ("shown, outside the top three", lambda f: int(f["top3"] or 0) == 0)):
        g = [f for f in young if test(f)]
        hit = [earn[(f["horse"], f["year"])] for f in g if (f["horse"], f["year"]) in earn]
        worth[label] = {"foals": len(g), "top50_share": len(hit) / len(g) if g else None, "typical": st.median(hit) if hit else None}
    print("\nWhat a finish is worth: " + "; ".join("%s %.0f%% were top-50 earners" % (k, 100 * w["top50_share"]) for k, w in worth.items() if w["top50_share"] is not None))
    if a.write:
        with open(os.path.join(HERE, "futurity_worth.json"), "w") as fh:
            json.dump(worth, fh, indent=1)
        with open(os.path.join(HERE, "sire_model.json"), "w") as fh:
            json.dump(report, fh, indent=1)
        print("Wrote qa/sire_model.json")


if __name__ == "__main__":
    main()
