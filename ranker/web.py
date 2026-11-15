"""Pack the workbook and the synthetic examples into one self-contained web page.

    python bvr.py export-web data/breeding_data.xlsx

writes docs/index.html, which GitHub Pages serves and which also opens straight
from disk. The page holds its data inline, so there is nothing else to deploy.
"""
from __future__ import annotations

import datetime as dt
import json
import os

from . import synth, workbook
from .core import Params, backtest, rank_stallions, truth_correlation

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(os.path.dirname(HERE), "web", "template.html")
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
            "synthetic": synthetic, "power": power}


def export(workbook_path, out_path, repo_url="", params=None, dates=None):
    data = build_data(workbook_path, params, dates)
    data["repo"] = repo_url
    blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    html = open(TEMPLATE, encoding="utf-8").read()
    marker = "/*__BVR_DATA__*/"
    if marker not in html:
        raise SystemExit("web/template.html has lost its data marker %s" % marker)
    html = html.replace(marker, "window.BVR=" + blob + ";")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return data, len(html)
