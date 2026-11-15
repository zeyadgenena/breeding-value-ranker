# Phase 1 findings and decision note

Date: 2026-11-14. Fee data extended on 2026-11-15.

## Where Phase 1 stands

**The backtest has not been run on real horses.** None of the three Phase 1
success criteria is met yet, and nothing below says whether the hypothesis is
true or false.

What is done:

- The data workbook, with the data model from the plan and 52 real stallions entered.
- A dated fee history for those stallions, 2018 to 2027: 474 rows (231 advertised fees, 23 private treaty, 220 auction bids), each with its source.
- The scoring, ranking and backtest script, with 17 passing tests.
- A check of all four data sources and what their terms allow.
- A test of the method on made-up data with a known answer, which shows how much real data the backtest needs before its verdict means anything.

What is not done: collecting foal-level records. That has to go through your own
AQHA member login (see below), so it is the next step and it is yours to start.

## The matcher and its test (added 2026-11-15)

The app's front page is now a simple matcher: what you have, your budget, one
best match. It ranks on stallion-level foal results from the public QData
leaderboards, which the original plan did not use, because foal-by-foal records
are still missing. It was tested against the 2019 to 2025 seasons over six
rounds. The full write-up is [qa/RESULTS.md](qa/RESULTS.md). In brief:

- At a $2,000 budget, 14 of 21 past picks went on to sire a top-50 earning foal from that crop, against 18% for the average stallion at that price. Under $1,500 it was about 1 pick in 4 or 5.
- In 122 public online sales, young horses by these stallions sold for 1.7 times the stud fee at the median, and none reached $20,000. The large outcomes are prize money, not resale.
- The test cannot say what one foal's chance is, because crop sizes are unknown. That still needs the AQHA all-foals record.

**Expected sale price and return (added 2026-11-15).** The app now gives a
likely sale price for a foal by every stallion and ranks the options by return
on the stud fee. A price model was trained in ten versions on 240 public sales,
and 128 combinations of factors were searched. Findings:

- A yearling colt or filly sells for about $2,600 to $2,900 whoever the sire is. A weanling sells for about $3,400 to $3,800. The stud fee does not move the price.
- So the best return on resale is the lowest stud fee: about 2.6 to 2.8 times a $1,000 fee, against 1.3 to 1.5 times a $2,000 fee. Real sales by $1,000 stallions came in a little lower, at 2.2 times.
- The best model explains 14% of the difference between sales, and the sire accounts for about one point of that. Two sales in three landed between half and double the estimate.
- These are public online auction prices. The best prospects sell privately, so the figures understate what a top sire's best foal can bring.
- One year after breeding there is no sale price, because the foal has only just been born. The first sale points are weanling (about 18 months) and yearling (about 2 years).

**More data and a foal-by-foal model (added 2026-11-15).** Three new public
sources: every QData halter leaderboard in full, every horse shown in the
futurity classes at the Halter Million in 2024 to 2026, and each sold lot's own
page. Findings:

- The ranking held on a wider pool: 86 stallions, eight seasons, 16 of 24 picks at a $2,000 budget against 16% for the average stallion.
- Foal by foal, a top-20 sire and a mare that has already produced an earner each add about 12 points to the chance of a top-three futurity finish: 14% with neither, 37% with both.
- Among top-20 sires, nothing tried tells whose foals place higher.
- The sale-price model did not improve with more detail. It still explains about 13%.
- Everything per foal is for foals that were shown. Crop sizes are still missing.

**Arabians (added 2026-11-15).** A first version exists because the horses this
tool is for are Arabian in type. It has prices for 218 stallions and 403 halter
placings, but the placings come from one barn's list of its own wins, so the
ranking is a list to check by hand. The best source, the Scottsdale show's full
class results, forbids automated collection in its terms and was not used.

This matcher is separate from the backtest described in the rest of this note,
which waits on foal-by-foal records.

## What the data sources can deliver

| Source | Finding |
|---|---|
| Quarter Horse Resource | Free official pedigrees, one horse per lookup. Good for sire, dam, dam sire, color. No bulk export. |
| QStallions directory | Much thinner than the plan assumed. It lists only stallions whose owners pay to enroll. On 2026-11-14 the halter category had 7 stallions: 5 with a dollar fee ($1,750 to $2,500), 2 at private treaty. Only 2 of AQHA's 2025 top-10 halter sires are in it. |
| QData Leaderboards | Free top-50 halter sires by progeny earnings, for all-time and each year from 2018 to 2026. Nine dated snapshots, but only of the winners. |
| AQHA show records | Not freely available per foal. The route is AQHA Records: Record 70, Get of Sire Totals, All Foals, at $5 per 100 foals for members ($10 for non-members). Membership is $65 a year. Produce of Dam is $4 per mare. |
| Sale results | Several public auction result pages exist. I did not verify which fields they publish. |
| Stallion-service auctions | Found on the second pass. Yearly futurity fundraiser auctions on internethorseauctions.com print each stallion's advertised breeding fee, chute fee and season on its lot page, and show the winning bid. Fourteen auctions, 2018 to 2025. |
| Internet Archive | Holds the full QStallions directory data for two past dates: 2023-10-30 (19 halter stallions, 15 with a dollar fee) and 2025-05-04 (7 halter stallions). |
| Historical stud fees | Found, through the two sources above plus the season label on each stallion's QStallions page. |

Two consequences:

1. **Automated collection from aqha.com is off the table.** Its robots.txt sets a 30 second crawl delay, disallows the show-leader detail pages, and blocks AI crawlers by name. Foal records should be ordered through your member account.
2. **Past fees can be found, one stallion at a time.** My first pass found no source of past stud fees and called that the biggest gap. The second pass found one: stallion-service auction lot pages. Seasons 2019 to 2025 can be priced for stallions that were offered there, and the workbook now holds those prices for 52 stallions. Foal records for 30 to 40 stallions should cost roughly $250 to $300 in total, so neither side now looks like a blocker.

Details and links are in the Sources tab of the workbook.

## Fee history for the seven listed stallions

Advertised (listed) fee by breeding season, in dollars. PT means private treaty.

| Stallion | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 |
|---|---|---|---|---|---|---|---|---|---|---|
| Best Kept Secrete | | PT | 2,500 | 2,500 | 2,500 | 2,500 | 2,500 | 2,500 | 2,500 | |
| Rumerz | | PT | 2,500 | 2,500 | 2,500 | 2,500 | 2,500 | 2,500 | 2,500 | |
| Heartz On Fire | | 2,000 | 2,000 | 2,000 | 2,000 | 2,000 | 2,000 | PT | | |
| Evinceble | | | 1,850 | 1,850 or 2,250 | 2,250 | 2,250 | 2,150 | 2,150 or 2,750 | | 2,250 |
| Raylan Givens | | | | | | | | 1,500 | | 2,000 |
| Quinlan | | | | | | | | 1,750 | 1,750 | |
| Valentino | 1,500 | | | | | PT | | PT | PT | |

Blank means no figure was found for that season. The workbook also holds 46 winning auction bids for the same years.

What the rows show:

- **These seven hardly change their fees.** Best Kept Secrete and Rumerz have been $2,500 for seven seasons, Heartz On Fire $2,000 for six. From these seven alone I first concluded that fees were too flat and too close together for price to matter. The wider pool below shows that was wrong: fees differ a lot between stallions.
- **Auction prices are lower and move more.** Across 38 lots with both figures, the winning bid for a breeding was 71 percent of the advertised fee at the median (range 48 to 103 percent). 46 of the 48 lots sold. If you would buy breedings this way, the auction price is the price that matters, and `--fee-basis auction` ranks on it.
- **Sources disagree on what the fee includes.** Evinceble's two figures for 2021 and for 2025 differ by about the size of the chute or booking fee ($350 to $600). Some pages fold it into the fee and some add it on top. The workbook records what each page printed in its own column.
- **Two of the seven have no current price.** Valentino was advertised at $1,500 in 2018, died in 2020, and has been private treaty, frozen semen only, since. Heartz On Fire has been private treaty since 2025.
- **Two are too new to judge.** Quinlan's first foals arrive in 2026. Raylan Givens' first crop was 2023.

One lead I did not use: search excerpts of the previous farm's public Facebook posts put Evinceble at $2,250 for 2022 (which matches) and $2,750 for 2026. I did not open those posts, so 2026 is not in the workbook.

## The wider pool: 45 more stallions

On 2026-11-15 I extended the fee history to every Quarter Horse stallion that was offered in at least three seasons of the East Coast Halter Futurity stallion-service auction. Three seasons is the least the backtest can use. That added 45 stallions to the seven above.

| | |
|---|---|
| Stallions in the workbook | 52 |
| With an advertised fee in three or more seasons | 44 |
| With an advertised fee in five or more seasons | 20 |
| Stallions a backtest could price, by as-of year | 36 (2019), 42 (2020), 44 (2021), 42 (2022), 38 (2023), 37 (2024) |
| Advertised fees on file | 231, from $500 to $2,750. Half fall between $1,000 and $2,000. |
| Auction bids on file | 220. Median 62 percent of that season's advertised fee, range 42 to 109 percent (184 could be matched). |
| Stallions with a dollar fee for 2025 or later | 17 |

What the pool shows:

- **The fee side is now big enough.** The synthetic test asked for about 40 stallions. A backtest at any as-of year from 2019 to 2024 could price 36 to 44.
- **Price differs a lot between stallions and little over time.** The dearest stallion costs more than five times the cheapest. Of the 44 stallions with three or more priced seasons, 15 never changed their fee and 14 moved it by more than a quarter. So "per dollar" has real differences to work with, but they are differences between stallions, not timing.
- **It covers leading sires and ordinary ones.** Eight of AQHA's 2025 top-ten halter sires are in the workbook (all but My Intention and FG Born Legacy), alongside stallions standing for $500 to $1,000.
- **Current prices are thinner.** Only 17 stallions have a dollar fee for 2025 or later, because I did not find the 2026 auction on this site. That does not affect a backtest, but a ranking for today would need this season's fees topped up.

What to check before relying on it:

- Lot pages are typed by consignors. Where pages disagreed on a registration number I kept the seven-digit AQHA-style one and noted the other in the Stallions tab. Confirm each against the free pedigree lookup before ordering records.
- Two stallions, DGS Vintage and MMR Jinx On Me, have no AQHA-style number on any page. Ten have no confirmed dam's sire.
- The pool is not a random sample. It is stallions whose owners gave breedings to a futurity auction in three or more years.

## What the synthetic test showed

I generated made-up horse populations (40 stallions, 18 years) in which the true
answer is known, then ran the full backtest on 100 of each. "Sire share" is how
much of true foal quality comes from the sire. A rule of thumb from animal
breeding puts it at about a quarter of heritability, so 8 percent matches a
trait with heritability near 0.3. Show points are a noisy stand-in for
conformation, so the real figure is probably at or below that.

How often the backtest passes when underpriced stallions really exist:

| Sire share | 38 foals per stallion | 95 foals per stallion | 237 foals per stallion |
|---|---|---|---|
| 4% | 6% | 42% | 73% |
| 8% | 42% | 78% | 97% |
| 15% | 58% | 93% | 99% |

How often it passes when there is nothing to find:

| World | 95 foals per stallion | 237 foals per stallion |
|---|---|---|
| Stallions do not differ at all | 10% | 5% |
| Stallions do not differ, but pricey stallions get better mares (dam adjustment on) | 10% | 23% |
| Same, dam adjustment off | 17% | 36% |

What this means for the real project:

- **About 100 scored foals per stallion across about 40 stallions** gives a realistic effect a 4 in 5 chance of being detected. At 40 foals per stallion it is a coin flip or worse. Halter is a small discipline, so the real pool may be smaller than this. If it is, a FAIL will mean "cannot tell", not "no effect".
- **Mare quality is the real threat.** When better mares go to pricier stallions, the method passes a no-effect world up to 1 time in 4 even with the dam adjustment on, because dam quality is measured with noise and the adjustment only removes part of it. More data makes this worse, not better. Check the `avg_dam_quality_then` column in the Backtest tab: if the top picks had better mares than the pool, discount the result.
- The plan's criterion, "outperform on at least one outcome measure", is too easy. A looser rule I tried first passed 12 to 14 percent of no-effect datasets and up to 41 percent of confounded ones. The script now uses one pre-chosen measure and a stricter bar.
- The three example files in `synthetic/` all return FAIL. For `no_effect` and `confounded` that is the right answer. The `planted` file misses narrowly (69th percentile against a bar of 71) even though its effect is real. That is the 1 in 5 miss rate showing up.

These percentages depend on how I built the made-up world. Treat them as a guide to scale, not as predictions.

## Where I departed from the plan, and why

- **Score.** Halter points become a percentile within each crop year, so foals of different ages are comparable. Unshown foals count as zero. Number of shows, grands and reserves are recorded but only points drive the score.
- **Small samples.** Effects are shrunk toward zero when a stallion has few foals. Without this, the value ranking is led by cheap stallions with three lucky foals.
- **Dam adjustment.** The plan's "foal average minus mare average" is reported, but the ranking uses a version that measures how much dam quality matters inside each stallion's own foals. Dam quality comes from her own record and from her foals by other stallions, so it needs no extra purchase when mares appear under several stallions.
- **Value per dollar.** A stallion with a below-average effect is never ranked as good value. Dividing a negative effect by a fee would otherwise rank an expensive poor stallion above a cheap poor one.
- **Comparison groups.** Added random picks at a similar fee. That is the fair test of "undervalued", because it holds price constant along with whatever comes bundled with price.
- **Timing.** Rank with data through year D, pay the season D+1 fee, judge foals born in D+2 and D+3.

## Limitations

- Public data is thinner than professional databases, and for fees it is much thinner than the plan assumed.
- Halter points reflect judging, fashion, and how hard an owner campaigns a horse, not only genetics.
- Stud fees reflect reputation, so part of any signal is just the market's view.
- Listed fees are sticky: a third of the stallions with three or more priced seasons never changed theirs. Most of the price variation is between stallions, not over time.
- The 52 stallions are those offered at a futurity auction, not a random sample of halter sires.
- Sources disagree on whether a fee includes the chute or booking fee, and some seasons have two different figures. The script uses the most recently dated listed figure for each season.
- A stallion at private treaty has no dollar fee and drops out of the ranking.
- Mare quality is only partly adjustable (see above).
- AQHA records give lifetime totals. Using them for a past date lets in a little hindsight. The script limits this to foals at least three years old at that date and reports how many were affected.
- Results are relative to the stallions you choose to enter. A pool of famous sires is not the market.
- Even a PASS is directional, not proof.

## Not verified

- Exactly which fields Record 70 prints (dam, foaling year, halter points per foal). Check the free sample on the AQHA records page before paying.
- Whether Quarter Horse Resource shows registration numbers.
- Which fields the public sale-result pages publish, and their terms of use.
- The registration numbers of the 45 pool stallions. They come from consignor-typed lot pages and are not yet checked against AQHA's pedigree lookup.
- This season's fee for most of the pool. Only 17 stallions have one for 2025 or later.
- Which season the two archived directory snapshots refer to. The data does not say, so I assumed the year of the snapshot.
- The workbook was built and read back by script. It has not been opened in Excel on this machine.

## How the sources were accessed

I read a handful of public pages through a web reader: the QStallions halter
listing and one stallion page, the QData leaderboard page, the Quarter Horse
Resource home page, one sale-results archive page, one third-party statistics
article, and on aqha.com the records page, the fee schedule, one news article
and robots.txt. After reading
robots.txt I made no further requests to aqha.com. The workbook holds no horse
data from aqha.com, only its published record prices in the Sources tab. The
seven stallion rows come from one view of the QStallions halter listing. Owner
names were on that page and were not stored.

For the fee history I read, one page at a time with a pause between requests:
27 auction listing pages and 245 lot pages on internethorseauctions.com (its
robots.txt sets no restrictions and its terms cover bidding only), three archived
QStallions data files (two used) and eight archived directory pages from the
Internet Archive, seven QStallions stallion pages, and one farm's stallion page. Consignor
and owner names appear on those pages and were not stored.

## Decision note

**Decision: hold. Do not start Phase 2, and do not stop.** Phase 1 has not
produced a result yet. Two revisions to the plan are needed before collecting:

1. **Fee source.** Replace "QStallions provides the price side" with a fee history built from stallion-service auction lot pages, the archived QStallions data and each stallion's own page: one dated Snapshots row per stallion per season. This is done for 52 stallions.
2. **Success test.** Replace "outperform on at least one outcome measure" with the fixed rule the script applies: dam-adjusted foal score, at least three windows, against cheap-but-average and same-price random picks.

Next step, a pilot that costs about $100:

1. Join AQHA ($65) and order Record 70 for the five stallions that now have a fee history: Rumerz, Best Kept Secrete, Heartz On Fire, Evinceble and Raylan Givens (about $5 to $10 each). Their registration numbers are in the Stallions tab.
2. Confirm the record lists every foal with its dam, foaling year and halter points.

The third pilot step, finding past fees, is done: those five have between two and seven priced seasons.

Then:

- **Go to full collection** if the record has the fields. The fee side is ready: 44 stallions in the workbook already have three or more priced seasons, so what remains is the all-foals record for each of them. Run the backtest. PASS leads to Phase 2. FAIL with a large pool means stop.
- **Stop or rethink** if foal counts average under about 40 per stallion. At that size the backtest cannot tell a real edge from luck.
- **Consider a second question** whatever the pilot shows. Breedings sold at auction for 62 percent of the advertised fee at the median, so it may be worth asking which ones sell for well under what the foals later justify. `--fee-basis auction` runs the same backtest on those prices.
