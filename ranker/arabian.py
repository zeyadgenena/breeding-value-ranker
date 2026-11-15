"""The Arabian side of the matcher: a first version built from public halter results.

Data lives in data/arabian/ (see SOURCES.md there):
    stallions.csv   stallions at stud in North America
    fees.csv        advertised fees, and what breedings sold for at futurity auctions
    results.csv     halter placings at major shows, with each horse's sire and dam
    sales.csv       the few public sale prices found

Much thinner than the Quarter Horse data. There is no leaderboard of prize money
and no list of every horse shown, so the record here is a count of placings.
"""
from __future__ import annotations

import csv
import os
import re
import statistics as st

POINTS = {"champion": 3, "gold": 3, "1": 3, "reserve": 2, "silver": 2, "2": 2}      # anything else that placed counts 1


def _rows(folder, name):
    path = os.path.join(folder, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8", errors="replace") as fh:
        return list(csv.DictReader(fh))


def norm(s):
    return " ".join(str(s or "").upper().replace("*", " ").split())


def _weight(year, latest):
    age = latest - year
    return 1.0 if age <= 3 else 0.6 if age <= 6 else 0.3


def price_of(rows, latest_season):
    """Advertised fee if there is one, else what a breeding to him sold for at a futurity auction."""
    listed = [(int(r["season_year"]), float(r["fee_usd"])) for r in rows if r["basis"] == "listed" and r["fee_usd"] and r["season_year"].isdigit()]
    # opening bids and bids caught mid-auction are not prices: a breeding that opened at $1,000 may have sold for far more
    final = [(int(r["season_year"]), float(r["fee_usd"]), False) for r in rows
             if r["basis"] == "auction" and r["fee_usd"] and r["season_year"].isdigit()
             and "NOT FINAL" not in r["fee_note"].upper() and "PRELIMINARY" not in r["fee_note"].upper()]
    auction = None
    if final:
        y = max(f[0] for f in final)
        same = [f for f in final if f[0] == y]
        firm = [f[1] for f in same if not f[2]] or [f[1] for f in same]
        auction = {"fee": st.median(firm), "year": y, "floor": all(f[2] for f in same)}
    if listed:
        y = max(l[0] for l in listed)
        fee = st.median(l[1] for l in listed if l[0] == y)
        return {"fee": fee, "year": y, "current": y >= latest_season - 1, "basis": "listed"}, auction
    if auction:
        return {"fee": auction["fee"], "year": auction["year"], "current": auction["year"] >= latest_season - 1, "basis": "auction", "floor": auction["floor"]}, None
    return None, None


def sire_records(results):
    """Per sire: points by year, the foals that placed, titles."""
    out = {}
    for r in results:
        sire = norm(r["sire"])
        if not sire or not r["year"].isdigit():
            continue
        p = POINTS.get(r["placing"].strip().lower(), 1)
        d = out.setdefault(sire, {"points": {}, "foals": set(), "titles": 0, "rows": 0, "latest": (0, "")})
        y = int(r["year"])
        d["points"][y] = d["points"].get(y, 0) + p
        d["foals"].add(norm(r["horse"]))
        d["titles"] += 1 if p >= 2 else 0
        d["rows"] += 1
        if y > d["latest"][0]:
            d["latest"] = (y, r["show"])
    return out


def carry_over(results, split):
    """Do the sires that placed foals up to `split` keep placing them afterwards? Returns the rank link and the group sizes."""
    rec = sire_records(results)
    xs, ys = [], []
    for s, d in rec.items():
        a = sum(p for y, p in d["points"].items() if y <= split)
        b = sum(p for y, p in d["points"].items() if y > split)
        if a > 0:
            xs.append(a)
            ys.append(b)
    if len(xs) < 8:
        return None

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
    rx, ry = ranks(xs), ranks(ys)
    mx, my = st.mean(rx), st.mean(ry)
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    link = sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / den if den else None
    order = sorted(range(len(xs)), key=lambda i: -xs[i])
    third = max(1, len(order) // 3)
    top = [ys[i] for i in order[:third]]
    rest = [ys[i] for i in order[third:]]
    return {"sires": len(xs), "link": link, "split": split, "top_third_kept": sum(1 for v in top if v > 0) / len(top), "rest_kept": sum(1 for v in rest if v > 0) / len(rest)}


def match_data(folder):
    stallions = _rows(folder, "stallions.csv")
    fees = _rows(folder, "fees.csv")
    results = _rows(folder, "results.csv")
    sales = _rows(folder, "sales.csv")
    if not stallions or not fees:
        raise FileNotFoundError(folder)
    by_fee = {}
    for r in fees:
        by_fee.setdefault(norm(r["stallion"]), []).append(r)
    seasons = [int(r["season_year"]) for r in fees if r["season_year"].isdigit()]
    latest_season = max(seasons)
    rec = sire_records(results)
    years = sorted({int(r["year"]) for r in results if r["year"].isdigit()})
    latest = years[-1] if years else latest_season
    shows = sorted({r["show"] for r in results})
    scores = {s: sum(p * _weight(y, latest) for y, p in d["points"].items()) for s, d in rec.items()}
    cut = sorted(scores.values(), reverse=True)[min(9, len(scores) - 1)] if scores else 0
    out, seen = [], set()
    for srow in stallions:
        name = norm(srow["stallion"])
        if not name or name in seen:
            continue
        seen.add(name)
        price, auction = price_of(by_fee.get(name, []), latest_season)
        d = rec.get(name)
        score = scores.get(name, 0.0)
        if d:
            n = len(d["foals"])
            text = "%d of his foals placed in halter at the shows we read, %d to %d. %s The latest was in %d (%s)." % (
                n, min(d["points"]), max(d["points"]), ("%d of the placings were a champion or reserve title." % d["titles"]) if d["titles"] else "None was a champion or reserve title.",
                d["latest"][0], d["latest"][1])
            if n == 1:
                text = text.replace("1 of his foals placed", "One of his foals placed")
            tiles = [["Foals placed at major shows", str(n), "%d to %d" % (min(d["points"]), max(d["points"]))],
                     ["Champion or reserve titles", str(d["titles"]), "of %d placings" % d["rows"]],
                     ["Latest placing", str(d["latest"][0]), d["latest"][1]]]
        else:
            text = "None of his foals appear in the halter results we could read. He may still have winners at shows we could not."
            tiles = []
        note = None
        if auction:
            note = "A breeding to him also sold for %s%s at a %d futurity auction. Those usually sell below the advertised fee." % (
                "at least " if auction["floor"] else "", "${:,.0f}".format(auction["fee"]), auction["year"])
        elif price and price["basis"] == "auction":
            note = "This is what a breeding to him sold for at a futurity auction%s, not his advertised fee, which is usually higher." % (
                " (an opening bid, so the final price may have been higher)" if price.get("floor") else "")
        out.append({"id": re.sub(r"[^A-Z0-9]+", "-", name), "name": name, "foaled": int(srow["foaled"]) if srow.get("foaled", "").isdigit() else None,
                    "sire": norm(srow.get("sire")), "dam": norm(srow.get("dam")), "dam_sire": "", "price": price, "pt": False,
                    "score": round(score, 2), "stat": (str(len(d["foals"])) + " placed") if d else "none",
                    "rec": {"tier": "strong" if d and score >= cut and score > 0 else "some" if d else "none", "text": text, "active": bool(d and d["latest"][0] >= latest - 1)},
                    "tiles": tiles, "note": note, "sale": None, "odds": None, "hits": None, "fut": None, "sold": None, "shown": None})
    priced = [s for s in out if s["price"]]
    with_rec = [s for s in priced if s["rec"]["tier"] != "none"]
    prices = [float(r["price_usd"]) for r in sales if r.get("price_usd") and r.get("sold", "Y") != "N"]
    check = carry_over(results, years[len(years) // 2 - 1]) if len(years) >= 4 else None
    kinds = {r.get("source_kind", "") for r in results}
    one_sided = not ({"full_class"} & kinds)
    notes = ["This is a first version for Arabians. It ranks on %d halter placings at %d shows, %d to %d." % (len(results), len(shows), years[0], years[-1])]
    if one_sided:
        notes.append("The placings are one-sided. They come from one training barn's published list of its own wins, so they favour stallions whose foals that barn showed, "
                     "and they leave out every horse that did not place. A stallion with no placing here may have many winners elsewhere.")
    notes.append("%d of the %d stallions with a price have a foal in those results. The rest are ranked by price only." % (len(with_rec), len(priced)))
    notes.append("Many prices are what a breeding sold for at a futurity auction. Those usually sell below the advertised stud fee. Opening bids are left out.")
    if check and check["link"] is not None and not one_sided:
        notes.append("One check so far: of the stallions with placings up to %d, the top third by record went on to place more foals %.0f%% of the time, against %.0f%% for the rest (%d stallions)."
                     % (check["split"], 100 * check["top_third_kept"], 100 * check["rest_kept"], check["sires"]))
    else:
        notes.append("It has not been tested against past seasons. The results are too one-sided for a fair test.")
    notes.append("There is no list of every horse shown, so we cannot give a chance per foal as we do for Quarter Horses.")
    paid = [(r["placing"].strip().lower(), float(r["prize_usd"]), r["year"]) for r in results if r.get("prize_usd")]
    champ = [p[1] for p in paid if p[0] in ("champion", "1")]
    ten = [p[1] for p in paid if p[0] not in ("champion", "1", "reserve", "2")]
    if champ and ten:
        d = lambda v: "${:,.0f}".format(round(v, -2))
        notes.append("Prize money is small next to Quarter Horse halter. The U.S. Nationals futurity paid its champion %s to %s and a top ten %s to %s (%s to %s). "
                     "For Arabians the money is in the sale, and the best sales are private." % (d(min(champ)), d(max(champ)), d(min(ten)), d(max(ten)), min(p[2] for p in paid), max(p[2] for p in paid)))
    if prices:
        notes.append("We found %d public sale prices for Arabians, too few to estimate what a foal sells for. Their typical price was %s." % (len(prices), "${:,.0f}".format(st.median(prices))))
    notes.append("A foal's market depends on its papers. If the mare is not a registered purebred, a foal by a registered purebred stallion can usually be registered as a Half-Arabian. "
                 "Check with the Arabian Horse Association before you breed.")
    how = ["We list %d Arabian stallions at stud in North America. %d have a price." % (len(out), len(priced)),
           "The price is the advertised stud fee where we found one. Otherwise it is what a breeding to him sold for at a futurity auction.",
           "A record is a count of his foals' halter placings at %s. A champion counts 3, a reserve 2, any other placing 1, and recent years count most."
           % (", ".join(shows[:-1]) + " and " + shows[-1] if len(shows) > 1 else (shows[0] if shows else "major shows")),
           "Strong record: one of the ten best records. Some record: at least one foal placed.",
           "It is a shortlist to check by hand, not a forecast."]
    return {"label": "Arabian", "sub": "Halter stallions, first version", "detail": None, "fee_chips": [1000, 2500, 5000, 7500, 10000],
            "total_chips": [10000, 25000, 50000, 100000], "stat_label": "Foals placed", "fee_label": "Price",
            "win_heading": "Strongest known foal record in your budget",
            "intro": "First version for Arabians. The prices are real, but the foal records are thin and one-sided, so treat the ranking as a list to check by hand. "
                     "The Quarter Horse side has far more data behind it.",
            "how": how, "notes": notes, "stallions": out, "record": None, "sales": None, "pricing": None, "foal": None,
            "summary": {"stallions": len(out), "priced": len(priced), "with_record": len(with_rec), "results": len(results), "shows": shows,
                        "years": [years[0], years[-1]] if years else [], "sales": len(prices), "check": check}}
