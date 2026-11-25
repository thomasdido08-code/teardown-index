# Data dictionary

All shares are fractions (0–1). These tables are the published output of the scoring pipeline run on GUR's database on 30 October 2026.

## raw/

| File | One row per | Columns |
|---|---|---|
| `index.csv` | attribution method × country | `method` (`group` = parent group, `strict` = strict ownership, `hq` = GUR's listed headquarters), `country` (`EU total` = the bloc), `components` (parts found), `raw_share` (share before de-duplication and weighting), `index_share` (the index), `ci_low`, `ci_high` (90% bootstrap range), `incidence` (share of weapon families with at least one part) |
| `groups.csv` | European manufacturer group with at least seven parts (subsidiaries merged into their owner) | `group`, `home` (parent-group attribution), `owner_strict`, `components`, `unique_parts`, `weapon_families`, `high_priority` (priority-list tier 1–2 parts), `dated`, `dated_2022_on` |
| `years.csv` | production year | `year`, `components` (dated parts made that year, 2005–2026) |
| `ratio.csv` | chipmaker | `firm`, `home`, `index_points`, `index_share`, `share_of_13` (share of the index among the 13 firms), `revenue_bn` (2021, $bn), `revenue_share`, `ratio` (share_of_13 ÷ revenue_share), `revenue_basis` |
| `ledgers.csv` | donor country | `country`, `mil_aid_bn` (bilateral military aid allocated, €bn, Jan 2022–Aug 2026), `gdp_2021_bn`, `index_share`, `ci_low`, `ci_high` |
| `crosscheck.csv` | measure | `measure`, `gur` (share in GUR data, listed HQ, raw count), `rusi_2022` (RUSI *Silicon Lifeline* as reported), `note` |
| `markcheck.csv` | firm | `firm`, `checked` (entries checked), `consistent` (marking carries the firm's part-number prefix or name) |
| `weighting.csv` | tier weighting | `weights` (tiers 1/2/3/4), `label`, `eu_index`, `eu_ci_low`, `eu_ci_high` (parent-group method), `us_index`, `china_index`, `germany_index`, `eu_rank_vs_countries` (EU bloc against single countries), `top10` (single countries with their shares, in order) |
| `stats.csv` | metric | `metric`, `value`: counts behind the method (parts, families, tiers, dated parts, parser calibration, photo spot-check, overlap with the International Working Group's top makers) |

## derived/

| File | Contents |
|---|---|
| `headline.json` | Headline figures recomputed from the tables by `scripts/build.py`, plus any failed consistency checks |
