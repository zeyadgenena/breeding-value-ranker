"""Run with:  python -m unittest discover tests"""
import copy
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ranker import matcher, synth, workbook  # noqa: E402
from ranker.core import (Dataset, Params, _midrank_percentiles, backtest, fee_at, fit_effects,  # noqa: E402
                         foal_totals, rank_stallions)


def tiny(outcomes, foals=None, snapshots=None):
    foals = foals or {"F1": {"sire_id": "S1", "dam_id": None, "year": 2015, "name": "F1"}}
    return Dataset(stallions={"S1": {"name": "S1"}, "S2": {"name": "S2"}},
                   snapshots=snapshots or [], mares={}, foals=foals, outcomes=outcomes)


class Scoring(unittest.TestCase):
    def test_ties_share_the_middle_rank(self):
        pct = _midrank_percentiles([(0, "a"), (0, "b"), (0, "c"), (5, "d")])
        self.assertAlmostEqual(pct["a"], 37.5)
        self.assertAlmostEqual(pct["d"], 87.5)

    def test_future_rows_are_invisible(self):
        ds = tiny([{"foal_id": "F1", "year": 2016, "points": 4.0},
                   {"foal_id": "F1", "year": 2019, "points": 9.0}])
        self.assertEqual(foal_totals(ds, 2017, Params())["F1"]["points"], 4.0)
        self.assertEqual(foal_totals(ds, None, Params())["F1"]["points"], 13.0)

    def test_lifetime_total_needs_a_mature_foal(self):
        ds = tiny([{"foal_id": "F1", "year": None, "points": 20.0}])
        self.assertNotIn("F1", foal_totals(ds, 2016, Params()))        # 1 year old: unknowable
        self.assertEqual(foal_totals(ds, 2018, Params())["F1"]["points"], 20.0)

    def test_unshown_foal_counts_as_zero(self):
        self.assertEqual(foal_totals(tiny([]), 2020, Params())["F1"]["points"], 0.0)

    def test_placing_rows_fall_back_to_horses_beaten(self):
        ds = tiny([{"foal_id": "F1", "year": 2016, "placing": 2, "class_size": 9}])
        t = foal_totals(ds, None, Params())["F1"]
        self.assertEqual((t["points"], t["shows"]), (7.0, 1))


class Fees(unittest.TestCase):
    SNAPS = [{"year": 2024, "fee": 2500.0, "basis": "listed", "date": "2024-01-10"},
             {"year": 2024, "fee": 2750.0, "basis": "listed", "date": "2024-04-25"},
             {"year": 2024, "fee": 1300.0, "basis": "auction", "date": "2024-05-27"},
             {"year": 2025, "fee": None, "basis": "private treaty", "date": "2025-05-04"}]

    def test_auction_bids_never_stand_in_for_listed_fees(self):
        self.assertEqual(fee_at(self.SNAPS, 2023, Params())["fee"], 2750.0)       # newest listed in 2024
        self.assertEqual(fee_at(self.SNAPS, 2023, Params(fee_basis="auction"))["fee"], 1300.0)
        self.assertEqual(fee_at(self.SNAPS, 2023, Params(fee_basis="any"))["fee"], 1300.0)

    def test_private_treaty_replaces_an_older_dollar_fee(self):
        self.assertIsNone(fee_at(self.SNAPS, None, Params()))                      # private treaty in 2025
        self.assertEqual(fee_at(self.SNAPS, None, Params(fee_basis="auction"))["fee"], 1300.0)

    def test_fee_must_be_from_the_right_seasons(self):
        self.assertEqual(fee_at(self.SNAPS, 2023, Params())["fee"], 2750.0)   # season 2024 fee
        self.assertIsNone(fee_at(self.SNAPS, 2021, Params()))                  # not yet published
        self.assertIsNone(fee_at(self.SNAPS, 2027, Params()))                  # too stale


    def test_todays_ranking_ignores_fees_that_are_too_old(self):
        foals = {"F%d" % i: {"sire_id": "S1" if i < 6 else "S2", "dam_id": None, "year": 2015, "name": "f"}
                 for i in range(12)}
        ds = tiny([], foals, [{"stallion_id": "S1", "year": 2027, "fee": 2000.0, "basis": "listed", "date": ""},
                              {"stallion_id": "S2", "year": 2021, "fee": 900.0, "basis": "listed", "date": ""}])
        ranked, skipped, _ = rank_stallions(ds, None, Params())
        self.assertEqual([r["stallion_id"] for r in ranked], ["S1"])
        self.assertIn("seasons old", skipped[0]["status"])
        ranked, _, _ = rank_stallions(ds, None, Params(fee_fallback="latest"))
        self.assertEqual(len(ranked), 2)


class Matcher(unittest.TestCase):
    def test_rising_beats_flat_beats_falling(self):
        self.assertGreater(matcher.score(100000, 50000), matcher.score(100000, 100000))
        self.assertGreater(matcher.score(100000, 100000), matcher.score(100000, 300000))

    def test_trend_is_capped(self):
        self.assertEqual(matcher.trend(100000, 1), 2.0)
        self.assertEqual(matcher.trend(1, 100000), 0.5)
        self.assertEqual(matcher.trend(100000, None), 1.0)      # no earlier list to compare with

    def test_score_ignores_later_years(self):
        ds = tiny([], snapshots=[{"stallion_id": "S1", "year": 2021, "fee": 1500.0, "basis": "listed", "date": ""}])
        ds.sire_stats = [{"stallion_id": "S1", "period": str(y), "rank": 5, "earners": 10, "earnings": e}
                         for y, e in ((2019, 40000.0), (2020, 80000.0), (2021, 10.0), (2022, 999999.0))]
        h = matcher.History(ds)
        self.assertEqual(h.score("S1", 2020), 80000.0 * 2.0)
        self.assertEqual(h.fee("S1", 2020), 1500.0)

    def test_real_workbook_has_a_track_record_file(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ds, review, _ = workbook.load(os.path.join(here, "data", "breeding_data.xlsx"))
        self.assertEqual(review, [])
        self.assertGreater(len(ds.sire_stats), 100)
        rec = matcher.track_record(matcher.History(ds, os.path.join(here, "qa", "top_earners.json")))
        at_2000 = [r for r in rec["by_budget"] if r["budget"] == 2000][0]
        self.assertGreater(at_2000["share"], 2 * at_2000["base"])   # picks beat the average stallion clearly


class NoHindsight(unittest.TestCase):
    def test_ranking_ignores_everything_after_the_date(self):
        ds = synth.generate("planted", seed=11)
        p, d = Params(), 2017
        before, _, _ = rank_stallions(ds, d, p)
        cut = copy.deepcopy(ds)
        cut.foals = {k: f for k, f in cut.foals.items() if f["year"] <= d}
        cut.outcomes = [o for o in cut.outcomes if o["year"] <= d and o["foal_id"] in cut.foals]
        cut.snapshots = [s for s in cut.snapshots if s["year"] <= d + 1]
        after, _, _ = rank_stallions(cut, d, p)
        self.assertEqual([(r["stallion_id"], round(r["value_per_1k"], 9)) for r in before],
                         [(r["stallion_id"], round(r["value_per_1k"], 9)) for r in after])
        self.assertGreater(len(before), 10)


class Ranking(unittest.TestCase):
    def test_cheap_below_average_never_outranks_above_average(self):
        ranked, _, _ = rank_stallions(synth.generate("planted", seed=5), None, Params())
        signs = [r["effect"] > 0 for r in ranked]
        self.assertEqual(signs, sorted(signs, reverse=True))

    def test_small_samples_are_shrunk(self):
        fit = fit_effects(synth.generate("planted", seed=5), None, Params())
        for s in fit.sires.values():
            self.assertLessEqual(abs(s["effect"]), abs(s["raw_effect"]) + 1e-12)

    def test_planted_effects_are_recovered(self):
        from ranker.core import truth_correlation
        ds = synth.generate("planted", seed=5, foals_per_year=25)
        self.assertGreater(truth_correlation(ds, fit_effects(ds, None, Params())), 0.7)


class Workbook(unittest.TestCase):
    def test_round_trip_matches_in_memory(self):
        ds = synth.generate("planted", seed=2, n_stallions=12, foals_per_year=6)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "s.xlsx")
            workbook.write_dataset(ds, path, "SYNTHETIC DATA test")
            loaded, review, _ = workbook.load(path)
        self.assertEqual(review, [])
        self.assertEqual(len(loaded.foals), len(ds.foals))
        a, _, _ = rank_stallions(ds, None, Params())
        b, _, _ = rank_stallions(loaded, None, Params())
        self.assertEqual([r["stallion_id"] for r in a], [r["stallion_id"] for r in b])
        for x, y in zip(a, b):
            self.assertAlmostEqual(x["effect"], y["effect"], places=9)

    def test_link_checks_flag_bad_parents(self):
        wb = workbook.build_workbook(seed_real_rows=False)
        wb["Stallions"].append(["S1", "GOOD SIRE", "1111111", 2010])
        wb["Foals"].append(["A", "ok", "2000001", "1111111", "3000001", "Good Sire", "DAM A", 2018])
        wb["Foals"].append(["B", "wrong name", "2000002", "1111111", "3000001", "OTHER SIRE", "DAM A", 2018])
        wb["Foals"].append(["C", "unknown sire", "2000003", "9999999", None, "GOOD SIRE", None, 2018])
        wb["Foals"].append(["D", "name only", "2000004", None, None, "good  sire", None, 2018])
        wb["Foals"].append(["E", "too early", "2000005", "1111111", None, None, None, 2011])
        wb["Outcomes"].append(["2000001", 2019, 3, 5.5])
        wb["Outcomes"].append(["nobody", 2019, 3, 5.5])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "l.xlsx")
            wb.save(path)
            ds, review, _ = workbook.load(path)
        self.assertEqual(sorted(ds.foals), ["A", "D"])
        self.assertEqual(ds.foals["A"]["dam_id"], "reg:3000001")
        self.assertEqual(len(ds.outcomes), 1)
        issues = " | ".join(r["issue"] for r in review)
        for needle in ("record says OTHER SIRE", "9999999 is not in Stallions",
                       "matched by name only", "sire was foaled 2010", "foal not found"):
            self.assertIn(needle, issues)

    def test_blank_template_runs_without_a_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, out = os.path.join(tmp, "t.xlsx"), os.path.join(tmp, "t_results.xlsx")
            workbook.build_workbook().save(path)
            ds, review, info = workbook.load(path)
            self.assertEqual(len(ds.stallions), 7)
            self.assertEqual(len(ds.foals), 0)          # the EXAMPLE rows are skipped
            p = Params()
            bt = backtest(ds, p)
            ranked, skipped, fit = rank_stallions(ds, None, p, bt["final"])
            self.assertEqual(bt["verdict"]["status"], "NOT ENOUGH DATA")
            workbook.write_results(path, out, ds, ranked, skipped, fit, bt, review, info, p)
            self.assertTrue(os.path.exists(out))


class Verdicts(unittest.TestCase):
    def test_backtest_uses_at_least_three_windows(self):
        bt = backtest(synth.generate("planted", seed=3), Params(random_draws=200))
        self.assertGreaterEqual(len(bt["verdict"]["usable_windows"]), 3)
        self.assertIn(bt["verdict"]["status"], ("PASS", "FAIL"))


class Pricing(unittest.TestCase):
    HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def model(self):
        from ranker.pricing import PriceModel
        return PriceModel.load(os.path.join(self.HERE, "qa"))

    def test_return_is_price_over_fee(self):
        pm = self.model()
        a, b = pm.expected(50000.0, 1000.0), pm.expected(50000.0, 2000.0)
        self.assertAlmostEqual(a["typical"], b["typical"])              # the fee does not move the price
        self.assertAlmostEqual(a["multiple"], a["typical"] / 1000.0)
        self.assertAlmostEqual(a["multiple"], 2 * b["multiple"])        # so half the fee is twice the return
        self.assertLess(a["low"], a["typical"])
        self.assertLess(a["typical"], a["high"])
        self.assertGreater(a["p3"], b["p3"])                            # 3x a small fee is easier to reach
        self.assertGreaterEqual(a["p3"], a["p10"])

    def test_no_estimate_outside_the_fees_seen_in_sales(self):
        pm = self.model()
        lo, hi = pm.m["fee_range_in_sales"]
        self.assertTrue(pm.expected(0.0, lo)["tested"])
        self.assertFalse(pm.expected(0.0, lo - 1)["tested"])
        self.assertFalse(pm.expected(0.0, hi + 1)["tested"])

    def test_scorecard_keeps_the_best_round(self):
        s = self.model().summary()
        kept = [r for r in s["scorecard"] if r["kept"]]
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["explained"], max(r["explained"] for r in s["scorecard"]))
        self.assertGreaterEqual(s["rounds"], 10)

    def test_training_finds_a_real_effect_and_not_a_fake_one(self):
        sys.path.insert(0, os.path.join(self.HERE, "qa"))
        import math
        import random
        import price_model as pmod
        rng = random.Random(7)
        rows = []
        for i in range(240):
            age = str(rng.randrange(3))
            noise = rng.gauss(0, 0.3)
            rows.append({"age_at_sale": age, "sex": "colt", "sire": "S%d" % (i % 20), "auction": "A%d" % (i % 30),
                         "fee": 1500.0, "win_prev": None, "win_bred": None, "year": 2022,
                         "price": math.exp(8.0 + (0.8 if age == "0" else 0.0) + noise), "noise": noise})
        real = pmod.cross_validate(rows, [pmod.f_age], False)
        self.assertGreater(real["explained"], 0.4)                      # age was planted, and it is found
        for r in rows:
            r["price"] = math.exp(8.0 + r["noise"])
        fake = pmod.cross_validate(rows, [pmod.f_age], False)
        self.assertLess(fake["explained"], 0.05)                        # nothing planted, nothing claimed

    def test_app_ranks_the_lower_fee_first_for_resale(self):
        from ranker import web
        ds, _, _ = workbook.load(os.path.join(self.HERE, "data", "breeding_data.xlsx"))
        m = web.match_data(ds, Params())
        priced = [s for s in m["stallions"] if s["sale"] and s["sale"]["tested"]]
        self.assertGreater(len(priced), 20)
        best = max(priced, key=lambda s: s["sale"]["multiple"])
        self.assertEqual(best["price"]["fee"], min(s["price"]["fee"] for s in priced))
        for s in priced:
            self.assertAlmostEqual(s["sale"]["multiple"], s["sale"]["typical"] / s["price"]["fee"], delta=0.06)
            self.assertGreater(s["sale"]["weanling"], s["sale"]["typical"])


if __name__ == "__main__":
    unittest.main()
