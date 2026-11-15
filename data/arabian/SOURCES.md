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

## Whole-class results (second pass)

# SOURCES (second pass)

Collected 2026-11-15 for a personal, non-commercial breeding-decision tool. Goal of this pass: full halter class sheets
(every placed horse, with sire and dam) from sources that are not one barn's own list of wins.

How requests were made: one at a time per host with `curl -A "Mozilla/5.0 (compatible; research-client)"`, at least 3.5 s
apart per host (30 s for arabianessence), cached under `raw/<host>/`, never re-downloaded. Full log: `raw/_fetchlog.tsv`
(time, host, URL, saved file, HTTP status). No logins, no forms, no CAPTCHAs, no site search queries. For every host the
robots.txt and the Terms of Use (or, where no terms page exists, the footer and the only legal page linked) were read
before any results file was downloaded. Finding a terms link requires loading the home page, so the home page was the
one page fetched before the terms on each host.

No names of owners, breeders, handlers, judges or farms were stored in any output file. The raw downloads contain them
because the published sheets do.

No page contained text addressed to automated agents. One tool (Firecrawl) returned a quota error when asked to render the
Internet Archive terms page; it was not used further.

## Hosts that supplied rows

### gcarabianstour.com (Global Champions Arabians Tour, the organiser's own site): 916 rows, `full_class`
- robots.txt: `User-agent: *` / `Disallow:` (empty, everything allowed) plus a sitemap line.
- Terms of Use: none. Neither the home page nor the results page links a terms, privacy or legal page; the footer is
  "© Global Champions Arabians Tour 2023-2025".
- Took: robots.txt, home page, `/results/` (the index of official result PDFs), and 12 PDFs: qualifying-class results and
  championship results for the six North American stops listed there. 15 requests in total (2 on the `www.` name).
  - GCAT Americas Scottsdale 2025 (18 & 20 Feb 2025), Miami 2025 (17-19 Apr 2025), Denver 2025 (8-9 Aug 2025),
    Las Vegas 2025 (26-28 Sep 2025), Scottsdale 2026 (13-15 Feb 2026), Miami 2026 (9-11 Apr 2026).
- Each sheet lists every horse in the class: rank, catalogue number, horse, colour, sire x dam, score. Qualifying classes
  are ranked 1..n; championships are Gold, Silver, Bronze, then 4..n.
- Skipped on this host: the two "performance classes" PDFs (not halter); all Europe and Middle East stops and São Paulo
  (not North America); GCAT Americas Las Vegas 2026 (2-4 Oct 2026) because the results page does not link its PDFs yet and
  no URL was guessed.
- Left out on purpose: page 5 of `GCAT-Denver-2025-qualifications-results.pdf` (Yearling Colts Section A, class 4A,
  6 horses). That one sheet carries the footer "© 2005–2025 arabianessence.com – All right reserved", and that site's
  terms forbid automated copying (see below). The same colts still appear in the Denver Yearling Colts Championship rows.

### www.ecaho.org (European Conference of Arab Horse Organizations, the show commission's own results pages): 144 rows, `full_class`
- robots.txt: `User-agent: *` / `Disallow:` (everything allowed).
- Terms of Use: none linked. The only legal page in the footer is the privacy policy (`/about-ecaho/gdpr`), which was read;
  it covers personal data and cookies and says nothing about automated access or reuse of results.
- Took: robots.txt, home page, privacy page, the shows list (2 pages), monthly archive pages used only to find which shows
  were held in the United States, Canada or Mexico, and three show pages.
  - Emirates Arabian Horse Global Cup, Scottsdale, 28 Mar 2024: 63 rows.
  - Emirates Arabian Horse Global Cup - North American Championship, Scottsdale, 11-14 Sep 2025: 81 rows.
  - Arabian National Breeder Final (EAHGC), Scottsdale, 16 Sep 2026: the page exists but has no classes or results yet
    (0 rows).
- Each show page lists every horse in each class: place, catalogue number, horse, birth date, colour, sire, dam, score.
- The first pass rejected this host because the per-class PDF has no sire or dam. The HTML show page does have them.
- Not done: the site search form (a form submission) and the per-class PDFs (nothing extra in them).
- Coverage note: only shows under the Emirates Arabian Horse Global Cup banner appear here for North America. In the
  months checked there were no other United States, Canadian or Mexican shows. Not every month of 2016-2026 was checked
  (each archive page takes 30-40 s); see the list of fetched files in the log.
- Search snippets suggest the March 2024 classes ran alongside the Arabian Breeders World Cup in Scottsdale. That is not
  stated in the downloaded page, so the show is named as ECAHO names it.

### www.arabhorse.com (Arabian Horse Network, a news site): 18 rows, `winners_only`
- robots.txt: disallows `/users/sign_in`, `/admin/`, `/users/password/` only.
- Terms of Use: none linked; footer is "© Designed by Arabhorse.com | All Rights Reserved".
- Took: home page, news index, and four news articles (7 requests with robots.txt). One article gave rows:
  "Emirates Arabian Horse Global Cup USA 2026" (Scottsdale, held with the Arabian National Breeder Finals, final on
  19 Sep 2026): Gold, Silver and Bronze in six championships, each with sire × dam.
- Not used: the GCAT Las Vegas 2026 article (winners named without sires), a photo-gallery article, and
  "From Las Vegas - Results" (it is the 2010 show, outside 2016-2026).

## Hosts declined because of their terms (nothing taken beyond robots.txt, home page and the terms page)

### paddockreport.com (PaddockReport: Arabian and Half-Arabian show results, sires, class history, "since 2016")
- robots.txt: allows `/` for all agents (it names assistant bots as allowed), disallows account pages and `/*?*q=`,
  blocks CCBot and Bytespider.
- Terms of Service, section 4 "Prohibited Uses": "You may not use our Service: ... To scrape or harvest data without
  written permission".
- 3 requests (robots.txt, home page, `/tos`). Nothing else fetched. The home page shows it holds U.S. Nationals results
  (the 2026 show was the latest added), a top-sires list and class history. This is the source that would answer the
  question properly; it needs the site's written permission, or reading by hand in a browser.

### www.arabianessence.tv / www.arabianessence.com (Arabian Essence TV; the .com name redirects to .tv)
- robots.txt: disallows system folders; `Crawl-delay: 30` for several named bots.
- Terms of Use, "Prohibited activities": you agree not to "(ii) access, monitor, reproduce, distribute, transmit,
  broadcast, display, sell, license, copy or otherwise exploit any Content of the Services, including but not limited to,
  user profiles and photos, using any robot, spider, scraper or other automated means or any manual process for any
  purpose not in accordance with this Agreement or without our express written permission". The same page also says
  copying or reproduction of content is "strictly prohibited without the prior written permission of Arabian Essence".
- 3 requests, 30 s apart (robots.txt, the .com URL that returned the home page, `/termsofuse`). No results page fetched.
  Search snippets show it holds scored class pages (with sire and dam) for the Las Vegas Arabian Breeders World Cup back
  to at least 2019.

### web.archive.org / archive.org (Internet Archive)
- robots.txt: web.archive.org returns 404; archive.org disallows `/control/` and `/report/` only.
- Terms of Use: could not be read. `archive.org/about/terms.php` returns a JavaScript shell with no text.
- Because the terms could not be read, nothing was fetched from the Wayback Machine in this pass (3 requests: two
  robots.txt and the terms URL). This is why archived copies of arabianhorseresults.com were not tried.

## Hosts checked that had nothing usable

- **www.arabianhorseresults.com / arabianhorseresults.com**: robots.txt is only a content-signals preamble with no
  directives. Both the `www.` and bare home pages return HTTP 404 from the web server. The site appears to be gone.
  3 requests.
- **www.arabianhorses.org** (Arabian Horse Association): robots.txt returns 404 (none). No terms page is linked; the
  footer has "Service Marks" (a PDF about trademark use, read: nothing on automated access) and "All Rights Reserved". One public results PDF found by search
  (`nat-show/archive/23USN_Results_699_SF.pdf`, a "Complete Placing Report") lists back numbers and judges' scores only:
  no horse names, no sires. Official national results stay behind the sign-in page and were not touched. 4 requests.
  Order note: that one PDF was downloaded after robots.txt and the home page footer were checked but before the
  "Service Marks" link was opened; that link turned out to be a trademark PDF, not terms.
- **ahtimes.com** (Arabian Horse Times): robots.txt allows everything; no terms page linked on the home page. The site is
  a marketing front; show coverage lives in Issuu flip-books (JavaScript readers, not fetched). A search hit showed it
  points readers to PaddockReport for results. 2 requests.
- **www.globalchampionsarabianstour.com**: a "Launching Soon" placeholder, not the tour's site. 2 requests.
- **www.arabianbreedersworldcup.com**: `/robots.txt` returned an HTML page that looks like a static snapshot, not a
  robots file. Not pursued. 1 request.
- **www.arabianhorseglobal.com**: robots.txt 404. Not pursued. 1 request.

## Looked for by web search and not found

- Regional championship results (AHA regions) that list sires: searches returned only the first pass's barn pages,
  magazine flip-books and ECAHO sheets.
- Breeder futurity results with sires or payouts (Minnesota Medallion Stallion, Region 12 Spotlight, Iowa Gold Star):
  searches returned unrelated racing futurities.
- Canadian Nationals class results with sires: only schedules, payout sheets (no horses) and flip-book coverage.
- U.S. Nationals class results with sires outside the AHA sign-in and PaddockReport: none.

## How results.csv was built

- Script: `scripts/build.py` (with `scripts/parse_ecaho.py`), run as `python3 -I`. PDF text was read with the PyMuPDF
  module that was already installed on this machine (`pdftotext` is not installed); nothing was installed. Everything
  else is the Python standard library.
- Every row comes from a downloaded file; `source_url` is the file's URL.
- `division`: all rows are `purebred`. None of these shows has Half-Arabian classes.
- `age_class`: `yearling`; `2yo` / `3yo` where the class is a single age; `junior` for GCAT junior classes and mixed
  2-3 year old classes; `senior` for mares and stallions 4 and over. There are no weanling classes in these shows.
- `placing`: the rank as a number for qualifying classes; `gold`, `silver`, `bronze`, then numbers, for GCAT
  championships. ECAHO championship pages list the qualified horses but rank only the three medals; the others are
  written as `qualified, no medal` (my label for "listed, no rank given").
- `entries_in_class`: the number of horses with a rank on the sheet (for ECAHO championships, the number listed). It is
  counted from the sheet. Neither source prints an entry count.
- Horses listed but not shown are not in `results.csv`. They are in `not_shown.csv` (177 lines): 152 marked `WD`
  (withdrawn) and 6 marked `E` in the GCAT sheets, 19 on ECAHO pages with no rank and no score.
- `foaled`: the birth year from the ECAHO page where given (144 rows). For yearling classes in the GCAT sheets and the
  arabhorse.com article it is the show year minus one (296 rows), which follows from the class definition.
  `results_extra.csv` says which is which. Blank otherwise.
- `dam_sire` and `prize_usd` are blank throughout: none of these sheets gives them.
- `results_extra.csv` (same row order as `results.csv`): the score, which scale it is on, the full birth date where
  given, the basis for `foaled`, and a note where a dam name was completed.

## Known data problems

- Dam names are sometimes clipped in the GCAT PDFs (the printed line is cut at the right edge, for example "MC" for
  "MC TEYNA"). Where the same horse appears on another downloaded sheet with a longer dam name that starts with the
  clipped one, the longer name was used (25 rows, flagged in `results_extra.csv`). A horse that appears only once can
  still carry a clipped dam name. Sire names come first on the line and were not seen clipped.
- Names are as published, upper-cased. The same sire is spelled more than one way across sheets, for example
  "IBN FARID" and "IBN FARID UAE", "TS KHIDAM EL SHAWAN" and "TS KHIDAM AL SHAWAN", "RFI FIORANO" and "RFI FIOANO".
  They were not merged. One filly (ELEGANZIA A) is printed with two different dams on two sheets.
- The same horse appears many times: once in its qualifying class and again in the championship at each show, and at
  several shows. 1,078 rows cover 389 distinct horses.

## ECAHO archive months checked for North American shows

2019/04, 2023/04, 2024/03, 2024/04, 2024/09, 2025/02, 2025/03, 2025/04, 2025/09, 2025/10, 2026/02, 2026/03, 2026/04, 2026/09, 2026/10.

United States shows found: March 2024, September 2025, September 2026. No Canadian or Mexican show in any month checked.

## Requests per host (from raw/_fetchlog.tsv; robots.txt, home and terms pages included)

| host | requests | HTTP status counts |
|---|---|---|
| www.ecaho.org | 23 | 200 x23 |
| gcarabianstour.com | 13 | 200 x13 |
| www.arabhorse.com | 7 | 200 x7 |
| www.arabianhorses.org | 4 | 200 x3, 404 x1 |
| paddockreport.com | 3 | 200 x3 |
| www.arabianhorseresults.com | 2 | 200 x1, 404 x1 |
| www.arabianessence.tv | 2 | 200 x2 |
| ahtimes.com | 2 | 200 x2 |
| archive.org | 2 | 200 x2 |
| www.globalchampionsarabianstour.com | 2 | 200 x2 |
| www.gcarabianstour.com | 2 | 200 x2 |
| www.arabianessence.com | 1 | 200 x1 |
| arabianhorseresults.com | 1 | 404 x1 |
| www.arabianhorseglobal.com | 1 | 404 x1 |
| web.archive.org | 1 | 404 x1 |
| www.arabianbreedersworldcup.com | 1 | 200 x1 |
| **total** | **67** | |

One request is missing from the log: an ECAHO archive request (2025/03) was in flight when the download queue was stopped
to re-order it, so it was cut off before it was logged. The same page was requested again later and that request is logged.
ECAHO requests ran one at a time throughout.

First request 2026-11-15T12:06:29, last request 2026-11-15T12:27:59 (local time). Limit was 200 downloads or about 40 minutes.

## Sale prices (second pass)

# SOURCES (second pass: auction sale prices)

Collected 2026-11-15 for a personal, non-commercial breeding-decision tool. Every request was made one at a time with
`curl -A "Mozilla/5.0 (compatible; research-client)"`, at least 4 s apart per host, and cached under `raw/`.
The full request log is `raw/_fetchlog.tsv` (time, host, URL, saved file, HTTP status). 250 requests in total, all HTTP 200.
No logins, forms, accounts or CAPTCHAs. No names of sellers, consignors, owners, buyers or bidders are stored in `sales.csv`
(the cached pages under `raw/` contain them, as published). No page contained text addressed to automated agents.

Result: `sales.csv` has 283 rows = the first pass's 91 rows + 192 new rows.

## Hosts fetched

### web.archive.org (Internet Archive Wayback Machine): 246 requests
- robots.txt: not re-downloaded. The first pass's cached copies (`../results/raw/robots/`) show web.archive.org returns
  404 for `/robots.txt` and archive.org disallows only `/control/` and `/report/`.
- Terms of Use: read this time from an archived static copy of `archive.org/about/terms.php`
  (`raw/wayback/archive_org_terms_archived.html`, terms dated 31 Dec 2014). Relevant lines: access "is granted for
  scholarship and research purposes only"; users agree "not to collect or store personal data about anyone". Nothing
  about automated access, scraping or AI. The personal-data line is why no people's names are in the CSV.
- What was taken (all are archived copies of `auction.ahtimes.com`, the Arabian Horse Times auction site):

| what | requests | outcome |
|---|---|---|
| archived Terms page | 1 | read |
| CDX index queries | 3 | all archived URLs of auction.ahtimes.com (4,813); every capture of lot pages (1,293); ahtauctions.com (none archived) |
| archived robots.txt of auction.ahtimes.com (2010) | 1 | read |
| 2019-2023 platform, lot pages (`/Event/LotDetails/ID`) | 82 | 53 horse rows; 14 ended lots with no price shown; 15 "Lot Ended" pages with no data |
| 2019-2023 platform, event listing pages (`/Event/Details/ID`) | 19 | 6 had lot tiles (5 new rows, 56 tiles matched rows already held); 13 said "Event not found" |
| 2010 platform, closed catalog pages (`catalog.asp?catid=..&show=closed`) | 11 | used to pick lots that had bids; no rows taken from them |
| 2010 platform, lot pages (`detail.asp?id=`) | 129 | 128 horse rows; 1 lot with no bids |

### auction.ahtimes.com / ahtauctions.com (origin of the archived pages; NOT contacted in this pass)
- robots.txt, 2010 archived copy (`raw/robots/auction.ahtimes.com_2010_archived.txt`): disallows `/images/`, `/jscripts/`,
  `/bin/`, `/uploaded/`, `/aspnet_client/`. Catalog and detail pages are allowed.
- robots.txt, 2026 live copy cached by the first pass: disallows `/Account/`, `/RealTime/`, `/signalr/`,
  `/Listing/History`, `/Listing/Action`, `/Listing/AddWatch`, `/Listing/CreateListingPage1` and system folders.
  Event and lot pages are allowed.
- Terms & Conditions (first pass's cached copy, re-read): auction rules only, no clause on automated access, scraping
  or AI. Page footer: "No part of this web page may be reproduced in any way without the prior written permission of
  Arabian Horse Times." Only facts were extracted (price, sold or not, date, pedigree); no page text is reproduced.

### www.arabhorse.com (Arabian Horse Network): 4 requests
- robots.txt (`raw/robots/www.arabhorse.com.txt`): disallows `/users/sign_in`, `/admin/`, `/users/password/` only.
- Terms of Use: the site has no terms page. The About page links only to a Privacy Policy; both were read
  (`raw/arabhorse/`) and neither says anything about automated access.
- Took: one news report on the 2015 IntArah Dream Embryo Auction (Las Vegas, 18 April 2015). It names one lot price:
  an embryo right to RH Triana, $200,000 (1 row, `lot_kind = embryo`). It also gives a total of $1,450,000 for 24 lots
  (18 unborn foals and 6 embryo rights, average $60,400), which is not lot-level and is not in the CSV.

## Hosts not fetched

- **scottsdaleshow.com, arabianhorseworld.com**: off limits by instruction. Not requested, directly or via the archive.
- **Live AHT auction site**: not requested. The first pass found it removes prices once a lot ends.
- **cpp.edu** 2015 and 2016 Kellogg sale articles: the first pass got 404 on the live URLs and its archive index has
  no copy, so no request was spent.
- Search results for Qatar, UAE, Poland and France Arabian auctions (thepeninsulaqatar.com, gulf-times.com, wam.ae,
  mdmar.net, polskieradio.pl, racingpost.com): outside North America and not in USD. Not fetched.
- No host was declined for a robots.txt or Terms of Use prohibition in this pass, because no other candidate host with
  lot-level North American Arabian prices was found by web search.

## What the archive holds, and what is left

- 2019-2023 platform: 703 lot IDs are archived. All lots that belong to horse-sale events have now been requested.
  The rest are stallion-service auctions (2020 and 2021 Medallion Stallion, 2021 and 2022 AEPA, 2021 and 2022 Spotlight,
  2021 Scottsdale Signature Stallion, 2021 AWPA: about 270 lots that probably still show closing prices) and tack or
  benefit items. Those were not fetched; they would all be `lot_kind = breeding` or `other`.
- From October 2023 on, the site replaced ended lots with a page that says only "Lot Ended", so the archive has no
  prices for the December 2023 sale (15 horses) or the 2024 Spotlight auction (about 165 breedings).
- These horse-sale events exist in the archive only as "Event not found" pages with no lots archived: CalPoly Pomona
  Select Sale 2022, AHT Advantage Auction April 2022 and January 2023, Vicki Humphrey Training Center Dispersal 2023,
  Cedar Ridge Spring Online Auction 2019. The Cedar Ridge 50th Anniversary Auction (2019) was archived only while
  bidding was open, so it has no closing prices.
- 2010 platform: 10 auctions, 298 horse lots listed as closed. 196 had at least one bid, 194 of those have an
  archived lot page, and 128 were fetched (those with 3 or more bids, most bids first) before the 250-download limit.
  Not fetched: 66 lots with 1 to 3 bids (51 of them had a single bid). 102 lots had no bids and are not sales.

## How the rows were built (`scripts/build.py`, standard library only)

- First-pass rows are kept. Each AHT row was re-read from the first pass's cached page: `foaled` was widened from a
  year to the full date on 35 rows, blanks were filled on 2 rows (sire and dam of AQUITAIN and BALLERINA ASI), and
  8 values were corrected where the lot's own pedigree line or breed line disagreed with the first pass
  (list in `scripts/first_pass_corrections.txt`: 4 spelling fixes, and the division of HRA TSIRIUS and
  TOTALLY TOSKCAN PF changed from half-arabian to purebred because their sire's name starts with "HA").
- The 5 lots the first pass dropped as "not a horse" are now included and labelled (3 embryos, 1 breeding right,
  1 summer-camp week).
- 2019-2023 lot pages: price is "Winning Bid" (`sold = Y`) or "Final Bid Price" with "Reserve Price Not Met"
  (`sold = N`, high bid). Lots with no bids are left out. Sire, dam and dam's sire come from the lot's subtitle line
  "(Sire x Dam, by Dam Sire)"; only when that is missing, from the description.
- Event listing pages: only tiles marked "Sold" are used, and only when the lot has no row from its own lot page.
  `sale_date` on those 5 rows is the event's "First Lot Closes" date.
- 2010 lot pages: structured fields (Sire, Dam, DOB, Sex, breed line). `sold = Y` for "Reserve met" (19 rows) and for
  lots with bids and no reserve shown (21 rows); `sold = N` for "Reserve not met" (88 rows).
- `foaled` is YYYY-MM-DD when the page gives a date, YYYY when it gives a year. On 10 rows from 2010 the page gives
  only an age ("Age: 6"), and `foaled` is sale year minus that age.
- `division` is blank when the page does not state the breed (63 horse rows).
- `lot_kind = breeding`: `sire` holds the stallion whose service was sold. `lot_kind = embryo`: `sire` and `dam` are
  the embryo's parents, `foaled` and `sex` are blank, and the due date is appended to the name to keep lots apart.
- De-duplicated on auction + horse.

## Known weak points

- One first-pass row (Cal Poly 2015 sale, CP CHARMMING NOTIONS) has `sale_date = 2015`: the month is not in the
  cached article.
- `auction` holds the published event title. Some titles include the name of the farm or training business that held
  the sale.
- Sire names are as published, so spelling variants exist (for example KHADRAJ NA and KHADRJA NA).
