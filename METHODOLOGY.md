# Teardown Index: method note

Edition 1 · 3 November 2026 · Thomas Di Domenico

## Summary

Traced to the parent companies that own the brands, EU firms supply 14.5% of the weighted foreign parts Ukrainian intelligence has recovered from Russian weapons (90% range 13.2–15.8%). That makes the EU, taken as a bloc, the second-largest source after the United States (65.8%).

The Teardown Index answers one question: whose firms make the foreign electronics found inside Russia's weapons? It does not measure trade volumes or who shipped the parts.

Two findings:

1. **GUR's own labels hide European exposure.** By listed headquarters the EU share is 5.0%; by parent group it is 14.5%. Most of the gap is STMicroelectronics, filed under Switzerland, and Infineon's US-listed units, filed under the United States.
2. **European exposure mostly tracks company size.** Against 2021 revenue, STMicroelectronics (0.81×), Infineon (0.65×) and NXP (0.40×) turn up less often than their size predicts. The exception is Switzerland's u-blox, whose navigation modules appear 3.9× more often than its revenue predicts.

How these parts relate to what Russia fires and loses is covered by the companion [Burn Rate Index](https://thomasdido08-code.github.io/burn-rate-index/).

## Data

The index rests on one primary source, GUR's components database, with supporting sources for aid and company size.

| Source | What it gives | Coverage | Retrieved |
|---|---|---|---|
| [GUR War & Sanctions: components in weapons](https://war-sanctions.gur.gov.ua/en/components) | 6,252 foreign components with weapon, part name, marking, manufacturer, HQ country and sometimes production date | All entries to 28 Oct 2026 | 30 Oct 2026 |
| [Kiel Institute Ukraine Support Tracker](https://www.kielinstitut.de/publications/ukraine-support-tracker-data-6453/) | Military aid allocated by country, € bn, and 2021 GDP | Release 31, Jan 2022–Aug 2026 | 30 Oct 2026 |
| Company annual results (see Sources) | 2021 revenue for 13 chipmakers | Calendar 2021 or nearest fiscal year | 30 Oct 2026 |

GUR is the intelligence service of a country at war. Its attributions are treated as claims and tested in Validation below.

## Method

The index is a country's share of all weighted foreign parts, after each part is counted once per weapon type and attributed to its parent company.

1. **Clean.** All 522 pages of GUR's list were collected; 10 duplicate entries were removed, leaving 6,252 parts.
2. **Merge weapon families.** Airframes and missiles of the same model (for example 21 separate Shahed-136 teardowns) are merged into 99 weapon families. A part counts once per family, leaving 5,536 entries. This stops heavily studied weapons from dominating.
3. **Weight by criticality.** Each part gets the weight of its tier on the Common High Priority List used by the EU, US, UK and Japan: integrated circuits ×4 (2,959 entries), navigation and radio modules ×3 (177), discrete and passive parts ×2 (1,454), everything else ×1 (946). Tiers are assigned from GUR's part names by keyword.
4. **Attribute to owners.** Three methods are reported: GUR's listed headquarters; parent group, which moves subsidiaries home (Infineon's International Rectifier, Cypress and Spansion; NXP's Freescale) and splits STMicroelectronics evenly between France and Italy, its two state shareholders; and strict ownership, which also moves Chinese-owned Nexperia and Ampleon to China and EPCOS to Japan's TDK. Parent group is the headline.
5. **Score.** Index = a country's weighted parts ÷ all weighted parts. Weapon-family incidence (share of families containing at least one part from that country) is reported beside it.
6. **Range.** The 99 weapon families are resampled with replacement 1,000 times; the 5th and 95th percentiles give the 90% range.
7. **Date the parts.** GUR publishes production dates for 563 parts. Year-week codes in chip markings (for example "2303" = 2023, week 3) raise this to 1,083.
8. **Adjust for size.** For 13 chipmakers, each firm's share of the index among them is divided by its share of their combined 2021 revenue. Euro and Swiss franc revenue are converted at 1.19 $/€ and 1.094 $/CHF.

## Results

Under parent-group attribution the United States leads by far, the EU bloc is second, and Germany is the largest single European source.

| Country | Index | 90% range | Weapon families hit | Parts found |
|---|---|---|---|---|
| United States | 65.8% | 62.5–69.2% | 99% | 3,936 |
| **EU (bloc)** | **14.5%** | **13.2–15.8%** | **90%** | **888** |
| China | 5.8% | 3.6–7.9% | 51% | 453 |
| Germany | 5.4% | 4.5–6.3% | 75% | 352 |
| Japan | 4.2% | 3.4–4.9% | 65% | 286 |
| Taiwan | 3.0% | 2.5–3.6% | 61% | 174 |
| France | 2.9% | 2.5–3.4% | 71% | 162 |
| Italy | 2.9% | 2.4–3.3% | 69% | 153 |
| Netherlands | 2.8% | 2.3–3.4% | 55% | 173 |
| Switzerland | 1.6% | 1.2–2.1% | 36% | 115 |

France, Italy and the Netherlands have overlapping ranges and cannot be ranked against each other. France's and Italy's places depend on the STMicroelectronics split.

**Size-adjusted.** Among 13 chipmakers, the ratio of index share to revenue share runs from 3.9× (u-blox) and 3.75× (Analog Devices) down to 0.14× (Micron). Russia's dependence concentrates in analog and RF chips, programmable chips (Xilinx 2.2×, Altera 3.1×) and satellite navigation. The large European firms sit below 1×, which most likely reflects their automotive-heavy product mix rather than better compliance; that explanation is untested.

**Timing.** Of 1,083 dated parts, 47% were made in 2022 or later, after the first EU export bans. GUR's own dates alone give 62%, because GUR tends to publish dates on newer parts.

## Robustness and validation

The EU share holds at 14–15% under every method except GUR's raw headquarters labels, and the source agrees with an independent teardown study on the largest supplier.

| EU share under | Raw count | Index | 90% range | Families hit |
|---|---|---|---|---|
| Parent group | 14.2% | 14.5% | 13.2–15.8% | 90% |
| Strict ownership | 13.7% | 14.1% | 12.8–15.4% | 90% |
| Listed HQ | 6.1% | 5.0% | 4.3–5.9% | 76% |

**Weighting.** The priority-list weights (×4/×3/×2/×1) are a judgement. Re-scoring with other weights barely moves the EU share, and the EU stays second behind the United States every time:

| Weights (tiers 1/2/3/4) | EU share | 90% range | United States | China | Top 10 single countries, in order |
|---|---|---|---|---|---|
| 4/3/2/1 (headline) | 14.5% | 13.2–15.9% | 65.7% | 5.8% | US, China, Germany, Japan, Taiwan, France, Italy, Netherlands, Switzerland, South Korea |
| 1/1/1/1 (unweighted) | 14.7% | 13.5–16.2% | 61.3% | 7.4% | US, China, Germany, Japan, Taiwan, Netherlands, France, Italy, Switzerland, Russia |
| 3/2/1/1 | 14.5% | 13.1–15.9% | 66.5% | 5.5% | US, China, Germany, Japan, Netherlands, France, Taiwan, Italy, Switzerland, South Korea |
| 5/3/2/1 | 14.5% | 13.2–15.9% | 66.8% | 5.4% | US, China, Germany, Japan, France, Taiwan, Italy, Netherlands, Switzerland, South Korea |

Weighting matters for the United States and China, not for the EU: the US share rises with the weight on integrated circuits, China's falls, because Chinese parts are more often discrete and passive ones. The first four places never change. Taiwan, France, Italy and the Netherlands swap places, as their overlapping ranges already said they could. Full table: `data/raw/weighting.csv`, from `scripts/pipeline/robustness.py`.

- **Cross-check with RUSI.** RUSI's *Silicon Lifeline* (Aug 2022) took apart 27 Russian weapons. As reported by eeNews Europe and VOA, US firms made 318 of more than 450 foreign parts (about 71%), against 67% here. Japan differs most (about 13% in RUSI, 4% here), likely because RUSI's early-war sample predates the shift to Chinese-made drone parts. RUSI's company tables were not checked.
- **Cross-check with the International Working Group on Russian Sanctions (2023).** Six of the seven leading makers it names are in this index's top seven groups.
- **Photo spot-check.** Of 10 random GUR entries, the logo or part number in GUR's own photo confirmed the maker in 7; 3 were too blurry to read; none contradicted it.
- **Marking check.** For eight firms, 61–90% of entries carry that firm's part-number prefix or name in the marking text. Most misses are short codes that do not name the part.
- **Date parser.** On the 563 parts GUR had already dated, the parser read a year for 330 and matched it exactly for 313 (95%).

## Limits and open questions

The index measures brand exposure in recovered weapons; it cannot show trade volumes, supply routes or corporate responsibility.

**Known limits**

- **Sampling.** Counts reflect what GUR chose to take apart and publish. Family-level counting and resampling reduce this but do not remove it.
- **Routes.** Most parts reach Russia through distributors in China, Hong Kong and Central Asia. GUR names importers for only 25 items.
- **Attribution.** The even STMicroelectronics split and keeping EPCOS under Germany in the headline method are choices; the strict method shows their effect.
- **Tiers.** Priority-list tiers come from part names by keyword, so some parts are misfiled.
- **Size adjustment.** Total 2021 revenue stands in for market share in the specific parts Russia buys, which is only available from paid research.
- **Not yet done.** A firm-by-firm match against CAR iTrace and RUSI's full company tables.

**Open questions**

1. ~~Is the priority-list weighting (4/3/2/1) defensible, or should the headline be unweighted?~~ **Answered (November 2026):** the EU share is 14.5–14.7% under every weighting tested, unweighted included (see Weighting above). The weights change the US and China shares, not the EU finding. The headline keeps 4/3/2/1 because it tracks the priority list the EU itself uses.
2. Is the parent-group attribution, especially the STMicroelectronics split, the right default?
3. Is total revenue an acceptable denominator for the size adjustment, or should that section be dropped?
4. What independent dataset would best test GUR's attributions?

## Sources

- [GUR War & Sanctions: components in weapons](https://war-sanctions.gur.gov.ua/en/components)
- [Kiel Institute Ukraine Support Tracker data](https://www.kielinstitut.de/publications/ukraine-support-tracker-data-6453/)
- [eeNews Europe on RUSI's Silicon Lifeline](https://www.eenewseurope.com/en/report-details-restricted-european-and-us-tech-in-russian-weapons-in-ukraine/) and [VOA](https://www.voanews.com/a/silicon-lifeline-report-reveals-western-technology-guiding-russia-s-weapons-in-ukraine/6708050.html)
- [Mezha on the International Working Group's 2023 report](https://mezha.media/en/2023/07/04/despite-the-sanctions-1-057-foreign-components-from-155-companies-are-used-in-russian-weapons)
- Revenue: [Analog Devices](https://investor.analog.com/news-releases/news-release-details/analog-devices-reports-record-fourth-quarter-and-fiscal-2021), [Maxim](https://www.sec.gov/Archives/edgar/data/743316/000074331621000021/maximq421epr.htm), [Texas Instruments](https://www.sec.gov/Archives/edgar/data/97476/000009747622000004/q42021txnex99-er1.htm), [STMicroelectronics](https://www.globenewswire.com/news-release/2022/01/27/2373956/0/en/STMicroelectronics-Reports-Q4-and-FY-2021-Financial-Results.html), [Infineon](https://evertiq.com/design/50941), [NXP](https://media.nxp.com/news-releases/news-release-details/nxp-semiconductors-reports-fourth-quarter-and-full-year-2021), [Microchip](https://www.sec.gov/Archives/edgar/data/827054/000082705422000076/exhibit991q4fy22.htm), [Xilinx](https://www.businesswire.com/news/home/20210504006183/en), [Intel](https://www.sec.gov/Archives/edgar/data/50863/000005086322000006/q421_earningsrelease.htm), [onsemi](https://www.businesswire.com/news/home/20220207005182/en/onsemi-Reports-Fourth-Quarter-and-2021-Financial-Results), [Micron](https://www.sec.gov/Archives/edgar/data/723125/000072312521000060/a2021q4ex991-pressrelease.htm), [Renesas](https://renesas.com/en/about/newsroom/renesas-reports-financial-results-year-ended-december-31-2021), [Vishay](https://ir.vishay.com/news-releases/news-release-details/vishay-reports-results-fourth-quarter-and-year-2021), [u-blox](https://www.u-blox.com/en/ad-hoc-releases/u-blox-reports-full-year-2021-financial-results)

## Change log

- **3 November 2026**: edition 1.
