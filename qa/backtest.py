#!/usr/bin/env python3
"""QA for the matcher: what would it have picked in past years, and how did those picks turn out?

    python qa/backtest.py                 # compare every ranking rule
    python qa/backtest.py --rule record3  # year-by-year detail for one rule

For each decision year D the rule sees only what was public by the end of D:
the stud fee for the next season (D+1) and the foal results up to D. A mare
bred in D+1 foals in D+2, so the picks are judged on that crop:

  hits      foals from the D+2 crop that made the top 50 halter money earners
            of the year, as weanlings (D+2) or yearlings (D+3). A top-50 foal
            wins roughly $11,000 to $18,000 or more in a year: the "diamond".
  hit $     what those foals won.
  sire $    everything the stallion's foals won in D+2 (all crops).

Every result is set against the average affordable stallion (what a random
pick within the same budget would have got) and against random draws.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from ranker import matcher  # noqa: E402
from ranker.core import Params, fee_at  # noqa: E402
from ranker.workbook import load  # noqa: E402

LAST_YEAR = 2026
BUDGETS = (1000, 1500, 2000, 2500, None)
TOP_K = 3


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
class Data:
    def __init__(self, workbook="data/breeding_data.xlsx"):
        ds, _, _ = load(os.path.join(os.path.dirname(HERE), workbook))
        self.ds = ds
        self.names = {sid: s["name"] for sid, s in ds.stallions.items()}
        self.by_name = {s["name"].upper(): sid for sid, s in ds.stallions.items()}
        self.foaled = {sid: s.get("foaling_year") for sid, s in ds.stallions.items()}
        self.snaps = {}
        for s in ds.snapshots:
            self.snaps.setdefault(s["stallion_id"], []).append(s)
        self.sire = {}       # (sid, year) -> {"e": earnings, "n": earners, "r": rank}
        for r in ds.sire_stats:
            if r["period"].isdigit():
                self.sire[(r["stallion_id"], int(r["period"]))] = {"e": r["earnings"] or 0.0, "n": r["earners"] or 0, "r": r["rank"]}
        self.years = sorted({y for _, y in self.sire})
        top = json.load(open(os.path.join(HERE, "top_earners.json")))
        self.top = {}        # (sid, crop, year) -> (count, earnings)
        for year, v in top["years"].items():
            for item in v["rows"].split(";"):
                name, crop, n, e = item.split("|")
                sid = self.by_name.get(name)
                if sid:
                    self.top[(sid, int(crop), int(year))] = (int(n), float(e))
        self.p = Params()

    # ---- what was knowable at the end of year D
    def fee(self, sid, d):
        f = fee_at(self.snaps.get(sid), d, self.p)
        return f["fee"] if f else None

    def bid_share(self, sid, d):
        """Latest auction bid as a share of that season's listed fee, seasons up to D."""
        listed, bids = {}, {}
        for s in self.snaps.get(sid, []):
            if s.get("fee") is None or s["year"] > d:
                continue
            if (s.get("basis") or "").lower() == "auction":
                bids.setdefault(s["year"], []).append(s["fee"])
            else:
                listed[s["year"]] = s["fee"]
        for y in sorted(bids, reverse=True):
            if y in listed:
                return st.median(bids[y]) / listed[y]
        return None

    def e(self, sid, y):
        return self.sire.get((sid, y), {}).get("e", 0.0)

    def n(self, sid, y):
        return self.sire.get((sid, y), {}).get("n", 0)

    def rank(self, sid, y):
        return self.sire.get((sid, y), {}).get("r")

    def past_hits(self, sid, d, crops_back=3):
        """Top-50 earner foals seen by the end of D, from the last few crops."""
        return sum(c for (s, crop, y), (c, _) in self.top.items() if s == sid and y <= d and crop >= d - crops_back + 1)

    # ---- how the D+2 crop turned out
    def outcome(self, sid, d):
        crop = d + 2
        hits = earn = 0
        for y in (crop, crop + 1):
            c, e = self.top.get((sid, crop, y), (0, 0.0))
            hits += c
            earn += e
        return {"hits": hits, "hit_earn": earn, "sire_e": self.e(sid, crop), "sire_n": self.n(sid, crop)}

    def universe(self, d):
        return [sid for sid in self.names if self.fee(sid, d) is not None]


# --------------------------------------------------------------------------
# ranking rules: each returns a score, higher is better, using data up to D only
# --------------------------------------------------------------------------
def _window(data, sid, d, k=3):
    ys = [y for y in range(d - k + 1, d + 1) if y >= data.years[0]]
    return ys


def r_final(data, sid, d):
    """The rule the app uses (ranker/matcher.py): last year's foal winnings x their trend."""
    last = data.e(sid, d)
    prev = data.e(sid, d - 1) if d - 1 >= data.years[0] else None
    return matcher.score(last, prev) if last > 0 else 0.2 * (prev or 0.0)


def r_record3(data, sid, d):
    """v1 of the app: tier by best leaderboard rank in three years, then total earnings."""
    ys = _window(data, sid, d)
    ranks = [data.rank(sid, y) for y in ys if data.rank(sid, y)]
    tier = 2 if ranks and min(ranks) <= 10 else 1 if ranks else 0
    return tier * 1e9 + sum(data.e(sid, y) for y in ys)


def r_total3(data, sid, d):
    return sum(data.e(sid, y) for y in _window(data, sid, d))


def r_last(data, sid, d):
    return data.e(sid, d)


def r_avg3(data, sid, d):
    """Winnings per money-earning foal: quality rather than volume."""
    ys = _window(data, sid, d)
    n = sum(data.n(sid, y) for y in ys)
    return sum(data.e(sid, y) for y in ys) / n if n >= 3 else 0.0


def r_momentum(data, sid, d):
    """Rising sires: this year's winnings minus the average of the two before."""
    prev = [data.e(sid, y) for y in (d - 1, d - 2) if y >= data.years[0]]
    return data.e(sid, d) - (sum(prev) / len(prev) if prev else 0.0)


def r_hits(data, sid, d):
    """Top-50 foals already produced from the last three crops, then winnings."""
    return data.past_hits(sid, d) * 1e7 + data.e(sid, d)


def r_value(data, sid, d):
    """Winnings per dollar of fee."""
    fee = data.fee(sid, d)
    return r_total3(data, sid, d) / fee if fee else 0.0


def r_young(data, sid, d):
    """Young stallions whose first foals are already winning."""
    born = data.foaled.get(sid) or 0
    young = 1 if born >= d - 8 else 0
    return young * (1e7 + data.e(sid, d)) + (1 - young) * data.e(sid, d) * 0.25


def r_recent_avg(data, sid, d):
    """Blend: last year's winnings, weighted by winnings per earner."""
    n = data.n(sid, d)
    avg = data.e(sid, d) / n if n else 0.0
    return data.e(sid, d) * (0.5 + avg / 10000.0)


def r_fee(data, sid, d):
    """Baseline: just take the dearest stallion you can afford."""
    return data.fee(sid, d) or 0.0


RULES = {"final": r_final, "record3": r_record3, "total3": r_total3, "last": r_last, "avg3": r_avg3, "momentum": r_momentum,
         "hits": r_hits, "value": r_value, "young": r_young, "recent_avg": r_recent_avg, "dearest": r_fee}


# --------------------------------------------------------------------------
# evaluation
# --------------------------------------------------------------------------
def picks(data, rule, d, budget, k=TOP_K):
    pool = [s for s in data.universe(d) if budget is None or data.fee(s, d) <= budget]
    scored = sorted(pool, key=lambda s: (-rule(data, s, d), data.fee(s, d), data.names[s]))
    return scored[:k], pool


def evaluate(data, rule, years, budgets=BUDGETS, k=TOP_K, draws=4000, seed=11):
    rng = random.Random(seed)
    rows = []
    for b in budgets:
        tot = {"hits": 0, "hit_earn": 0.0, "sire_e": 0.0, "fee": 0.0, "n": 0, "with_hit": 0}
        base = {"hits": 0.0, "hit_earn": 0.0, "sire_e": 0.0, "fee": 0.0, "with_hit": 0.0}
        sims = [0.0] * draws
        for d in years:
            chosen, pool = picks(data, rule, d, b, k)
            if len(pool) < k:
                continue
            outs = {s: data.outcome(s, d) for s in pool}
            for s in chosen:
                o = outs[s]
                tot["hits"] += o["hits"]; tot["hit_earn"] += o["hit_earn"]; tot["sire_e"] += o["sire_e"]
                tot["fee"] += data.fee(s, d); tot["n"] += 1; tot["with_hit"] += o["hits"] > 0
            for key in ("hits", "hit_earn", "sire_e"):
                base[key] += k * st.mean(outs[s][key] for s in pool)
            base["with_hit"] += k * st.mean(1.0 if outs[s]["hits"] > 0 else 0.0 for s in pool)
            base["fee"] += k * st.mean(data.fee(s, d) for s in pool)
            for i in range(draws):
                sims[i] += sum(outs[s]["hit_earn"] for s in rng.sample(pool, k))
        if not tot["n"]:
            continue
        beat = sum(1 for x in sims if x < tot["hit_earn"]) / draws
        rows.append({"budget": b, "picks": tot["n"], "hits": tot["hits"], "base_hits": base["hits"],
                     "with_hit": tot["with_hit"] / tot["n"], "base_with_hit": base["with_hit"] / tot["n"],
                     "hit_earn": tot["hit_earn"] / tot["n"], "base_hit_earn": base["hit_earn"] / tot["n"],
                     "sire_e": tot["sire_e"] / tot["n"], "base_sire_e": base["sire_e"] / tot["n"],
                     "fee": tot["fee"] / tot["n"], "base_fee": base["fee"] / tot["n"], "beats_random": beat})
    return rows


def summary_line(name, rows):
    """One number per rule: hit winnings per pick against a random affordable pick, pooled over budgets."""
    got = sum(r["hit_earn"] * r["picks"] for r in rows)
    exp = sum(r["base_hit_earn"] * r["picks"] for r in rows)
    hits = sum(r["hits"] for r in rows)
    base = sum(r["base_hits"] for r in rows)
    wh = sum(r["with_hit"] * r["picks"] for r in rows) / sum(r["picks"] for r in rows)
    return "%-11s hits %3d vs %5.1f expected | picks with a top-50 foal %3.0f%% | winnings per pick $%6.0f vs $%6.0f (x%.1f)" % (
        name, hits, base, 100 * wh, got / sum(r["picks"] for r in rows), exp / sum(r["picks"] for r in rows), got / exp if exp else 0)


def honest_record(data, years, budgets=(1000, 1500, 2000, None), k=TOP_K):
    """Leave one season out: choose the best rule on the other seasons, score it on the one held back.

    This is what the app quotes. Picking the winner and scoring it on the same
    seasons flatters it; this does not.
    """
    def with_hit(rule, d, b):
        chosen, pool = picks(data, rule, d, b, k)
        if len(pool) < k:
            return None, None
        return (sum(1 for s in chosen if data.outcome(s, d)["hits"] > 0),
                k * st.mean(1.0 if data.outcome(s, d)["hits"] > 0 else 0.0 for s in pool))
    table = {n: {(d, b): with_hit(r, d, b) for d in years for b in budgets} for n, r in RULES.items()}
    rows = {b: {"budget": b, "picks": 0, "hit": 0, "base": 0.0} for b in budgets}
    chosen_rules = []
    for test in years:
        train = [d for d in years if d != test]
        best = max(RULES, key=lambda n: sum(table[n][(d, b)][0] or 0 for d in train for b in budgets))
        chosen_rules.append(best)
        for b in budgets:
            got, base = table[best][(test, b)]
            if got is None:
                continue
            rows[b]["picks"] += k; rows[b]["hit"] += got; rows[b]["base"] += base
    out = []
    for b in budgets:
        r = rows[b]
        if r["picks"]:
            r["base"] = r["base"] / r["picks"]; r["share"] = r["hit"] / r["picks"]
            out.append(r)
    in_sample = {str(b): sum(table["final"][(d, b)][0] or 0 for d in years) for b in budgets}
    return {"first_season": years[0] + 1, "last_season": years[-1] + 1, "k": k,
            "method": "leave one season out: rule chosen on the other seasons",
            "rules_chosen": chosen_rules, "final_rule_in_sample_hits": in_sample, "by_budget": out}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="save the honest track record to qa/track_record.json for the app")
    ap.add_argument("--rule", choices=sorted(RULES))
    ap.add_argument("--first", type=int, default=2018, help="first decision year")
    ap.add_argument("--last", type=int, default=2024, help="last decision year")
    a = ap.parse_args()
    data = Data()
    years = list(range(a.first, a.last + 1))
    print("Decision years %d-%d. Stallions with a fee each year: %s" % (
        years[0], years[-1], {d: len(data.universe(d)) for d in years}))
    if not a.rule:
        for name, rule in RULES.items():
            print(summary_line(name, evaluate(data, rule, years)))
        rec = honest_record(data, years)
        print("\nHonest track record (rule chosen without the season it is scored on):")
        for r in rec["by_budget"]:
            print("  budget %-5s %2d of %d picks sired a top-50 foal (%.0f%%) | average affordable stallion %.0f%%" % (
                r["budget"] or "any", r["hit"], r["picks"], 100 * r["share"], 100 * r["base"]))
        if a.write:
            with open(os.path.join(HERE, "track_record.json"), "w") as fh:
                json.dump(rec, fh, indent=1)
            print("Wrote qa/track_record.json")
        return
    rule = RULES[a.rule]
    for r in evaluate(data, rule, years):
        print("budget %-6s picks %2d | hits %2d vs %4.1f | with a top-50 foal %3.0f%% vs %3.0f%% | winnings/pick $%6.0f vs $%6.0f | "
              "fee $%4.0f vs $%4.0f | beats %2.0f%% of random draws" % (
                  r["budget"] or "any", r["picks"], r["hits"], r["base_hits"], 100 * r["with_hit"], 100 * r["base_with_hit"],
                  r["hit_earn"], r["base_hit_earn"], r["fee"], r["base_fee"], 100 * r["beats_random"]))
    print()
    for d in years:
        chosen, pool = picks(data, rule, d, 2000)
        if len(pool) < TOP_K:
            continue
        print("%d (season %d, crop %d), budget $2,000, %d affordable:" % (d, d + 1, d + 2, len(pool)))
        for s in chosen:
            o = data.outcome(s, d)
            print("    %-22s fee $%-5.0f -> top-50 foals %d ($%6.0f), sire winnings that year $%7.0f" % (
                data.names[s], data.fee(s, d), o["hits"], o["hit_earn"], o["sire_e"]))


if __name__ == "__main__":
    main()
