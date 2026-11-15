"""Pack the workbook and the synthetic examples into one self-contained web page.

    python bvr.py export-web data/breeding_data.xlsx

writes docs/index.html, which GitHub Pages serves and which also opens straight
from disk. The page holds its data inline, so there is nothing else to deploy.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os

from . import synth, workbook
from .core import Params, backtest, fee_at, rank_stallions, truth_correlation
from .matcher import History, track_record
from .pricing import PriceModel

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(os.path.dirname(HERE), "web", "template.html")    # the simple matcher
EXPLORE = os.path.join(os.path.dirname(HERE), "web", "explore.html")      # every chart and table
QA = os.path.join(os.path.dirname(HERE), "qa")                             # test data the matcher also shows
POWER = os.path.join(os.path.dirname(HERE), "web", "power.json")

SCENARIOS = [
    ("planted", "Underpriced stallions exist",
     "A made-up world in which stallions really do differ, and fees follow each stallion's own show "
     "record rather than his foals. Some are underpriced, so the backtest ought to pass."),
    ("no_effect", "Stallions do not differ",
     "A made-up world in which every stallion is the same. Any ranking is noise, so the backtest "
     "ought to fail."),
    ("confounded", "Same stallions, better mares",
     "A made-up world in which stallions are the same but the pricier ones get better mares. The "
     "backtest ought to fail, and this is the world most likely to fool it."),
]
SYNTH_SEED = 3   # the same seed as the workbooks in synthetic/


def _round(x, n=2):
    return None if x is None else round(float(x), n)


def _results(ds, p, dates=None):
    bt = backtest(ds, p, dates)
    ranked, skipped, fit = rank_stallions(ds, None, p, bt["final"])
    v, primary = bt["verdict"], bt["primary"]
    windows = []
    for w in bt["windows"]:
        groups = {}
        for name, g in (w.get("groups") or {}).items():
            groups[name] = {"stallions": g["stallions"], "judged": g["evaluated"], "foals": g["foals"],
                            "fee": _round(g["mean_fee"], 0), "score": _round(g["fwd_score"]),
                            "adj": _round(g["fwd_adj"]), "earners": _round(g["pct_earners"], 1),
                            "sale": _round(g["mean_sale"], 0), "mare_q": _round(g.get("past_mare_q"), 1)}
        windows.append({"asof": w["asof"], "crops": w["forward_crops"], "pool": w["pool"],
                        "note": w.get("note") or "", "groups": groups,
                        "pct": _round((w.get("matched_percentile") or {}).get(primary), 1)})
    return {
        "counts": {"stallions": len(ds.stallions), "foals": len(ds.foals),
                   "outcomes": len(ds.outcomes), "mares": len(ds.mares)},
        "primary": primary,
        "verdict": {"status": v["status"], "why": v["why"], "windows": v["usable_windows"],
                    "wins_cheap": v["wins_vs_cheap"], "pct": _round(v["mean_percentile"], 1),
                    "bar": _round(v["bar"], 1)},
        "windows": windows,
        "model": {"grand_mean": _round(fit.grand_mean), "slope": _round(fit.slope, 3),
                  "mare_mean": _round(fit.mare_mean), "mare_active": fit.mare_active,
                  "k": _round(fit.k, 1), "sire_share": _round(fit.sire_share, 4),
                  "truth_corr": _round(truth_correlation(ds, fit), 2)},
        "ranking": [{"rank": r["rank"], "id": r["stallion_id"], "name": r["name"], "fee": r["fee"],
                     "fee_year": r["fee_year"], "foals": r["n"], "mean_score": _round(r["mean_score"], 1),
                     "raw": _round(r["raw_effect"]), "shrink": _round(r["shrink"], 2),
                     "effect": _round(r["effect"]), "se": _round(r["se"]),
                     "value": _round(r["value_per_1k"]),
                     "truth": _round((ds.truth or {}).get(r["stallion_id"]), 3) if ds.truth else None}
                    for r in ranked],
        "not_ranked": len(skipped),
    }


def _median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2.0


def _load(name):
    path = os.path.join(QA, name)
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        return json.load(fh)


BANDS = ("$1,000 or less", "$1,001 to $1,500", "$1,501 to $2,000", "more than $2,000")


def _band(fee):
    return 0 if fee <= 1000 else 1 if fee <= 1500 else 2 if fee <= 2000 else 3


HERE_DATA = os.path.dirname(os.path.abspath(__file__))


def _name(x):
    """One spelling per stallion across the sources (qa/v2data.py keeps the list)."""
    s = " ".join(str(x or "").upper().replace(";", " ").replace("(P)", " ").split())
    return {"ELANTE": "EL ANTE", "ENVINCEBLE": "EVINCEBLE", "LFL ELIGANCE": "LFL ELIGIANCE", "RUMEREZ": "RUMERZ", "SAIL ON SAILER": "SAIL ON SAILOR"}.get(s, s)


def _dollars(v):
    if v >= 1e6:
        return "$%.1f million" % (v / 1e6)
    return "${:,.0f}".format(round(v, -3) if v >= 10000 else v)


def _rec(r, latest, years):
    """Add the sentence the page shows, and whether he was on last year's list."""
    span = "%d to %d" % (years[0], years[-1]) if years else ""
    r["active"] = bool(r["y"] == latest and r["e"] > 0)
    if r["tier"] == "none" or not r["y"]:
        r["text"] = "None of his foals are on the halter leaderboards for %s." % span
    elif r["y"] < latest:
        r["text"] = "His foals were last on the leaderboard in %d, when they won %s." % (r["y"], _dollars(r["e"]))
    else:
        r["text"] = "His foals won %s in halter classes in %d, and %d of them earned money." % (_dollars(r["e"]), r["y"], r["n"])
        if r["prev"] and r["e"] / r["prev"] >= 1.2:
            r["text"] += " That is up from %s the year before." % _dollars(r["prev"])
        elif r["prev"] and r["e"] / r["prev"] <= 0.8:
            r["text"] += " That is down from %s the year before." % _dollars(r["prev"])
    return r


def match_data(ds, p):
    """What the matcher needs per stallion: a price, a track record and a score.

    Price: the current advertised fee, else the last advertised one (flagged as
    old). A stallion whose newest row is private treaty has no price.
    Score: last year's foal winnings times their trend (ranker/matcher.py).
    Badge: "strong" = top ten on a leaderboard in the last three years,
    "some" = on one, "none" = absent.
    """
    hist = History(ds, os.path.join(QA, "top_earners.json"))
    seasons = [s["year"] for s in ds.snapshots if s.get("year") is not None]
    newest_season = max(seasons) if seasons else None
    latest = hist.years[-1] if hist.years else None
    recent = hist.years[-3:]
    stats = {}
    for r in ds.sire_stats:
        stats.setdefault(r["stallion_id"], {})[r["period"]] = r
    shown = (_load("active_foals_2026.json") or {}).get("stallions", {})
    pm = PriceModel.load(QA)
    foal = _load("foal_model.json")               # chance of a top-three futurity finish (qa/foal_model.py)
    fut = (_load("sire_model.json") or {}).get("sires", {})      # what his foals did at the futurity, 2024 to 2026
    top50 = {}                                    # his foals among last year's top 50 money earners
    earners_csv = os.path.join(QA, "leaders", "earners.csv")
    if os.path.exists(earners_csv) and latest:
        import csv as _csv
        with open(earners_csv, newline="") as fh:
            for r in _csv.DictReader(fh):
                if r["period"] == str(latest):
                    top50[_name(r["sire"])] = top50.get(_name(r["sire"]), 0) + 1

    def chance(weights, rank, proven):
        z = weights[0] + weights[1] * (1.0 if rank <= 20 else 0.0) + weights[2] * proven
        return 1.0 / (1.0 + math.exp(-z))
    sold = {}                                   # what each stallion's young foals actually fetched
    ages = {}                                   # how many sales the model saw at each age
    prices = []
    by_band = {}                                # real sales, grouped by the sire's stud fee
    sales_csv = os.path.join(QA, "price_training.csv")
    if os.path.exists(sales_csv):
        import csv
        with open(sales_csv, newline="") as fh:
            for r in csv.DictReader(fh):
                sold.setdefault(r["sire"].upper(), []).append(float(r["price"]))
                ages[r["age_at_sale"]] = ages.get(r["age_at_sale"], 0) + 1
                prices.append(float(r["price"]))
                if r["fee"]:
                    by_band.setdefault(_band(float(r["fee"])), []).append((float(r["price"]), float(r["fee"])))
    out = []
    for sid, st in ds.stallions.items():
        rows = hist.snaps.get(sid, [])
        non = [s for s in rows if (s.get("basis") or "").strip().lower() != "auction" and s.get("year") is not None]
        newest = max(non, key=lambda s: (s["year"], str(s.get("date") or "")), default=None)
        cur = fee_at(rows, newest_season - 1, p) if newest_season else None
        price = None
        if cur:
            price = {"fee": cur["fee"], "year": cur["year"], "current": True}
        elif newest is not None and newest.get("fee") is not None:
            price = {"fee": newest["fee"], "year": newest["year"], "current": False}
        listed = {}
        for s in sorted(non, key=lambda s: (s["year"], str(s.get("date") or ""))):
            if s.get("fee") is not None:
                listed[s["year"]] = s["fee"]
        ratios = [s["fee"] / listed[s["year"]] for s in rows
                  if (s.get("basis") or "").strip().lower() == "auction" and s.get("fee") and listed.get(s["year"])]
        mine = stats.get(sid, {})
        seen = [mine[str(y)] for y in recent if str(y) in mine]
        best = min((r["rank"] for r in seen if r.get("rank")), default=None)
        lastrow = seen[-1] if seen else None
        foals = shown.get(sid)
        sale = None
        if pm and price:
            won = hist.e(sid, latest) or 0.0
            e = pm.expected(won, price["fee"])                 # sold as a yearling
            w = pm.expected(won, price["fee"], age=0)          # sold as a weanling
            sale = {"typical": round(e["typical"], -2), "low": round(e["low"], -2), "high": round(e["high"], -2),
                    "multiple": _round(e["multiple"], 2), "p3": _round(e["p3"], 2), "p10": _round(e["p10"], 3),
                    "weanling": round(w["typical"], -2), "weanling_multiple": _round(w["multiple"], 2),
                    "tested": e["tested"]}
            real = by_band.get(_band(price["fee"]), [])
            if len(real) >= 5:                                 # what foals of stallions at this fee actually fetched
                sale["real"] = {"n": len(real), "median": _median([x[0] for x in real]), "label": BANDS[_band(price["fee"])],
                                "multiple": _round(_median([x[0] / x[1] for x in real]), 2)}
        mine_sold = sold.get((st.get("name") or "").upper(), [])
        hits = top50.get(_name(st.get("name")), 0)
        f = fut.get(_name(st.get("name")))
        odds = None
        now = mine.get(str(latest)) if latest else None                  # his row on last year's leaderboard
        rank_now = now["rank"] if now and now.get("rank") else 99
        if foal:
            odds = {"no": _round(chance(foal["weights_top3"], rank_now, 0), 3), "yes": _round(chance(foal["weights_top3"], rank_now, 1), 3),
                    "win_no": _round(chance(foal["weights_win"], rank_now, 0), 3), "win_yes": _round(chance(foal["weights_win"], rank_now, 1), 3),
                    "money_no": _round(chance(foal["weights_money"], rank_now, 0), 3), "money_yes": _round(chance(foal["weights_money"], rank_now, 1), 3)}
        out.append({
            "id": sid, "name": st.get("name"), "foaled": st.get("foaling_year"), "sire": st.get("sire"),
            "dam": st.get("dam"), "dam_sire": st.get("dam_sire"), "price": price,
            "pt": bool(newest is not None and newest.get("fee") is None),
            "share": _round(_median(ratios), 2), "bids": len(ratios),
            "score": _round((hist.e(sid, latest) or 0.0) + hits / 100.0, 2) if latest else 0,     # last year's foal winnings; top-50 foals break ties
            "hits": hits, "rank": rank_now if rank_now < 99 else None, "odds": odds,
            "fut": {"shown": f["shown"], "starts": f["starts"], "top3": f["top3"], "wins": f["wins"]} if f else None,
            "sale": sale,
            "sold": {"n": len(mine_sold), "median": _median(mine_sold)} if len(mine_sold) >= 3 else None,
            "rec": _rec({"tier": "strong" if best is not None and best <= 10 else "some" if seen else "none",
                         "y": int(lastrow["period"]) if lastrow else None, "e": lastrow["earnings"] if lastrow else 0,
                         "n": lastrow["earners"] if lastrow else 0,
                         "prev": (hist.e(sid, int(lastrow["period"]) - 1) if lastrow else None)}, latest, recent),
            "shown": {"n": foals["shown"], "y": foals["year"], "big": foals["at_least_20000"],
                      "median": foals["median"]} if foals else None})
    dates = sorted({r["date"] for r in ds.sire_stats if r.get("date")})
    record = _load("track_record2.json") or _load("track_record.json")     # the leave-one-season-out figures from qa/backtest2.py
    if not record:
        record = track_record(hist)
        if record:
            for row in record["by_budget"]:
                row.pop("seasons", None)
    n_priced = sum(1 for s in out if s["price"])
    how = ["We track %d Quarter Horse halter stallions and what each has charged for a breeding. %d have a published price." % (len(out), n_priced)]
    if pm:
        how.append("The sale price comes from %d young horses sold at public online auctions, by %d stallions. Return is that price divided by the stud fee. "
                   "It leaves out the cost of raising the foal." % (pm.m["sales"], pm.m["sires"]))
    how.append("A record is prize money won by a stallion's foals in halter classes, from the public QData leaderboards. Strong record: in the top ten sires "
               "in at least one of the last three years. Some record: on the top-50 list.")
    how.append("Chance of a prize winner ranks by what his foals won in halter last year. We tried twelve ways of ranking against eight past seasons. "
               "Several did equally well, and this is the plainest of them.")
    if foal:
        how.append("The top-three chance uses two things that were known before each mare was bred: where the sire stood on the leaderboard, and whether the dam "
                   "had already produced an earner. It was trained on every weanling and yearling shown at the futurity in %d to %d." % (foal["years"][0], foal["years"][-1]))
    how.append("It is a guide, not a guarantee. We cannot see how many foals each stallion has in total, so nothing here is the chance for every foal born.")
    return {"label": "Quarter Horse", "sub": "Halter stallions", "detail": "explore.html", "fee_chips": [1000, 1500, 2000, 2500, 3000],
            "total_chips": [5000, 10000, 20000, 50000], "how": how, "notes": [],
            "years": recent, "latest": latest, "read_on": dates[-1] if dates else "", "stallions": out,
            "record": record, "sales": _load("sales_summary.json"), "mare_facts": _load("mare_facts.json"),
            "foal": {"class_size": foal.get("typical_class_size", 21), "proven_at": 10000, "money_at": int(round(foal["money_cutoff"], -3)),
                     "money_rate": foal["money_rate"], "money_forward": foal["money_score"]["forward"],
                     "worth": _load("futurity_worth.json"), "proven_rate": foal["dam_rates"]["proven"], "other_rate": foal["dam_rates"]["other"],
                     "foals": foal["foals"], "sires": foal["sires"], "years": foal["years"], "base": foal["base_rate"], "forward": foal["kept_round"]["forward"],
                     "split": foal["forward_split"], "rounds": len(foal["scorecard"]), "combinations": (foal.get("search") or {}).get("combinations"),
                     "scorecard": [{"name": r["round"].split(" ", 1)[1].replace(" (the one kept)", ""), "forward": round(r["forward"], 2), "each_year": round(r["each_year"], 2),
                                    "kept": r["round"] == foal["kept"]} for r in foal["scorecard"]]} if foal else None, "pricing": dict(pm.summary(), weanlings=ages.get("0", 0), yearlings=ages.get("1", 0),
                            two_year_olds=ages.get("2", 0), top=max(prices, default=0),
                            at_least_10000=sum(1 for x in prices if x >= 10000),
                            at_least_20000=sum(1 for x in prices if x >= 20000)) if pm else None}


def build_data(workbook_path, params=None, dates=None):
    p = params or Params()
    ds, review, info = workbook.load(workbook_path)
    fees = {}
    for s in ds.snapshots:
        fees.setdefault(s["stallion_id"], []).append({
            "d": s.get("date") or "", "y": s["year"], "fee": s["fee"],
            "basis": (s.get("basis") or "listed").strip().lower(), "src": s.get("source") or "",
            "note": s.get("note") or "", "chute": s.get("chute") or ""})
    stallions = []
    for sid, st in ds.stallions.items():
        rows = sorted(fees.get(sid, []), key=lambda r: (r["y"], r["d"]))
        stallions.append({"id": sid, "name": st.get("name"), "reg": st.get("reg"),
                          "foaled": st.get("foaling_year"), "sire": st.get("sire"), "dam": st.get("dam"),
                          "dam_sire": st.get("dam_sire"), "color": st.get("color"),
                          "notes": st.get("notes") or "", "fees": rows})
    real = _results(ds, p, dates)
    real["review"] = len(review)
    real["warnings"] = info.get("warnings", [])

    synthetic = []
    for key, title, blurb in SCENARIOS:
        sds = synth.generate(key, seed=SYNTH_SEED)
        res = _results(sds, p)
        res.update({"key": key, "title": title, "blurb": blurb})
        synthetic.append(res)

    power = json.load(open(POWER)) if os.path.exists(POWER) else None
    return {"generated": dt.date.today().isoformat(), "source": os.path.basename(str(workbook_path)),
            "fee_staleness": p.fee_staleness, "stallions": stallions, "real": real,
            "synthetic": synthetic, "power": power, "match": match_data(ds, p)}


def export(workbook_path, out_path, repo_url="", params=None, dates=None):
    data = build_data(workbook_path, params, dates)
    data["repo"] = repo_url
    marker = "/*__BVR_DATA__*/"
    out_dir = os.path.dirname(out_path) or "."
    os.makedirs(out_dir, exist_ok=True)

    def write(template, target, payload):
        blob = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
        html = open(template, encoding="utf-8").read()
        if marker not in html:
            raise SystemExit("%s has lost its data marker %s" % (template, marker))
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(html.replace(marker, "window.BVR=" + blob + ";"))
        return os.path.getsize(target)

    # the front page carries only what the matcher shows; the detailed page carries everything
    breeds = {"qh": data["match"]}
    try:
        from . import arabian
        arab = arabian.match_data(os.path.join(os.path.dirname(HERE_DATA), "data", "arabian"))
        if arab:
            breeds["arabian"] = arab
    except FileNotFoundError:
        pass
    front = {"generated": data["generated"], "repo": repo_url, "breeds": breeds}
    size = write(TEMPLATE, out_path, front)
    write(EXPLORE, os.path.join(out_dir, "explore.html"), data)
    return data, size
