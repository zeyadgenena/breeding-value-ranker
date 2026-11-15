#!/usr/bin/env python3
"""What did mares that were, or became, producers of halter earners sell for?

    python qa/mares.py --write    # saves qa/mare_facts.json for the app

Joins the public mare sales (qa/mare_sales.csv) to the leading-dams lists and the
futurity results. The numbers are small and are reported as counts, not rates.
"""
import csv
import json
import os
import statistics as st
import sys

from v2data import V2, HERE, norm, _csv


def main():
    v = V2()
    lead = {}
    for r in _csv("leaders", "dams.csv"):
        if r["period"].isdigit():
            lead.setdefault(int(r["period"]), set()).add(norm(r["dam"]))
    ever = set().union(*lead.values()) | {norm(r["dam"]) for r in v.top50} | {f["dam"] for f in v.futurity if int(f["top3"] or 0) > 0}
    mares = _csv("mare_sales.csv")
    for r in mares:
        r["n"], r["p"], r["y"] = norm(r["horse"]), float(r["price"]), int(r["sale_date"][:4])
    already = [r for r in mares if any(r["n"] in lead.get(y, ()) for y in range(2017, r["y"] + 1))]
    later = [r for r in mares if r["n"] in ever and r not in already]
    box = lambda rows: {"n": len(rows), "low": min(r["p"] for r in rows), "high": max(r["p"] for r in rows), "median": st.median(r["p"] for r in rows)} if rows else {"n": 0}
    out = {"mares_sold": len(mares), "typical": st.median(r["p"] for r in mares), "already_producers": box(already), "became_producers": box(later)}
    print(out)
    if "--write" in sys.argv:
        with open(os.path.join(HERE, "mare_facts.json"), "w") as fh:
            json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
