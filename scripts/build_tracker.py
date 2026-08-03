#!/usr/bin/env python3
from __future__ import annotations

import base64
import difflib
import html
import json
import mimetypes
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"site"
DATA=ROOT/"data"
ASSETS=ROOT/"assets"
TEMPLATE=ROOT/"templates"/"index.html.tpl"

MLB_URL="https://www.mlb.com/amp/news/mlb-trade-deadline-2026-deal-tracker.html"
CBS_URL="https://www.cbssports.com/mlb/news/mlb-trade-deadline-tracker-2026/"
CUTOFF=(2026,7,31)

TEAM_IDS={
    "ARI":109,"ATL":144,"BAL":110,"BOS":111,"CHC":112,"CIN":113,"CLE":114,
    "COL":115,"DET":116,"HOU":117,"KC":118,"LAD":119,"WSH":120,"NYM":121,
    "OAK":133,"PIT":134,"SD":135,"SEA":136,"SF":137,"STL":138,"TB":139,
    "TEX":140,"TOR":141,"MIN":142,"PHI":143,"CWS":145,"MIA":146,"NYY":147,
    "MIL":158,"LAA":108,
}
DISPLAY={
    "ARI":"Diamondbacks","ATL":"Braves","BAL":"Orioles","BOS":"Red Sox",
    "CHC":"Cubs","CIN":"Reds","CLE":"Guardians","COL":"Rockies","DET":"Tigers",
    "HOU":"Astros","KC":"Royals","LAD":"Dodgers","WSH":"Nationals","NYM":"Mets",
    "OAK":"Athletics","PIT":"Pirates","SD":"Padres","SEA":"Mariners","SF":"Giants",
    "STL":"Cardinals","TB":"Rays","TEX":"Rangers","TOR":"Blue Jays","MIN":"Twins",
    "PHI":"Phillies","CWS":"White Sox","MIA":"Marlins","NYY":"Yankees",
    "MIL":"Brewers","LAA":"Angels",
}
ALIASES={
    "arizona":"ARI","diamondbacks":"ARI","atlanta":"ATL","braves":"ATL",
    "baltimore":"BAL","orioles":"BAL","boston":"BOS","red sox":"BOS",
    "chi cubs":"CHC","chicago cubs":"CHC","cubs":"CHC","cincinnati":"CIN",
    "reds":"CIN","cleveland":"CLE","guardians":"CLE","colorado":"COL",
    "rockies":"COL","detroit":"DET","tigers":"DET","houston":"HOU",
    "astros":"HOU","kansas city":"KC","royals":"KC","la dodgers":"LAD",
    "los angeles dodgers":"LAD","dodgers":"LAD","washington":"WSH",
    "nationals":"WSH","ny mets":"NYM","new york mets":"NYM","mets":"NYM",
    "athletics":"OAK","oakland":"OAK","pittsburgh":"PIT","pirates":"PIT",
    "san diego":"SD","padres":"SD","seattle":"SEA","mariners":"SEA",
    "san francisco":"SF","giants":"SF","st louis":"STL","cardinals":"STL",
    "tampa bay":"TB","rays":"TB","texas":"TEX","rangers":"TEX",
    "toronto":"TOR","blue jays":"TOR","minnesota":"MIN","twins":"MIN",
    "philadelphia":"PHI","phillies":"PHI","chi white sox":"CWS",
    "chicago white sox":"CWS","white sox":"CWS","miami":"MIA","marlins":"MIA",
    "ny yankees":"NYY","new york yankees":"NYY","yankees":"NYY",
    "milwaukee":"MIL","brewers":"MIL","la angels":"LAA",
    "los angeles angels":"LAA","angels":"LAA",
}

@dataclass(frozen=True)
class Side:
    team:str
    acquired:str

@dataclass(frozen=True)
class Trade:
    date:str
    a:Side
    b:Side
    status:str
    sources:tuple[str,...]
    reporter:str=""

def make_session():
    session=requests.Session()
    retry=Retry(
        total=4,
        backoff_factor=1.5,
        status_forcelist=(429,500,502,503,504),
        allowed_methods=("GET",),
    )
    session.mount("https://",HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent":"Mozilla/5.0 (compatible; MLBTradeTracker/1.0)"})
    return session

def clean(value):
    return re.sub(r"\s+"," ",value.replace("\xa0"," ")).strip()

def parse_date(label):
    match=re.fullmatch(r"(Aug\.|August|July)\s+(\d{1,2})",label,re.I)
    if not match:
        return None
    month=8 if match.group(1).lower().startswith("aug") else 7
    return (2026,month,int(match.group(2)))

def canonical_team(name):
    value=clean(name).lower()
    value=re.sub(r"[.'’]","",value)
    value=clean(value)
    if value in ALIASES:
        return ALIASES[value]
    for alias,code in sorted(ALIASES.items(),key=lambda item:-len(item[0])):
        if value==alias or value.endswith(" "+alias):
            return code
    raise ValueError(f"Unknown team: {name}")

def parse_get_line(text):
    match=re.match(r"(.+?)\s+get(?:s)?:\s*(.+)$",clean(text),re.I)
    if not match:
        raise ValueError(text)
    return Side(canonical_team(match.group(1)),clean(match.group(2)))

def parse_mlb(markup):
    soup=BeautifulSoup(markup,"html.parser")
    current_date=None
    pending=[]
    results=[]
    seen=set()
    for tag in soup.find_all(["h2","h3","h4","p","li"]):
        text=clean(tag.get_text(" ",strip=True))
        if parse_date(text):
            current_date=text
            pending=[]
            continue
        if not current_date or parse_date(current_date)<CUTOFF:
            continue
        if " get:" not in text.lower() and " gets:" not in text.lower():
            continue
        identity=(current_date,text)
        if identity in seen:
            continue
        seen.add(identity)
        try:
            pending.append(parse_get_line(text.lstrip("•- ")))
        except ValueError:
            continue
        if len(pending)==2:
            results.append(Trade(current_date,pending[0],pending[1],"MLB",("MLB.com",)))
            pending=[]
    if len(results)<10:
        raise RuntimeError(f"MLB parser found only {len(results)} trades from July 31 forward.")
    return results

def parse_cbs(markup):
    soup=BeautifulSoup(markup,"html.parser")
    current_date=None
    results=[]
    for tag in soup.find_all(["h2","h3","table"]):
        if tag.name in ("h2","h3"):
            heading=clean(tag.get_text(" ",strip=True))
            if parse_date(heading):
                current_date=heading
            continue
        if not current_date or parse_date(current_date)<CUTOFF:
            continue
        rows=[]
        for row in tag.find_all("tr"):
            cells=[clean(cell.get_text(" ",strip=True)) for cell in row.find_all(["th","td"])]
            if len(cells)>=2 and cells[0].lower() not in ("team",""):
                rows.append(cells[:2])
        if len(rows)>=2:
            try:
                first=Side(canonical_team(rows[0][0]),rows[0][1])
                second=Side(canonical_team(rows[1][0]),rows[1][1])
            except ValueError:
                continue
            results.append(Trade(current_date,first,second,"CBS",("CBS Sports",)))
    if len(results)<10:
        raise RuntimeError(f"CBS parser found only {len(results)} trades from July 31 forward.")
    return results

def normalized_players(value):
    value=value.lower()
    value=re.sub(r"\b(rhp|lhp|of|inf|if|c|ss|1b|2b|3b|ptbnl|cash considerations|cash)\b"," ",value)
    return clean(re.sub(r"[^a-z0-9áéíóúñüç -]"," ",value))

def pair_key(trade):
    teams=sorted((trade.a.team,trade.b.team))
    return (trade.date.lower(),teams[0],teams[1])

def similarity(first,second):
    a=normalized_players(first.a.acquired+" "+first.b.acquired)
    b=normalized_players(second.a.acquired+" "+second.b.acquired)
    return difflib.SequenceMatcher(None,a,b).ratio()

def merge_ledgers(mlb,cbs):
    used=set()
    merged=[]
    for mlb_trade in mlb:
        candidates=[
            (index,cbs_trade)
            for index,cbs_trade in enumerate(cbs)
            if index not in used and pair_key(cbs_trade)==pair_key(mlb_trade)
        ]
        if candidates:
            index,best=max(candidates,key=lambda item:similarity(mlb_trade,item[1]))
            if similarity(mlb_trade,best)>=0.35:
                used.add(index)
                merged.append(Trade(
                    mlb_trade.date,mlb_trade.a,mlb_trade.b,
                    "VERIFIED",("MLB.com","CBS Sports")
                ))
                continue
        merged.append(Trade(
            mlb_trade.date,mlb_trade.a,mlb_trade.b,
            "UNVERIFIED - MLB ONLY",("MLB.com",)
        ))
    for index,cbs_trade in enumerate(cbs):
        if index not in used:
            merged.append(Trade(
                cbs_trade.date,cbs_trade.a,cbs_trade.b,
                "UNVERIFIED - CBS ONLY",("CBS Sports",)
            ))

    overrides={}
    override_path=DATA/"reporters.json"
    if override_path.exists():
        overrides=json.loads(override_path.read_text(encoding="utf-8"))
    enriched=[]
    for trade in merged:
        key=f"{trade.date}|{trade.a.team}|{trade.b.team}|{trade.a.acquired}"
        enriched.append(Trade(
            trade.date,trade.a,trade.b,trade.status,trade.sources,
            overrides.get(key,"")
        ))
    return enriched

def data_uri(path):
    mime=mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    raw=base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{raw}"

def logo_uri(session,code):
    logo_dir=ASSETS/"team-logos"
    logo_dir.mkdir(exist_ok=True)
    svg=logo_dir/f"{code}.svg"
    if not svg.exists():
        response=session.get(
            f"https://www.mlbstatic.com/team-logos/{TEAM_IDS[code]}.svg",
            timeout=30,
        )
        response.raise_for_status()
        if "<svg" not in response.text[:500]:
            raise RuntimeError(f"Invalid logo response for {code}.")
        svg.write_text(response.text,encoding="utf-8")
    return data_uri(svg)

def source_buttons(sources):
    buttons=[]
    for source in sources:
        url=MLB_URL if source=="MLB.com" else CBS_URL
        buttons.append(
            f'<a class="source" href="{url}" target="_blank" rel="noopener">{source}</a>'
        )
    return "".join(buttons)

def render(trades,session):
    team_codes=sorted({code for trade in trades for code in (trade.a.team,trade.b.team)})
    logos={code:logo_uri(session,code) for code in team_codes}
    cards=[]
    for trade in trades:
        css_class="verified" if trade.status=="VERIFIED" else "unverified"
        buttons=source_buttons(trade.sources)
        reporter=(
            f'<div class="reporter">Reported by {html.escape(trade.reporter)}</div>'
            if trade.reporter else ""
        )
        cards.append(f'''<article class="trade-card {css_class}">
<div class="trade-date">{html.escape(trade.date.upper())}</div>
<div class="logo-pair"><img src="{logos[trade.a.team]}" alt="{trade.a.team} logo"><span>↔</span><img src="{logos[trade.b.team]}" alt="{trade.b.team} logo"></div>
<div class="trade-details"><p><strong>{DISPLAY[trade.a.team]} get:</strong> {html.escape(trade.a.acquired)}</p><p><strong>{DISPLAY[trade.b.team]} get:</strong> {html.escape(trade.b.acquired)}</p><div class="mobile-sources"><span class="status {css_class}">{html.escape(trade.status)}</span>{buttons}{reporter}</div></div>
<div class="desktop-sources"><span class="status {css_class}">{html.escape(trade.status)}</span>{buttons}{reporter}</div>
</article>''')

    pages=[]
    for start_index in range(0,len(cards),10):
        page_number=start_index//10+1
        start=start_index+1
        end=min(start_index+10,len(cards))
        pages.append(f'''<section class="page">
<div class="page-header"><strong>Page {page_number} - Trades {start}-{end}</strong><span>Newest first - vertical page scroll</span></div>
<div class="trade-head"><div>Date</div><div>Teams</div><div>Full return</div><div>Source / status</div></div>
{"".join(cards[start_index:start_index+10])}
<div class="page-footer">Showing {start}-{end} of {len(cards)} trades</div>
</section>''')

    verified=sum(trade.status=="VERIFIED" for trade in trades)
    unverified=len(trades)-verified
    first_unverified=next((trade for trade in trades if trade.status!="VERIFIED"),None)
    if first_unverified:
        callout=(
            f"<strong>Unverified:</strong> {DISPLAY[first_unverified.a.team]} get: "
            f"{html.escape(first_unverified.a.acquired)}; "
            f"{DISPLAY[first_unverified.b.team]} get: "
            f"{html.escape(first_unverified.b.acquired)}."
        )
    else:
        callout="No one-source trades."

    updated=datetime.now(ZoneInfo("America/Chicago")).strftime("%b. %-d - %-I:%M %p CT")
    output=TEMPLATE.read_text(encoding="utf-8")
    replacements={
        "__NL__":data_uri(ASSETS/"national_league.png"),
        "__AL__":data_uri(ASSETS/"american_league.png"),
        "__UPDATED__":updated,
        "__VERIFIED__":str(verified),
        "__UNVERIFIED__":str(unverified),
        "__PAGES__":"".join(pages),
        "__UNVERIFIED_TEXT__":callout,
        "__MLB_URL__":MLB_URL,
        "__CBS_URL__":CBS_URL,
    }
    for marker,value in replacements.items():
        output=output.replace(marker,value)
    return output

def main():
    session=make_session()
    mlb_response=session.get(MLB_URL,timeout=30)
    mlb_response.raise_for_status()
    cbs_response=session.get(CBS_URL,timeout=30)
    cbs_response.raise_for_status()

    merged=merge_ledgers(
        parse_mlb(mlb_response.text),
        parse_cbs(cbs_response.text),
    )
    canonical={"trades":[asdict(trade) for trade in merged]}
    snapshot_path=DATA/"snapshot.json"
    previous={}
    if snapshot_path.exists():
        previous=json.loads(snapshot_path.read_text(encoding="utf-8"))

    if previous.get("trades")==canonical["trades"]:
        print("Ledger unchanged; preserving the existing site and timestamp.")
        return

    canonical["updated_at_ct"]=datetime.now(ZoneInfo("America/Chicago")).isoformat()
    snapshot_path.write_text(
        json.dumps(canonical,ensure_ascii=False,indent=2),
        encoding="utf-8",
    )
    (SITE/"index.html").write_text(render(merged,session),encoding="utf-8")

    previous_entries={
        json.dumps(item,sort_keys=True,ensure_ascii=False)
        for item in previous.get("trades",[])
    }
    changed_entries=[
        item for item in canonical["trades"]
        if json.dumps(item,sort_keys=True,ensure_ascii=False) not in previous_entries
    ]
    lines=[
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
    (DATA/"change_summary.md").write_text(
        "\n".join(lines)+"\n",
        encoding="utf-8",
    )

if __name__=="__main__":
    main()
