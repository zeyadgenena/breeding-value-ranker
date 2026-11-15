"""Synthetic horses for testing the pipeline. NOT real data.

The generator plants a known answer so we can check whether the method finds
it, and whether it stays quiet when there is nothing to find.

Scenarios
---------
planted     Stallions differ in true offspring quality. Fees follow each
            stallion's own show record, which is only loosely tied to how his
            foals turn out, so some stallions are underpriced. This is the
            world in which the project's hypothesis is true.
no_effect   Stallions do not differ at all. Any ranking is noise.
confounded  Stallions do not differ, but expensive stallions get the better
            mares, so their foals look better anyway.
"""
from __future__ import annotations

import math
import random

from .core import Dataset, Params, backtest, truth_correlation

SCENARIOS = ("planted", "no_effect", "confounded")
COLORS = ("Sorrel", "Chestnut", "Bay", "Brown", "Palomino", "Black", "Gray")
DAM_VAR = 0.20      # share of foal quality that comes from the dam


def _poisson(rng, lam):
    if lam <= 0:
        return 0
    limit, k, prod = math.exp(-lam), 0, rng.random()
    while prod > limit:
        k += 1
        prod *= rng.random()
    return k


def generate(scenario="planted", seed=1, n_stallions=40, foals_per_year=10.0,
             sire_share=0.08, first_year=2008, last_year=2025, now_year=2026):
    """Build a Dataset. `sire_share` is the share of foal-quality variance that
    is due to the sire (about a quarter of heritability for a half-sib family)."""
    if scenario not in SCENARIOS:
        raise ValueError("scenario must be one of %s" % (SCENARIOS,))
    rng = random.Random(seed)
    sd_sire = math.sqrt(sire_share) if scenario == "planted" else 0.0
    sd_dam = math.sqrt(DAM_VAR)
    sd_noise = math.sqrt(max(0.05, 1.0 - sire_share - DAM_VAR))
    sorting = 1.2 if scenario == "confounded" else 0.3   # how strongly good mares go to pricey stallions

    stallions, snapshots, truth, meta = {}, [], {}, {}
    for i in range(1, n_stallions + 1):
        sid = "SYN-S%02d" % i
        z_true = rng.gauss(0, 1)
        own = 0.4 * z_true + math.sqrt(1 - 0.16) * rng.gauss(0, 1)   # own show record
        start = rng.randint(first_year, last_year - 6)
        end = min(last_year - 1, start + rng.randint(6, 14))
        base_fee = 2500.0 * math.exp(0.45 * own + 0.15 * rng.gauss(0, 1))
        stallions[sid] = {"name": "SYN STALLION %02d" % i, "reg": "SYN1%05d" % i,
                          "foaling_year": start - rng.randint(3, 6),
                          "sire": "SYN SIRE %02d" % rng.randint(1, 12),
                          "dam": None, "dam_sire": "SYN DAMSIRE %02d" % rng.randint(1, 12)}
        truth[sid] = sd_sire * z_true
        meta[sid] = {"own": own, "start": start, "end": end}
        for season in range(start, end + 1):
            # the market learns about his foals only slowly
            learned = 0.1 * min(1.0, (season - start) / 8.0) * (z_true if sd_sire else 0.0)
            fee = base_fee * math.exp(learned + 0.05 * rng.gauss(0, 1))
            snapshots.append({"stallion_id": sid, "year": season,
                              "fee": max(500.0, round(fee / 250.0) * 250.0),
                              "basis": "listed", "source": "synthetic"})

    mares, mare_meta, foals, outcomes = {}, {}, {}, []

    def new_mare(season):
        mid = "SYN-M%04d" % (len(mares) + 1)
        z = rng.gauss(0, 1)
        own_latent = 0.6 * z + 0.8 * rng.gauss(0, 1)
        own_points = None
        if rng.random() < 0.6:
            own_points = round(max(0.0, 6.0 * math.exp(0.8 * own_latent) - 4.0) * 2) / 2.0
        mares[mid] = {"name": "SYN MARE %04d" % len(mares), "reg": "SYN2%05d" % len(mares),
                      "own_points": own_points, "foaling_year": season - rng.randint(3, 8)}
        mare_meta[mid] = {"m": sd_dam * z, "tier": z + 0.5 * rng.gauss(0, 1), "first": season}
        return mid

    for season in range(first_year, last_year):
        crop = season + 1
        active = [s for s, m in meta.items() if m["start"] <= season <= m["end"]]
        if not active:
            continue
        needed = _poisson(rng, foals_per_year * len(active)) if foals_per_year * len(active) < 50 \
            else int(round(rng.gauss(foals_per_year * len(active), math.sqrt(foals_per_year * len(active)))))
        available = [m for m, mm in mare_meta.items() if mm["first"] <= season <= mm["first"] + 9]
        while len(available) * 0.6 < needed:
            available.append(new_mare(season))
        for mid in rng.sample(available, needed):
            tier = mare_meta[mid]["tier"]
            weights = [math.exp(0.4 * meta[s]["own"] + sorting * tier * meta[s]["own"]) for s in active]
            sid = rng.choices(active, weights)[0]
            fid = "SYN-F%05d" % (len(foals) + 1)
            foals[fid] = {"name": "SYN FOAL %05d" % (len(foals) + 1), "reg": "SYN3%05d" % (len(foals) + 1),
                          "sire_id": sid, "dam_id": mid, "year": crop,
                          "sex": rng.choice(("Stallion", "Mare", "Gelding")),
                          "color": rng.choice(COLORS)}
            q = truth[sid] + mare_meta[mid]["m"] + sd_noise * rng.gauss(0, 1)
            if rng.random() < 1.0 / (1.0 + math.exp(0.7 - 1.3 * q)):
                campaign = math.exp(rng.gauss(0, 0.5))   # owner effort, unrelated to the horse
                for age, weight in enumerate((0.30, 0.40, 0.20, 0.10)):
                    year = crop + age
                    if year > now_year:
                        break
                    shows = _poisson(rng, 5.0 * weight * campaign * math.exp(0.25 * q))
                    if shows == 0:
                        continue
                    per_show = 0.9 * math.exp(0.8 * q + rng.gauss(0, 0.4))
                    grands = sum(1 for _ in range(shows)
                                 if rng.random() < min(0.6, 0.05 * math.exp(q)))
                    outcomes.append({"foal_id": fid, "year": year, "shows": shows,
                                     "points": round(shows * per_show * 2) / 2.0,
                                     "placing": None, "class_size": None,
                                     "grands": grands, "reserves": 0, "earnings": None,
                                     "sale_price": None, "source": "synthetic"})
            if rng.random() < 0.25:
                year = crop + (0 if rng.random() < 0.5 else 1)
                if year <= now_year:
                    price = math.exp(math.log(5000) + 0.45 * (q + rng.gauss(0, 0.5))
                                     + 0.35 * meta[sid]["own"] + rng.gauss(0, 0.45))
                    outcomes.append({"foal_id": fid, "year": year, "shows": 0, "points": 0.0,
                                     "placing": None, "class_size": None, "grands": 0,
                                     "reserves": 0, "earnings": None,
                                     "sale_price": round(price / 100.0) * 100.0,
                                     "source": "synthetic"})

    return Dataset(stallions=stallions, snapshots=snapshots, mares=mares, foals=foals,
                   outcomes=outcomes, truth=truth)


def power_table(reps=40, configs=None, seed0=1000, progress=None):
    """Run the whole backtest on many synthetic datasets and count verdicts.

    Returns a list of rows: one per configuration.
    """
    if configs is None:
        configs = []
        for share in (0.04, 0.08, 0.15):
            for fpy in (4.0, 10.0, 25.0):
                configs.append({"scenario": "planted", "sire_share": share,
                                "foals_per_year": fpy, "mare_adjust": True})
        for fpy in (10.0, 25.0):
            configs.append({"scenario": "no_effect", "sire_share": 0.08,
                            "foals_per_year": fpy, "mare_adjust": True})
            configs.append({"scenario": "confounded", "sire_share": 0.08,
                            "foals_per_year": fpy, "mare_adjust": True})
            configs.append({"scenario": "confounded", "sire_share": 0.08,
                            "foals_per_year": fpy, "mare_adjust": False})
    rows = []
    for ci, cfg in enumerate(configs):
        passes = fails = other = 0
        corrs, lifts, pcts, foals_per_stallion = [], [], [], []
        for r in range(reps):
            ds = generate(cfg["scenario"], seed=seed0 + 97 * ci + r,
                          foals_per_year=cfg["foals_per_year"], sire_share=cfg["sire_share"])
            p = Params(mare_adjust=cfg["mare_adjust"], random_draws=400, seed=r)
            res = backtest(ds, p)
            v = res["verdict"]["status"]
            passes += v == "PASS"
            fails += v == "FAIL"
            other += v not in ("PASS", "FAIL")
            c = truth_correlation(ds, res["final"])
            if c is not None:
                corrs.append(c)
            prim = res["primary"]
            for w in res["windows"]:
                g = w.get("groups") or {}
                pk, rd = g.get("Top value picks"), g.get("Random, similar fee (median)")
                if pk and rd and pk[prim] is not None and rd[prim] is not None:
                    lifts.append(pk[prim] - rd[prim])
                    if w["matched_percentile"].get(prim) is not None:
                        pcts.append(w["matched_percentile"][prim])
            sizes = [s["n"] for s in res["final"].sires.values()]
            if sizes:
                foals_per_stallion.append(sum(sizes) / len(sizes))
        rows.append({
            "scenario": cfg["scenario"], "sire_share": cfg["sire_share"],
            "foals_per_stallion_year": cfg["foals_per_year"],
            "avg_foals_per_stallion": sum(foals_per_stallion) / len(foals_per_stallion),
            "mare_adjust": cfg["mare_adjust"], "reps": reps,
            "pass_rate": passes / reps, "fail_rate": fails / reps, "no_verdict": other / reps,
            "corr_with_truth": sum(corrs) / len(corrs) if corrs else None,
            "avg_lift_vs_random": sum(lifts) / len(lifts) if lifts else None,
            "avg_random_percentile": sum(pcts) / len(pcts) if pcts else None,
        })
        if progress:
            progress(rows[-1])
    return rows
