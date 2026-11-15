"""The matcher's ranking rule and its track record.

The rule was chosen by testing ten candidates against the 2019 to 2025 breeding
seasons (see qa/RESULTS.md). It is deliberately simple:

    score = what his foals won in halter last year  x  trend

where trend is last year's winnings over the year before, kept between 0.5 and
2. A stallion whose foals are winning more each year moves up; one whose
winnings are fading moves down. Within a budget, the highest score is the match.
"""
from __future__ import annotations

import json
import os
import statistics as st

from .core import Params, fee_at

TESTED_BUDGETS = (1000, 1500, 2000, None)
TOP_K = 3


def trend(e_last, e_prev, lo=0.5, hi=2.0):
    """How last year's winnings compare with the year before, clipped. None = no earlier list."""
    if e_prev is None:
        return 1.0
    if e_prev <= 0:
        return hi if e_last > 0 else 1.0
    return max(lo, min(hi, e_last / e_prev))


def score(e_last, e_prev):
    return (e_last or 0.0) * trend(e_last or 0.0, e_prev)


class History:
    """Fees, yearly foal winnings and top-50 foals, as they stood at any past year."""

    def __init__(self, ds, top_earners_path=None):
        self.ds, self.p = ds, Params()
        self.names = {sid: s["name"] for sid, s in ds.stallions.items()}
        self.snaps = {}
        for s in ds.snapshots:
            self.snaps.setdefault(s["stallion_id"], []).append(s)
        self.sire = {}
        for r in ds.sire_stats:
            if r["period"].isdigit():
                self.sire[(r["stallion_id"], int(r["period"]))] = r
        self.years = sorted({y for _, y in self.sire})
        self.top = {}          # (stallion, crop, year) -> (top-50 foals, their winnings)
        if top_earners_path and os.path.exists(top_earners_path):
            by_name = {s["name"].upper(): sid for sid, s in ds.stallions.items()}
            with open(top_earners_path) as fh:
                years = json.load(fh)["years"]
            for year, v in years.items():
                for item in v["rows"].split(";"):
                    name, crop, n, e = item.split("|")
                    if name in by_name:
                        self.top[(by_name[name], int(crop), int(year))] = (int(n), float(e))

    def fee(self, sid, d):
        f = fee_at(self.snaps.get(sid), d, self.p)
        return f["fee"] if f else None

    def e(self, sid, y):
        if not self.years or y < self.years[0]:
            return None
        r = self.sire.get((sid, y))
        return (r["earnings"] or 0.0) if r else 0.0

    def n(self, sid, y):
        r = self.sire.get((sid, y))
        return (r["earners"] or 0) if r else 0

    def score(self, sid, d):
        """The rule, using only lists up to year d."""
        last = self.e(sid, d) or 0.0
        if last > 0:
            return score(last, self.e(sid, d - 1))
        return 0.2 * (self.e(sid, d - 1) or 0.0)      # off this year's list: far below anyone on it

    def universe(self, d):
        return [sid for sid in self.names if self.fee(sid, d) is not None]

    def crop_hits(self, sid, d):
        """Top-50 foals from the crop conceived the season after d: as weanlings (d+2) and yearlings (d+3)."""
        crop = d + 2
        return sum(self.top.get((sid, crop, y), (0, 0.0))[0] for y in (crop, crop + 1))

    def picks(self, d, budget, k=TOP_K):
        pool = [s for s in self.universe(d) if budget is None or self.fee(s, d) <= budget]
        return sorted(pool, key=lambda s: (-self.score(s, d), self.fee(s, d), self.names[s]))[:k], pool


def track_record(hist, first=None, last=None, budgets=TESTED_BUDGETS, k=TOP_K):
    """For each budget: how often the top picks went on to sire a top-50 foal, against the average
    affordable stallion. Decision years run from the first leaderboard year to three years ago."""
    if not hist.top or not hist.years:
        return None
    first = first or hist.years[0]
    last = last or hist.years[-1] - 2
    out = []
    for b in budgets:
        n = hit = 0
        base = 0.0
        detail = []
        for d in range(first, last + 1):
            chosen, pool = hist.picks(d, b, k)
            if len(pool) < k:
                continue
            got = [(hist.names[s], hist.fee(s, d), hist.crop_hits(s, d)) for s in chosen]
            n += k
            hit += sum(1 for g in got if g[2] > 0)
            base += k * st.mean(1.0 if hist.crop_hits(s, d) > 0 else 0.0 for s in pool)
            detail.append({"season": d + 1, "picks": [{"name": g[0], "fee": g[1], "top50": g[2]} for g in got]})
        if n:
            out.append({"budget": b, "picks": n, "hit": hit, "share": hit / n, "base": base / n, "seasons": detail})
    return {"first_season": first + 1, "last_season": last + 1, "k": k, "by_budget": out}
