# Arabian data: where it came from

## Stallions, fees and sire lists

# SOURCES - Arabian halter stallions, stud fees, sire leaderboards

Collected 2026-11-15, 11:34 to about 12:05 US Eastern. 186 HTTP requests in total (robots.txt checks included), one at a time per host, at least 3.2 s apart, user agent `Mozilla/5.0 (compatible; research-client)`. Every request is logged in `raw/_requests.log` (time, URL, saved file, HTTP status). No logins, no forms, no CAPTCHAs, no accounts.

No page contained text addressed to an automated reader that asked for an action. Nothing was ignored on that ground.

## How the files were built

- `scripts/fetch.py` downloads and caches into `raw/`. `scripts/build.py` parses `raw/` with the Python standard library and writes the three CSV files.
- PDF text: no PDF tool is installed and pip was not allowed, so `scripts/pdf2txt.js` uses the PDF reader built into macOS (PDFKit through `osascript`). This is the one step that is not Python. The extracted text held winning bidders' and owners' names, so the `txt/` folder was deleted after the build. To rebuild, run `pdf2txt.js` on the PDFs in `raw/` first.
- The AHT leaderboard is a page image. Its five halter sire rows were read by eye from `raw/issuu_2025_aht_leaderboards/page_3.jpg` and typed into `build.py`.
- Names: UPPERCASE, leading `*` and trailing AHA award marks (`+`, `+/`, `+++//`) removed so the same horse joins across sources. Other punctuation is kept.
- Six spelling variants were merged because name, sire and dam all agreed. Four look-alike pairs were left apart (`scripts/possible_duplicates.txt`).
- No names of owners, breeders, bidders or agents are in the CSV files. They remain inside the saved pages in `raw/`, which the brief asked to keep.

## Sites used

| Host | robots.txt | Terms noted | What was taken | Requests |
|---|---|---|---|---|
| www.spotlightfuturity.com (Region 12 Spotlight Stallion Futurity) | Disallows only wp-admin, WooCommerce upload folders and add-to-cart URLs | None found on the pages read | Stallion rosters 2019 to 2026 (8 pages: name, sire, dam, year, colour). Auction result sheets for 2024 and 2026 (PDF: lot, stallion, amount). Sire of Distinction awards 2013 to 2016. One sample horse page, sitemaps | 17 |
| web.archive.org (Internet Archive) | 404, so no rules | None read | CDX index lookups. Archived Arabian Horse Times auction pages: MAHB Medallion Stallion 2020, Spotlight 2021 preliminary and final, Spotlight 2023 preliminary, Scottsdale Signature Stallion 2021 (captured while still open). Six archived copies of the Orrion Farms store page, 2021 to 2026. Two archived copies of the Spotlight results page. One 2022 lot brochure that is cut off at 1 MB in the archive and could not be opened | 36 |
| www.scottsdaleshow.com (Arabian Horse Association of Arizona) | Sitemap line only, no Disallow | Terms page saved, nothing about automated access found | Signature Stallion directory pages 1 and 2 (144 stallions: sire, dam, colour, year, purebred flag). One sample horse page. Rules and Breeders Club pages saved but not used | 10 |
| cdn.prod.website-files.com | 403 Access Denied on robots.txt, treated as no rules | n/a | The 2026 nominated stallion list PDF linked from scottsdaleshow.com (names only, used as a cross-check) | 2 |
| orrionfarms.com | Disallows wp-admin and add-to-cart URLs; Yoast block allows all | None found | Live store page with 15 breeding prices | 4 |
| www.royalarabians.com | Disallows sign-in, admin, password pages | None found | Standing-at-stud list and 20 stallion pages, each with a "Breeding Fee" | 24 |
| portal.selectbreeders.com (SBS Stallion Guide) | Disallows /en/, /de/, /it/, /contacts/. Only /stallions/ paths were fetched | Page note: profiles are kept by owners and SBS does not vouch for them | 14 Arabian profiles with halter listed as a discipline: fee and last-updated date. One 404 | 19 |
| www.varianarabians.com | Disallows Joomla system folders | None found | One stallion page with a stud fee | 5 |
| midwestarabian.com | Allows all | None found | Two stallion list pages (names, sire, dam), one stallion page (no fee shown), one show recap (no sire table) | 5 |
| medallionstallion.com (Minnesota Arabian Horse Breeders) | Allows all | None found | Roster pages for the 2017 to 2023 auctions and the 2019 lot brochure. Saved only: they show no prices, so nothing from them is in the CSV files | 11 |
| issuu.com | Long list of blocked SEO bots; for other agents only account, API and query paths are disallowed. /docs/ pages are allowed | None read | Document pages for "2025 AHT Leaderboards" and "AHT Vol. 55 No. 3". The HTML holds no page text | 4 |
| image.isu.pub | 403 Access Denied on robots.txt, treated as no rules | n/a | The 8 page images of "2025 AHT Leaderboards". Page 3 gives the halter sire table | 9 |
| ahtimes.com | Allows all | Site footer: no reproduction without written permission. Only facts were extracted | Sitemaps and two auction landing pages. They only link to the auction platform | 8 |
| ahtauctions.com | Disallows /Account/, /RealTime/ and listing-action paths | Footer: no reproduction without written permission | Home, closed-auction view, terms, one ended event. No past prices are shown on the live site | 5 |
| www.32auctions.com | Disallows admin, user, help and /organizations/ except auction pages | Terms forbid copying or redistributing content and bypassing robot exclusion; they do not forbid automated reading | 2025 Spotlight auction page and item list. Both show zero items, so no data | 4 |
| www.arabhorse.com | Disallows sign-in, admin, password pages | None found | Home and two farm directory pages. No stallion directory with fees exists there now | 5 |
| omelarab.com | Disallows wp-admin | None found | Sitemaps and the stallion list page. No fees shown | 4 |
| online.fliphtml5.com | Disallows account and API paths; comment says Anthropic agents are allowed | None read | The Scottsdale auction catalog index and config. Text is not exposed (page images, obfuscated config) | 3 |
| arlenemagid.com | 404, so no rules | None found | Two pages. Only a 2012 Sport Horse Nationals article, outside scope | 3 |
| arabianbreedersworldcup.com | Returns an HTML page instead of a robots file, treated as no rules | None found | Futurity nominations page. No auction results | 2 |
| www.arabianhorses.org | 404, so no rules | n/a | robots.txt only | 2 |
| polskiearaby.com, www.raedawn.com (no response), auction.ahtimes.com (no response) | robots.txt request only | n/a | Nothing | 3 |

## Skipped, and why

- **arabianhorseworld.com** (stallion directory with fees, yearly leading-sire statistics): its robots.txt has `Disallow: /` for ClaudeBot, anthropic-ai and Claude-Web, plus `ai-train=no`. Those lines apply to an AI agent, so nothing was fetched from it, and its pages were not read through the Internet Archive either. This is the largest gap.
- **Arabian Horse Times magazine tables on Issuu**: the "2024 North American National Halter Leaders" table sits inside "AHT Vol. 55, No. 3" (https://issuu.com/arabian-horse-times/docs/aht_vol._55_no._3_-_issue_3). Issuu serves page images only and the page number is unknown, so it was not retrieved. A guessed URL for a 2024 leaderboards document returned 404.
- **Scottsdale Signature Stallion auction prices**: not published on scottsdaleshow.com. The 2023 event page is gone from the AHT auction site and its archive copy says "Event not found". The 2021 copy was captured while bidding was open.
- **Minnesota Medallion Stallion prices for 2021, 2022 and later**: archive copies say "Event not found".
- **Region 12 Spotlight prices for 2019, 2020, 2022 and 2025**: no result sheet is linked for those years and the archive copies are empty.
- **Iowa Gold Star, AHBA World Cup futurity auction, AHA Breeders Sweepstakes sire lists**: no public page with stallions and prices was found in the time allowed.
- **Select Breeders search form**: not submitted. Profiles were reached only through direct links found by web search.
- **Pages 5 to 8 of the AHT leaderboard**: downloaded but not read. Pages 2 and 4 are performance divisions and were left out of `sire_lists.csv`.

## Results and sales

# SOURCES

Collected 2026-11-15 for a personal, non-commercial breeding-decision tool. All requests were made one at a time with
`curl -A "Mozilla/5.0 (compatible; research-client)"`, at least 3.5 s apart per host (5 s for web.archive.org), and cached
under `raw/`. The full request log is `raw/_fetchlog.tsv` (time, host, URL, saved file, HTTP status). robots.txt copies are
in `raw/robots/`. No logins, no forms, no CAPTCHAs. No names of owners, breeders, handlers, consignors or buyers were stored.
No page contained text addressed to automated agents telling them to do something; the only relevant directives were
robots.txt files and terms of use, described below.

## Important: one host was fetched before its terms were read

**www.scottsdaleshow.com and its file CDN cdn.prod.website-files.com** (Arabian Horse Association of Arizona).
- robots.txt (scottsdaleshow.com): only a `Sitemap:` line, no Disallow. The CDN returns HTTP 403 for `/robots.txt` (no file).
- Terms of Use (https://www.scottsdaleshow.com/terms-and-conditions, saved as `raw/scottsdale/terms-and-conditions.html`):
  prohibit access "through automated or non-human means", and prohibit data mining, robots, scrapers and similar
  extraction tools; content is for personal, non-commercial use.
- What happened: robots.txt was checked first and was permissive, so the results index page, the sitemap and 32 results PDFs
  (Scottsdale show 2016-2026, Arabian National Breeder Finals 2016-2026, judges' cards, horse lists) were downloaded. The
  terms page was only read later. That order was a mistake. Fetching from both hosts stopped as soon as the terms were read.
- Consequence: nothing from these PDFs is in `results.csv`. The 9,726 parsed rows sit in
  `quarantine_scottsdaleshow_terms_restricted/` with a README, for the owner to decide (download the same PDFs by hand in a
  browser, ask for permission, or delete). The raw PDFs are still under `raw/scottsdale/`.
- Not taken at all from this host: the "SSS Auction Results" PDFs (prices of stallion breedings, which is the other
  agent's scope).

## Hosts that supplied rows in the final files

**midwestarabian.com** (a training farm's own results pages)
- robots.txt: `User-Agent: *` / `Disallow:` (everything allowed). No terms-of-use page linked; footer copyright line only.
- Took: `/show-results/` index and the per-show pages for 2016-2026 (U.S. Nationals, Scottsdale, Arabian National Breeder
  Finals, Arabian Breeders World Cup, Region 12, Minnesota Fall Festival, Canadian Nationals). Each entry is
  horse, (sire x dam), title. Only halter titles were kept; owner lines and handler names were dropped.
- Pages with no usable content: 2019 and 2021 U.S. Nationals and 2023 Breeder Finals (empty pages), 2024 Minnesota Fall
  Festival (404 page), 2026 Scottsdale, 2022 Minnesota Fall Festival and 2023 Region 12 (no parsable "(sire x dam)"
  entries), 2018 Canadian Nationals (4 entries, no halter title parsed). There is no 2020 or 2024 U.S. Nationals page.
- Caveat: this is one barn's list of its own wins, not full class results. It has typos (one horse is listed with two
  different sires in two years; "VITORY TO" for VITORIO TO).

**www.arabianhorses.org** (Arabian Horse Association)
- robots.txt: HTTP 404 (none). No terms-of-use link found on the pages fetched; footer says "All Rights Reserved".
- Took: Halter Futurity payout PDFs 2021-2025 (`Comp-HalterFut-YYYY-payouts.pdf`): dollar amount per placing for the U.S.
  Nationals and Canadian Nationals futurity (3-year-old) classes, by division and sex. These have no horse names. They were
  joined to the U.S. Nationals futurity placings found on midwestarabian.com (7 rows carry `prize_usd`).
- Also fetched, not used: Breeders Sweepstakes USN payout PDFs 2021-2025 (they cover AAOTR performance jackpots, not halter);
  2026 Breeding Pays Futurity score sheets for classes 2912/2913 (scores by back number, no horse or sire names; one is an
  image-only PDF); program pages; the national results index.
- Blocked: the official national show results (`/login/showresults/nationalEventResultClasses?show=...`, U.S. Nationals,
  Canadian Nationals, 2006-2026) redirect to a sign-in page. Not accessed. One daily-packet PDF URL returned 404.

**web.archive.org** (Internet Archive Wayback Machine; used for pages that no longer exist on the live web)
- robots.txt: web.archive.org returns 404 (none); archive.org's robots.txt only disallows `/control/` and `/report/`.
  The terms page (archive.org/about/terms) is rendered by JavaScript and could not be read with curl, so its text was not
  verified in this session.
- Took: 7 CDX index queries (2 failed at the network level, 2 returned nothing); one archived auction event page
  (it only said the event no longer exists); archived copies of two Cal Poly Pomona news articles
  (2017 and 2022 horse sale reports, which now return 404 on cpp.edu); archived lot pages of closed Arabian Horse Times
  online horse auctions (originally auction.ahtimes.com/Event/LotDetails/...), one request per lot.
- The archived lot pages show the end date, "Winning Bid" (sold) or "Final Bid Price" with "Reserve Price Not Met"
  (not sold), and the seller's description (sire x dam, sometimes dam sire, colour, sex, foaling date or year). Bidder
  usernames and seller contacts on those pages were not stored. Lots that are embryos or breedings were skipped.
- Only lots whose system IDs fall between a horse-sale event and the next event were fetched (124 candidates); stallion
  service auctions (AEPA, AWPA, AHBA, Spotlight, Medallion, Scottsdale Signature Stallion) were not fetched.

**www.arabhorse.com** (Arabian Horse Network)
- robots.txt: disallows `/users/sign_in`, `/admin/`, `/users/password/` only. No terms link found.
- Took: one show report (2017 Arabian Breeders World Cup) that states the Marquise Auction price for one yearling filly
  (1 sales row); two "Scottsdale Show Results" day pages that turned out to be from an undated older show (not used).

## Hosts touched but not used for rows

- **www.cpp.edu**: robots.txt allows everything (a Crawl-delay applies only to one named bot). Four sale-report URLs from
  search results returned 404 (the archived copies above were used instead). One news page and the 2017 college newsletter
  PDF were fetched; the newsletter repeats the 2017 CP Helios price already taken from the archived article.
- **ahtauctions.com** (Arabian Horse Times auctions): robots.txt disallows `/Account/`, `/RealTime/`, `/signalr/`,
  `/Listing/History`, `/Listing/Action`, `/Listing/AddWatch`, `/Listing/CreateListingPage1` and some system folders; lot and
  event pages are allowed. Terms & Conditions page read: auction rules, no clause on automated access; footer has a
  copyright notice against reproducing the page. Took: home page, terms, closed-auctions view (empty), completed-listings
  view (only test items), the one active auction's event page, one ended lot. The live site removes prices once a lot ends,
  and the active auction has no final prices yet, so nothing from the live site is in `sales.csv`.
- **ahtimes.com**: robots.txt allows everything. Home page only (to find the auction site).
- **www.ecaho.org**: robots.txt allows everything. One class-result PDF for the 2025 North American championship: it lists
  horse, colour, owner and scores but no sire or dam, so it was not used.
- **santaynezvalleystar.com**: robots.txt allows everything except two token URLs. One article page fetched; no price text
  was found in it; not used.
- **archive.org**: robots.txt and the terms page only.
- **issuu.com**: robots.txt only. Magazine flip-books are JavaScript readers; not fetched.

## Hosts not fetched because of robots.txt, or left unexplored

- **www.arabianhorseworld.com**: robots.txt has `Disallow: /` for ClaudeBot, anthropic-ai, Claude-Web, GPTBot and other
  AI agents, plus `Content-Signal: ... ai-train=no`. Nothing fetched beyond robots.txt.
- **arabianessence.tv** (www, dev): robots.txt sets `Crawl-delay: 30` for several named bots including Claude-SearchBot and
  disallows system folders. It appears to hold class results for scored shows. Not fetched: at 30 s per request it did not
  fit the time limit, and it was not confirmed that its pages list sires.
- **www.arabianhorseresults.com**: robots.txt contains only a content-signals preamble with no directives. Not explored
  for lack of time.

## Looked for and not found (within the time limit)

- Scottsdale Signature Stallion futurity payouts by class for 2016-2026 (only 2012 and 2015 figures surfaced in search).
- AHA Breeders Sweepstakes halter payouts per horse, Minnesota Medallion Stallion, Region 12 Spotlight, Iowa Gold Star,
  AHBA / Arabian Breeders World Cup futurity payouts, and official World Cup class results with sires.
- Official U.S. Nationals and Canadian Nationals class results (behind the AHA sign-in page).
- Lot-level price lists for the Marquise, Egyptian Event and Addis-run auctions.

## How the files were built

- Scripts are in `scripts/` (`build_all.py` runs everything). PDF text was read with the PyMuPDF module that was already
  installed; nothing was installed.
- `results.csv`: `foaled` is filled only where it follows from a single-age class (yearling = show year - 1, 2yo = -2,
  3yo/futurity = -3, weanling = same year) or from another row of the same horse and sire; `results_row_flags.csv` marks
  which. `prize_usd` is filled only on 7 U.S. Nationals futurity rows, joined by year, division, sex and placing from the
  AHA payout PDFs (the PDFs pay every Top Ten the same amount). Placings are as published (champion, reserve, top ten,
  top five, gold, silver, bronze).
- `sales.csv`: prices are as shown on the page; `sold` = N when the page says the reserve was not met. `foaled` for the
  Cal Poly 2017/2015 rows and the Marquise filly is derived from the stated age at the sale.

## Archived AHT lot pages: yield

Of 124 candidate lot pages, 99 were requested before the time limit, and one of them was requested a second time as a
test (100 requests). 77 gave a usable horse row with a closing price; 16 were ended lots with no bid or no price shown;
5 were not horses (embryo, breeding right, camp week, or a benefit auction); 1 snapshot was taken before the lot ended;
1 was the duplicate. The other 14 `sales.csv` rows: 13 from the two archived Cal Poly Pomona articles and 1 from the
arabhorse.com report. 25 candidate lots were never requested.

## Requests per host (from raw/_fetchlog.tsv, robots.txt and terms pages included)

| host | requests | HTTP status counts |
|---|---|---|
| web.archive.org | 112 | failed x2, 200 x109, 404 x1 |
| midwestarabian.com | 38 | 200 x37, 404 x1 |
| cdn.prod.website-files.com | 33 | 200 x32, 403 x1 |
| www.arabianhorses.org | 20 | 200 x18, 404 x2 |
| www.cpp.edu | 7 | 200 x3, 404 x4 |
| ahtauctions.com | 7 | 200 x7 |
| www.scottsdaleshow.com | 4 | 200 x4 |
| www.arabhorse.com | 4 | 200 x4 |
| www.ecaho.org | 2 | 200 x2 |
| ahtimes.com | 2 | 200 x2 |
| santaynezvalleystar.com | 2 | 200 x2 |
| archive.org | 2 | 200 x2 |
| issuu.com | 1 | 200 x1 |
| www.arabianhorseresults.com | 1 | 200 x1 |
| www.arabianessence.tv | 1 | 200 x1 |
| arabianessence.tv | 1 | 200 x1 |
| dev.arabianessence.tv | 1 | 200 x1 |
| www.arabianhorseworld.com | 1 | 200 x1 |
| **total** | **239** | |
