#!/usr/bin/env python3
"""Score the Teardown Index from a GUR snapshot.

    python scripts/pipeline/score.py data/raw/gur/gur_components_2026-10-30.csv
    python scripts/pipeline/score.py data/raw/gur/gur_raw_2026-11-25.jsonl.gz --cutoff 2026-10-28
    python scripts/pipeline/score.py SNAPSHOT --weights 1,1,1,1 --out build/unweighted

Input: either the flat edition-1 export (CSV) or a raw scrape from
scrape_gur.py (.jsonl.gz). Output: the published tables (index.csv,
groups.csv, years.csv, ratio.csv, ledgers.csv, stats.csv) in --out, plus
review.csv listing every name that had to be classified by rule.

Steps, in order (METHODOLOGY.md, "Method"):
  1. clean          drop repeated GUR entries (the same component id listed
                    twice, which happens when GUR's pages shift during a scrape)
  2. family         weapon -> weapon family (data/pipeline/families.csv)
  3. owner          manufacturer -> parent group and home country under each
                    attribution method (data/pipeline/owners.csv)
  4. tier           part name -> priority-list tier (data/pipeline/tiers.csv),
                    weight 4/3/2/1 by default
  5. de-duplicate   a part counts once per family: same family, name, first
                    marking line and parent group
  6. score          index = a country's weighted parts / all weighted parts
  7. range          resample the families with replacement (1,000 draws),
                    5th and 95th percentiles
  8. dates          GUR's production date, else a YYWW code in the marking
  9. size           13 chipmakers: share of their index points / share of
                    their combined 2021 revenue

Standard library only. Deterministic: the bootstrap uses a fixed seed.
"""
import argparse
import collections
import csv
import gzip
import json
import math
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOOKUP = os.path.join(ROOT, "data", "pipeline")
METHODS = ("group", "strict", "hq")
REPORT_COUNTRIES = ["United States of America", "People's Republic of China", "Switzerland", "Japan", "Taiwan",
                    "Germany", "Netherlands", "France", "Italy", "Ireland", "Great Britain", "Republic of Korea",
                    "Sweden", "russian federation"]
SHORT = {"United States of America": "United States", "People's Republic of China": "China",
         "Great Britain": "United Kingdom", "Republic of Korea": "South Korea", "russian federation": "Russia"}


# ------------------------------------------------------------------ input
def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_snapshot(path, cutoff=None):
    """Return a list of dicts with the fields the pipeline needs."""
    if path.endswith(".jsonl.gz"):
        rows = []
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                j = json.loads(line)
                pub = j.get("Publication date", "")
                if cutoff and pub:
                    d, m, y = pub.split(".")
                    if f"{y}-{m}-{d}" > cutoff:
                        continue
                rows.append({
                    "id": str(j["id"]), "weapon": j.get("weapon", ""), "part_name": j.get("part_name", ""),
                    "marking": j.get("marking", ""), "manufacturer": j.get("Manufacturer", ""),
                    "hq_country_gur": j.get("Manufacturer's headquarters country", ""),
                    "production_date_gur": j.get("Production date", ""), "url": j.get("url", ""),
                })
        return rows
    rows = read_csv(path)
    for r in rows:
        r["id"] = r.get("id") or r.get("﻿id")
    return rows


def lookups():
    fam = {r["weapon"]: r["weapon_family"] for r in read_csv(os.path.join(LOOKUP, "families.csv"))}
    own = {r["manufacturer"]: (r["parent_group"], r["home_parent_group"], r["home_strict"])
           for r in read_csv(os.path.join(LOOKUP, "owners.csv"))}
    tier = {r["part_name"]: int(r["tier"]) for r in read_csv(os.path.join(LOOKUP, "tiers.csv"))}
    return fam, own, tier


# ------------------------------------------------------------------ helpers
def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def first_line(marking):
    return norm((marking or "").split("\n")[0])


def homes(country):
    """A home country, or the two halves of a split one, with their weight."""
    if country in rules.SPLIT:
        return [(c, 0.5) for c in rules.SPLIT[country]]
    return [(country, 1.0)]


def percentile(xs, q):
    """Linear interpolation between closest ranks (numpy's default)."""
    xs = sorted(xs)
    pos = (len(xs) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def round_half_up(x):
    return int(math.floor(x + 0.5))


# ------------------------------------------------------------------ pipeline
def prepare(rows, weights, years_from):
    fam, own, tier = lookups()
    review = []

    # 1. clean
    seen_id, clean = set(), []
    for r in rows:
        if r["id"] in seen_id:
            continue
        seen_id.add(r["id"])
        clean.append(r)
    dropped = len(rows) - len(clean)

    for r in clean:
        # 2. family
        if r["weapon"] in fam:
            r["family"] = fam[r["weapon"]]
        else:
            r["family"] = rules.keyword_family(r["weapon"])
            review.append(("family", r["weapon"], r["family"]))
        # 3. owner
        if r["manufacturer"] in own:
            r["parent"], r["home_group"], r["home_strict"] = own[r["manufacturer"]]
        else:
            r["parent"], r["home_group"], r["home_strict"] = rules.keyword_owner(r["manufacturer"], r["hq_country_gur"])
            review.append(("owner", r["manufacturer"], r["home_group"]))
        r["home_hq"] = rules.hq_country(r["manufacturer"], r["hq_country_gur"])
        # 4. tier
        if r["part_name"] in tier:
            r["tier"] = tier[r["part_name"]]
        else:
            r["tier"] = rules.keyword_tier(r["part_name"])
            review.append(("tier", r["part_name"], r["tier"]))
        r["weight"] = weights[r["tier"] - 1]
        # 8. dates
        gy = rules.gur_year(r.get("production_date_gur", ""))
        if years_from == "snapshot":
            r["year"] = int(r["year"]) if r.get("year") else None
            r["year_source"] = r.get("year_source", "")
        elif gy:
            r["year"], r["year_source"] = gy, "GUR"
        else:
            my = rules.marking_year(r["marking"])
            r["year"], r["year_source"] = (my, "parsed marking") if my else (None, "")
        r["gur_year"] = gy

    # 5. de-duplicate within family
    unique, seen = [], set()
    for r in clean:
        key = (r["family"], r["part_name"], first_line(r["marking"]), r["parent"])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return clean, unique, dropped, review


def points_by_country(unique, method):
    """Weighted points per country, and the total."""
    col = "home_" + method
    pts = collections.Counter()
    for r in unique:
        for c, share in homes(r[col]):
            pts[c] += r["weight"] * share
    return pts, sum(r["weight"] for r in unique)


def family_points(unique, method):
    """Per family: (points per country incl. 'EU total', total points)."""
    by_fam = collections.defaultdict(list)
    for r in unique:
        by_fam[r["family"]].append(r)
    return {f: (with_eu(points_by_country(rs, method)[0]), sum(r["weight"] for r in rs)) for f, rs in by_fam.items()}


def with_eu(pts):
    out = dict(pts)
    out["EU total"] = sum(v for c, v in pts.items() if c in rules.EU)
    return out


def index_table(clean, unique, draws, seed):
    fams = sorted({r["family"] for r in unique})
    rng = random.Random(seed)
    samples = [[rng.choice(fams) for _ in fams] for _ in range(draws)]
    n_rows = len(clean)
    out = []
    for m in METHODS:
        col = "home_" + m
        comps = collections.Counter()
        for r in clean:
            for c, share in homes(r[col]):
                comps[c] += share
        comps = with_eu(comps)
        pts, total = points_by_country(unique, m)
        pts = with_eu(pts)
        fam_hit = collections.defaultdict(set)
        for r in unique:
            for c, _ in homes(r[col]):
                fam_hit[c].add(r["family"])
                if c in rules.EU:
                    fam_hit["EU total"].add(r["family"])
        fp = family_points(unique, m)
        boot = collections.defaultdict(list)
        for s in samples:
            t = sum(fp[f][1] for f in s)
            for c in REPORT_COUNTRIES + ["EU total"]:
                boot[c].append(sum(fp[f][0].get(c, 0) for f in s) / t)
        for c in REPORT_COUNTRIES + ["EU total"]:
            out.append({
                "method": m, "country": SHORT.get(c, c),
                "components": round_half_up(comps.get(c, 0)),
                "raw_share": round(comps.get(c, 0) / n_rows, 5),
                "index_share": round(pts.get(c, 0) / total, 5),
                "ci_low": round(percentile(boot[c], 0.05), 5),
                "ci_high": round(percentile(boot[c], 0.95), 5),
                "incidence": round(len(fam_hit.get(c, ())) / len(fams), 5),
            })
    return out


def groups_table(clean, unique, min_components=7):
    """European manufacturer groups with at least min_components entries.
    Subsidiaries GUR lists under their own name are merged into the group
    that owns them (rules.GROUP_MERGE)."""
    by = collections.defaultdict(list)
    for r in clean:
        homes_ = {c for c, _ in homes(r["home_group"])}
        if homes_ & rules.EUROPE:
            by[rules.GROUP_MERGE.get(r["parent"], r["parent"])].append(r)
    out = []
    for g, rs in by.items():
        if len(rs) < min_components:
            continue
        out.append({
            "group": g, "home": rs[0]["home_group"], "owner_strict": rs[0]["home_strict"],
            "components": len(rs),
            "unique_parts": len({(r["part_name"], first_line(r["marking"])) for r in rs}),
            "weapon_families": len({r["family"] for r in rs}),
            "high_priority": sum(1 for r in rs if r["tier"] in (1, 2)),
            "dated": sum(1 for r in rs if r["year"]),
            "dated_2022_on": sum(1 for r in rs if r["year"] and r["year"] >= 2022),
        })
    return sorted(out, key=lambda r: -r["components"])


def years_table(clean):
    c = collections.Counter(r["year"] for r in clean if r["year"] and r["year"] >= 2005)
    return [{"year": y, "components": c[y]} for y in sorted(c)]


def ratio_table(unique):
    firms = read_csv(os.path.join(LOOKUP, "firms.csv"))
    revenue = {r["firm"]: r for r in read_csv(os.path.join(LOOKUP, "revenue_2021.csv"))}
    total = sum(r["weight"] for r in unique)
    pts = collections.Counter()
    for r in unique:
        for f in firms:
            if re.search(f["manufacturer_pattern"], r["manufacturer"], re.I):
                pts[f["firm"]] += r["weight"]
                break
    sum_pts = sum(pts[f["firm"]] for f in firms)
    sum_rev = sum(float(revenue[f["firm"]]["revenue_bn_usd"]) for f in firms)
    out = []
    for f in firms:
        rev = float(revenue[f["firm"]]["revenue_bn_usd"])
        s13, rs = pts[f["firm"]] / sum_pts, rev / sum_rev
        out.append({"firm": f["firm"], "home": f["home"], "index_points": pts[f["firm"]],
                    "index_share": round(pts[f["firm"]] / total, 5), "share_of_13": round(s13, 5),
                    "revenue_bn": round(rev, 3), "revenue_share": round(rs, 5), "ratio": round(s13 / rs, 3),
                    "revenue_basis": revenue[f["firm"]]["revenue_basis"]})
    return sorted(out, key=lambda r: -r["ratio"])


def ledgers_table(index_rows):
    kiel = read_csv(os.path.join(LOOKUP, "kiel_aid.csv"))
    idx = {r["country"]: r for r in index_rows if r["method"] == "group"}
    out = []
    for k in kiel:
        i = idx.get(SHORT.get(k["country"], k["country"]), {})
        out.append({"country": k["country"], "mil_aid_bn": k["mil_aid_bn_eur"], "gdp_2021_bn": k["gdp_2021_bn_usd"],
                    "index_share": i.get("index_share", ""), "ci_low": i.get("ci_low", ""), "ci_high": i.get("ci_high", "")})
    return out


def stats_table(rows_in, clean, unique, dropped):
    t = collections.Counter(r["tier"] for r in unique)
    gur = [r for r in clean if r["gur_year"]]
    calib = [(r["gur_year"], rules.marking_year(r["marking"])) for r in gur]
    calib = [(g, m) for g, m in calib if m]
    dated = [r for r in clean if r["year"]]
    return [
        ("entries_read", len(rows_in)), ("duplicates_dropped", dropped),
        ("components", len(clean)), ("weapon_families", len({r["family"] for r in clean})),
        ("unique_in_family", len(unique)),
        ("dated", len(dated)), ("dated_2022_on", sum(1 for r in dated if r["year"] >= 2022)),
        ("gur_dated", len(gur)), ("gur_dated_2022_on", sum(1 for r in gur if r["gur_year"] >= 2022)),
        ("calib_parsed", len(calib)), ("calib_exact", sum(1 for g, m in calib if g == m)),
        ("calib_within1", sum(1 for g, m in calib if abs(g - m) <= 1)),
        ("tier1", t[1]), ("tier2", t[2]), ("tier3", t[3]), ("tier4", t[4]),
        ("pre_2005", sum(1 for r in dated if r["year"] < 2005)),
    ]


def write(path, rows, fields=None):
    with open(path, "w", newline="", encoding="utf-8") as f:
        if rows and isinstance(rows[0], tuple):
            w = csv.writer(f, lineterminator="\n")
            w.writerow(fields)
            w.writerows(rows)
        else:
            w = csv.DictWriter(f, fieldnames=fields or list(rows[0].keys()), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("snapshot")
    p.add_argument("--out", default=os.path.join(ROOT, "build"))
    p.add_argument("--weights", default="4,3,2,1", help="weights for tiers 1-4")
    p.add_argument("--draws", type=int, default=1000)
    p.add_argument("--seed", type=int, default=20261030)
    p.add_argument("--cutoff", help="raw scrape only: keep entries published on or before YYYY-MM-DD")
    p.add_argument("--years", choices=["parser", "snapshot"], default="parser",
                   help="'snapshot' reuses the edition-1 year column instead of the parser")
    a = p.parse_args()
    weights = [float(x) for x in a.weights.split(",")]

    rows = load_snapshot(a.snapshot, a.cutoff)
    clean, unique, dropped, review = prepare(rows, weights, a.years)
    index_rows = index_table(clean, unique, a.draws, a.seed)

    os.makedirs(a.out, exist_ok=True)
    write(os.path.join(a.out, "index.csv"), index_rows)
    write(os.path.join(a.out, "groups.csv"), groups_table(clean, unique))
    write(os.path.join(a.out, "years.csv"), years_table(clean))
    write(os.path.join(a.out, "ratio.csv"), ratio_table(unique))
    write(os.path.join(a.out, "ledgers.csv"), ledgers_table(index_rows))
    write(os.path.join(a.out, "stats.csv"), stats_table(rows, clean, unique, dropped), ["metric", "value"])
    review = sorted(set(review), key=lambda r: (r[0], str(r[1])))
    write(os.path.join(a.out, "review.csv"), review or [("", "", "")], ["kind", "name", "classified_as"])

    eu = next(r for r in index_rows if r["method"] == "group" and r["country"] == "EU total")
    print(f"{len(clean):,} components, {len(unique):,} unique in family, "
          f"{len({r['family'] for r in clean})} families; EU (parent group) {eu['index_share']:.3%} "
          f"[{eu['ci_low']:.3%}-{eu['ci_high']:.3%}]; {len(review)} names classified by rule -> review.csv")


if __name__ == "__main__":
    main()
