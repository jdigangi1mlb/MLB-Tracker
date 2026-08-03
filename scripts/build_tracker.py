#!/usr/bin/env python3
from __future__ import annotations

import base64
import difflib
import html
import json
import mimetypes
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DATA = ROOT / "data"
ASSETS = ROOT / "assets"
TEMPLATE = ROOT / "templates" / "index.html.tpl"

MLB_URL = "https://www.mlb.com/amp/news/mlb-trade-deadline-2026-deal-tracker.html"
CBS_URL = "https://www.cbssports.com/mlb/news/mlb-trade-deadline-tracker-2026/"
CUTOFF = (2026, 7, 31)
DEADLINE_DATE = "Aug. 3"
DEADLINE_TIME = "5:00 PM CT"

TEAM_IDS = {
    "ARI": 109, "ATL": 144, "BAL": 110, "BOS": 111, "CHC": 112,
    "CIN": 113, "CLE": 114, "COL": 115, "DET": 116, "HOU": 117,
    "KC": 118, "LAD": 119, "WSH": 120, "NYM": 121, "OAK": 133,
    "PIT": 134, "SD": 135, "SEA": 136, "SF": 137, "STL": 138,
    "TB": 139, "TEX": 140, "TOR": 141, "MIN": 142, "PHI": 143,
    "CWS": 145, "MIA": 146, "NYY": 147, "MIL": 158, "LAA": 108,
}

DISPLAY = {
    "ARI": "Diamondbacks", "ATL": "Braves", "BAL": "Orioles",
    "BOS": "Red Sox", "CHC": "Cubs", "CIN": "Reds",
    "CLE": "Guardians", "COL": "Rockies", "DET": "Tigers",
    "HOU": "Astros", "KC": "Royals", "LAD": "Dodgers",
    "WSH": "Nationals", "NYM": "Mets", "OAK": "Athletics",
    "PIT": "Pirates", "SD": "Padres", "SEA": "Mariners",
    "SF": "Giants", "STL": "Cardinals", "TB": "Rays",
    "TEX": "Rangers", "TOR": "Blue Jays", "MIN": "Twins",
    "PHI": "Phillies", "CWS": "White Sox", "MIA": "Marlins",
    "NYY": "Yankees", "MIL": "Brewers", "LAA": "Angels",
}

ALIASES = {
    "arizona": "ARI", "diamondbacks": "ARI", "atlanta": "ATL",
    "braves": "ATL", "baltimore": "BAL", "orioles": "BAL",
    "boston": "BOS", "red sox": "BOS", "chi cubs": "CHC",
    "chicago cubs": "CHC", "cubs": "CHC", "cincinnati": "CIN",
    "reds": "CIN", "cleveland": "CLE", "guardians": "CLE",
    "colorado": "COL", "rockies": "COL", "detroit": "DET",
    "tigers": "DET", "houston": "HOU", "astros": "HOU",
    "kansas city": "KC", "royals": "KC", "la dodgers": "LAD",
    "los angeles dodgers": "LAD", "dodgers": "LAD",
    "washington": "WSH", "nationals": "WSH", "ny mets": "NYM",
    "new york mets": "NYM", "mets": "NYM", "athletics": "OAK",
    "oakland": "OAK", "pittsburgh": "PIT", "pirates": "PIT",
    "san diego": "SD", "padres": "SD", "seattle": "SEA",
    "mariners": "SEA", "san francisco": "SF", "giants": "SF",
    "st louis": "STL", "cardinals": "STL", "tampa bay": "TB",
    "rays": "TB", "texas": "TEX", "rangers": "TEX",
    "toronto": "TOR", "blue jays": "TOR", "minnesota": "MIN",
    "twins": "MIN", "philadelphia": "PHI", "phillies": "PHI",
    "chi white sox": "CWS", "chicago white sox": "CWS",
    "white sox": "CWS", "miami": "MIA", "marlins": "MIA",
    "ny yankees": "NYY", "new york yankees": "NYY",
    "yankees": "NYY", "milwaukee": "MIL", "brewers": "MIL",
    "la angels": "LAA", "los angeles angels": "LAA", "angels": "LAA",
}

DATE_RE = re.compile(
    r"^(Aug\.|August|July)\s+(\d{1,2})(?:\s*\([^)]*\))?$",
    re.IGNORECASE,
)
GET_RE = re.compile(r"^(.+?)\s+get(?:s)?:\s*(.*)$", re.IGNORECASE)


@dataclass(frozen=True)
class Side:
    team: str
    acquired: str


@dataclass(frozen=True)
class Trade:
    date: str
    a: Side
    b: Side
    status: str
    sources: tuple[str, ...]
    reporter: str = ""
    winner: str = ""


def make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/126 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    })
    return session


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def parse_date(label: str) -> tuple[int, int, int] | None:
    match = DATE_RE.fullmatch(clean(label))
    if not match:
        return None
    month = 8 if match.group(1).lower().startswith("aug") else 7
    return (2026, month, int(match.group(2)))


def display_date(label: str) -> str:
    parsed = parse_date(label)
    if not parsed:
        raise ValueError(f"Invalid date label: {label!r}")
    _, month, day = parsed
    return f"Aug. {day}" if month == 8 else f"July {day}"


def canonical_team(name: str) -> str:
    value = clean(name).lower()
    value = re.sub(r"[.'’]", "", value)
    value = clean(value)
    if value in ALIASES:
        return ALIASES[value]
    for alias, code in sorted(ALIASES.items(), key=lambda item: -len(item[0])):
        if value == alias or value.endswith(" " + alias):
            return code
    raise ValueError(f"Unknown team: {name}")


def parse_get_line(text: str) -> Side:
    match = GET_RE.match(clean(text).lstrip("•- "))
    if not match or not clean(match.group(2)):
        raise ValueError(text)
    return Side(canonical_team(match.group(1)), clean(match.group(2)))


def _mlb_tokens(markup: str) -> list[str]:
    soup = BeautifulSoup(markup, "html.parser")
    root = soup.find("article") or soup.find("main") or soup
    return [clean(token) for token in root.stripped_strings if clean(token)]


def parse_mlb(markup: str) -> list[Trade]:
    """Parse MLB from leaf text tokens instead of relying on specific tag names.

    MLB has changed date headings and trade rows among h-tags, paragraphs,
    strong tags and linked player text. Token parsing survives those changes.
    """
    tokens = _mlb_tokens(markup)
    current_date: str | None = None
    pending: list[Side] = []
    results: list[Trade] = []
    seen_sides: set[tuple[str, str, str]] = set()
    index = 0

    while index < len(tokens):
        token = tokens[index]
        parsed_date = parse_date(token)
        if parsed_date:
            current_date = display_date(token)
            pending = []
            index += 1
            continue

        if not current_date or parse_date(current_date) < CUTOFF:
            index += 1
            continue

        match = GET_RE.match(token.lstrip("•- "))
        if not match:
            index += 1
            continue

        team_text = clean(match.group(1))
        acquired = clean(match.group(2))

        # MLB often puts "Team get:" in one node and linked player text in
        # the following node. Join only until the next structural boundary.
        if not acquired:
            pieces: list[str] = []
            cursor = index + 1
            while cursor < len(tokens):
                next_token = tokens[cursor]
                if (
                    parse_date(next_token)
                    or GET_RE.match(next_token.lstrip("•- "))
                    or next_token.lower().startswith("--source")
                ):
                    break
                pieces.append(next_token)
                cursor += 1
                if len(" ".join(pieces)) > 350:
                    break
            acquired = clean(" ".join(pieces))
            index = max(index, cursor - 1)

        if not acquired:
            index += 1
            continue

        try:
            side = Side(canonical_team(team_text), acquired)
        except ValueError:
            index += 1
            continue

        identity = (current_date, side.team, side.acquired)
        if identity in seen_sides:
            index += 1
            continue
        seen_sides.add(identity)
        pending.append(side)

        if len(pending) == 2:
            results.append(
                Trade(current_date, pending[0], pending[1], "MLB", ("MLB.com",))
            )
            pending = []

        index += 1

    if len(results) < 10:
        raise RuntimeError(
            f"MLB parser found only {len(results)} trades from July 31 forward."
        )
    return results


def parse_cbs(markup: str) -> list[Trade]:
    soup = BeautifulSoup(markup, "html.parser")
    current_date: str | None = None
    results: list[Trade] = []

    for tag in soup.find_all(["h2", "h3", "table"]):
        if tag.name in ("h2", "h3"):
            heading = clean(tag.get_text(" ", strip=True))
            if parse_date(heading):
                current_date = display_date(heading)
            continue

        if not current_date or parse_date(current_date) < CUTOFF:
            continue

        rows: list[list[str]] = []
        for row in tag.find_all("tr"):
            cells = [
                clean(cell.get_text(" ", strip=True))
                for cell in row.find_all(["th", "td"])
            ]
            if len(cells) >= 2 and cells[0].lower() not in ("team", ""):
                rows.append(cells[:2])

        if len(rows) >= 2:
            try:
                first = Side(canonical_team(rows[0][0]), rows[0][1])
                second = Side(canonical_team(rows[1][0]), rows[1][1])
            except ValueError:
                continue
            results.append(
                Trade(current_date, first, second, "CBS", ("CBS Sports",))
            )

    if len(results) < 10:
        raise RuntimeError(
            f"CBS parser found only {len(results)} trades from July 31 forward."
        )
    return results


def normalized_players(value: str) -> str:
    value = value.lower()
    value = re.sub(
        r"\b(rhp|lhp|of|inf|if|c|ss|1b|2b|3b|ptbnl|cash considerations|cash)\b",
        " ",
        value,
    )
    return clean(re.sub(r"[^a-z0-9áéíóúñüç -]", " ", value))


def pair_key(trade: Trade) -> tuple[str, str]:
    # MLB controls the displayed date. Match CBS presence by the two teams and
    # return-package similarity because the ledgers can post the same deal under
    # adjacent dates.
    teams = sorted((trade.a.team, trade.b.team))
    return (teams[0], teams[1])


def similarity(first: Trade, second: Trade) -> float:
    a = normalized_players(first.a.acquired + " " + first.b.acquired)
    b = normalized_players(second.a.acquired + " " + second.b.acquired)
    return difflib.SequenceMatcher(None, a, b).ratio()


def _load_mapping(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def merge_ledgers(mlb: list[Trade], cbs: list[Trade]) -> list[Trade]:
    used: set[int] = set()
    merged: list[Trade] = []

    for mlb_trade in mlb:
        candidates = [
            (index, cbs_trade)
            for index, cbs_trade in enumerate(cbs)
            if index not in used and pair_key(cbs_trade) == pair_key(mlb_trade)
        ]
        if candidates:
            index, best = max(candidates, key=lambda item: similarity(mlb_trade, item[1]))
            if similarity(mlb_trade, best) >= 0.35:
                used.add(index)
                merged.append(
                    Trade(
                        mlb_trade.date,
                        mlb_trade.a,
                        mlb_trade.b,
                        "VERIFIED",
                        ("MLB.com", "CBS Sports"),
                    )
                )
                continue
        merged.append(
            Trade(
                mlb_trade.date,
                mlb_trade.a,
                mlb_trade.b,
                "UNVERIFIED - MLB ONLY",
                ("MLB.com",),
            )
        )

    for index, cbs_trade in enumerate(cbs):
        if index not in used:
            merged.append(
                Trade(
                    cbs_trade.date,
                    cbs_trade.a,
                    cbs_trade.b,
                    "UNVERIFIED - CBS ONLY",
                    ("CBS Sports",),
                )
            )

    reporters = _load_mapping(DATA / "reporters.json")
    winners = _load_mapping(DATA / "winners.json")
    enriched: list[Trade] = []
    for trade in merged:
        key = f"{trade.date}|{trade.a.team}|{trade.b.team}|{trade.a.acquired}"
        enriched.append(
            Trade(
                trade.date,
                trade.a,
                trade.b,
                trade.status,
                trade.sources,
                reporters.get(key, ""),
                winners.get(key, ""),
            )
        )
    return enriched


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    raw = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{raw}"


def logo_uri(session: requests.Session, code: str) -> str:
    logo_dir = ASSETS / "team-logos"
    logo_dir.mkdir(exist_ok=True)
    svg = logo_dir / f"{code}.svg"
    if not svg.exists():
        response = session.get(
            f"https://www.mlbstatic.com/team-logos/{TEAM_IDS[code]}.svg",
            timeout=30,
        )
        response.raise_for_status()
        if "<svg" not in response.text[:500]:
            raise RuntimeError(f"Invalid logo response for {code}.")
        svg.write_text(response.text, encoding="utf-8")
    return data_uri(svg)


def source_buttons(sources: tuple[str, ...]) -> str:
    buttons: list[str] = []
    for source in sources:
        url = MLB_URL if source == "MLB.com" else CBS_URL
        buttons.append(
            f'<a class="source" href="{url}" target="_blank" '
            f'rel="noopener">{html.escape(source)}</a>'
        )
    return "".join(buttons)


def render(trades: list[Trade], session: requests.Session) -> str:
    team_codes = sorted({code for trade in trades for code in (trade.a.team, trade.b.team)})
    logos = {code: logo_uri(session, code) for code in team_codes}
    cards: list[str] = []

    for trade in trades:
        css_class = "verified" if trade.status == "VERIFIED" else "unverified"
        buttons = source_buttons(trade.sources)
        reporter = (
            f'<div class="reporter">Reported by {html.escape(trade.reporter)}</div>'
            if trade.reporter else ""
        )
        a_winner = " winner" if trade.winner == trade.a.team else ""
        b_winner = " winner" if trade.winner == trade.b.team else ""
        cards.append(f'''<article class="trade-card {css_class}">
<div class="trade-date">{html.escape(trade.date.upper())}</div>
<div class="logo-pair"><img class="{a_winner.strip()}" src="{logos[trade.a.team]}" alt="{trade.a.team} logo"><span>↔</span><img class="{b_winner.strip()}" src="{logos[trade.b.team]}" alt="{trade.b.team} logo"></div>
<div class="trade-details"><p><strong>{DISPLAY[trade.a.team]} get:</strong> {html.escape(trade.a.acquired)}</p><p><strong>{DISPLAY[trade.b.team]} get:</strong> {html.escape(trade.b.acquired)}</p><div class="mobile-sources"><span class="status {css_class}">{html.escape(trade.status)}</span>{buttons}{reporter}</div></div>
<div class="desktop-sources"><span class="status {css_class}">{html.escape(trade.status)}</span>{buttons}{reporter}</div>
</article>''')

    now = datetime.now(ZoneInfo("America/Chicago"))
    updated_date = now.strftime("%b. %-d")
    updated_time = now.strftime("%-I:%M %p CT")
    updated_full = f"{updated_date} · {updated_time}"
    output = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "__NL__": data_uri(ASSETS / "national_league.png"),
        "__AL__": data_uri(ASSETS / "american_league.png"),
        "__UPDATED_DATE__": updated_date,
        "__UPDATED_TIME__": updated_time,
        "__UPDATED_FULL__": updated_full,
        "__DEADLINE_DATE__": DEADLINE_DATE,
        "__DEADLINE_TIME__": DEADLINE_TIME,
        "__ROWS__": "".join(cards),
    }
    for marker, value in replacements.items():
        output = output.replace(marker, value)
    return output


def main() -> None:
    session = make_session()
    mlb_response = session.get(MLB_URL, timeout=30)
    mlb_response.raise_for_status()
    cbs_response = session.get(CBS_URL, timeout=30)
    cbs_response.raise_for_status()

    mlb = parse_mlb(mlb_response.text)
    cbs = parse_cbs(cbs_response.text)
    print(f"Parsed {len(mlb)} MLB trades and {len(cbs)} CBS trades from July 31 forward.")
    merged = merge_ledgers(mlb, cbs)

    canonical = {"trades": [asdict(trade) for trade in merged]}
    snapshot_path = DATA / "snapshot.json"
    previous: dict = {}
    if snapshot_path.exists():
        previous = json.loads(snapshot_path.read_text(encoding="utf-8"))

    if previous.get("trades") == canonical["trades"]:
        print("Ledger unchanged; preserving the existing site and timestamp.")
        return

    canonical["updated_at_ct"] = datetime.now(ZoneInfo("America/Chicago")).isoformat()
    snapshot_path.write_text(
        json.dumps(canonical, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (SITE / "index.html").write_text(render(merged, session), encoding="utf-8")

    previous_entries = {
        json.dumps(item, sort_keys=True, ensure_ascii=False)
        for item in previous.get("trades", [])
    }
    changed_entries = [
        item
        for item in canonical["trades"]
        if json.dumps(item, sort_keys=True, ensure_ascii=False) not in previous_entries
    ]
    lines = [
        "# MLB trade tracker changed",
        "",
        f"Detected {len(merged)} trades from July 31 forward.",
        "",
        "## New or changed entries",
    ]
    for item in changed_entries:
        lines.append(
            f"- {item['date']}: {item['a']['team']} / "
            f"{item['b']['team']} — {item['status']}"
        )
    (DATA / "change_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
