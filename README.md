# Breeding Value Ranker (Phase 1)

Personal tool. It ranks halter stallions by expected foal quality per dollar of
stud fee, and tests whether that ranking would have worked using only what was
known at each past date. Quarter Horses have the full treatment. Arabians have a
first version on much thinner data.

**The app:** open `docs/index.html`, or the hosted copy if this repository has
GitHub Pages turned on. Say what you have (a mare, a stallion, or no horse yet)
and what you can spend. It ranks every stallion in your budget, either by the
return if you sell the foal or by the chance of a prize winner, and says why the
first one is first. `docs/explore.html` holds the detail: every stallion's fee
history, the market as a whole and the backtest.

**Does it work?** [qa/RESULTS.md](qa/RESULTS.md) tests the matcher against the
2019 to 2025 seasons, and shows the ten versions of the sale-price model that
were trained on 240 public sales.

Read [FINDINGS.md](FINDINGS.md) first. The short version: the tooling is built
and tested, but the backtest has not been run on real horses yet, because the
foal-level data has to come through your own AQHA member login.

## What is here

| Path | What it is |
|---|---|
| `data/breeding_data.xlsx` | The workbook you fill in. Tabs: Stallions, Snapshots, Mares, Foals, Outcomes, plus Sources and a column Dictionary. 52 real stallions are already entered, with 474 dated fee rows covering 2018 to 2027. |
| `docs/index.html` | The matcher. One self-contained file, built by `bvr.py export-web`. GitHub Pages serves it from `/docs`. |
| `docs/explore.html` | Every chart and table behind it, built by the same command. |
| `web/` | The two page templates and the stored simulation results. Edit these, not the files in `docs/`. |
| `qa/` | The test of the matcher against past seasons: scripts, the data they use, and [RESULTS.md](qa/RESULTS.md). |
| `ranker/matcher.py` | The matcher's ranking rule: last year's foal winnings times their trend. |
| `ranker/arabian.py` | The Arabian ranking, from the files in `data/arabian/`. |
| `data/arabian/` | Arabian stallions, prices, halter placings and sale prices, with `SOURCES.md`. |
| `qa/leaders/` | Every public QData halter leaderboard, 2017 to 2026: sires, top-50 earners with dam and dam's sire, dams, broodmare sires. |
| `qa/futurity_results.csv` | Every horse shown in 277 futurity classes, 2024 to 2026, with sire, dam and finishing place. |
| `qa/backtest2.py`, `qa/foal_model.py`, `qa/futurity.py`, `qa/price_model2.py` | The second round of tests: a wider backtest, the foal-by-foal model, the futurity checks, and the price model retried. |
| `ranker/pricing.py` | The expected sale price of a foal and the return on the stud fee. Reads the model that `qa/price_model.py` trains. |
| `bvr.py` | The command-line script. |
| `ranker/` | The calculations (`core.py`), Excel reading and writing (`workbook.py`), synthetic test data (`synth.py`). |
| `synthetic/` | Three made-up datasets and their results, so you can see what the output looks like. These horses do not exist. |
| `tests/` | 34 checks, including one that proves the backtest cannot see the future and one that proves the price model does not find effects that are not there. |
| `FINDINGS.md` | Findings, limitations and the decision note. |

## Setup (once)

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install -r requirements.txt
```

## Use

Fill the five input tabs in `data/breeding_data.xlsx`, then:

```bash
.venv/bin/python bvr.py run data/breeding_data.xlsx
```

That writes `data/breeding_data_results.xlsx`: your tabs plus six results tabs
(Results summary, Ranking, Backtest, Backtest picks, Foal scores, Link review).
The results are plain values written by the script, so run it again after any
change to the inputs.

Useful options:

- `--asof 2017 2019 2021` chooses the backtest dates yourself. By default the
  script picks up to five, two years apart.
- `--fee-fallback latest` prices every past date with the newest fee on file.
  Use it only if you cannot find historical fees; it lets hindsight into the
  price and the results tab says so.
- `--fee-basis auction` prices stallions by what a breeding sold for at
  stallion-service auctions instead of the advertised fee. The default,
  `listed`, ignores auction rows. The two are never mixed.
- `--no-dam-adjust` turns off the adjustment for mare quality.
- `--top-k 5` fixes the number of top picks per window.

After changing the workbook, re-run the matcher's test and rebuild the pages:

```bash
.venv/bin/python qa/backtest.py --write
```

```bash
.venv/bin/python qa/price_model.py --write
```

```bash
.venv/bin/python qa/backtest2.py --write
```

```bash
.venv/bin/python qa/futurity.py --write
```

```bash
.venv/bin/python qa/foal_model.py --write
```

```bash
.venv/bin/python bvr.py export-web
```

Other commands:

```bash
.venv/bin/python bvr.py synth --scenario planted
```

```bash
.venv/bin/python bvr.py power --reps 100
```

```bash
.venv/bin/python -m unittest discover tests
```

## How it works

1. **Link foals to parents (Step 2).** Each foal is matched to its sire by
   registration number, cross-checked against the sire name on the foal's
   record. Anything that does not line up goes to the Link review tab and is
   left out until fixed. A dam needs only her registration number on the foal
   row; she does not need her own row in Mares.
2. **Score each foal (Step 3).** Halter points become a 0 to 100 percentile
   within the foal's own crop year, so a yearling is compared with yearlings.
   Unshown foals count as zero points.
3. **Stallion effect (Step 4).** How far a stallion's foals sit above what
   their crop and their dams predict. Dam quality is her own halter record plus
   how her foals by other stallions did. Effects are shrunk toward zero when a
   stallion has few foals, and every effect carries a margin of error.
4. **Value per dollar (Step 5).** Effect divided by stud fee, per $1,000.
   Stallions with a below-average effect are never ranked as good value. The
   fee is the newest listed figure for the season. A stallion whose newest row
   is private treaty, or whose newest fee is more than two seasons old, has no
   current price and is not ranked.
5. **Backtest (Steps 6 and 7).** For each as-of year D: rank with data through
   D, price with the fee for season D+1, then judge the foals born in D+2 and
   D+3. The top picks are compared with cheap-but-average stallions, with
   random picks, with random picks at a similar fee, and with the priciest
   stallions.
6. **Verdict.** Fixed in advance: at least three windows, picks beat
   cheap-but-average in more than half of them, and their average standing
   against same-price random picks clears a bar that luck reaches about 1 time
   in 20.

## Data rules

- Never overwrite a fee. Add a dated Snapshots row.
- Enter every registered foal of a stallion, not only the ones that showed.
- Prefer one Outcomes row per foal per year over lifetime totals.
- Collect by hand or through your own AQHA login. Nothing here scrapes a site.
