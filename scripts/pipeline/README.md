# Scoring pipeline

This folder rebuilds the index tables in `data/raw/` from GUR's components database. Everything is Python 3 standard library; there is nothing to install.

```
python scripts/pipeline/scrape_gur.py                              # 1. scrape GUR (about 3 hours)
python scripts/pipeline/score.py data/raw/gur/<snapshot> --out build/   # 2. score
python scripts/pipeline/compare.py build/                          # 3. compare with the published tables
python scripts/pipeline/robustness.py data/raw/gur/<snapshot>      # 4. weighting robustness table
```

| File | What it does |
|---|---|
| `scrape_gur.py` | Reads every list page of [GUR War & Sanctions: components](https://war-sanctions.gur.gov.ua/en/components), then every component page, one request every 1.5 seconds. Saves `data/raw/gur/gur_raw_<date>.jsonl.gz`: every labelled field GUR shows, including the publication date. |
| `score.py` | Cleans, merges weapon families, attributes owners, assigns tiers, de-duplicates within families, scores the three attribution methods, bootstraps the 90% range (1,000 draws, fixed seed), dates the parts and runs the size adjustment. Writes the tables plus `review.csv`. |
| `rules.py` | The rules: EU membership, the STMicroelectronics split, the date parser, and the keyword rules for names that are not yet in a lookup table. |
| `compare.py` | The acceptance test against `data/raw/`. |
| `robustness.py` | Re-scores under alternative tier weights. |
| `make_lookups.py` | One-off: wrote the lookup tables from the edition-1 snapshot. |

## Inputs

- `data/raw/gur/gur_components_2026-10-30.csv`: the edition-1 snapshot (6,252 components, all entries to 28 October 2026, scraped 30 October 2026).
- `data/pipeline/families.csv` (201 weapons → 99 families), `owners.csv` (642 manufacturers → parent group and home under each method), `tiers.csv` (2,483 part names → tier): the decisions made for edition 1, one row per name.
- `data/pipeline/firms.csv`: which manufacturer names belong to each of the 13 chipmakers in the size adjustment.
- `data/pipeline/revenue_2021.csv`, `kiel_aid.csv`: chipmaker revenue and Kiel aid figures, sources in METHODOLOGY.md.

## New names

A new scrape will contain weapons, manufacturers and part names that are not in the lookup tables. `score.py` classifies them by rule (`rules.py`) and lists every one in `review.csv`. Check each, then add it to the lookup table by hand, so that every decision is recorded and reviewable.

## Acceptance test on the 30 October 2026 snapshot

```
python scripts/pipeline/score.py data/raw/gur/gur_components_2026-10-30.csv --years snapshot --out build/
python scripts/pipeline/compare.py build/
```

Result: 307 of 308 checks pass.

- **Exact:** components, weapon families (99), unique parts within families (5,536), raw shares, family incidence and component counts for every country under all three methods; European group counts; GUR-dated parts (563).
- **Index shares:** within 0.0007 (0.07 points) of the published values for every country and method. EU (parent group): 14.523% against 14.512%.
- **90% ranges:** within 0.005 of the published bounds. The edition-1 random seed was not kept, so ranges cannot match to the last digit.
- **Size ratios:** within 5%.
- **One failure:** GUR-dated parts made 2022 or later, 347 against 348 published. GUR's dates parse identically on all 563 dated parts, so the published count was off by one.

**Why index shares are not exact.** The published index was computed with tier assignments that differ from the tier column saved in the snapshot on a handful of parts: the published total is 16,221 weighted points, the snapshot column gives 16,236 (2,959/177/1,454/946 parts in tiers 1–4 published, 2,965/177/1,451/943 in the column). The keyword list that produced the published tiers was not kept. The difference is 15 points out of 16,221 (0.09%), well inside every 90% range.

**Dates.** `--years snapshot` reuses edition 1's year column. Without it, the pipeline uses the stricter parser in `rules.py`. Edition 1's parser read year-week codes out of part numbers (for example `LMX2306` as 2023, `MAX1831` as 2018) and missed codes such as `#2216`. The stricter parser dates 1,178 parts instead of 1,083, reads 337 of 348 GUR-dated parts exactly (96.8%, against 313 of 330, 94.8%), and finds 40.2% made in 2022 or later instead of 46.6%.

## Running a live scrape locally

```
python scripts/pipeline/scrape_gur.py
python scripts/pipeline/score.py data/raw/gur/gur_raw_<date>.jsonl.gz --cutoff 2026-10-28 --out build/live_cutoff
python scripts/pipeline/compare.py build/live_cutoff
```

`--cutoff` keeps entries GUR published on or before that date, which approximates the edition-1 snapshot. Expect small differences: GUR edits entries after publication (names, manufacturers, dates), and new names go through the keyword rules.
