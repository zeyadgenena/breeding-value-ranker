# Testing the matcher against the past

Date: 2026-11-15

The question: if the matcher had been used in past years, would its picks have
paid off? This note records what was tested, round by round, and what the app
now does as a result.

## The short version

- **The picks were good at finding stallions that sire winners.** At a $2,000
  budget, 14 of 21 past picks went on to sire a foal that finished in the top 50
  halter money earners of its year. For the average stallion at that price it
  was 18%.
- **Budget matters more than cleverness.** Under $1,500 the picks still beat the
  average three to one, but only about 1 pick in 4 or 5 produced a top-50 foal.
  The stallions that keep producing them have mostly cost $1,500 to $2,000.
- **Resale at public auction did not pay.** In 122 public online sales of young
  horses by these stallions, the typical price was 1.7 times the stud fee. None
  sold for $20,000. A better sire did not mean a better price.
- **A price model says the same.** Ten versions were trained on 240 sales and
  128 combinations of factors were searched. The best explains 14% of the
  difference between one sale and the next, and almost none of that is the
  sire. A yearling sells for about $2,600 to $2,900 whoever sired it, so the
  return on a breeding is highest where the stud fee is lowest.
- **So the "diamond" is a foal that wins, not a foal that flips.** A top-50 foal
  wins $11,000 to $87,000 in a year. That is where the 10x outcome shows up.

## What was tested

For each decision year from 2018 to 2024 the rule saw only what was public by
the end of that year: the stud fee for the next season and the foal results so
far. A mare bred the next season foals the year after, so each pick was judged
on that crop, as weanlings and as yearlings.

| | |
|---|---|
| Stallions | 52, of which 23 to 44 had a fee in any one year |
| Seasons | 2019 to 2025 (seven) |
| Picks | top 3 within each budget, each season: 21 per budget |
| A hit | a foal from that crop in the year's top 50 halter money earners |
| Top-50 foals by these stallions | 216 across 2018 to 2026 |

Data: `qa/top_earners.json`, the Sire stats and Snapshots tabs of the workbook,
`qa/young_horse_sales.csv` and `qa/mare_sales.csv`. Re-run with
`python qa/backtest.py` and `python qa/sales.py`.

## Round by round

**Round 1. Does the first version work at all?** The first version ranked by
three years of foal winnings. Its picks sired a top-50 foal far more often than
the average affordable stallion (71% against 18% at $2,000). Buying the dearest
stallion you can afford did much worse than using the record (57%), so the
record adds something price alone does not.

**Round 2. Who were the bargains, with hindsight?** Secret Gunfighter at $1,000
(2021 and 2022 seasons), Solaris at $1,000 (2022), Evinceble at $1,850 before he
had a single foal on the ground, Raylan Givens at $1,500 (2025). Two kinds:
proven sires priced low, and young champions whose first foals then won. Top-50
foals came from 58% of stallion-seasons priced $1,501 to $2,000, and from 7% of
those priced $1,000 or less.

**Round 3. Quality per foal, and newcomers.** Tried ranking by winnings per
earning foal, by past top-50 foals, and by letting in unproven young stallions
that were priced high for a newcomer. None beat simply using recent winnings.
What an auction page says about a stallion's own show record was no help: 46 of
52 claim a world title somewhere.

**Round 4. Recency and trend.** The misses were mostly older sires whose foal
winnings were already falling (Telasecret, Very Cool late on). Weighting the
latest year, and moving a stallion up or down by whether his winnings are rising
or falling, did slightly better at every budget.

**Round 5. Do breeders' bids tell us anything?** What a breeding sold for at the
futurity auction, as a share of the fee, was tested as a demand signal. On its
own it was poor, and added to the rule it changed almost nothing.

**Round 6. Sale prices.** 122 young horses by these stallions were found in
public online sales from 2017 to 2025. Nothing predicted price: not the rule's
score when the mare was bred, not the sire's winnings the year before the sale.
Only the stud fee had a weak link.

**Round 7. A model of the sale price.** The app needed a number: what is this
foal likely to sell for? The sales were widened to every halter stallion with a
known fee history, not only the 52 in the workbook: 240 young horses by 59
stallions at 51 auctions. A price model was then trained in ten versions, each
one tested on auctions it had not seen. See "What a foal is likely to sell for"
below. The result: age, sex and the year of sale matter a little. The sire's
record adds about one point. The stud fee adds nothing.

## The rule the app now uses

    score = what his foals won in halter last year  x  trend

Trend is last year's winnings over the year before, kept between 0.5 and 2.
Within a budget the highest score is the match. It is in `ranker/matcher.py`.

## How well it did

Top 3 picks per season and budget, seasons 2019 to 2025.

| Budget | Picks that sired a top-50 foal | Average stallion at that price |
|---|---|---|
| $1,000 | 5 of 21 (24%) | 6% |
| $1,500 | 4 of 21 (19%) | 8% |
| $2,000 | 14 of 21 (67%) | 18% |
| Any | 16 of 21 (76%) | 21% |

These are the conservative figures the app quotes. Ten rules were compared on
the same seven seasons, and choosing the winner on the seasons you then score it
on flatters it. So each season here was scored with the rule that did best on
the other six. Scored the flattering way, the final rule gets 6, 7, 17 and 18.

## What young horses actually sold for

| | Sales | Typical price | Against the stud fee |
|---|---|---|---|
| Weanlings | 15 | $3,500 | 2.3x |
| Yearlings | 58 | $2,500 | 1.4x |
| Two-year-olds | 49 | $3,000 | 1.7x |
| All | 122 | $2,600 (middle half $1,550 to $4,200) | 1.7x; 26% reached 3x; none reached 10x |

The best was $18,100 for a weanling by Very Cool (9.1x). One yearling sold for
$6,900 and went on to be a top-50 earner that same year, so the winners are not
priced as winners at these sales.

Mares aged three and up by halter sires: 108 sales, typical price $3,100, middle
half $1,750 to $6,200. The app uses this for the "no horse yet" path.

## What a foal is likely to sell for

Data: `qa/price_training.csv`, 240 sales from 2017 to 2025: 29 weanlings, 108
yearlings and 103 two-year-olds. 125 have a known stud fee. Re-run with
`python qa/price_model.py --search`.

Each version predicts the logarithm of the price. To score a version, every
auction is left out in turn, the model is trained on the other 50, and it is
scored on the one left out. "Typical miss" is how far the estimate usually is
from the real price. "Explained" is the share of the difference between sales
that the model accounts for, on sales it has not seen.

| Version | What it used | Typical miss | Explained |
|---|---|---|---|
| 0 | One typical price for every horse | 63% | 0% |
| 1 | Age at sale | 65% | 0% |
| 2 | Age and stud fee | 70% | 2% |
| 3 | Age, stud fee, sire's foal winnings the year before the sale | 71% | below 0% |
| 4 | Age, stud fee, sire's foal winnings when the mare was bred | 67% | 9% |
| 5 | Age and stud fee, plus each sire's own price level | 70% | 1% |
| 6 | Age, stud fee and sex, plus each sire's own price level | 67% | 6% |
| 7 | Age, stud fee and year of sale, plus each sire's own price level | 69% | 5% |
| 8 | Age, plus each sire's own price level | 67% | below 0% |
| 9 | Age, sex, sire's foal winnings when the mare was bred (kept) | 63% | 14% |

After the ten versions, all 128 combinations of the six factors were searched,
with and without a per-sire level. Version 9 came out best. The runner-up that
uses nothing about the sire (age, sex and year of sale) explains 12.7%, so the
sire accounts for about one point of the 14.

Three checks on the kept model:

- **Leaving the fee out does not flatter cheap stallions.** With the stud fee
  added back, its weight is close to zero (-0.03) and the estimate for a $1,000
  stallion does not change.
- **Within the 125 sales with a known fee, the model explains nothing.** What
  it does explain across all 240 is mostly that older sales (2017 to 2021) and
  geldings were cheaper.
- **Two sales in three landed between half and double the estimate.** That is
  the honest width of the range the app shows.

What the model gives the app, for a colt or filly:

| Sold as | Estimate | When |
|---|---|---|
| Weanling | $3,400 to $3,800 | about 18 months after breeding |
| Yearling | $2,600 to $2,900 | about 2 years after breeding |

The low end is a sire with no foal winnings last year, the high end one whose
foals won $350,000. One year after breeding there is no sale price: a mare
carries for about 11 months, so the foal has only just been born.

What actually happened, by the sire's stud fee (all ages, both sexes, geldings
included):

| Stud fee | Sales | Typical price | Against the fee |
|---|---|---|---|
| $1,000 or less | 15 | $2,200 | 2.2x |
| $1,001 to $1,500 | 22 | $2,850 | 1.9x |
| $1,501 to $2,000 | 68 | $2,900 | 1.7x |
| More than $2,000 | 20 | $1,575 | 0.6x |

No sale in the data is by a stallion standing for under $1,000 or over $3,000,
so the app gives no estimate outside that range. Of the 240 sales, 7 reached
$10,000 and none reached $20,000.

**What this means for the app.** Ranked by return on resale, the cheapest
stallions come first, because the price hardly moves with the sire. Ranked by
chance of a prize winner, the strongest records come first. The app offers
both, and says which is which.

**Why more training rounds will not help.** The model has stopped improving
because the signal is not in this data. Public online auctions are where
ordinary young horses sell. The best prospects by the best sires change hands
privately. Better estimates need different data: private sale prices, or the
foal-by-foal AQHA record.

## What a foal by a top stallion wins

Seven stallions publish a report of every foal that was shown this year. Among
foals shown in 2026:

| Stallion | Foals shown | Typical lifetime winnings | Won $20,000 or more |
|---|---|---|---|
| Raylan Givens | 31 | $20,500 | 17 |
| Evinceble | 47 | $7,200 | 13 |
| Rumerz | 10 | $4,500 | 2 |
| Best Kept Secrete | 9 | $5,700 | 1 |
| Heartz On Fire | 8 | $17,800 | 3 |
| Quinlan | 4 | $10,600 | 1 |

Only foals that were shown appear, so this says nothing about the ones that
never reached a show ring.

## Limits

- **No crop sizes.** We cannot see how many foals each stallion has, so "sired a
  top-50 foal" is not "your foal's chance". A popular stallion has more chances.
  This is the main thing the paid AQHA all-foals record would fix.
- **Seven seasons, 52 stallions.** The gap between picks and average is large,
  but the differences between the better rules are within noise.
- **Sale prices are from one auction company's online sales.** Private sales,
  where the best halter prospects usually change hands, are invisible. This is
  the main reason the sale estimates sit so close together.
- **The mare is not in the price model.** The sales name the dam but say
  nothing about her quality, so the estimate does not change with the mare.
- **Return leaves out the cost of raising the foal** to sale age.
- **Prices are advertised fees**, and for many stallions the latest one on file
  is from 2024.
- **Prize money is not profit.** It leaves out the cost of raising, fitting and
  showing a horse.
