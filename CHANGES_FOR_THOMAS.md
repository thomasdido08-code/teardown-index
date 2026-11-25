# Changes for Thomas: Teardown Index

What changed on branch `iaw-prep-2026-12` (25 November 2026), why, and how to defend each choice. Every method change has a "sceptic asks / you answer" pair.

## Headline numbers, before and after

| Figure | Edition 1 (3 Nov) | Edition 1.1 (25 Nov) | Why it moved |
|---|---|---|---|
| EU share, parent group | 14.512% (rounds to 14.5%) | 14.523% (14.5%) | tier assignments on a few parts, below |
| 90% range | 13.2–15.8% | 13.2–15.9% | bootstrap seed not kept in edition 1 |
| United States | 65.8% | 65.7% | same as EU |
| EU share, listed HQ | 5.0% | 5.0% | – |
| Dated parts made 2022 or later | 46.6% | **40.2%** | stricter date parser |
| Dated parts | 1,083 | 1,178 | stricter parser finds more real codes |
| Date parser exact on GUR-dated parts | 95% (313/330) | 97% (337/348) | – |
| European groups table | 13 hand-picked | 19 (every group with 7+ parts) | documented rule |

The one change you'll notice in a pitch is **47% → 40%**: "made after the first EU export bans". It is still a large share. Say 40%.

## 1. The scoring pipeline is now public (`scripts/pipeline/`)

**What.** A scraper for GUR's components database and the scoring code: cleaning, weapon families, owners, tiers, de-duplication within families, the three attribution methods, the family bootstrap, dates and the size adjustment. The 30 October snapshot is in `data/raw/gur/`, so anyone can rebuild the tables.

**Acceptance test.** On the 30 October snapshot, 307 of 308 checks pass. Counts, raw shares and incidence are exact. Index shares are within 0.07 points. Ranges are within bootstrap noise.

**Why not exact?** Two things from edition 1 were not saved: the keyword list that assigned tiers, and the bootstrap seed. The tier column saved in the snapshot differs from what the published index used on a handful of parts: 15 weighted points out of 16,221 (0.09%). I did not try to fake an exact match. The pipeline uses the saved column, and edition 1.1 publishes its output.

- *Sceptic: "So your published numbers couldn't be reproduced?"* → They reproduce to within 0.07 points on every country and method, and the exact pipeline is now public, so edition 1.1 can be reproduced exactly. The small gap came from a tier list that wasn't saved; it changes no ranking and no headline at one decimal place.
- *Sceptic: "Tiers come from a lookup table, not keyword rules?"* → The lookup records the decision made for each of the 2,483 part names in the snapshot. Keyword rules (`rules.py`) classify new names, and every one they classify is listed for manual review. That is more auditable than rules alone.

**What to run locally.** The live scrape takes several hours at a polite rate (it was running when this was written). Run it yourself and compare:

```
python scripts/pipeline/scrape_gur.py
python scripts/pipeline/score.py data/raw/gur/gur_raw_<date>.jsonl.gz --cutoff 2026-10-28 --out build/live
python scripts/pipeline/compare.py build/live
```

Expect small differences: GUR edits entries after publication.

## 2. Stricter date parser (46.6% → 40.2%)

**What.** Edition 1's parser read year-week codes out of part numbers. `LMX2306` became "2023, week 6", `MAX1831` became "2018". It also missed real codes after a "#". The new parser skips the part-number line, accepts only a four-digit code (optionally with "#" before or up to three letters after), and on one-line markings only a bare four-digit token.

- *Sceptic: "You changed the parser and the number fell. Why trust this one?"* → It is tested against GUR's own dates: it reads a year for 348 of the 563 parts GUR dated and gets 337 exactly right (97%), better than the old 95%. And the old parser's false dates were visibly wrong when you looked at them.
- *Sceptic: "Year codes on chips can be ambiguous."* → Yes. That's why it's a share of *dated* parts and why GUR's own dates are reported separately (62% from 2022). The direction is the same either way: a large share of parts were made after the 2022 bans.

## 3. Weighting robustness (answers open question 1)

| Weights (tiers 1/2/3/4) | EU share | US | China |
|---|---|---|---|
| 4/3/2/1 (headline) | 14.5% | 65.7% | 5.8% |
| 1/1/1/1 (unweighted) | 14.7% | 61.3% | 7.4% |
| 3/2/1/1 | 14.5% | 66.5% | 5.5% |
| 5/3/2/1 | 14.5% | 66.8% | 5.4% |

The EU is second under every weighting, and the top four never change order.

- *Sceptic: "Your weights are arbitrary."* → They follow the priority list the EU, US, UK and Japan use, and the EU finding doesn't depend on them: unweighted it is 14.7%. Weighting changes the US and China shares, because Chinese parts are more often discrete and passive.

## 4. STMicroelectronics and the size adjustment (open questions 2 and 3)

- **STMicro split.** Half France/half Italy, all France or all Italy: the EU share is 14.5% every time. The question that matters is whether STMicro counts as European at all. Filed under Switzerland, as GUR lists it, the EU share is 8.9%.
  - *Sceptic: "STMicro is Swiss."* → Its headquarters are in Geneva, but its main shareholders, through a joint holding, are the French and Italian states. We count it as EU-owned and publish the listed-HQ method beside it (5.0% EU), so readers can see the effect.
- **Size adjustment.** STMicro (0.76–0.86×), Infineon (0.54–0.70×) and NXP (0.40–0.42×) stay below 1× under every weighting. u-blox's 3.9× is a finding about navigation *modules*: it vanishes if only chips count.
  - *Sceptic: "Total revenue is the wrong denominator."* → Agreed that it's a stand-in. Segment revenue is paid data. The section is labelled indicative, and the page now says the product-mix explanation is untested.

## 5. Publication check

- No secrets or local paths in the repository.
- **Font licence was missing**: README promised SIL OFL, but the OFL file wasn't there. Added, with the copyright notices for all three fonts, taken from the official repositories.
- All paths in `index.html` are relative and the page renders locally with edition 1.1 data and no console errors.
- External links: all resolve. GUR, Kiel, RUSI coverage, u-blox, Renesas, Evertiq and Mezha answered a scripted check; the 11 that refuse scripts (SEC filings for Intel, Micron, Maxim, Microchip and TI; Analog Devices, Vishay and NXP investor pages; GlobeNewswire for STMicro; Business Wire for Xilinx and onsemi) were opened in a browser on 25 November and each shows the right 2021 results release.
- CITATION.cff updated to version 1.1, 25 November 2026.

## Things you need to decide or do

1. **The repo is already public on GitHub** (you described it as private). If that was not intended, change it yourself; I haven't touched visibility.
2. **The GUR snapshot is now in the repo** (`data/raw/gur/`, 6,252 rows) so that the index can be rebuilt. GUR publishes it openly, but it carries no explicit licence. Keep it, or replace it with the scraper alone?
3. **Related link to the Diversion Risk Scorer**: not added, because that repo is private. When it's public, add under "Related" in README.md:
   `[Diversion Risk Scorer](https://thomasdido08-code.github.io/diversion-risk-scorer/): which recipient states carry the highest risk that arms sold to them are diverted.`
4. **Out of scope, as you asked:** the firm-by-firm match against CAR iTrace and RUSI.

**Ready to go public:** yes, once you decide point 2.
