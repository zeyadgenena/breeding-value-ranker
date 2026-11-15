#!/usr/bin/env python3
"""Does the foal model hold on classes it never saw?

    python qa/replicate.py            # print the test
    python qa/replicate.py --write    # also save qa/replication.json

The foal model was trained on the WCHA, Big Money and Breeders Halter Futurity
classes. The same show also runs Paint Horse classes (open, jackpot, Gold and
Platinum Breeders' Futurity). They are in qa/futurity_other_foals.csv and were
never used in training. Many of those foals are by the same sires.

The kept model is applied as it stands, with no refitting. Horses that also
appear in the training classes are left out, so every foal here is new to it.
"""
import json
import os
import statistics as st
import sys

from v2data import V2, HERE, norm, _csv
import foal_model as fm


def main():
    v = V2()
    trained_on = {(f["horse"], f["year"]) for f in v.futurity}
    other = _csv("futurity_other_foals.csv")
    for r in other:
        r["year"] = int(r["year"])
        r["pct"] = float(r["open_pct"] or r["best_pct"] or 0)
        r["sire"], r["dam"], r["horse"] = norm(r["sire"]), norm(r["dam"]), norm(r["horse"])
    keep = [r for r in other if r["sire"] and (r["horse"], r["year"]) not in trained_on]
    v.futurity = keep                                   # build the same features, from the same public lists, for the new foals
    rows = fm.build(v)
    with open(os.path.join(HERE, "foal_model.json")) as fh:
        model = json.load(fh)
    w = model["weights_top3"]
    feats = [fm.f_top20, fm.f_dam]
    scores = [fm.prob(w, x) for x in fm.X(rows, feats)]
    auc = fm.auc(scores, [r["top3"] for r in rows])
    rate = lambda part: st.mean(r["top3"] for r in part) if part else None
    cells = {}
    for label, test in (("top-20 sire", lambda r: r["sire_rank"] <= 20), ("other sire", lambda r: r["sire_rank"] > 20),
                        ("proven dam", lambda r: r["dam_proven"] == 1), ("other dam", lambda r: r["dam_proven"] == 0)):
        part = [r for r in rows if test(r)]
        cells[label] = {"foals": len(part), "top3": rate(part)}
    out = {"foals": len(rows), "left_out_as_already_seen": len(other) - len(keep), "sires": len({r["sire"] for r in rows}), "base": rate(rows), "sorting": auc, "cells": cells}
    print("%d new weanlings and yearlings by %d sires (%d others were already in the training classes). %.0f%% made a top three." % (
        out["foals"], out["sires"], out["left_out_as_already_seen"], 100 * out["base"]))
    for k, c in cells.items():
        print("  %-12s %3d foals, %s top three" % (k, c["foals"], "%.0f%%" % (100 * c["top3"]) if c["top3"] is not None else "n/a"))
    print("The kept model, applied unchanged, sorts these foals at %.2f (0.50 is a coin toss)." % auc if auc else "Too few foals to score.")
    if "--write" in sys.argv:
        with open(os.path.join(HERE, "replication.json"), "w") as fh:
            json.dump(out, fh, indent=1)
        print("Wrote qa/replication.json")


if __name__ == "__main__":
    main()
