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
- **Foal by foal, the mare counts as much as the stallion.** New data lists
  every horse shown at the futurity, not only the winners. A foal by a top-20
  sire finished in the top three 24% of the time, against 14% for other sires.
  A mare that had already produced an earner added as much again: 37%.
- **Among the leading sires, the foals finish alike.** Once a stallion is in the
  top 20, nothing we tried says whose foals place higher. The stallion decides
  whether a foal is in the hunt. The mare and the individual decide the rest.

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

**Round 8. A wider pool.** The first test used 52 stallions and seven seasons.
With every public leaderboard pulled in full (2017 to 2026) the test now covers
86 stallions and eight seasons. The result held. See "The wider backtest".

**Round 9. Every horse shown, not only the winners.** The futurity classes at
the Halter Million publish each class in full: every horse, its sire, its dam
and where it finished. 277 classes from 2024 to 2026 give 628 horses by 83
sires out of 498 dams. This is the first data here with losers in it.

**Round 10. Does the ranking predict futurity results?** Yes, at the stallion
level. A stallion's leaderboard winnings one year tracked how many top-three
futurity finishers he had the next (link 0.69 and 0.79). The top five picks held
48% and 72% of all top-three finishes.

**Round 11. The mare.** A dam that had been among the year's top 50 dams by foal
winnings before she was bred had foals that finished in the top three 33% of the
time, against 19% for other dams (2024: 21% of 28 against 15% of 185; 2025: 31% of 26 against 21% of 163; 2026: 43% of 35 against 23% of 164). Her sire's
record as a broodmare sire added nothing. A first look said it did (0.72), but
that used lists published after the foal showed. With the hindsight removed the
effect vanished.

**Round 12. A foal-by-foal model.** Seventeen versions and 561 combinations,
each allowed only what was public before the mare was bred. See "Foal by foal".

**Round 13. Sale price again, with more detail.** Each sold lot's own page was
read for height, futurity eligibility, the horse's own record, the dam's sire
and the dam's produce record: 276 sales by 77 sires. No single addition helped.
The best of 794 combinations explains 13%, the same as before. The first price
model stays.

## The rule the app now uses

    score = what his foals won in halter last year

Within a budget the highest score is first. Twelve rules were compared on eight
seasons. Several did equally well, and this is the plainest. The earlier rule
multiplied by a trend. On the wider pool the trend added nothing.

## The wider backtest

Top 3 picks per season and budget, breeding seasons 2018 to 2025, 86 stallions.
A hit is a pick that sired a foal in the year's top 50 halter money earners
from that crop. "Sorting" is how well the rule sorts all stallions in a season
into those that did and did not: 0.50 is a coin toss, 1.00 is perfect.

| Rule | $1,000 | $1,500 | $2,000 | Any budget | Sorting |
|---|---|---|---|---|---|
| Last year's winnings (in use) | 5 of 24 | 5 of 24 | 18 of 24 | 21 of 24 | 0.85 |
| Last year's winnings x trend (the old rule) | 6 | 5 | 18 | 20 | 0.84 |
| Number of earners | 4 | 7 | 15 | 19 | 0.83 |
| Three-year smooth | 4 | 5 | 17 | 20 | 0.84 |
| Winnings per earner | 6 | 6 | 14 | 17 | 0.84 |
| Top-50 foals last year | 6 | 7 | 18 | 20 | 0.85 |
| Young top-50 foals | 6 | 7 | 18 | 20 | 0.85 |
| Blend of winnings, breadth and young winners | 6 | 7 | 18 | 22 | 0.85 |
| The dearest you can afford | 3 | 6 | 9 | 14 | 0.82 |
| Average stallion | 6% | 9% | 16% | 21% | 0.50 |

The figures the app quotes are lower than the best row, on purpose. Each season
is scored with the rule that did best on the other seven:

| Budget | Picks that sired a top-50 foal | Average stallion at that price |
|---|---|---|
| $1,000 | 5 of 24 (21%) | 6% |
| $1,500 | 6 of 24 (25%) | 9% |
| $2,000 | 16 of 24 (67%) | 16% |
| Any | 21 of 24 (88%) | 21% |

Re-run with `python qa/backtest2.py`.

## Foal by foal

Data: `qa/futurity_foals.csv`, 601 weanlings and yearlings shown, 2024 to 2026.
21% finished in the top three of an open class and 18% were among the year's top
50 money earners (about $16,000 or more). Re-run with `python qa/foal_model.py`.

**The timing rule.** A weanling shown in 2026 was bred in 2025, so the model may
use lists only up to 2024. The first draft used the list from the year before
the show, which a breeder would not have had. Fixing that lowered every score.
The scores below are the honest ones.

"Forward" trains on 2024 and 2025 and tests on 2026. "Each year" holds every
year out in turn. 0.50 is a coin toss.

| Version | Forward | Each year |
|---|---|---|
| 0 The same chance for every foal | 0.50 | 0.50 |
| 1 Sire's leaderboard tier (top 5, 6 to 20, other) | 0.60 | 0.59 |
| 2 Sire's winnings, as a number | 0.53 | 0.58 |
| 3 Sire's tier and how many earners he had | 0.60 | 0.59 |
| 4 Sire's tier and whether the dam has produced an earner | 0.64 | 0.57 |
| 5 Version 4 and the finish of the dam's earlier foal | 0.64 | 0.57 |
| 6 Version 5 and whether the dam's sire is a listed broodmare sire | 0.62 | 0.61 |
| 7 Version 5 and the sire's own futurity average | 0.64 | 0.57 |
| 8 Version 5 and age class | 0.61 | 0.56 |
| 9 Version 4 with tier and dam working together | 0.64 | 0.57 |
| 10 Sire's winnings and the dam's record | 0.58 | 0.60 |
| 11 Version 4 and whether the dam was a winner herself | 0.63 | 0.58 |
| 12 Version 4 and whether the sire's winnings are rising or falling | 0.63 | 0.57 |
| 13 Version 4 and the sire's top-50 foals | 0.60 | 0.59 |
| 14 The dam's record and the sire's top-50 foals | 0.55 | 0.58 |
| 15 Sire's tier, his number of earners and the dam's record | 0.65 | 0.60 |
| 16 Sire in the top 20 or not, and the dam's record (kept) | 0.61 | 0.60 |

The search of 561 combinations found nothing above 0.65 and 0.61. Version 16 is
kept because it is the simplest of the versions that tie, and because the three
sire tiers did not come out in order: foals of sires ranked 6 to 20 placed a
little better than foals of the top five. Two groups is all the data supports.

Where to draw the line for a leading sire was tested too. With the dam's record
in the model, a top-5 line sorts no better than chance (22% of their foals made
a top three, against 21% for everyone else). A top-20 line is the best of the
six tried (26% against 15%), and top 30 and top 50 are close behind.

What the kept model says, and what happened:

| Sire | Dam | Chance of a top three | Chance of a top-50 money year | Foals | Top three, actual |
|---|---|---|---|---|---|
| In the top 20 | Has produced an earner | 37% | 28% | 55 | 40% |
| In the top 20 | No record | 24% | 18% | 277 | 23% |
| Other | Has produced an earner | 23% | 23% | 34 | 21% |
| Other | No record | 14% | 15% | 235 | 14% |

- **Forward check on 2026:** of the third of foals the model rated highest, 35%
  made a top three. Of the third it rated lowest, 20%.
- **How sure are the two effects?** Resampling whole mares 2,000 times: a proven
  dam is worth +13 points (90% range +5 to +22), a top-20 sire +11 points (+6
  to +17). Both hold for weanlings and for yearlings.
- **What a finish is worth.** 58% of class winners were among the year's top 50
  money earners, and those won a typical $27,600. For foals outside the top
  three it was 10%.
- **A weanling's result lasts a little.** 31% of weanlings came back as
  yearlings. Top-three weanlings made a top three again 31% of the time, others
  20%. Across all ages a horse's finish one year tracked the next (link 0.42).

**What a producing mare costs.** In 108 public mare sales the typical price was
$3,100. The five that were already listed producers sold for $1,150 to $9,600.
The four that later produced an earner had sold for $7,100 to $10,100. Small
numbers, from `python qa/mares.py`.

Three cautions. The model only knows foals that were shown: the ones that never
reached the ring are missing. A proven dam often comes with an owner who can
afford the best trainer, and the data cannot separate the two. Three years is a
short history.

## The Arabian side (first version)

Added because the horses this tool is now for are Arabian in type. Data is in
`data/arabian/`, with every source and its rules in `SOURCES.md` there.

| | |
|---|---|
| Stallions | 486 listed, 218 with a price |
| Prices | An advertised fee, or what a breeding sold for at a futurity auction. Opening bids are left out. |
| Whole-class results | 379 horses by 145 sires, shown at 8 shows, 2024 to 2026. Every horse in the class with its place. |
| A barn's list of wins | 403 placings, 2016 to 2025. One-sided, so a footnote only. |
| Sale prices | 153 sold horses, 2010 to 2022 |

How it ranks: by how many of a stallion's foals finished in the top three of a
class, then by their average finish. Re-run the checks with
`python qa/arabian_model.py`.

- **One check so far.** The top third of sires by top-three foals in 2025 (34
  sires) went on to sire 56% of the top-three finishers among new foals in 2026.
  35% of them had one, against 4% of the other sires. With the thin 2024 season
  added (one show) the pooled figures are 34%, and 42% against 16%. A third
  search for earlier seasons on the allowed sources found none.
- **The mare shows up more than the stallion here too.** Two different foals
  out of the same mare finished alike (link 0.33 on 74 pairs). Two foals by the
  same sire did so less (0.14). The same horse a year later: 0.57.
- **Sale prices.** 113 Arabians sold at public online auction in 2015 to 2022
  for a typical $4,700 (middle half $2,400 to $10,100). 16 reached $20,000.
  Thirty-two versions of a price model were tried. The best explains 11%.
- **It is narrow.** Two seasons of the international-style circuit in North
  America (GCAT Americas and the Emirates Global Cup). The U.S. Nationals,
  Canadian Nationals and regional shows are not in it.
- **Prize money is small.** The U.S. Nationals futurity paid its champion $8,700
  to $11,500 in 2022 to 2025. For Arabians the money is in the sale.
- **Sources set aside because their rules forbid automated collection:** the
  Scottsdale show's own results (full classes, 2016 to 2026), PaddockReport
  (U.S. Nationals results back to 2016), Arabian Essence, arabianhorseworld.com,
  and the Arabian Horse Association's results behind its sign-in. Scottsdale's
  files and PaddockReport's pages can be read by hand in a browser, or used with
  written permission.

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

- **The per-foal chance is for foals that are shown.** It is not the chance for
  every foal born. That still needs crop sizes.
- **Three years of futurity results.** Enough to see the mare effect, not enough
  to tell one leading sire's foals from another's.

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
