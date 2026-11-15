"""What a young halter horse is likely to sell for at public auction.

The model is trained and checked in qa/price_model.py and stored in
qa/price_model.json. It is deliberately modest: in testing nothing predicted
these prices well, so it gives a typical price and a wide range, and it lets a
sire's foal winnings move the estimate only as much as the sales data supports.
"""
from __future__ import annotations

import json
import math
import os


class PriceModel:
    def __init__(self, path):
        with open(path) as fh:
            self.m = json.load(fh)
        self.resid = self.m["residuals"]

    @classmethod
    def load(cls, qa_dir):
        path = os.path.join(qa_dir, "price_model.json")
        return cls(path) if os.path.exists(path) else None

    def _q(self, q):
        pos = q * (len(self.resid) - 1)
        lo, hi = int(math.floor(pos)), int(math.ceil(pos))
        return self.resid[lo] + (self.resid[hi] - self.resid[lo]) * (pos - lo)

    def expected(self, winnings, fee, age=1):
        """Sale price of a colt or filly (average of the two) at the given age, by a sire whose
        foals won `winnings` last year, and how that compares with the stud fee."""
        m = self.m
        mu = m["intercept"] + (m["yearling"] if age == 1 else m["two_year_old"] if age == 2 else 0.0)
        mu += m["winnings_log"] * math.log1p(max(0.0, winnings or 0.0) / 10000.0) + 0.5 * m["filly"]
        typical = math.exp(mu)
        lo_fee, hi_fee = m["fee_range_in_sales"]

        def chance(multiple):
            need = math.log(multiple * fee) - mu
            return sum(1 for r in self.resid if r >= need) / len(self.resid)
        return {"typical": typical, "low": math.exp(mu + self._q(0.25)), "high": math.exp(mu + self._q(0.75)),
                "multiple": typical / fee, "p3": chance(3), "p10": chance(10),
                "tested": bool(lo_fee <= fee <= hi_fee)}

    def summary(self):
        k = self.m["kept_round"]
        card = [{"name": r["round"].split(" ", 1)[1].replace(" (the one kept)", ""), "typical_miss": round(r["typical_miss"], 3),
                 "explained": round(r["explained"], 3), "kept": r["round"] == k["round"]} for r in self.m["scorecard"]]
        return {"sales": self.m["sales"], "sires": self.m["sires"], "explained": k["explained"],
                "within_double_or_half": k["within_double_or_half"], "fee_range": self.m["fee_range_in_sales"],
                "rounds": len(card), "combinations": self.m.get("combinations_tried"), "scorecard": card}
