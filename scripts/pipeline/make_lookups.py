#!/usr/bin/env python3
"""Write the reviewed lookup tables in data/pipeline/ from the edition-1 snapshot.

Run once; afterwards the tables are edited by hand when score.py reports a
new name it had to classify by rule.

    python scripts/pipeline/make_lookups.py data/raw/gur/gur_components_2026-10-30.csv
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "pipeline")


def fix(s):
    return s.replace("�", "–")  # en dash lost in the edition-1 export


def main(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    tables = {
        "families.csv": (["weapon", "weapon_family"],
                         lambda r: (r["weapon"], r["weapon_family"])),
        "owners.csv": (["manufacturer", "parent_group", "home_parent_group", "home_strict"],
                       lambda r: (r["manufacturer"], r["parent_group"], fix(r["home_parent_group"]), fix(r["home_strict"]))),
        "tiers.csv": (["part_name", "tier"],
                      lambda r: (r["part_name"], r["chpl_tier_approx"])),
    }
    os.makedirs(OUT, exist_ok=True)
    for name, (cols, f) in tables.items():
        seen = {}
        for r in rows:
            v = f(r)
            if v[0] in seen and seen[v[0]] != v:
                raise SystemExit(f"{name}: '{v[0]}' maps to two values")
            seen[v[0]] = v
        with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(cols)
            w.writerows(sorted(seen.values(), key=lambda v: v[0].lower()))
        print(f"{name}: {len(seen):,} rows")


if __name__ == "__main__":
    main(sys.argv[1])
