"""Shared data for the second round of Quarter Horse testing. Everything is keyed by the stallion's name.

fees        stud fee by breeding season, for the 52 workbook stallions and the 36 extra ones
board       the yearly halter sire leaderboards, 2017 to 2026, every stallion on them
top50       top-50 halter money earners per year, with sire, dam and dam's sire
futurity    every horse shown in the futurity classes, 2024 to 2026
"""
from __future__ import annotations

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)


def _csv(*parts):
    path = os.path.join(HERE, *parts)
    if not os.path.exists(path):
        return []
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


# the same stallion spelled differently in different sources
ALIASES = {"ELANTE": "EL ANTE", "ENVINCEBLE": "EVINCEBLE", "LFL ELIGANCE": "LFL ELIGIANCE", "RUMEREZ": "RUMERZ", "SAIL ON SAILER": "SAIL ON SAILOR"}


def norm(name):
    s = str(name or "").upper().replace(";", " ").replace("(P)", " ")       # (P) marks a Paint registration, not a different horse
    s = " ".join(s.split())
    return ALIASES.get(s, s)


class V2:
    def __init__(self, workbook=None):
        from ranker import workbook as wbk
        ds, _, _ = wbk.load(workbook or os.path.join(ROOT, "data", "breeding_data.xlsx"))
        self.fees = {}                                   # name -> {season: fee}
        names = {sid: norm(s["name"]) for sid, s in ds.stallions.items()}
        newest = {}
        for s in sorted(ds.snapshots, key=lambda s: (s.get("year") or 0, str(s.get("date") or ""))):
            if (s.get("basis") or "").strip().lower() == "auction" or s.get("year") is None:
                continue
            nm = names.get(s["stallion_id"])
            if nm is None:
                continue
            newest[(nm, s["year"])] = s.get("fee")       # the newest row for a season wins; None = private treaty
        for (nm, y), fee in newest.items():
            self.fees.setdefault(nm, {})[int(y)] = fee
        self.workbook_names = set(names.values())
        with open(os.path.join(HERE, "extra_sires.json")) as fh:
            for nm, v in json.load(fh)["stallions"].items():
                for y, fee in v["fees"].items():
                    self.fees.setdefault(norm(nm), {})[int(y)] = fee
        self.board = {}                                  # (name, year) -> row
        self.years = set()
        for r in _csv("leaders", "sires.csv"):
            if r["period"].isdigit():
                y = int(r["period"])
                self.years.add(y)
                self.board[(norm(r["name"]), y)] = {"rank": int(r["rank"] or 0), "earners": int(r["money_earners"] or 0), "earnings": float(r["earnings"] or 0)}
        self.years = sorted(self.years)
        self.top50 = [r for r in _csv("leaders", "earners.csv") if r["period"].isdigit()]
        self.hits = {}                                   # (sire, crop, year) -> [top-50 foals, their winnings]
        for r in self.top50:
            if r["foaled"]:
                k = (norm(r["sire"]), int(r["foaled"]), int(r["period"]))
                h = self.hits.setdefault(k, [0, 0.0])
                h[0] += 1
                h[1] += float(r["earnings"] or 0)
        self.bm_sires = {(norm(r["name"]), int(r["period"])): r for r in _csv("leaders", "broodmare_sires.csv") if r["period"].isdigit()}
        self.futurity = _csv("futurity_foals.csv")
        for r in self.futurity:
            r["year"] = int(r["year"])
            r["pct"] = float(r["open_pct"] or r["best_pct"] or 0)
            r["sire"], r["dam"] = norm(r["sire"]), norm(r["dam"])

    # ---- as things stood at the end of year d ----
    def fee(self, name, d, stale=2):
        """Fee for the season after d, or the latest advertised one within `stale` seasons. None = no price."""
        f = self.fees.get(name, {})
        seasons = [y for y in f if d + 1 - stale <= y <= d + 1]
        if not seasons:
            return None
        return f[max(seasons)]

    def e(self, name, y):
        r = self.board.get((name, y))
        return r["earnings"] if r else 0.0

    def n(self, name, y):
        r = self.board.get((name, y))
        return r["earners"] if r else 0

    def crop_hits(self, name, d):
        """Top-50 foals from the crop conceived the season after d: as weanlings (d+2) and yearlings (d+3)."""
        crop = d + 2
        return sum(self.hits.get((name, crop, y), [0, 0.0])[0] for y in (crop, crop + 1))

    def crop_money(self, name, d):
        crop = d + 2
        return sum(self.hits.get((name, crop, y), [0, 0.0])[1] for y in (crop, crop + 1))

    def universe(self, d):
        return sorted(nm for nm in self.fees if self.fee(nm, d) is not None)
