"""The Arabian side of the matcher: a first version built from public halter results.

Data lives in data/arabian/ (see SOURCES.md there):
    stallions.csv        stallions at stud in North America
    fees.csv             advertised fees, and what breedings sold for at futurity auctions
    results_classes.csv  whole classes: every horse shown, its sire and dam and its place
    results.csv          one training barn's list of its own wins (one-sided, used only as a footnote)
    sales.csv            public sale prices

Much thinner than the Quarter Horse data: two seasons of one show circuit.
"""
from __future__ import annotations

import csv
import json
import os
import re
import statistics as st

ALIASES = {"IBN FARID": "IBN FARID UAE"}


def _rows(folder, name):
    path = os.path.join(folder, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8", errors="replace") as fh:
        return list(csv.DictReader(fh))


def norm(s):
    s = " ".join(str(s or "").upper().replace("*", " ").replace(".", "").split())
    return ALIASES.get(s, s)


def price_of(rows, latest_season):
    """Advertised fee if there is one, else what a breeding to him sold for at a futurity auction."""
    listed = [(int(r["season_year"]), float(r["fee_usd"])) for r in rows if r["basis"] == "listed" and r["fee_usd"] and r["season_year"].isdigit()]
    # opening bids and bids caught mid-auction are not prices: a breeding that opened at $1,000 may have sold for far more
    final = [(int(r["season_year"]), float(r["fee_usd"])) for r in rows
             if r["basis"] == "auction" and r["fee_usd"] and r["season_year"].isdigit()
             and "NOT FINAL" not in r["fee_note"].upper() and "PRELIMINARY" not in r["fee_note"].upper()]
    auction = None
    if final:
        y = max(f[0] for f in final)
        auction = {"fee": st.median(f[1] for f in final if f[0] == y), "year": y}
    if listed:
        y = max(l[0] for l in listed)
        fee = st.median(l[1] for l in listed if l[0] == y)
        return {"fee": fee, "year": y, "current": y >= latest_season - 1, "basis": "listed"}, auction
    if auction:
        return {"fee": auction["fee"], "year": auction["year"], "current": auction["year"] >= latest_season - 1, "basis": "auction"}, None
    return None, None


def foal_years(classes):
    """One row per horse per year from the whole-class results: its average finish in the classes it was shown in.

    A finish is a percentile of the class: 100 = won, 50 = middle. Championship rounds are kept apart, because only
    the top horses from each class go through to them."""
    out = {}
    for r in classes:
        if r.get("source_kind") != "full_class" or not r["year"].isdigit() or not r["sire"]:
            continue
        place = int(r["placing"]) if r["placing"].isdigit() else None
        n = int(r["entries_in_class"]) if r.get("entries_in_class", "").isdigit() else None
        k = (norm(r["horse"]), int(r["year"]))
        f = out.setdefault(k, {"horse": k[0], "year": k[1], "sire": norm(r["sire"]), "dam": norm(r["dam"]), "age": r.get("age_class", ""), "pcts": [], "top3": 0, "medal": 0, "starts": 0})
        if "champion" in r["class_name"].lower():
            if place and place <= 3:
                f["medal"] = 1
            continue
        if place and n:
            f["pcts"].append(100.0 * (1.0 - (place - 0.5) / max(n, place)))
            f["starts"] += 1
            if place <= 3:
                f["top3"] = 1
    return [dict(f, pct=st.mean(f["pcts"])) for f in out.values() if f["pcts"]]


def sire_table(foals, k=6.0):
    by = {}
    for f in foals:
        by.setdefault(f["sire"], []).append(f)
    out = {}
    for s, v in by.items():
        horses = {f["horse"] for f in v}
        mean = st.mean(f["pct"] for f in v)
        out[s] = {"shown": len(horses), "starts": sum(f["starts"] for f in v), "top3": len({f["horse"] for f in v if f["top3"]}),
                  "medal": len({f["horse"] for f in v if f["medal"]}), "avg": mean, "score": (len(v) * mean + k * 50.0) / (len(v) + k),
                  "years": sorted({f["year"] for f in v})}
    return out


def carry_over(foals):
    """Season by season: rank sires on their foals up to one year, then see who sires the NEW top-three foals the next year.

    Returns the pooled result over every pair of years with enough horses, and each pair."""
    years = sorted({f["year"] for f in foals})
    pairs = []
    for y in years[:-1]:
        past = sire_table([f for f in foals if f["year"] <= y and f["year"] >= y - 2])       # the three seasons up to y
        seen = {f["horse"] for f in foals if f["year"] <= y}
        nxt = [f for f in foals if f["year"] == y + 1 and f["horse"] not in seen]
        if len(past) < 12 or len(nxt) < 30:
            continue
        later = {}
        for f in nxt:
            d = later.setdefault(f["sire"], [0, 0])
            d[0] += 1
            d[1] += f["top3"]
        order = sorted(past, key=lambda s: (-past[s]["top3"], -past[s]["shown"]))
        third = max(1, len(order) // 3)
        top, rest = order[:third], order[third:]
        total = sum(v[1] for v in later.values())
        pairs.append({"from": y, "to": y + 1, "sires": len(past), "new_foals": len(nxt), "top_third": third, "top3_total": total,
                      "top3_by_top": sum(later.get(s, [0, 0])[1] for s in top),
                      "top_again": sum(1 for s in top if later.get(s, [0, 0])[1] > 0), "rest": len(rest),
                      "rest_again": sum(1 for s in rest if later.get(s, [0, 0])[1] > 0)})
    if not pairs:
        return None
    tot = sum(p["top3_total"] for p in pairs)
    return {"from": pairs[0]["from"], "to": pairs[-1]["to"], "seasons": len(pairs), "top_third": sum(p["top_third"] for p in pairs),
            "top_share_of_top3": (sum(p["top3_by_top"] for p in pairs) / tot) if tot else None,
            "top_placed_again": sum(p["top_again"] for p in pairs) / sum(p["top_third"] for p in pairs),
            "rest_placed_again": (sum(p["rest_again"] for p in pairs) / sum(p["rest"] for p in pairs)) if sum(p["rest"] for p in pairs) else 0.0, "pairs": pairs}


def match_data(folder):
    stallions = _rows(folder, "stallions.csv")
    fees = _rows(folder, "fees.csv")
    if not stallions or not fees:
        raise FileNotFoundError(folder)
    classes = _rows(folder, "results_classes.csv")
    barn = _rows(folder, "results.csv")
    sales = _rows(folder, "sales.csv")
    by_fee = {}
    for r in fees:
        by_fee.setdefault(norm(r["stallion"]), []).append(r)
    latest_season = max(int(r["season_year"]) for r in fees if r["season_year"].isdigit())
    foals = foal_years(classes)
    table = sire_table(foals)
    years = sorted({f["year"] for f in foals})
    shows = sorted({r["show"] for r in classes if r.get("source_kind") == "full_class"})
    barn_wins = {}
    for r in barn:
        d = barn_wins.setdefault(norm(r["sire"]), {"n": 0, "years": set()})
        d["n"] += 1
        if r["year"].isdigit():
            d["years"].add(int(r["year"]))
    rank = sorted(table, key=lambda s: (-table[s]["top3"], -table[s]["score"]))
    strong = set(rank[:10])
    span = "%d to %d" % (years[0], years[-1]) if years else ""
    info = {norm(s["stallion"]): s for s in stallions}
    out, seen = [], set()
    for name in list(info) + [s for s in table if s not in info]:      # sires of shown foals count even when no stud listing was found
        if not name or name in seen:
            continue
        seen.add(name)
        srow = info.get(name, {})
        price, auction = price_of(by_fee.get(name, []), latest_season)
        d = table.get(name)
        bw = barn_wins.get(name)
        if d:
            text = "%d of his foals were shown in the classes we could read, %s. %s Their average finish was %d, where 50 is the middle of the class." % (
                d["shown"], span, "%d finished in the top three of a class." % d["top3"] if d["top3"] else "None finished in the top three of a class.", round(d["avg"]))
            if d["shown"] == 1:
                text = text.replace("1 of his foals were shown", "One of his foals was shown").replace("Their average finish", "Its average finish")
            tiles = [["Foals shown", str(d["shown"]), span], ["Finished in a top three", str(d["top3"]), "of the %d shown" % d["shown"]],
                     ["Average finish", str(round(d["avg"])), "50 is the middle of the class"]]
        else:
            text = "None of his foals appear in the classes we could read. He may still have winners at shows we could not."
            tiles = []
        extra = []
        if bw and bw["years"]:
            extra.append("A training barn's own list of wins also credits his foals with %d placings at U.S. shows, %d to %d. That list is one-sided, so it does not count in the ranking."
                         % (bw["n"], min(bw["years"]), max(bw["years"])))
        if auction:
            extra.append("A breeding to him also sold for %s at a %d futurity auction. Those usually sell below the advertised fee." % ("${:,.0f}".format(auction["fee"]), auction["year"]))
        elif price and price["basis"] == "auction":
            extra.append("The price is what a breeding to him sold for at a futurity auction, not his advertised fee, which is usually higher.")
        out.append({"id": re.sub(r"[^A-Z0-9]+", "-", name), "name": name, "foaled": int(srow["foaled"]) if str(srow.get("foaled", "")).isdigit() else None,
                    "sire": norm(srow.get("sire")), "dam": norm(srow.get("dam")), "dam_sire": "", "price": price, "pt": False,
                    "score": round(d["top3"] + d["score"] / 1000.0, 4) if d else 0.0,
                    "stat": ("%d of %d" % (d["top3"], d["shown"])) if d else "none shown",
                    "rec": {"tier": "strong" if d and name in strong and d["top3"] > 0 else "some" if d else "none", "text": text, "active": bool(d and years and years[-1] in d["years"])},
                    "tiles": tiles, "note": " ".join(extra) or None, "sale": None, "odds": None, "hits": None, "rank": None, "fut": None, "sold": None, "shown": None})
    priced = [s for s in out if s["price"]]
    with_rec = [s for s in priced if s["rec"]["tier"] != "none"]
    prices = sorted(float(r["price_usd"]) for r in sales if r.get("price_usd") and r.get("sold", "Y") != "N" and r.get("lot_kind", "horse") in ("horse", ""))
    check = carry_over(foals)
    model = None
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(folder))), "qa", "arabian_model.json")
    if os.path.exists(path):
        with open(path) as fh:
            model = json.load(fh)
    notes = ["This is a first version for Arabians. It ranks on %d horses shown in whole classes at %d shows, %s: every horse in the class, not only the winners."
             % (len({f["horse"] for f in foals}), len(shows), span),
             "It is narrow. The shows are the international-style circuit in North America (GCAT Americas and the Emirates Global Cup). "
             "U.S. Nationals, Canadian Nationals, Scottsdale's own classes and the regional shows are not in it, because their results could not be collected within their sites' rules.",
             "%d of the %d stallions with a price have a foal in those classes. The rest are listed by price only." % (len(with_rec), len(priced))]
    if check and check["top_share_of_top3"] is not None:
        notes.append("Tested on %s: each year the top third of sires by top-three foals so far went on to sire %.0f%% of the next year's top-three finishers among new foals. "
                     "%.0f%% of those sires had one, against %.0f%% of the other sires." % (
                         ("%d season%s, %d to %d" % (check["seasons"], "" if check["seasons"] == 1 else "s", check["from"], check["to"])), 100 * check["top_share_of_top3"],
                         100 * check["top_placed_again"], 100 * check["rest_placed_again"]))
    else:
        notes.append("It has not been tested against past seasons: two seasons is not enough history.")
    notes.append("Many prices are what a breeding sold for at a futurity auction. Those usually sell below the advertised stud fee. Opening bids are left out.")
    paid = [(r["placing"].strip().lower(), float(r["prize_usd"]), r["year"]) for r in barn if r.get("prize_usd")]
    champ = [p[1] for p in paid if p[0] in ("champion", "1")]
    ten = [p[1] for p in paid if p[0] not in ("champion", "1", "reserve", "2")]
    if champ and ten:
        d = lambda v: "${:,.0f}".format(round(v, -2))
        notes.append("Prize money is small next to Quarter Horse halter. The U.S. Nationals futurity paid its champion %s to %s and a top ten %s to %s (%s to %s). "
                     "For Arabians the money is in the sale, and the best sales are private." % (d(min(champ)), d(max(champ)), d(min(ten)), d(max(ten)), min(p[2] for p in paid), max(p[2] for p in paid)))
    g = (model or {}).get("groups")
    if g and g.get("all_recent", {}).get("n"):
        a, y = g["all_recent"], g["young"]
        d = lambda v: "${:,.0f}".format(round(v, -2))
        best = model.get("price_best")
        notes.append("Sale prices: %d Arabians sold at public online auction, 2015 to 2022, for a typical %s (middle half %s to %s). The %d aged three or under made a typical %s. "
                     "%d of the %d reached $20,000." % (a["n"], d(a["median"]), d(a["q1"]), d(a["q3"]), y["n"], d(y["median"]), g["over_20000"], a["n"]))
        if best:
            notes.append("Nothing we tried says which horse will be one of those. The best of %d versions of a price model explains %.0f%% of the difference between sales, "
                         "so the page gives no sale estimate per stallion." % (model["price_versions"], max(0.0, 100 * best["explained"])))
    elif prices:
        notes.append("We found %d public sale prices for Arabian horses, too few to estimate what a foal sells for. Their typical price was %s." % (len(prices), "${:,.0f}".format(st.median(prices))))
    notes.append("A foal's market depends on its papers. If the mare is not a registered purebred, a foal by a registered purebred stallion can usually be registered as a Half-Arabian. "
                 "Check with the Arabian Horse Association before you breed.")
    how = ["We list %d Arabian stallions. %d have a price." % (len(out), len(priced)),
           "The price is the advertised stud fee where we found one. Otherwise it is what a breeding to him sold for at a futurity auction.",
           "A record counts his foals shown in whole classes at %d shows in %s, and how many finished in the top three of a class. Stallions are ranked by that count, then by their foals' average finish."
           % (len(shows), span),
           "Strong record: one of the ten best by that count. Some record: at least one foal shown.",
           "It is a shortlist to check by hand, not a forecast."]
    return {"label": "Arabian", "sub": "Halter stallions, first version", "detail": None, "fee_chips": [1000, 2500, 5000, 7500, 10000],
            "total_chips": [10000, 25000, 50000, 100000], "stat_label": "Top three, of shown", "fee_label": "Price",
            "win_heading": "Strongest known foal record in your budget",
            "intro": "First version for Arabians: two seasons of one show circuit. Treat the ranking as a list to check by hand. The Quarter Horse side has far more data behind it.",
            "how": how, "notes": notes, "stallions": out, "record": None, "sales": None, "pricing": None, "foal": None,
            "summary": {"stallions": len(out), "priced": len(priced), "with_record": len(with_rec), "horses_shown": len({f["horse"] for f in foals}), "sires_shown": len(table),
                        "shows": shows, "years": [years[0], years[-1]] if years else [], "sales": len(prices), "check": check}}
