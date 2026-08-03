<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>MLB Trade Deadline Tracker 2026</title>
<style>
:root{--navy:#07285b;--navy2:#0f3a77;--red:#cf2336;--ink:#172335;--muted:#66758b;--line:#d1d8e2;--bg:#eef2f6;--white:#fff;--green:#13783f;--green-bg:#e5f5ea;--amber:#8a5a08;--amber-bg:#f9efd3;--gold:#8b6500}
*{box-sizing:border-box}
html,body{margin:0;width:100%;max-width:100%;overflow-x:hidden;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;-webkit-text-size-adjust:100%}
.tracker{width:100%;max-width:1440px;margin:0 auto;background:var(--white)}
.header{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:22px;align-items:center;padding:22px 24px 18px;border-bottom:6px solid var(--red)}
.title-wrap{min-width:0}h1{margin:0;color:var(--navy);font-size:56px;line-height:.98;letter-spacing:-.04em;font-weight:900}
.header-right{display:flex;flex-direction:column;gap:14px}.logo-row{display:flex;align-items:center;justify-content:center;gap:18px}
.logo-box{width:128px;height:102px;display:flex;align-items:center;justify-content:center;border-bottom:8px solid var(--gold)}
.logo-box img{width:94px;height:94px;object-fit:contain}.logo-divider{width:2px;height:74px;background:#a9b4c2}
.meta-row{display:grid;grid-template-columns:1fr 1fr;gap:12px}.meta-card{min-width:0;min-height:86px;padding:12px 14px 13px;display:flex;flex-direction:column;justify-content:center;border:1px solid var(--line);border-radius:16px;background:var(--white)}
.meta-label{margin-bottom:6px;color:var(--red);font-size:11px;font-weight:900;letter-spacing:.11em;text-transform:uppercase}.meta-date,.meta-time{color:var(--navy);font-size:16px;font-weight:900;line-height:1.08}.meta-time{white-space:nowrap}
.content{padding:22px 24px 26px}.log-card{overflow:hidden;border:1px solid var(--line);border-radius:16px;background:var(--white)}
.log-header{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:14px 18px;background:var(--navy);color:var(--white)}
.log-header strong{font-size:22px;line-height:1}.log-header span{color:#dfe8f2;font-size:14px;white-space:nowrap}
.trade-head{display:grid;grid-template-columns:94px 222px minmax(0,1fr) 182px;background:var(--navy2);color:var(--white);font-size:12px;font-weight:900;text-transform:uppercase}
.trade-head div{padding:10px 12px;border-right:1px solid #6f87a6}.trade-card{display:grid;grid-template-columns:94px 222px minmax(0,1fr) 182px;grid-template-areas:"date logos details source";border-bottom:1px solid var(--line)}
.trade-card:nth-of-type(odd){background:#f9fbfd}.trade-card.unverified{background:var(--amber-bg)}.trade-card>div{min-width:0;padding:13px 12px;border-right:1px solid var(--line)}
.trade-date{grid-area:date;display:flex;align-items:center;justify-content:center;text-align:center;color:var(--red);font-size:15px;font-weight:900}.logo-pair{grid-area:logos;display:flex;align-items:center;justify-content:center;gap:14px}
.logo-pair img{width:74px;height:74px;object-fit:contain;flex:0 0 74px}.logo-pair img.winner{filter:drop-shadow(0 5px 0 #8b6500) drop-shadow(0 0 5px #f1d27a)}.logo-pair span{color:var(--red);font-size:28px;font-weight:900}
.trade-details{grid-area:details;display:flex;flex-direction:column;justify-content:center}.trade-details p{margin:0 0 8px;font-size:14px;line-height:1.34;overflow-wrap:anywhere}.trade-details p:last-of-type{margin-bottom:0}.trade-details strong{color:var(--navy)}
.desktop-sources{grid-area:source;display:flex;flex-direction:column;justify-content:center;align-items:stretch;text-align:center}.mobile-sources{display:none}.status{display:inline-block;align-self:center;margin:0 0 7px;padding:5px 9px;border-radius:999px;font-size:10px;font-weight:900;white-space:nowrap}
.status.verified{color:var(--green);background:var(--green-bg);border:1px solid #90c6a4}.status.unverified{color:var(--amber);background:#fff4d7;border:1px solid #dcb16b}.source{display:block;margin:3px 0;padding:7px 8px;color:var(--navy);background:#fff;border:1px solid var(--line);border-radius:8px;font-size:12px;font-weight:900;text-decoration:none}.reporter{margin-top:6px;color:var(--muted);font-size:11px}
.footer{display:flex;justify-content:flex-end;padding:12px 24px 14px;background:var(--navy);color:#fff;font-size:12px}
@media(max-width:900px){.tracker{max-width:none}.header{grid-template-columns:minmax(0,1fr) 198px;gap:14px;align-items:start;padding:16px 16px 14px}h1{font-size:34px;line-height:.96}.header-right{gap:10px}.logo-row{gap:10px}.logo-box{width:90px;height:72px;border-bottom:6px solid var(--gold)}.logo-box img{width:66px;height:66px}.logo-divider{height:56px}.meta-row{grid-template-columns:1fr 1fr;gap:8px}.meta-card{min-height:66px;padding:9px 8px 10px;border-radius:14px}.meta-label{margin-bottom:4px;font-size:8px}.meta-date,.meta-time{font-size:11px}.content{padding:14px 12px 16px}.log-header{padding:12px 14px}.log-header strong{font-size:19px}.log-header span{font-size:12px;text-align:right;white-space:normal}.trade-head{display:none}.trade-card{grid-template-columns:56px 110px minmax(0,1fr);grid-template-areas:"date logos details";min-height:148px}.trade-card>div{padding:10px 8px}.trade-date{writing-mode:vertical-rl;transform:rotate(180deg);letter-spacing:.03em;font-size:13px}.logo-pair{flex-direction:column;gap:2px}.logo-pair img{width:56px;height:56px;flex-basis:56px}.logo-pair span{font-size:16px;line-height:1}.trade-details p{margin-bottom:6px;font-size:13px;line-height:1.3}.desktop-sources{display:none}.mobile-sources{display:flex;flex-wrap:wrap;align-items:center;gap:5px;margin-top:8px}.mobile-sources .status{margin:0;align-self:auto}.mobile-sources .source{display:inline-block;margin:0;padding:5px 7px;font-size:11px}.mobile-sources .reporter{width:100%;margin-top:2px}.footer{padding:10px 12px 12px}}
@media(max-width:430px){.header{grid-template-columns:minmax(0,1fr) 186px;gap:10px;padding-left:12px;padding-right:12px}h1{font-size:31px}.logo-box{width:84px;height:68px}.logo-box img{width:62px;height:62px}.meta-card{padding-left:6px;padding-right:6px}.meta-date,.meta-time{font-size:10.5px}.trade-card{grid-template-columns:52px 101px minmax(0,1fr)}}
</style>
</head>
<body>
<div class="tracker">
<header class="header">
<div class="title-wrap"><h1>MLB Trade Deadline Tracker 2026</h1></div>
<div class="header-right">
<div class="logo-row"><div class="logo-box"><img src="__NL__" alt="National League logo"></div><div class="logo-divider"></div><div class="logo-box"><img src="__AL__" alt="American League logo"></div></div>
<div class="meta-row"><div class="meta-card"><div class="meta-label">Last checked</div><div class="meta-date">__UPDATED_DATE__</div><div class="meta-time">__UPDATED_TIME__</div></div><div class="meta-card"><div class="meta-label">Deadline</div><div class="meta-date">__DEADLINE_DATE__</div><div class="meta-time">__DEADLINE_TIME__</div></div></div>
</div>
</header>
<main class="content"><section class="log-card"><div class="log-header"><strong>Trade Log</strong><span>Newest first · vertical page scroll</span></div><div class="trade-head"><div>Date</div><div>Teams</div><div>Full return</div><div>Source / status</div></div>__ROWS__</section></main>
<footer class="footer">Updated __UPDATED_FULL__</footer>
</div>
</body>
</html>
