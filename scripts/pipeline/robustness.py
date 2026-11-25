#!/usr/bin/env python3
"""Re-score the index under alternative priority-list weights.

    python scripts/pipeline/robustness.py data/raw/gur/gur_components_2026-10-30.csv

Writes data/raw/weighting.csv: for each weighting of tiers 1-4, the EU
share (parent-group method) with its 90% range, the US and China shares,
where the EU bloc ranks against single countries, and the top 10 single
countries in order. The headline weighting is 4/3/2/1.
"""
import argparse
import collections
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules  # noqa: E402
import score  # noqa: E402

WEIGHTINGS = [("4,3,2,1", "headline"), ("1,1,1,1", "unweighted"), ("3,2,1,1", "flatter"), ("5,3,2,1", "steeper")]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("snapshot")
    p.add_argument("--out", default=os.path.join(score.ROOT, "data", "raw", "weighting.csv"))
    a = p.parse_args()
    rows_in = score.load_snapshot(a.snapshot)
    out = []
    for w, label in WEIGHTINGS:
        weights = [float(x) for x in w.split(",")]
        clean, unique, _, _ = score.prepare([dict(r) for r in rows_in], weights, "snapshot")
        idx = {(r["method"], r["country"]): r for r in score.index_table(clean, unique, 1000, 20261030)}
        pts, total = score.points_by_country(unique, "group")
        countries = sorted(((v / total, c) for c, v in pts.items() if c != "Unidentified"), reverse=True)
        eu = idx[("group", "EU total")]
        eu_rank = 1 + sum(1 for s, c in countries if c not in rules.EU and s > eu["index_share"])
        out.append({
            "weights": w.replace(",", "/"), "label": label,
            "eu_index": eu["index_share"], "eu_ci_low": eu["ci_low"], "eu_ci_high": eu["ci_high"],
            "us_index": idx[("group", "United States")]["index_share"],
            "china_index": idx[("group", "China")]["index_share"],
            "germany_index": idx[("group", "Germany")]["index_share"],
            "eu_rank_vs_countries": eu_rank,
            "top10": "; ".join(f"{score.SHORT.get(c, c)} {s:.1%}" for s, c in countries[:10]),
        })
        print(f"{w}: EU {eu['index_share']:.1%} [{eu['ci_low']:.1%}-{eu['ci_high']:.1%}], rank {eu_rank}")
    score.write(a.out, out)


if __name__ == "__main__":
    main()
