"""Excel in and out: the blank workbook, the loader (with Step 2 link checks)
and the results tabs."""
from __future__ import annotations

import datetime as dt

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from .core import MEASURES, Dataset, pass_bar

FONT = "Arial"
INPUT_FILL = PatternFill("solid", fgColor="2F3B4C")
RESULT_FILL = PatternFill("solid", fgColor="5A4A78")
NOTE_FILL = PatternFill("solid", fgColor="FFF2CC")
EXAMPLE_NOTE = "Example row showing the format. The script ignores it. Delete it or leave it."

INPUT_TABS = ("Stallions", "Snapshots", "Mares", "Foals", "Outcomes")
EXTRA_TABS = ("Sire stats",)   # stallion-level results copied from public leaderboards
RESULT_TABS = ("Results summary", "Ranking", "Backtest", "Backtest picks",
               "Foal scores", "Link review")

# tab -> [(column, width, meaning)]
COLUMNS = {
    "Stallions": [
        ("stallion_id", 12, "Your own short id. Any text, unique per stallion."),
        ("name", 26, "Registered name."),
        ("reg_number", 14, "AQHA registration number. Foals are matched to their sire on this."),
        ("foaling_year", 12, "Year the stallion was foaled."),
        ("sire", 24, "His sire."),
        ("dam", 24, "His dam."),
        ("dam_sire", 24, "His dam's sire."),
        ("color", 12, "Coat color."),
        ("stud_fee", 11, "Optional shortcut. A fee here together with fee_year counts as one "
                         "snapshot. Fee history belongs in the Snapshots tab."),
        ("fee_year", 10, "Breeding season the stud_fee applies to."),
        ("notes", 48, "Anything worth remembering."),
    ],
    "Snapshots": [
        ("snapshot_date", 14, "Date you saw it, or the publication date of the source (YYYY-MM-DD). "
                              "Add a new row each time; never overwrite an old one."),
        ("stallion_id", 12, "Must match Stallions (id, registration number or name)."),
        ("stud_fee", 11, "US dollars. Leave blank for private treaty."),
        ("fee_basis", 15, "listed = the advertised fee. auction = the winning bid for one breeding at a "
                          "stallion-service auction (a different, usually lower price; the ranking "
                          "ignores it unless you run with --fee-basis auction). private treaty or other."),
        ("fee_year", 10, "Breeding season the fee applies to. If blank, the year of snapshot_date is used."),
        ("halter_money_earners", 13, "Optional sire statistic exactly as shown on that date."),
        ("halter_progeny_earnings", 15, "Optional sire statistic exactly as shown on that date."),
        ("stats_period", 12, "What the statistics cover, for example 2025 or all-time."),
        ("source", 46, "URL or publication."),
        ("notes", 52, "Anything worth remembering."),
        ("chute_or_booking_fee", 34, "Chute or booking fee as printed, and whether stud_fee already "
                                     "includes it. Sources differ on this, so compare all-in prices."),
    ],
    "Mares": [
        ("mare_id", 12, "Your own short id. If blank, the registration number is used."),
        ("name", 26, "Registered name."),
        ("reg_number", 14, "AQHA registration number. Foals are matched to their dam on this."),
        ("foaling_year", 12, "Year the mare was foaled."),
        ("sire", 24, "Her sire."),
        ("dam", 24, "Her dam (the dam line)."),
        ("own_halter_points", 13, "Her own lifetime AQHA halter points. Blank means unknown, not zero."),
        ("own_halter_shows", 13, "Number of shows behind those points, if known."),
        ("notes", 60, "Anything worth remembering."),
    ],
    "Foals": [
        ("foal_id", 12, "Optional. If blank, the registration number is used."),
        ("name", 26, "Registered name."),
        ("reg_number", 14, "The foal's own AQHA registration number."),
        ("sire_reg_number", 14, "Sire's registration number as printed on the foal's record."),
        ("dam_reg_number", 14, "Dam's registration number as printed on the foal's record. "
                               "She does not need a row in Mares; the number alone identifies her."),
        ("sire_name", 24, "Sire's name as printed. Used to cross-check the number match."),
        ("dam_name", 24, "Dam's name as printed."),
        ("foaling_year", 12, "Year foaled. Required."),
        ("sex", 10, "Stallion, Mare or Gelding."),
        ("coat_color", 12, "Coat color."),
        ("notes", 60, "Anything worth remembering."),
    ],
    "Sire stats": [
        ("stallion_id", 12, "Must match Stallions (id, registration number or name)."),
        ("as_of_date", 13, "Date the leaderboard was read (YYYY-MM-DD)."),
        ("period", 10, "The year the figures cover, or all-time."),
        ("rank", 7, "The stallion's place on that list."),
        ("money_earners", 13, "Number of his foals that earned halter money in that period."),
        ("progeny_earnings", 15, "Total halter money his foals earned in that period, US dollars."),
        ("list_size", 9, "How many stallions the list shows. A stallion missing from it earned less "
                         "than list_cutoff, or nothing."),
        ("list_cutoff", 11, "Earnings of the last stallion on that list, US dollars."),
        ("source", 46, "URL or publication."),
        ("notes", 52, "Anything worth remembering."),
    ],
    "Outcomes": [
        ("foal_id", 12, "The foal's id or registration number."),
        ("year", 8, "Year the results were earned. Leave blank if the row is a lifetime total."),
        ("halter_shows", 11, "Number of halter shows in that year (or lifetime)."),
        ("halter_points", 11, "AQHA halter points in that year (or lifetime). Points already reflect "
                              "placing and class size."),
        ("placing", 9, "Only for a row that records one single show: the placing."),
        ("class_size", 10, "Only for a single-show row: horses in the class."),
        ("grands", 8, "Grand champion titles."),
        ("reserves", 9, "Reserve champion titles."),
        ("earnings", 11, "Halter money earned, US dollars."),
        ("sale_price", 11, "Public sale price, US dollars, if the foal sold."),
        ("sale_type", 16, "For example weanling auction, yearling auction, private."),
        ("source", 30, "Record number, URL or catalog."),
        ("notes", 60, "Anything worth remembering."),
    ],
}

# What the QStallions halter directory displayed on 2026-11-14 (one page view).
SEED_DATE = "2026-11-14"
SEED_URL = "https://qstallions.com/StallionDir?id=Halter&w=2"
SEED_STALLIONS = [
    # id, name, registration number, foaled, sire, dam, dam sire, color, fee shown on 2026-11-14
    ("ST001", "BEST KEPT SECRETE", "5663506", 2015, "HEZA SECRET AGENT", "HUSH DONT TELL", "FEARLES", "Chestnut", 2500),
    ("ST002", "EVINCEBLE", "5811744", 2017, "MR ELUSIVE", "LADIES N LACE", "VERY COOL", "Bay", 2250),
    ("ST003", "HEARTZ ON FIRE", "5659040", 2015, "SECRETZ", "KIDS KEEPING COOL", "THE FINEST KID", "Brown", None),
    ("ST004", "QUINLAN", "6159341", 2022, "MY INTENTION", "SHEZ PURE ELEGANCE", "HEZA SECRET AGENT", "Sorrel", 1750),
    ("ST005", "RAYLAN GIVENS", "5928955", 2019, "MY INTENTION", "EXCUSES XCUSES", "MR ELUSIVE", "Sorrel", 2000),
    ("ST006", "RUMERZ", "5534307", 2013, "SECRETZ", "KIDS KEEPING COOL", "THE FINEST KID", "Brown", 2500),
    ("ST007", "VALENTINO", "5522336", 2013, "THE TOP SECRET", "INNOCENT TOUCH", "TOUCHDOWN KID", "Chestnut", None),
]

SOURCES = [
    ("Source", "What it gives", "Access and cost", "Automated access", "What we found on 2026-11-14"),
    ("Quarter Horse Resource (quarterhorseresource.com)",
     "Official AQHA five-generation pedigree, coat colors, current owner and breeder.",
     "Free. One horse per search.",
     "No terms page or robots rules found on the home page. No bulk export. Treat as manual lookups only.",
     "Good for filling sire, dam, dam sire and color, and for confirming a name. Not yet confirmed "
     "whether registration numbers are shown; check on your first lookup."),
    ("QStallions directory (qstallions.com)",
     "Stud fee (with season on the stallion's page), pedigree, sire summary, top-10 point earners "
     "and money earners per stallion.",
     "Free to read. Only stallions whose owners pay to enroll are listed.",
     "No robots.txt (404) and no terms link found. Small enough to copy by hand.",
     "The halter category listed 7 stallions: 5 with a dollar fee ($1,750 to $2,500) and 2 at "
     "private treaty. Only 2 of AQHA's 2025 top-10 halter sires are in it. One stallion page "
     "still showed a 2024 fee, so check the season on each page. This is the weakest link: "
     "the free fee data is far thinner than the plan assumed."),
    ("QData Leaderboards (qstallions.com/leaders)",
     "Top 50 halter sires by progeny money earned: number of earners, total and average earnings. "
     "Also dams, broodmare sires and individual earners.",
     "Free.",
     "Nine small tables. Copy by hand.",
     "Lists exist for all-time and for each year 2018 to 2026. Read on 2026-11-15 for all-time and "
     "2022 to 2026; the rows for stallions in this workbook are in the Sire stats tab. Top 50 only, "
     "so a stallion missing from a list earned less than its cutoff, or nothing. These are totals: "
     "a stallion with more foals has more chances to be on the list."),
    ("AQHA Records (aqha.com, member login)",
     "Record 70 Get of Sire Totals, All Foals: every registered foal with its race and show summary. "
     "Record 80 Produce of Dam. Record 40 Open Show Detail by class and year.",
     "Membership $65 for 12 months. Record 70: $5 per 100 foals (members), $10 non-members. "
     "Record 75 performing foals only: same price. Record 80: $4 per dam. Record 40: $4 per horse. "
     "Record 44 life show record: $3 per horse.",
     "aqha.com robots.txt sets a 30 second crawl delay, disallows the show-leader detail pages, "
     "/documents/ and any URL with a query string, and blocks AI crawlers by name. "
     "Do not automate anything on aqha.com. Order records through your own member login.",
     "This is the foal-level source. Before buying, open the free sample of Record 70 on the "
     "records page and confirm it shows each foal's dam, foaling year and halter points. "
     "Order All Foals (70), not Performing Foals (75): the unshown foals are the denominator."),
    ("AQHA annual Top Halter Sires articles (aqha.com)",
     "Top 10 halter sires for the year: progeny earnings, number of earners, top earners with dams.",
     "Free articles for 2023, 2024 and 2025.",
     "Read in a browser and type in what you need. Nothing from aqha.com was stored by the script.",
     "Useful as a cross-check on the leaderboards."),
    ("Sale results (prohorseservices.com/results/archive and others)",
     "Auction results for quarter horse sales, weanling sales and halter futurity stallion-service sales.",
     "Free to read.",
     "Terms not checked. Copy by hand from each results page.",
     "The archive lists the sales, but the fields on each result (lot, sire, dam, price) were not "
     "verified. Stallion-service auctions show what a breeding really sold for, which can stand in "
     "for a missing listed fee (fee_basis = auction)."),
    ("Breeders Halter Futurity (breedershalterfuturity.com)",
     "Class results for halter futurities, by class.",
     "Free to read.",
     "Terms not checked.",
     "A possible public source of single-show placings. Not verified in detail."),
    ("Stallion-service auctions (internethorseauctions.com)",
     "Yearly futurity fundraiser auctions of breedings: East Coast Halter Futurity, Go for the Gold, "
     "Best in the West. Each lot page prints the stallion's advertised breeding fee, chute fee, "
     "season and registration number. The listing shows the winning bid.",
     "Free to read. Fourteen auctions found for 2018 to 2025, with 41 to 219 lots each, 1,437 in "
     "all (not all halter, not all Quarter Horses).",
     "robots.txt has no restrictions and the site terms cover bidding only. One page per lot, "
     "so pull only the stallions you are tracking.",
     "The best fee-history source found. Read for 52 stallions: the seven listed ones, plus every "
     "Quarter Horse stallion offered in at least three seasons of the East Coast Halter Futurity "
     "auction. 44 of them have an advertised fee for three or more seasons. Lot pages differ on "
     "whether the advertised fee includes the chute or booking fee, and double-registered horses "
     "sometimes show another registry's number. Long listings run over several pages, so check "
     "them all."),
    ("Internet Archive copies of QStallions data (web.archive.org)",
     "The full QStallions directory as it stood on a past date: fee, fee terms, registration number, "
     "pedigree and discipline for every enrolled stallion.",
     "Free. Only two dates were archived with data: 2023-10-30 (19 halter stallions, 15 with a "
     "dollar fee) and 2025-05-04 (7 halter stallions).",
     "Public archive. Two files.",
     "The directory page itself is archived about 40 times since 2019, but those copies hold no "
     "rows because the table loads separately. The halter list shrank from 19 to 7 in 18 months."),
    ("Historical stud fees",
     "What each stallion cost in past seasons. The backtest cannot price the past without this.",
     "The two sources above, plus farm websites (terrybradshawqh.com/stallions is archived every "
     "year back to 2015) and stallion pages on QStallions, which label the season of the fee.",
     "Manual, a page at a time.",
     "Found. No longer the main risk: seasons 2019 to 2025 can be priced for stallions that were "
     "offered in the auctions. Stallions never offered there still have no history."),
]

README_LINES = [
    ("Breeding Value Ranker: data workbook", "title"),
    ("Personal use. Ranks stallions by expected foal halter quality per dollar of stud fee, "
     "and backtests whether that ranking would have worked.", None),
    ("", None),
    ("Which tabs you fill in", "head"),
    ("Stallions, Snapshots, Mares, Foals, Outcomes (dark blue headers). One row per record. "
     "Column meanings are in the Dictionary tab.", None),
    ("Rows whose id starts with EXAMPLE only show the format. The script skips them.", None),
    ("The Stallions and Snapshots tabs already hold seven real stallions from the QStallions halter "
     "directory. Every fee row names its source and the date it was seen.", None),
    ("", None),
    ("Which tabs the script writes", "head"),
    ("Results summary, Ranking, Backtest, Backtest picks, Foal scores, Link review (purple headers). "
     "They are written by bvr.py as plain values, not formulas, because the backtest filters by date "
     "and resamples. After changing any input, run the script again; do not edit these tabs by hand.", None),
    ("", None),
    ("How to run", "head"),
    ("python bvr.py run data/breeding_data.xlsx", None),
    ("This writes data/breeding_data_results.xlsx: your tabs plus the results tabs.", None),
    ("", None),
    ("Three rules that keep the backtest honest", "head"),
    ("1. Never overwrite a fee. Add a new Snapshots row with its date, so the backtest can use only "
     "what was known at each date.", None),
    ("2. Enter every registered foal of a stallion, not only the ones that showed. Foals with no "
     "Outcomes rows are counted as unshown, and they are the denominator.", None),
    ("3. Prefer one Outcomes row per foal per year. A lifetime total (year blank) is only trusted "
     "for foals at least three years old at the backtest date, and it lets a little hindsight in.", None),
    ("", None),
    ("Where the data comes from", "head"),
    ("See the Sources tab. Collection is manual or through your own AQHA member login. "
     "Nothing in this project scrapes a website.", None),
]


# --------------------------------------------------------------------------
# Writing helpers
# --------------------------------------------------------------------------
def _font(**kw):
    return Font(name=FONT, size=10, **kw)


def _header(ws, headers, widths, fill):
    for c, (h, w) in enumerate(zip(headers, widths), 1):
        cell = ws.cell(row=1, column=c, value=h)
        cell.font = _font(bold=True, color="FFFFFF")
        cell.fill = fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"


def _append(ws, values, formats=None, italic=False, color=None):
    ws.append(list(values))
    r = ws.max_row
    for c in range(1, len(values) + 1):
        cell = ws.cell(row=r, column=c)
        cell.font = _font(italic=italic, color=color)
        if formats and c - 1 < len(formats) and formats[c - 1]:
            cell.number_format = formats[c - 1]
    return r


def _text_sheet(ws, lines, width=120):
    ws.column_dimensions["A"].width = width
    for text, kind in lines:
        ws.append([text])
        cell = ws.cell(row=ws.max_row, column=1)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        if kind == "title":
            cell.font = Font(name=FONT, size=14, bold=True)
        elif kind == "head":
            cell.font = _font(bold=True)
        elif kind == "warn":
            cell.font = _font(bold=True, color="9C0006")
            cell.fill = NOTE_FILL
        else:
            cell.font = _font()


def build_workbook(seed_real_rows=True, banner=None):
    """A workbook with the data-model tabs. `banner` marks synthetic files."""
    wb = Workbook()
    ws = wb.active
    ws.title = "README"
    lines = list(README_LINES)
    if banner:
        lines = [(banner, "warn"), ("", None)] + [
            ln for ln in lines if "seven real stallions" not in ln[0]]
    _text_sheet(ws, lines)

    for tab in INPUT_TABS + EXTRA_TABS:
        ws = wb.create_sheet(tab)
        cols = COLUMNS[tab]
        _header(ws, [c[0] for c in cols], [c[1] for c in cols], INPUT_FILL)

    dv = DataValidation(type="list", formula1='"listed,private treaty,auction,other"', allow_blank=True)
    wb["Snapshots"].add_data_validation(dv)
    dv.add("D2:D5000")
    dv = DataValidation(type="list", formula1='"Stallion,Mare,Gelding"', allow_blank=True)
    wb["Foals"].add_data_validation(dv)
    dv.add("I2:I50000")

    if seed_real_rows:
        st, sn = wb["Stallions"], wb["Snapshots"]
        for sid, name, reg, year, sire, dam, dam_sire, color, fee in SEED_STALLIONS:
            _append(st, [sid, name, reg, year, sire, dam, dam_sire, color, None, None,
                         "From the QStallions halter directory, %s." % SEED_DATE],
                    formats=[None] * 8 + ["$#,##0"])
            _append(sn, [SEED_DATE, sid, fee, "listed" if fee else "private treaty", None, None, None, None,
                         SEED_URL, "As displayed on %s. The listing does not say which season the fee is for; "
                                   "confirm on the stallion's own page and fill fee_year." % SEED_DATE],
                    formats=[None, None, "$#,##0", None, None, "#,##0", "$#,##0"])
        grey = "7F7F7F"
        _append(wb["Mares"], ["EXAMPLE-M1", "EXAMPLE MARE", "0000002", 2012, "EXAMPLE SIRE", "EXAMPLE DAM",
                              34.5, 12, EXAMPLE_NOTE], italic=True, color=grey)
        _append(wb["Foals"], ["EXAMPLE-F1", "EXAMPLE FOAL", "0000003", "0000001", "0000002",
                              "EXAMPLE STALLION", "EXAMPLE MARE", 2021, "Mare", "Sorrel", EXAMPLE_NOTE],
                italic=True, color=grey)
        _append(wb["Outcomes"], ["EXAMPLE-F1", 2022, 6, 14.5, None, None, 2, 1, 3200, 8500,
                                 "yearling auction", "AQHA Record 70", EXAMPLE_NOTE],
                italic=True, color=grey, formats=[None] * 8 + ["$#,##0", "$#,##0"])

    ws = wb.create_sheet("Sources")
    _header(ws, SOURCES[0], [34, 46, 46, 50, 70], INPUT_FILL)
    for row in SOURCES[1:]:
        r = _append(ws, row)
        for c in range(1, 6):
            ws.cell(row=r, column=c).alignment = Alignment(wrap_text=True, vertical="top")

    ws = wb.create_sheet("Dictionary")
    _header(ws, ["tab", "column", "meaning"], [14, 26, 110], INPUT_FILL)
    for tab in INPUT_TABS + EXTRA_TABS:
        for name, _, meaning in COLUMNS[tab]:
            r = _append(ws, [tab, name, meaning])
            ws.cell(row=r, column=3).alignment = Alignment(wrap_text=True, vertical="top")
    return wb


def write_dataset(ds: Dataset, path, banner):
    """Write an in-memory dataset (synthetic) through the same tabs a user fills."""
    wb = build_workbook(seed_real_rows=False, banner=banner)
    st, sn, ma, fo, oc = (wb[t] for t in INPUT_TABS)
    for sid, s in ds.stallions.items():
        _append(st, [sid, s["name"], s["reg"], s.get("foaling_year"), s.get("sire"), s.get("dam"),
                     s.get("dam_sire"), None, None, None, "synthetic"])
    for s in ds.snapshots:
        _append(sn, ["%d-01-01" % s["year"], s["stallion_id"], s["fee"], s["basis"], s["year"],
                     None, None, None, s["source"], None], formats=[None, None, "$#,##0"])
    for mid, m in ds.mares.items():
        _append(ma, [mid, m["name"], m["reg"], m.get("foaling_year"), None, None,
                     m.get("own_points"), None, "synthetic"])
    for fid, f in ds.foals.items():
        sire, dam = ds.stallions[f["sire_id"]], ds.mares[f["dam_id"]]
        _append(fo, [fid, f["name"], f["reg"], sire["reg"], dam["reg"], sire["name"], dam["name"],
                     f["year"], f["sex"], f["color"], None])
    for o in ds.outcomes:
        _append(oc, [o["foal_id"], o["year"], o["shows"], o["points"], None, None, o["grands"],
                     o["reserves"], None, o["sale_price"],
                     "auction" if o["sale_price"] else None, "synthetic", None],
                formats=[None] * 8 + ["$#,##0", "$#,##0"])
    wb.save(path)


# --------------------------------------------------------------------------
# Loading, with the Step 2 link checks
# --------------------------------------------------------------------------
def _blank(v):
    return v is None or str(v).strip() == ""


def _txt(v):
    return None if _blank(v) else str(v).strip()


def _num(v):
    if _blank(v) or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace("$", "").replace(",", "").strip())
    except ValueError:
        return None


def _int(v):
    n = _num(v)
    return None if n is None else int(round(n))


def _year(v):
    if isinstance(v, (dt.date, dt.datetime)):
        return v.year
    n = _num(v)
    if n is not None:
        return int(n) if 1900 <= n <= 2100 else None
    s = _txt(v) or ""
    return int(s[:4]) if s[:4].isdigit() and 1900 <= int(s[:4]) <= 2100 else None


def _reg(v):
    if _blank(v):
        return None
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).strip().upper().replace(" ", "").replace("-", "") or None


def _name(v):
    s = _txt(v)
    return " ".join(s.upper().split()) if s else None


def _rows(wb, tab):
    if tab not in wb.sheetnames:
        return
    it = wb[tab].iter_rows(values_only=True)
    try:
        header = [(_txt(h) or "").lower() for h in next(it)]
    except StopIteration:
        return
    for i, row in enumerate(it, start=2):
        d = {h: v for h, v in zip(header, row) if h}
        if all(_blank(v) for v in d.values()):
            continue
        first = _txt(row[0]) or ""
        if first.upper().startswith("EXAMPLE"):
            continue
        d["_row"] = i
        yield d


def load(path):
    """Read the workbook. Returns (Dataset, link review rows, info dict)."""
    wb = load_workbook(path, read_only=True, data_only=True)
    review, info = [], {"warnings": []}

    def flag(tab, row, ident, name, issue, effect):
        review.append({"tab": tab, "row": row, "id": ident, "name": name,
                       "issue": issue, "effect": effect})

    stallions, by_reg, by_name, snapshots = {}, {}, {}, []
    for r in _rows(wb, "Stallions"):
        reg, name = _reg(r.get("reg_number")), _txt(r.get("name"))
        sid = _txt(r.get("stallion_id")) or reg or name
        if sid is None:
            continue
        if sid in stallions:
            flag("Stallions", r["_row"], sid, name, "duplicate stallion_id", "row ignored")
            continue
        stallions[sid] = {"name": name, "reg": reg, "foaling_year": _year(r.get("foaling_year")),
                          "sire": _txt(r.get("sire")), "dam": _txt(r.get("dam")),
                          "dam_sire": _txt(r.get("dam_sire")), "color": _txt(r.get("color")),
                          "notes": _txt(r.get("notes"))}
        if reg:
            if reg in by_reg:
                flag("Stallions", r["_row"], sid, name,
                     "same registration number as %s" % by_reg[reg], "check which is right")
            else:
                by_reg[reg] = sid
        if _name(name):
            by_name.setdefault(_name(name), sid)
        fee, fee_year = _num(r.get("stud_fee")), _year(r.get("fee_year"))
        if fee is not None and fee_year is not None:
            snapshots.append({"stallion_id": sid, "year": fee_year, "fee": fee,
                              "basis": "listed", "source": "Stallions tab"})
        elif fee is not None:
            flag("Stallions", r["_row"], sid, name, "stud_fee without fee_year",
                 "fee ignored; add fee_year or a Snapshots row")

    for r in _rows(wb, "Snapshots"):
        ref = _txt(r.get("stallion_id"))
        sid = ref if ref in stallions else by_reg.get(_reg(ref)) or by_name.get(_name(ref))
        if sid is None:
            flag("Snapshots", r["_row"], ref, None, "stallion not found in Stallions", "row ignored")
            continue
        year = _year(r.get("fee_year")) or _year(r.get("snapshot_date"))
        if year is None:
            flag("Snapshots", r["_row"], sid, stallions[sid]["name"],
                 "no fee_year and no snapshot_date", "row ignored")
            continue
        seen = r.get("snapshot_date")
        seen = seen.strftime("%Y-%m-%d") if isinstance(seen, (dt.date, dt.datetime)) else (_txt(seen) or "")
        snapshots.append({"stallion_id": sid, "year": year, "fee": _num(r.get("stud_fee")),
                          "basis": _txt(r.get("fee_basis")), "source": _txt(r.get("source")),
                          "date": seen, "note": _txt(r.get("notes")),
                          "chute": _txt(r.get("chute_or_booking_fee"))})

    sire_stats = []
    for r in _rows(wb, "Sire stats"):
        ref = _txt(r.get("stallion_id"))
        sid = ref if ref in stallions else by_reg.get(_reg(ref)) or by_name.get(_name(ref))
        period = _txt(r.get("period"))
        if sid is None or period is None:
            flag("Sire stats", r["_row"], ref, None,
                 "stallion not found in Stallions" if sid is None else "no period", "row ignored")
            continue
        if isinstance(r.get("period"), float) and r["period"].is_integer():
            period = str(int(r["period"]))
        seen = r.get("as_of_date")
        seen = seen.strftime("%Y-%m-%d") if isinstance(seen, (dt.date, dt.datetime)) else (_txt(seen) or "")
        sire_stats.append({"stallion_id": sid, "period": period.lower(), "rank": _int(r.get("rank")),
                           "earners": _int(r.get("money_earners")), "earnings": _num(r.get("progeny_earnings")),
                           "list_size": _int(r.get("list_size")), "cutoff": _num(r.get("list_cutoff")),
                           "date": seen, "source": _txt(r.get("source"))})

    mares, mare_by_reg, mare_by_name = {}, {}, {}
    for r in _rows(wb, "Mares"):
        reg, name = _reg(r.get("reg_number")), _txt(r.get("name"))
        mid = _txt(r.get("mare_id")) or reg or name
        if mid is None:
            continue
        if mid in mares:
            flag("Mares", r["_row"], mid, name, "duplicate mare_id", "row ignored")
            continue
        mares[mid] = {"name": name, "reg": reg, "own_points": _num(r.get("own_halter_points"))}
        if reg:
            mare_by_reg.setdefault(reg, mid)
        if _name(name):
            mare_by_name.setdefault(_name(name), mid)
    info["mares_listed"] = len(mares)

    foals, foal_by_reg, seen_rows = {}, {}, 0
    for r in _rows(wb, "Foals"):
        seen_rows += 1
        reg, name = _reg(r.get("reg_number")), _txt(r.get("name"))
        fid = _txt(r.get("foal_id")) or reg or name or "row %d" % r["_row"]
        if fid in foals or (reg and reg in foal_by_reg):
            flag("Foals", r["_row"], fid, name, "duplicate foal", "row ignored")
            continue
        year = _year(r.get("foaling_year"))
        if year is None:
            flag("Foals", r["_row"], fid, name, "no foaling_year", "foal left out")
            continue

        # sire
        sreg, sname = _reg(r.get("sire_reg_number")), _name(r.get("sire_name"))
        sid = None
        if sreg and sreg in by_reg:
            sid = by_reg[sreg]
            if sname and sname != _name(stallions[sid]["name"]):
                flag("Foals", r["_row"], fid, name,
                     "sire number %s belongs to %s but the foal's record says %s"
                     % (sreg, stallions[sid]["name"], sname), "foal left out until resolved")
                continue
        elif sreg:
            hint = " (a stallion named %s exists with a different number)" % sname \
                if sname in by_name else ""
            flag("Foals", r["_row"], fid, name,
                 "sire number %s is not in Stallions%s" % (sreg, hint), "foal left out")
            continue
        elif sname and sname in by_name:
            sid = by_name[sname]
            flag("Foals", r["_row"], fid, name, "sire matched by name only, no registration number",
                 "foal kept; add the number")
        else:
            flag("Foals", r["_row"], fid, name, "no sire given or sire not in Stallions", "foal left out")
            continue
        sire_year = stallions[sid].get("foaling_year")
        if sire_year and year < sire_year + 2:
            flag("Foals", r["_row"], fid, name,
                 "foaled %d but the sire was foaled %d" % (year, sire_year), "foal left out until resolved")
            continue

        # dam: a number or a name is enough to identify her across foals
        dreg, dname = _reg(r.get("dam_reg_number")), _name(r.get("dam_name"))
        did = None
        if dreg:
            did = mare_by_reg.get(dreg)
            if did is None:
                did = "reg:" + dreg
                mares[did] = {"name": _txt(r.get("dam_name")), "reg": dreg, "own_points": None}
                mare_by_reg[dreg] = did
            elif dname and _name(mares[did]["name"]) and dname != _name(mares[did]["name"]):
                flag("Foals", r["_row"], fid, name,
                     "dam number %s belongs to %s but the foal's record says %s"
                     % (dreg, mares[did]["name"], dname), "foal kept, dam treated as unknown")
                did = None
        elif dname:
            did = mare_by_name.get(dname)
            if did is None:
                did = "name:" + dname
                mares[did] = {"name": _txt(r.get("dam_name")), "reg": None, "own_points": None}
                mare_by_name[dname] = did
        foals[fid] = {"name": name, "reg": reg, "sire_id": sid, "dam_id": did, "year": year,
                      "sex": _txt(r.get("sex")), "color": _txt(r.get("coat_color"))}
        if reg:
            foal_by_reg[reg] = fid
    info["foal_rows"] = seen_rows
    info["mares_from_foal_records"] = len(mares) - info["mares_listed"]

    outcomes, kinds = [], {"points": 0, "placing": 0}
    for r in _rows(wb, "Outcomes"):
        ref = _txt(r.get("foal_id"))
        fid = ref if ref in foals else foal_by_reg.get(_reg(ref))
        if fid is None:
            flag("Outcomes", r["_row"], ref, None,
                 "foal not found (missing from Foals, or left out above)", "row ignored")
            continue
        year = _year(r.get("year"))
        if year is not None and year < foals[fid]["year"]:
            flag("Outcomes", r["_row"], fid, foals[fid]["name"],
                 "result dated %d, before the foal was born" % year, "row ignored")
            continue
        o = {"foal_id": fid, "year": year, "shows": _int(r.get("halter_shows")),
             "points": _num(r.get("halter_points")), "placing": _int(r.get("placing")),
             "class_size": _int(r.get("class_size")), "grands": _int(r.get("grands")),
             "reserves": _int(r.get("reserves")), "earnings": _num(r.get("earnings")),
             "sale_price": _num(r.get("sale_price")), "source": _txt(r.get("source"))}
        if o["points"] is not None:
            kinds["points"] += 1
        elif o["placing"] is not None:
            kinds["placing"] += 1
        outcomes.append(o)
    if kinds["points"] and kinds["placing"]:
        info["warnings"].append(
            "Outcomes mixes %d rows scored by AQHA points with %d rows scored by placing only. "
            "The two scales are not comparable; use one kind." % (kinds["points"], kinds["placing"]))
    wb.close()
    return (Dataset(stallions=stallions, snapshots=snapshots, mares=mares, foals=foals,
                    outcomes=outcomes, sire_stats=sire_stats), review, info)


# --------------------------------------------------------------------------
# Results tabs
# --------------------------------------------------------------------------
def _table(wb, title, headers, widths, rows, formats, index=None):
    ws = wb.create_sheet(title, index) if index is not None else wb.create_sheet(title)
    _header(ws, headers, widths, RESULT_FILL)
    for row in rows:
        _append(ws, row, formats)
    return ws


def write_results(input_path, out_path, ds, ranked, skipped, fit, bt, review, info, params,
                  synthetic=False):
    wb = load_workbook(input_path)
    for tab in RESULT_TABS:
        if tab in wb.sheetnames:
            del wb[tab]

    v = bt["verdict"]
    primary = bt["primary"]
    label = {"fwd_score": "average foal score", "fwd_adj": "average foal score, adjusted for the dam",
             "pct_earners": "share of foals earning points", "mean_sale": "average sale price"}

    # ---- Results summary ------------------------------------------------
    lines = [("Breeding Value Ranker: results", "title"),
             ("Written by bvr.py on %s from %s. Plain values, not formulas: run the script again "
              "after changing any input tab." % (dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                                 str(input_path).split("/")[-1]), None)]
    if synthetic:
        lines.append(("SYNTHETIC DATA. These horses do not exist. This file only proves the "
                      "pipeline works.", "warn"))
    lines += [("", None), ("Backtest verdict: %s" % v["status"], "head"), (v["why"], None),
              ("Measure used for the verdict: %s." % label[primary], None),
              ("Rule (fixed in advance): at least three time windows; the top value picks must beat "
               "the cheap-but-average group in more than half of them; and their average standing "
               "against random picks at a similar fee must clear a bar that chance alone reaches "
               "about 1 time in 20 (77th percentile for 3 windows, 74th for 4, 71st for 5).", None),
              ("", None), ("Window by window", "head")]
    for w in bt["windows"]:
        g = w.get("groups") or {}
        pk = g.get("Top value picks")
        if not pk:
            lines.append(("As of %d: not usable, %s." % (w["asof"], w["note"]), None))
            continue
        ch, rd = g["Cheap but average"], g["Random, similar fee (median)"]
        pct = w["matched_percentile"].get(primary)

        def f(x):
            return "n/a" if x is None else "%.1f" % x
        lines.append((
            "As of %d (foals born %s; %d stallions in the pool; %d picks, %d with enough foals to judge, "
            "%d foals): picks %s, cheap-but-average %s, random at a similar fee %s. "
            "Picks beat %s of random same-price draws.%s"
            % (w["asof"], w["forward_crops"], w["pool"], pk["stallions"], pk["evaluated"], pk["foals"],
               f(pk[primary]), f(ch[primary]), f(rd[primary]),
               "n/a" if pct is None else "%.0f%%" % pct,
               " Note: %s." % w["note"] if w["note"] else ""), None))
    if not bt["windows"]:
        lines.append(("No window could be run. A window needs dated fees and foals born at least "
                      "three years after the as-of year.", None))
    if any(v["per_measure"][m]["n"] for m in MEASURES):
        lines += [("", None), ("Other outcome measures (not part of the verdict)", "head")]
        for m in MEASURES:
            pm = v["per_measure"][m]
            lines.append(("%s: picks beat cheap-but-average in %d of %d windows and beat the median "
                          "same-price random pick in %d of %d."
                          % (label[m].capitalize(), pm["cheap"], pm["n"], pm["random"], pm["n"]), None))
        lines.append(("Four measures give four chances to look good by luck. Only the one named "
                      "above counts toward the verdict.", None))

    n_fee = len({s["stallion_id"] for s in ds.snapshots if s.get("fee") is not None})
    with_mare = sum(1 for q in fit.mare_q.values() if q is not None)
    lines += [("", None), ("Data used", "head"),
              ("%d stallions, %d of them with at least one dollar fee on file. %d ranked today."
               % (len(ds.stallions), n_fee, len(ranked)), None),
              ("%d foals linked to a sire (of %d rows in Foals). %d outcome rows. %d mares "
               "(%d listed in Mares, %d known only from foal records)."
               % (len(ds.foals), info.get("foal_rows", len(ds.foals)), len(ds.outcomes),
                  len(ds.mares), info.get("mares_listed", 0), info.get("mares_from_foal_records", 0)), None),
              ("%d rows need a look in the Link review tab." % len(review), None),
              ("", None), ("How the stallion effect was estimated", "head")]
    if fit.mare_active:
        lines.append(("Dam adjustment: ON. %d of %d foals have a dam quality figure. Each point of dam "
                      "quality is worth %.2f points of foal score (measured inside each stallion's own foals)."
                      % (with_mare, len(fit.mare_q), fit.slope), None))
    else:
        lines.append(("Dam adjustment: OFF (%d foals with dam information, %d needed). Effects are plain "
                      "foal averages, so a stallion bred to better mares will look better than he is."
                      % (fit.mare_pairs, params.min_mare_pairs), "warn"))
    share = fit.sire_share
    lines.append(("Share of the spread in foal scores that sits between stallions: %s. Shrinkage constant "
                  "k = %.0f (%s): a stallion needs about %.0f scored foals before half of his raw "
                  "advantage is believed."
                  % ("not estimable" if share is None else "%.1f%%" % (100 * share),
                     fit.k, fit.k_source, fit.k), None))

    warns = list(info["warnings"])
    leak = max([w.get("lifetime_only_foals", 0) for w in bt["windows"]] or [0])
    if leak:
        warns.append("Up to %d foals per window were scored from lifetime totals. Those totals can "
                     "include points won after the backtest date, which flatters the ranking slightly. "
                     "Year-by-year Outcomes rows remove this." % leak)
    if params.fee_fallback == "latest":
        warns.append("Fee fallback is on: every past date was priced with the most recent fee on file. "
                     "That is hindsight in the price, so value-per-dollar results are optimistic.")
    if not ds.foals:
        warns.append("No foals yet, so nothing could be scored. Fill the Foals and Outcomes tabs.")
    if warns:
        lines += [("", None), ("Warnings", "head")] + [(w, "warn") for w in warns]
    lines += [("", None), ("Settings", "head")] + [
        ("%s = %s" % (k, val), None) for k, val in sorted(vars(params).items())]
    ws = wb.create_sheet("Results summary", 1)
    _text_sheet(ws, lines, width=150)

    # ---- Ranking --------------------------------------------------------
    rows = []
    for r in ranked:
        rows.append([r["rank"], r["stallion_id"], r["name"], r["fee"], r["fee_year"], r["n"],
                     r["mean_score"], r["n_mare"], r["mean_mare_q"], r["foal_minus_mare"],
                     r["raw_effect"], r["raw_se"], r["shrink"], r["effect"], r["se"],
                     r["effect"] - 1.28 * r["se"], r["effect"] + 1.28 * r["se"],
                     r["value_per_1k"], r["status"]])
    for r in skipped:
        rows.append([None, r["stallion_id"], r["name"], r["fee"], r["fee_year"], r["foals"]]
                    + [None] * 12 + [r["status"]])
    one = "0.0"
    _table(wb, "Ranking",
           ["rank", "stallion_id", "name", "stud_fee", "fee_year", "foals_scored", "avg_foal_score",
            "foals_with_dam_info", "avg_dam_quality", "foal_avg_minus_dam_avg", "raw_effect",
            "raw_margin_of_error", "share_believed", "effect", "effect_margin_of_error",
            "effect_low_80", "effect_high_80", "effect_per_$1,000", "status"],
           [7, 12, 26, 10, 9, 9, 10, 10, 10, 12, 10, 11, 10, 9, 11, 10, 10, 11, 44],
           rows, [None, None, None, "$#,##0", "0", "0", one, "0", one, one, one, one, "0%",
                  one, one, one, one, "0.00", None])

    # ---- Backtest -------------------------------------------------------
    rows = []
    for w in bt["windows"]:
        for name, g in (w.get("groups") or {}).items():
            pct = None
            if name == "Top value picks":
                pct = (w.get("matched_percentile") or {}).get(primary)
            rows.append([w["asof"], w["forward_crops"], name, g["stallions"], g["evaluated"],
                         g["foals"], g["mean_fee"], g["past_effect"], g["past_mare_q"],
                         g["fwd_score"], g["fwd_adj"], g["pct_earners"], g["mean_sale"], g["sold"],
                         None if pct is None else pct / 100.0, w["note"] if name == "Top value picks" else None])
        if not w.get("groups"):
            rows.append([w["asof"], w["forward_crops"], "not usable"] + [None] * 12 + [w["note"]])
    _table(wb, "Backtest",
           ["as_of_year", "foals_born", "group", "stallions", "stallions_judged", "foals_judged",
            "avg_fee_then", "avg_effect_then", "avg_dam_quality_then", "later_avg_foal_score",
            "later_score_dam_adjusted", "later_pct_point_earners", "later_avg_sale_price",
            "foals_sold", "picks_beat_this_share_of_same_price_random", "note"],
           [10, 11, 30, 9, 9, 9, 11, 10, 11, 11, 11, 11, 12, 8, 16, 60],
           rows, ["0", None, None, "0", "0", "0", "$#,##0", one, one, one, one, one,
                  "$#,##0", "0", "0%", None])

    rows = []
    for w in bt["windows"]:
        for pk in w.get("picks", []):
            rows.append([pk["asof"], pk["rank"], pk["stallion_id"], pk["name"], pk["fee"],
                         pk["foals_then"], pk["effect_then"], pk["value_per_1k"], pk["forward_foals"],
                         pk["fwd_score"], pk["fwd_adj"], pk["pct_earners"]])
    _table(wb, "Backtest picks",
           ["as_of_year", "rank_then", "stallion_id", "name", "fee_then", "foals_then", "effect_then",
            "effect_per_$1,000_then", "later_foals", "later_avg_foal_score",
            "later_score_dam_adjusted", "later_pct_point_earners"],
           [10, 9, 12, 26, 10, 9, 10, 12, 9, 11, 11, 11],
           rows, ["0", "0", None, None, "$#,##0", "0", one, "0.00", "0", one, one, one])

    # ---- Foal scores ----------------------------------------------------
    rows = []
    for fid, sc in sorted(fit.scores.items(), key=lambda kv: (ds.foals[kv[0]]["year"], -kv[1])):
        f, t = ds.foals[fid], fit.totals[fid]
        sire = ds.stallions.get(f["sire_id"], {})
        rows.append([fid, f["name"], f["year"], f["sire_id"], sire.get("name"), f["dam_id"],
                     t["shows"], t["points"], t["grands"], t["reserves"], sc,
                     fit.mare_q.get(fid), t["sale_price"]])
    _table(wb, "Foal scores",
           ["foal_id", "name", "foaling_year", "sire_id", "sire", "dam_id", "halter_shows",
            "halter_points", "grands", "reserves", "score_0_to_100", "dam_quality", "sale_price"],
           [13, 24, 10, 11, 24, 16, 9, 9, 8, 9, 10, 10, 11],
           rows, [None, None, "0", None, None, None, "0", one, "0", "0", one, one, "$#,##0"])

    # ---- Link review ----------------------------------------------------
    _table(wb, "Link review", ["tab", "row", "id", "name", "issue", "what the script did"],
           [12, 7, 16, 26, 80, 40],
           [[r["tab"], r["row"], r["id"], r["name"], r["issue"], r["effect"]] for r in review],
           [None] * 6)
    wb.save(out_path)
