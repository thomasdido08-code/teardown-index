#!/usr/bin/env python3
"""Acceptance test: compare pipeline output with the published tables.

    python scripts/pipeline/compare.py build/          # against data/raw/
    python scripts/pipeline/compare.py build/ --strict  # exit 1 on any failure

Tolerances:
  counts (components, families, tiers)    exact
  raw_share, incidence                    0.00001 (rounding)
  index_share                             0.0015  (the residual tier
                                          differences explained in
                                          scripts/pipeline/README.md)
  ci_low, ci_high                         0.005   (bootstrap noise: the
                                          edition-1 random seed was not kept)
  size ratio                              5% relative
Prints one line per check and a summary.
"""
import argparse
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PUB = os.path.join(ROOT, "data", "raw")


def read(d, name):
    with open(os.path.join(d, name), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("build")
    p.add_argument("--strict", action="store_true")
    a = p.parse_args()
    fails, checks = [], 0

    def check(label, got, want, tol=0.0, rel=False):
        nonlocal checks
        checks += 1
        g, w = float(got), float(want)
        diff = abs(g - w) / abs(w) if rel and w else abs(g - w)
        ok = diff <= tol + 1e-12
        if not ok:
            fails.append(f"{label}: got {got}, published {want}")
        return ok

    pub = {(r["method"], r["country"]): r for r in read(PUB, "index.csv")}
    got = {(r["method"], r["country"]): r for r in read(a.build, "index.csv")}
    worst = 0.0
    for k, w in pub.items():
        g = got.get(k)
        if not g:
            fails.append(f"index {k}: missing")
            continue
        check(f"index {k} components", g["components"], w["components"])
        check(f"index {k} raw_share", g["raw_share"], w["raw_share"], 0.00001)
        check(f"index {k} incidence", g["incidence"], w["incidence"], 0.00001)
        check(f"index {k} index_share", g["index_share"], w["index_share"], 0.0015)
        worst = max(worst, abs(float(g["index_share"]) - float(w["index_share"])))
        check(f"index {k} ci_low", g["ci_low"], w["ci_low"], 0.005)
        check(f"index {k} ci_high", g["ci_high"], w["ci_high"], 0.005)

    ps = {r["metric"]: r["value"] for r in read(PUB, "stats.csv")}
    gs = {r["metric"]: r["value"] for r in read(a.build, "stats.csv")}
    for m in ("components", "weapon_families", "unique_in_family", "gur_dated", "gur_dated_2022_on"):
        check(f"stats {m}", gs[m], ps[m])

    pr = {r["firm"]: r for r in read(PUB, "ratio.csv")}
    for r in read(a.build, "ratio.csv"):
        check(f"ratio {r['firm']}", r["ratio"], pr[r["firm"]]["ratio"], 0.05, rel=True)

    pg = {r["group"].lower(): r for r in read(PUB, "groups.csv")}
    for r in read(a.build, "groups.csv"):
        w = pg.get(r["group"].lower())
        if w:
            for c in ("components", "weapon_families"):
                check(f"groups {r['group']} {c}", r[c], w[c])

    print(f"{checks - len(fails)}/{checks} checks passed; largest index_share difference {worst:.5f}")
    for f in fails:
        print("  FAIL", f)
    if a.strict and fails:
        sys.exit(1)


if __name__ == "__main__":
    main()
