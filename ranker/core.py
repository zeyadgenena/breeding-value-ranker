"""Scoring, stallion effects, value per dollar and the point-in-time backtest.

Standard library only, so the maths runs anywhere Python does.

Vocabulary used throughout
--------------------------
as-of year D   Everything is computed from what was knowable at the end of
               year D. `None` means "everything known today".
score          A foal's halter result as a 0-100 percentile within its own
               foaling-year crop (50 = typical foal of that crop in this
               dataset). Unshown foals count as zero points.
mare quality   0-100. Average of the mare's own halter record (percentile
               among mares) and the average score of her foals by OTHER
               stallions, whichever of the two exist.
effect         How many score points a stallion's foals sit above what their
               crop and their dams predict, shrunk toward zero when he has
               few foals.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# --------------------------------------------------------------------------
# Data containers
# --------------------------------------------------------------------------
@dataclass
class Dataset:
    stallions: Dict[str, dict]   # id -> name, reg, foaling_year, sire, dam, dam_sire
    snapshots: List[dict]        # stallion_id, year, fee (None = private treaty), basis, source, date
    mares: Dict[str, dict]       # id -> name, reg, own_points
    foals: Dict[str, dict]       # id -> name, reg, sire_id, dam_id, year, sex, color
    outcomes: List[dict]         # foal_id, year (None = lifetime total), shows, points,
                                 # placing, class_size, grands, reserves, earnings, sale_price
    truth: Optional[Dict[str, float]] = None   # synthetic data only: the planted effects
    sire_stats: List[dict] = field(default_factory=list)   # stallion_id, period, rank, earners,
                                                           # earnings, cutoff, date, source


@dataclass
class Params:
    maturity_years: int = 3      # a lifetime-only total is trusted at date D only for crops this old
    min_foals: int = 5           # scored foals a stallion needs before he can be ranked
    fee_staleness: int = 2       # how many seasons old a fee may be
    fee_fallback: str = "none"   # "latest" = use today's fee at every date (look-ahead in price)
    fee_basis: str = "listed"    # "listed" = advertised fees only; "auction" = winning bids at
                                 # stallion-service auctions only; "any" = whichever is newest
    top_frac: float = 0.25       # share of the pool taken as "top picks"
    top_k: Optional[int] = None  # or a fixed number of picks
    gestation_lag: int = 2       # rank with data through D -> breed in D+1 -> foal born D+2
    horizon: int = 2             # forward crops: D+2 .. D+1+horizon
    min_forward_foals: int = 3   # forward foals a stallion needs to be evaluated
    random_draws: int = 2000
    default_k: float = 15.0      # shrinkage constant when the data cannot estimate one
    mare_adjust: bool = True
    min_mare_pairs: int = 30     # foals with mare info needed before adjusting for mares
    max_windows: int = 5
    seed: int = 7


UNIFORM_VAR = 100.0 ** 2 / 12.0   # variance of a 0-100 percentile


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def _quantile(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    pos = q * (len(xs) - 1)
    lo, hi = int(math.floor(pos)), int(math.ceil(pos))
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def _midrank_percentiles(pairs):
    """[(value, key)] -> {key: percentile 0-100}; ties share the middle rank."""
    pairs = sorted(pairs, key=lambda t: t[0])
    n, out, i = len(pairs), {}, 0
    while i < n:
        j = i
        while j < n and pairs[j][0] == pairs[i][0]:
            j += 1
        pct = 100.0 * (i + (j - i) / 2.0) / n
        for _, key in pairs[i:j]:
            out[key] = pct
        i = j
    return out


def row_points(o):
    """Step 3: one outcome row -> points.

    Uses AQHA halter points when the row has them. If the row is a single show
    with a placing and a class size instead, it falls back to 'horses beaten'
    (class size minus placing). That stand-in is ours, not an AQHA scale, so
    do not mix the two kinds of row in one dataset.
    """
    if o.get("points") is not None:
        return float(o["points"])
    if o.get("placing") is not None and o.get("class_size") is not None:
        return float(max(0, o["class_size"] - o["placing"]))
    return 0.0


def row_shows(o):
    if o.get("shows") is not None:
        return int(o["shows"])
    return 1 if o.get("placing") is not None else 0


# --------------------------------------------------------------------------
# Step 3: score outcomes, point in time
# --------------------------------------------------------------------------
def foal_totals(ds: Dataset, asof: Optional[int], p: Params, _index=None):
    """Per-foal totals using only rows that existed at the end of `asof`.

    A foal with no outcome rows counts as unshown (zero points), which is only
    right if the foal list came from an all-foals record, not a
    performers-only one.
    """
    if _index is None:
        _index = {}
        for o in ds.outcomes:
            _index.setdefault(o["foal_id"], []).append(o)
    out = {}
    for fid, f in ds.foals.items():
        fy = f.get("year")
        if fy is None or (asof is not None and fy > asof):
            continue
        t = {"points": 0.0, "shows": 0, "grands": 0, "reserves": 0,
             "earnings": 0.0, "sale_price": None, "lifetime_only": False}
        used_lifetime = unknowable = used_dated = False
        for o in _index.get(fid, ()):
            y = o.get("year")
            if y is None:
                if asof is not None and fy > asof - p.maturity_years:
                    unknowable = True   # the total exists today; its value at `asof` does not
                    continue
                used_lifetime = True
            elif asof is not None and y > asof:
                continue
            else:
                used_dated = True
            t["points"] += row_points(o)
            t["shows"] += row_shows(o)
            t["grands"] += int(o.get("grands") or 0)
            t["reserves"] += int(o.get("reserves") or 0)
            t["earnings"] += float(o.get("earnings") or 0.0)
            if o.get("sale_price") is not None and t["sale_price"] is None:
                t["sale_price"] = float(o["sale_price"])
        if unknowable and not (used_lifetime or used_dated):
            continue   # nothing usable about this foal at this date
        t["lifetime_only"] = bool(used_lifetime and asof is not None)
        out[fid] = t
    return out


def cohort_scores(ds: Dataset, totals):
    """0-100 percentile of halter points within each foaling-year crop."""
    by_year = {}
    for fid, t in totals.items():
        by_year.setdefault(ds.foals[fid]["year"], []).append((t["points"], fid))
    scores = {}
    for pairs in by_year.values():
        scores.update(_midrank_percentiles(pairs))
    return scores


# --------------------------------------------------------------------------
# Mare quality
# --------------------------------------------------------------------------
def _mare_index(ds: Dataset, scores):
    own = [(m["own_points"], mid) for mid, m in ds.mares.items()
           if m.get("own_points") is not None]
    own_pct = _midrank_percentiles(own) if own else {}
    produce = {}   # dam -> sire -> [sum of scores, count]
    for fid, sc in scores.items():
        f = ds.foals[fid]
        dam = f.get("dam_id")
        if dam is None:
            continue
        cell = produce.setdefault(dam, {}).setdefault(f.get("sire_id"), [0.0, 0])
        cell[0] += sc
        cell[1] += 1
    return own_pct, produce


def _mare_quality(own_pct, produce, dam_id, sire_id):
    """Mare quality for one mating, never using the foals of the stallion being judged."""
    if dam_id is None:
        return None
    vals = []
    if dam_id in own_pct:
        vals.append(own_pct[dam_id])
    total = count = 0
    for sid, (s, c) in produce.get(dam_id, {}).items():
        if sid != sire_id:
            total += s
            count += c
    if count:
        vals.append(total / count)
    return sum(vals) / len(vals) if vals else None


# --------------------------------------------------------------------------
# Step 4: stallion effect
# --------------------------------------------------------------------------
@dataclass
class Fit:
    asof: Optional[int]
    totals: dict
    scores: dict
    mare_q: dict            # foal -> mare quality or None
    resid: dict             # foal -> score after removing the mare's part
    slope: float            # score points per mare-quality point (within stallions)
    mare_active: bool
    mare_pairs: int
    mare_mean: float
    grand_mean: float
    within_var: float
    between_var: Optional[float]
    k: float
    k_source: str
    sires: Dict[str, dict] = field(default_factory=dict)
    lifetime_only_foals: int = 0

    @property
    def sire_share(self):
        if self.between_var is None:
            return None
        tot = self.between_var + self.within_var
        return self.between_var / tot if tot > 0 else 0.0


def fit_effects(ds: Dataset, asof: Optional[int], p: Params, _index=None) -> Fit:
    totals = foal_totals(ds, asof, p, _index)
    scores = cohort_scores(ds, totals)
    own_pct, produce = _mare_index(ds, scores)

    by_sire, mare_q = {}, {}
    for fid in scores:
        f = ds.foals[fid]
        sid = f.get("sire_id")
        if sid is None or sid not in ds.stallions:
            continue
        mare_q[fid] = _mare_quality(own_pct, produce, f.get("dam_id"), sid)
        by_sire.setdefault(sid, []).append(fid)

    known = [v for v in mare_q.values() if v is not None]
    mare_mean = _mean(known) if known else 50.0

    # Slope of foal score on mare quality, estimated INSIDE each stallion's own
    # foals so that "good stallions get good mares" cannot inflate it.
    sxx = sxy = 0.0
    pairs = 0
    for fids in by_sire.values():
        pts = [(mare_q[f], scores[f]) for f in fids if mare_q[f] is not None]
        if len(pts) < 2:
            continue
        mx, my = _mean(x for x, _ in pts), _mean(y for _, y in pts)
        sxx += sum((x - mx) ** 2 for x, _ in pts)
        sxy += sum((x - mx) * (y - my) for x, y in pts)
        pairs += len(pts)
    slope, active = 0.0, False
    if p.mare_adjust and pairs >= p.min_mare_pairs and sxx > 0:
        slope, active = min(1.5, max(0.0, sxy / sxx)), True

    resid = {}
    for fid, mq in mare_q.items():
        resid[fid] = scores[fid] - slope * ((mare_mean if mq is None else mq) - mare_mean)

    n_total, n_sires = len(resid), len(by_sire)
    grand = _mean(resid.values()) if resid else 50.0

    ssw = ssb = 0.0
    sum_n2 = 0
    sires = {}
    for sid, fids in by_sire.items():
        n = len(fids)
        m = _mean(resid[f] for f in fids)
        ssw += sum((resid[f] - m) ** 2 for f in fids)
        ssb += n * (m - grand) ** 2
        sum_n2 += n * n
        with_mare = [f for f in fids if mare_q[f] is not None]
        sires[sid] = {
            "n": n,
            "mean_score": _mean(scores[f] for f in fids),
            "n_mare": len(with_mare),
            "mean_mare_q": _mean(mare_q[f] for f in with_mare),
            # the plan's literal Step 4: foal average minus mare average
            "foal_minus_mare": (_mean(scores[f] for f in with_mare)
                                - _mean(mare_q[f] for f in with_mare)) if with_mare else None,
            "raw_effect": m - grand,
        }

    # How much of the spread is between stallions rather than between foals?
    between = None
    if n_sires >= 3 and n_total - n_sires >= n_sires:
        within = ssw / (n_total - n_sires)
        n0 = (n_total - sum_n2 / n_total) / (n_sires - 1)
        between = max(0.0, (ssb / (n_sires - 1) - within) / n0) if n0 > 0 else 0.0
        if between > 1e-9 and within > 0:
            k, src = min(200.0, max(1.0, within / between)), "estimated from this data"
        else:
            k, src = 200.0, "no stallion-to-stallion spread detected, so effects are shrunk hard"
    else:
        within = ssw / (n_total - n_sires) if n_total > n_sires else UNIFORM_VAR
        k, src = p.default_k, "default, too little data to estimate"
    if within <= 0:
        within = UNIFORM_VAR

    for s in sires.values():
        n = s["n"]
        s["shrink"] = n / (n + k)
        s["effect"] = s["raw_effect"] * s["shrink"]
        s["raw_se"] = math.sqrt(within / n)
        s["se"] = math.sqrt(within / (n + k))

    return Fit(asof=asof, totals=totals, scores=scores, mare_q=mare_q, resid=resid,
               slope=slope, mare_active=active, mare_pairs=pairs, mare_mean=mare_mean,
               grand_mean=grand, within_var=within, between_var=between, k=k,
               k_source=src, sires=sires,
               lifetime_only_foals=sum(1 for t in totals.values() if t["lifetime_only"]))


# --------------------------------------------------------------------------
# Step 5: value per dollar
# --------------------------------------------------------------------------
def _snapshots_by_stallion(ds):
    idx = {}
    for s in ds.snapshots:
        idx.setdefault(s["stallion_id"], []).append(s)
    return idx


def fee_at(snaps, asof: Optional[int], p: Params):
    """The fee you would pay acting on an as-of-D ranking: the season D+1 fee,
    or the most recent earlier one that is not too stale."""
    best = best_key = None
    for s in snaps or ():
        if s.get("year") is None:
            continue
        # An auction bid and an advertised fee are different prices. Never mix them.
        is_auction = (s.get("basis") or "").strip().lower() == "auction"
        if (p.fee_basis == "listed" and is_auction) or (p.fee_basis == "auction" and not is_auction):
            continue
        if s.get("fee") is None and (is_auction or p.fee_fallback == "latest"):
            continue
        if asof is not None and p.fee_fallback != "latest":
            if s["year"] > asof + 1 or s["year"] < asof + 1 - p.fee_staleness:
                continue
        # Newest season wins; within a season, the most recently observed figure.
        # A row with no dollar fee (private treaty) competes too, so a stallion
        # who has gone to private treaty is not priced at his old fee.
        key = (s["year"], str(s.get("date") or ""))
        if best is None or key > best_key:
            best, best_key = s, key
    return best if best and best.get("fee") is not None else None


def rank_stallions(ds: Dataset, asof: Optional[int], p: Params, fit: Optional[Fit] = None,
                   _snap_index=None):
    """Returns (ranked rows, not-ranked rows, fit)."""
    fit = fit or fit_effects(ds, asof, p)
    snap_index = _snap_index or _snapshots_by_stallion(ds)
    ranked, skipped = [], []
    # "Today" is the newest season anyone in the workbook has a fee for, so a
    # stallion last priced several seasons ago is not ranked at that old price.
    fee_asof = asof
    if asof is None and p.fee_fallback != "latest":
        seasons = [x["year"] for x in ds.snapshots if x.get("year") is not None]
        fee_asof = max(seasons) - 1 if seasons else None
    for sid, st in ds.stallions.items():
        s = fit.sires.get(sid)
        snap = fee_at(snap_index.get(sid), fee_asof, p)
        n = s["n"] if s else 0
        base = {"stallion_id": sid, "name": st.get("name"), "foals": n,
                "fee": snap["fee"] if snap else None,
                "fee_year": snap["year"] if snap else None}
        if snap is None:
            any_snap = snap_index.get(sid)
            base["status"] = "not ranked: no fee on file"
            if any_snap and asof is not None:
                base["status"] = "not ranked: no dollar fee near this date"
            elif any_snap:
                base["status"] = ("not ranked: no current dollar fee (private treaty, or the newest fee "
                                  "is more than %d seasons old)" % p.fee_staleness)
            skipped.append(base)
            continue
        if n < p.min_foals:
            base["status"] = "not ranked: only %d scored foals (need %d)" % (n, p.min_foals)
            skipped.append(base)
            continue
        base.update(s)
        base["value_per_1k"] = s["effect"] / snap["fee"] * 1000.0
        base["status"] = "ranked"
        ranked.append(base)
    # A below-average stallion is never good value, however cheap. Positive
    # effects sort by value per dollar, the rest by effect.
    ranked.sort(key=lambda r: (r["effect"] > 0,
                               r["value_per_1k"] if r["effect"] > 0 else r["effect"]),
                reverse=True)
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
    return ranked, skipped, fit


# --------------------------------------------------------------------------
# Steps 6 and 7: backtest and verdict
# --------------------------------------------------------------------------
MEASURES = ["fwd_score", "fwd_adj", "pct_earners", "mean_sale"]


def _forward(ds, final: Fit, years):
    """Per stallion: foals born in `years`, judged with everything known today."""
    acc = {}
    for fid, sc in final.scores.items():
        f = ds.foals[fid]
        if f["year"] not in years or fid not in final.resid:
            continue
        a = acc.setdefault(f["sire_id"], {"n": 0, "score": 0.0, "adj": 0.0,
                                          "earners": 0, "sales": []})
        t = final.totals[fid]
        a["n"] += 1
        a["score"] += sc
        a["adj"] += final.resid[fid]
        a["earners"] += 1 if t["points"] > 0 else 0
        if t["sale_price"] is not None:
            a["sales"].append(t["sale_price"])
    for a in acc.values():
        a["m_score"] = a["score"] / a["n"]
        a["m_adj"] = a["adj"] / a["n"]
        a["m_earn"] = 100.0 * a["earners"] / a["n"]
    return acc


def _group(ids, by_id, fwd, p):
    ev = [s for s in ids if fwd.get(s, {}).get("n", 0) >= p.min_forward_foals]
    sales = [x for s in ev for x in fwd[s]["sales"]]
    return {
        "stallions": len(ids),
        "evaluated": len(ev),
        "foals": sum(fwd[s]["n"] for s in ev),
        "mean_fee": _mean(by_id[s]["fee"] for s in ids),
        "past_effect": _mean(by_id[s]["effect"] for s in ids),
        "past_mare_q": _mean(by_id[s]["mean_mare_q"] for s in ids
                             if by_id[s].get("mean_mare_q") is not None),
        "fwd_score": _mean(fwd[s]["m_score"] for s in ev),
        "fwd_adj": _mean(fwd[s]["m_adj"] for s in ev),
        "pct_earners": _mean(fwd[s]["m_earn"] for s in ev),
        "mean_sale": _mean(sales),
        "sold": len(sales),
    }


def backtest_window(ds, asof, p, final: Fit, rng, _index=None, _snap_index=None):
    years = set(range(asof + p.gestation_lag, asof + p.gestation_lag + p.horizon))
    fit = fit_effects(ds, asof, p, _index)
    pool, _, _ = rank_stallions(ds, asof, p, fit, _snap_index)
    w = {"asof": asof, "forward_crops": "%d-%d" % (min(years), max(years)),
         "pool": len(pool), "groups": {}, "picks": [], "note": "",
         "lifetime_only_foals": fit.lifetime_only_foals,
         "mare_active": fit.mare_active}
    if len(pool) < 6:
        w["note"] = "pool too small (%d ranked stallions, need 6)" % len(pool)
        return w

    by_id = {r["stallion_id"]: r for r in pool}
    k = p.top_k or max(3, int(round(len(pool) * p.top_frac)))
    k = max(1, min(k, len(pool) // 2))
    picks = [r["stallion_id"] for r in pool[:k]]

    fees = [r["fee"] for r in pool]
    effects = [r["effect"] for r in pool]
    med_fee = _quantile(fees, 0.5)
    lo, hi = _quantile(effects, 0.25), _quantile(effects, 0.75)
    cheap = [r["stallion_id"] for r in pool
             if r["fee"] <= med_fee and lo <= r["effect"] <= hi and r["stallion_id"] not in picks]
    if len(cheap) < 2:
        cheap = [r["stallion_id"] for r in pool
                 if r["fee"] <= med_fee and r["stallion_id"] not in picks]
        w["note"] = "few cheap-and-average stallions, so that group is every cheap non-pick"
    priciest = [r["stallion_id"] for r in sorted(pool, key=lambda r: -r["fee"])[:k]]

    fwd = _forward(ds, final, years)
    w["groups"]["Top value picks"] = _group(picks, by_id, fwd, p)
    w["groups"]["Cheap but average"] = _group(cheap, by_id, fwd, p)
    w["groups"]["Priciest"] = _group(priciest, by_id, fwd, p)
    w["groups"]["Whole pool"] = _group(list(by_id), by_id, fwd, p)

    # Random picks of the same size from the same pool, two ways:
    #   plain        any k stallions
    #   similar fee  for each top pick, a random stallion at about the same
    #                price. This is the fair test of "undervalued": it holds
    #                price constant, and with it whatever comes bundled with
    #                price (better mares, better-funded owners).
    ids = list(by_id)
    partners = {}
    for sid in picks:
        fee = by_id[sid]["fee"]
        near = [o for o in ids if fee / 1.25 <= by_id[o]["fee"] <= fee * 1.25]
        if len(near) < 3:
            near = sorted(ids, key=lambda o: abs(math.log(by_id[o]["fee"] / fee)))[:3]
        partners[sid] = near

    def plain():
        return rng.sample(ids, k)

    def similar_fee():
        chosen = []
        for sid in picks:
            options = [o for o in partners[sid] if o not in chosen] or partners[sid]
            chosen.append(rng.choice(options))
        return chosen

    pk = w["groups"]["Top value picks"]
    for label, key, sampler in (("Random (median)", "random_percentile", plain),
                                ("Random, similar fee (median)", "matched_percentile", similar_fee)):
        draws = {m: [] for m in MEASURES}
        fee_draws = []
        for _ in range(p.random_draws):
            g = _group(sampler(), by_id, fwd, p)
            fee_draws.append(g["mean_fee"])
            for m in MEASURES:
                if g[m] is not None:
                    draws[m].append(g[m])
        row = {"stallions": k, "evaluated": None, "foals": None, "sold": None,
               "mean_fee": _mean(fee_draws), "past_effect": None, "past_mare_q": None}
        for m in MEASURES:
            row[m] = _quantile(draws[m], 0.5) if draws[m] else None
        w["groups"][label] = row
        w[key] = {}
        for m in MEASURES:
            if pk[m] is None or not draws[m]:
                w[key][m] = None
                continue
            below = sum(1 for x in draws[m] if x < pk[m])
            ties = sum(1 for x in draws[m] if x == pk[m])
            w[key][m] = 100.0 * (below + 0.5 * ties) / len(draws[m])

    for r in pool[:k]:
        f = fwd.get(r["stallion_id"], {})
        w["picks"].append({
            "asof": asof, "rank": r["rank"], "stallion_id": r["stallion_id"],
            "name": r["name"], "fee": r["fee"], "foals_then": r["n"],
            "effect_then": r["effect"], "value_per_1k": r["value_per_1k"],
            "forward_foals": f.get("n", 0), "fwd_score": f.get("m_score"),
            "fwd_adj": f.get("m_adj"), "pct_earners": f.get("m_earn"),
        })
    return w


def choose_windows(ds, p):
    """As-of years with fees on file and complete forward crops, latest first,
    spaced so forward crops do not overlap."""
    foal_years = [f["year"] for f in ds.foals.values() if f.get("year") is not None]
    snap_years = [s["year"] for s in ds.snapshots
                  if s.get("year") is not None and s.get("fee") is not None]
    if not foal_years or not snap_years:
        return []
    last = max(foal_years) - p.gestation_lag - p.horizon + 1
    first = min(foal_years) + 2
    if p.fee_fallback != "latest":
        first = max(first, min(snap_years) - 1)
    out, d = [], last
    while d >= first and len(out) < p.max_windows:
        out.append(d)
        d -= p.horizon
    return sorted(out)


def backtest(ds: Dataset, p: Params, dates: Optional[List[int]] = None):
    rng = random.Random(p.seed)
    index = {}
    for o in ds.outcomes:
        index.setdefault(o["foal_id"], []).append(o)
    snap_index = _snapshots_by_stallion(ds)
    final = fit_effects(ds, None, p, index)
    dates = sorted(dates) if dates else choose_windows(ds, p)
    windows = [backtest_window(ds, d, p, final, rng, index, snap_index) for d in dates]
    primary = "fwd_adj" if final.mare_active else "fwd_score"
    return {"windows": windows, "final": final, "primary": primary,
            "verdict": verdict(windows, primary)}


def pass_bar(n_windows):
    """Mean percentile the picks must reach against same-price random picks.

    A random pick lands at a uniformly random percentile (mean 50, sd 28.9),
    so the mean over n independent windows has sd 28.9 / sqrt(n). The bar is
    the one-sided 5 percent point: 77 for 3 windows, 74 for 4, 71 for 5.
    """
    return 50.0 + 1.645 * 28.87 / math.sqrt(n_windows)


def verdict(windows, primary):
    """The pass rule, fixed before looking at any real results.

    PASS needs at least three usable windows and both of:
      1. the top picks beat the cheap-but-average group in more than half of
         the windows, and
      2. averaged over the windows, the top picks sit high enough against
         random picks at a similar fee that chance alone would do it about
         1 time in 20 (see pass_bar).
    Anything else with three or more windows is FAIL.
    """
    usable, wins_cheap, wins_random, pcts = [], 0, 0, []
    per_measure = {m: {"cheap": 0, "random": 0, "n": 0} for m in MEASURES}
    for w in windows:
        g = w.get("groups") or {}
        pk, ch = g.get("Top value picks"), g.get("Cheap but average")
        rd = g.get("Random, similar fee (median)")
        if not pk or not ch or not rd:
            continue
        for m in MEASURES:
            if pk[m] is None or ch[m] is None or rd[m] is None:
                continue
            per_measure[m]["n"] += 1
            per_measure[m]["cheap"] += pk[m] > ch[m]
            per_measure[m]["random"] += pk[m] > rd[m]
        pct = (w.get("matched_percentile") or {}).get(primary)
        if pk[primary] is None or ch[primary] is None or pct is None:
            continue
        usable.append(w["asof"])
        wins_cheap += pk[primary] > ch[primary]
        wins_random += pk[primary] > rd[primary]
        pcts.append(pct)
    n = len(usable)
    mean_pct = _mean(pcts)
    bar = pass_bar(n) if n else None
    if n < 3:
        status = "NOT ENOUGH DATA"
        why = ("Only %d usable time window(s); the plan needs at least three. "
               "No conclusion can be drawn yet." % n)
    else:
        ok_cheap = wins_cheap > n / 2.0
        ok_random = mean_pct >= bar
        status = "PASS" if (ok_cheap and ok_random) else "FAIL"
        why = ("Across %d windows the top picks beat the cheap-but-average group in %d, "
               "and ranked at the %.0fth percentile on average against random picks at a "
               "similar fee (the bar is %.0f)." % (n, wins_cheap, mean_pct, bar))
    return {"status": status, "why": why, "usable_windows": usable,
            "wins_vs_cheap": wins_cheap, "wins_vs_random": wins_random,
            "mean_percentile": mean_pct, "bar": bar,
            "per_measure": per_measure, "primary": primary}


def truth_correlation(ds: Dataset, fit: Fit):
    """Synthetic data only: how well do estimated effects track the planted ones?"""
    if not ds.truth:
        return None
    xs, ys = [], []
    for sid, s in fit.sires.items():
        if sid in ds.truth and s["n"] >= 5:
            xs.append(ds.truth[sid])
            ys.append(s["effect"])
    if len(xs) < 3:
        return None
    mx, my = _mean(xs), _mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy)
