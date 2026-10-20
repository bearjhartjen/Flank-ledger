#!/usr/bin/env python3
"""
Build a self-contained desktop HTML viewer for 'The Flank.md' (Flamingo & Cactus ledger).

    python3 generate_viewer.py

Reads  ~/Desktop/The Flank.md
Writes ~/Desktop/Flank Ledger Viewer.html
"""

import base64
import io
import json
import re
from datetime import datetime
from pathlib import Path

SRC = Path("/home/bearjoshuahartjen/Desktop/The Flank.md")
OUT = Path("/home/bearjoshuahartjen/Desktop/Flank Ledger Viewer.html")
LOGO = Path("/home/bearjoshuahartjen/Documents/Lamoka1-project/Images/FlamingonCactus.png")


# --------------------------------------------------------------------------- logo
def logo_data_uri() -> str:
    """White-on-black logo -> transparent background with a black mark."""
    from PIL import Image

    im = Image.open(LOGO).convert("L")
    im = im.resize((320, 320), Image.LANCZOS)
    # white artwork -> opaque, black background -> transparent
    rgba = Image.merge(
        "RGBA",
        (
            Image.new("L", im.size, 26),   # ink colour
            Image.new("L", im.size, 26),
            Image.new("L", im.size, 26),
            im,                            # alpha from luminance
        ),
    )
    buf = io.BytesIO()
    rgba.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


# --------------------------------------------------------------------------- parse
def parse_ledger(text: str):
    blocks = re.split(r"^##\s+Transaction\s+(\d+)\s*$", text, flags=re.M)
    txs = []
    for i in range(1, len(blocks), 2):
        num = int(blocks[i])
        fields = {}
        for line in blocks[i + 1].splitlines():
            m = re.match(r"^-\s+\*\*(.+?):\*\*\s*(.*)$", line.strip())
            if m:
                fields[m.group(1).strip().lower()] = m.group(2).strip()
        txs.append((num, fields))
    return txs


def money(raw):
    """(value_or_None, display). Only '$'-prefixed or bare-numeric values are money."""
    if raw is None:
        return None, ""
    s = raw.strip()
    if s == "$":
        return None, ""
    m = re.fullmatch(r"\$?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", s)
    if m:
        return float(m.group(1).replace(",", "")), s
    return None, s


def parse_date(raw):
    """(iso_or_None, display)."""
    if raw is None:
        return None, ""
    s = raw.strip()
    if not s:
        return None, ""
    m = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", s)
    if m:
        mo, da, yr = (int(x) for x in m.groups())
        try:
            dt = datetime(yr, mo, da)
        except ValueError:
            return None, s
        return dt.strftime("%Y-%m-%d"), dt.strftime("%b %d, %Y")
    if s.lower() == "unknown":
        return None, "Unknown"
    return None, s


records = []
for num, f in parse_ledger(SRC.read_text(encoding="utf-8")):
    w_val, w_txt = money(f.get("withdraw of"))
    d_val, d_txt = money(f.get("deposit of"))
    b_val, b_txt = money(f.get("new balance"))
    iso, disp = parse_date(f.get("transaction was made on"))
    notes = f.get("notes", "").replace("\\$", "$")
    empty = w_val is None and d_val is None and b_val is None and not notes
    records.append(
        {
            "n": num,
            "withdraw": w_val,
            "withdrawText": w_txt,
            "deposit": d_val,
            "depositText": d_txt,
            "balance": b_val,
            "balanceText": b_txt,
            "silver": f.get("silver holdings", ""),
            "notes": notes,
            "date": iso,
            "dateText": disp,
            "empty": empty,
        }
    )

filled = [r for r in records if not r["empty"]]
print(f"parsed {len(records)} blocks, {len(filled)} filled, {len(records)-len(filled)} blank")
print("last balance:", filled[-1]["balance"], "| last silver:", filled[-1]["silver"])

DATA = json.dumps(filled, separators=(",", ":"))
LOGO_URI = logo_data_uri()
print(f"logo embedded ({len(LOGO_URI)//1024} KiB data URI)")


# --------------------------------------------------------------------------- template
HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>The Flank Ledger &mdash; Flamingo &amp; Cactus</title>
<style>
  :root{
    --paper:#ffffff;
    --paper2:#fbfaf7;
    --ink:#141414;
    --ink2:#3d3d3d;
    --muted:#6b6b6b;
    --faint:#8c8c8c;
    --rule:#c9c9c9;
    --rule2:#e3e1da;
    --link:#0b2a8c;
    --up:#1c6b3a;
    --upfill:#ffffff;
    --down:#9c1f16;
    --gold:#8a6a12;
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0}
  body{
    background:var(--paper);
    color:var(--ink);
    font:15px/1.55 Georgia,"Times New Roman",Times,serif;
    min-width:1120px;               /* desktop only */
    -webkit-font-smoothing:antialiased;
  }
  .page{max-width:1080px;margin:0 auto;padding:26px 28px 64px}

  /* ---------- masthead ---------- */
  .masthead{text-align:center;padding:6px 0 4px}
  .masthead img{display:block;margin:0 auto;width:96px;height:96px;object-fit:contain}
  h1{
    font-size:34px;font-weight:400;letter-spacing:2.5px;text-transform:uppercase;
    margin:14px 0 2px;
  }
  .tagline{color:var(--muted);font-size:14px;font-style:italic;margin:0 0 18px}
  .hr{height:2px;background:var(--ink);margin:0}
  .hr.thin{height:1px;background:var(--rule)}

  .headline{text-align:center;padding:24px 0 6px}
  .headline .item{margin:0 auto 26px}
  .headline .k{font-size:11px;letter-spacing:2.4px;text-transform:uppercase;color:var(--muted);font-family:"Helvetica Neue",Arial,sans-serif}
  .headline .v{font-size:40px;font-variant-numeric:tabular-nums;line-height:1.15;margin-top:5px}
  .headline .v.gold{color:var(--gold)}
  .headline .n{font-size:12.5px;color:var(--faint);font-family:"Helvetica Neue",Arial,sans-serif}

  .stats{
    text-align:center;color:var(--muted);font-size:13.5px;padding:0 0 20px;
    font-family:"Helvetica Neue",Arial,sans-serif;
  }
  .stats b{color:var(--ink2);font-weight:600}

  /* ---------- chart ---------- */
  .chartwrap{position:relative;margin:6px 0 4px}
  svg.chart{display:block;width:100%}
  .candle-up{fill:var(--upfill);stroke:var(--up);stroke-width:1.4}
  .candle-dn{fill:var(--down);stroke:var(--down);stroke-width:1.4}
  .wick{stroke:#55585c;stroke-width:1}
  .gl{stroke:var(--rule2);stroke-width:1}
  .avgline{stroke:#1c4fd8;stroke-width:1.6;stroke-dasharray:7 5}
  .mavg{fill:none;stroke:#1c4fd8;stroke-width:2.2;stroke-linejoin:round;stroke-linecap:round}
  .mavgdot{fill:#1c4fd8}
  .avglbl{font:11px "Helvetica Neue",Arial,sans-serif;fill:#1c4fd8;font-weight:600}
  .axlbl{font:11px "Helvetica Neue",Arial,sans-serif;fill:var(--muted)}
  .axlbl.b{font-weight:600;fill:var(--ink)}
  .tooltip{
    position:absolute;pointer-events:none;background:#fff;border:1px solid var(--ink);
    padding:8px 11px;font:12.5px/1.5 "Helvetica Neue",Arial,sans-serif;color:var(--ink);
    box-shadow:2px 2px 0 rgba(0,0,0,.14);min-width:168px;opacity:0;transition:opacity .08s;
  }
  .tooltip .tt-t{font-weight:700;letter-spacing:.4px;text-transform:uppercase;font-size:11px;color:var(--muted);margin-bottom:4px}
  .tooltip .tt-r{display:flex;justify-content:space-between;gap:18px}
  .tooltip .tt-r span:last-child{font-variant-numeric:tabular-nums}
  .caption{font:12.5px "Helvetica Neue",Arial,sans-serif;color:var(--faint);text-align:center;margin:6px 0 26px}
  .note{
    font:12.5px/1.5 "Helvetica Neue",Arial,sans-serif;color:var(--muted);
    text-align:center;margin:2px auto 14px;max-width:760px;
    border-left:2px solid var(--rule);padding-left:12px;
  }
  .note b{color:var(--ink2)}
  .legend{
    display:flex;gap:22px;justify-content:center;
    font:12px "Helvetica Neue",Arial,sans-serif;color:var(--muted);margin:0 0 20px;
  }
  .legend .sw{
    display:inline-block;width:11px;height:11px;border-radius:2px;
    margin-right:6px;vertical-align:-1px;
  }

  /* ---------- toolbar ---------- */
  .toolbar{display:flex;gap:10px;align-items:center;margin:0 0 12px;flex-wrap:wrap}
  input[type=search],select{
    font:14px Georgia,serif;color:var(--ink);background:#fff;
    border:1px solid var(--rule);border-radius:2px;padding:7px 10px;
  }
  input[type=search]{min-width:300px}
  input[type=search]:focus,select:focus{outline:2px solid var(--ink);outline-offset:-1px}
  .btn{
    font:13px "Helvetica Neue",Arial,sans-serif;letter-spacing:.6px;text-transform:uppercase;
    background:#fff;color:var(--ink);border:1px solid var(--ink);border-radius:2px;
    padding:7px 14px;cursor:pointer;
  }
  .btn:hover{background:var(--ink);color:#fff}
  .count{margin-left:auto;font:13px "Helvetica Neue",Arial,sans-serif;color:var(--muted)}

  /* ---------- table ---------- */
  table{width:100%;border-collapse:collapse;font-size:14px}
  thead th{
    font:11.5px "Helvetica Neue",Arial,sans-serif;letter-spacing:1.3px;text-transform:uppercase;
    color:var(--ink);text-align:left;padding:8px 10px;border-bottom:2px solid var(--ink);
    white-space:nowrap;
  }
  thead th.r{text-align:right}
  tbody td{padding:8px 10px;border-bottom:1px solid var(--rule2);vertical-align:top}
  tbody tr:hover{background:var(--paper2)}
  td.r{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
  td.n{color:var(--faint);text-align:right;width:44px;font-variant-numeric:tabular-nums}
  td.date{white-space:nowrap;color:var(--muted)}
  td.silver{white-space:nowrap;color:var(--gold)}
  td.notes{color:var(--ink2);font-size:13.5px;line-height:1.45}
  .with{color:var(--down)}
  .dep{color:var(--up)}
  .bal{font-weight:600}
  .empty-msg{color:var(--muted);text-align:center;padding:26px;font-style:italic}

  footer{
    margin-top:30px;padding-top:14px;border-top:1px solid var(--rule);
    font:12.5px "Helvetica Neue",Arial,sans-serif;color:var(--faint);text-align:center;
  }
  footer a{color:var(--link)}

  @media print{
    body{background:#fff;min-width:0;font-size:11pt}
    .page{max-width:none;padding:0}
    .toolbar,.chartwrap,.caption,.btn{display:none}
    thead th{position:static}
    tbody tr{break-inside:avoid}
  }
</style>
</head>
<body>
<div class="page">

  <div class="masthead">
    <img src="__LOGO__" alt="Flamingo and Cactus">
    <h1>The Flank Ledger</h1>
    <p class="tagline">Flamingo &amp; Cactus Group</p>
  </div>
  <div class="hr"></div>

  <div class="headline">
    <div class="item">
      <div class="k">Current Balance</div>
      <div class="v" id="h-balance">&mdash;</div>
      <div class="n" id="h-balance-note"></div>
    </div>
    <div class="item last">
      <div class="k">Silver Holdings</div>
      <div class="v gold" id="h-silver">&mdash;</div>
      <div class="n">physical reserve</div>
    </div>
  </div>

  <div class="stats" id="stats"></div>
  <div class="hr thin"></div>

  <div class="chartwrap">
    <svg class="chart" id="chart"></svg>
    <div class="tooltip" id="tip"></div>
  </div>
  <p class="note"><b>Note:</b> this graph tracks <b>US dollar holdings</b> only. The silver holdings
  (<span id="note-silver">200g, 2.6oz</span>) are physical assets held separately &mdash; they are not
  valued in dollars, and are <b>not</b> included in the plotted line, the moving average, or the totals above.</p>
  <p class="caption">
    One candle per transaction &mdash; hollow for a transaction that left the balance higher, solid for one that left it lower.
    Hover a candle for detail.
  </p>
  <div class="legend">
    <span><span class="sw" style="background:#ffffff;border:1.4px solid var(--up)"></span>Balance rose</span>
    <span><span class="sw" style="background:var(--down)"></span>Balance fell</span>
    <span><span class="sw" style="height:0;border-top:2px solid #1c4fd8;border-radius:0;width:18px"></span>Moving average (&nbsp;9&nbsp;transactions)</span>
  </div>
  <div class="hr thin"></div>

  <div style="height:22px"></div>

  <div class="toolbar">
    <input type="search" id="q" placeholder="Search notes, dates, amounts&hellip;">
    <select id="filter">
      <option value="all">All transactions</option>
      <option value="in">Deposits only</option>
      <option value="out">Withdrawals only</option>
      <option value="2026">Year 2026</option>
      <option value="2025">Year 2025</option>
    </select>
    <button class="btn" id="print">Print</button>
    <span class="count" id="count"></span>
  </div>

  <table>
    <thead>
      <tr>
        <th class="n">#</th>
        <th>Date</th>
        <th class="r">Withdraw</th>
        <th class="r">Deposit</th>
        <th class="r">Balance</th>
        <th>Silver</th>
        <th>Notes</th>
      </tr>
    </thead>
    <tbody id="rows"></tbody>
  </table>

  <footer>
    Generated from <code>The Flank.md</code> &mdash; a read-only viewer.<br>
    Edit the Markdown and re-run <code>generate_viewer.py</code> to refresh.
  </footer>
</div>

<script>
const TX = __DATA__;

const num = v => typeof v === "number" ? v : null;
const money = n => n === null || n === undefined
  ? "&mdash;"
  : "$" + n.toLocaleString(undefined,{minimumFractionDigits:2, maximumFractionDigits:2});
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

/* ------------------------------------------------------------------ summary */
const totals = TX.reduce((a,t)=>{
  a.deposits   += num(t.deposit)  || 0;
  a.withdrawals+= num(t.withdraw) || 0;
  if (t.balance !== null) a.lastBalance = t.balance;
  if (t.silver) a.silver = t.silver;
  a.count++;
  return a;
},{deposits:0, withdrawals:0, lastBalance:null, silver:"", count:0});

const dated = TX.filter(t => t.date);
const lastTx = TX[TX.length-1];

document.getElementById("h-balance").textContent = money(totals.lastBalance);
document.getElementById("h-balance-note").textContent =
  "as of " + (lastTx.dateText || "the last entry");
document.getElementById("h-silver").textContent = totals.silver || "&mdash;";
document.getElementById("note-silver").textContent = totals.silver || "none on record";

document.getElementById("stats").innerHTML =
  `<b>${totals.count}</b> transactions &nbsp;&middot;&nbsp; ` +
  (dated.length ? dated[0].dateText + " &ndash; " + dated[dated.length-1].dateText : "undated") +
  ` &nbsp;&middot;&nbsp; deposits <b>${money(totals.deposits)}</b>` +
  ` &nbsp;&middot;&nbsp; withdrawals <b>${money(totals.withdrawals)}</b>`;

/* ------------------------------------------------------------------ candles */
function buildCandles(){
  /* One candle per transaction.
     open  = the balance carried in from the previous transaction
     close = the new balance after this one
     high  = max(open, close), low = min(open, close)
     The ledger itself has two places where the running balance jumps by more
     than the recorded deposit/withdrawal; those candles get flagged. */
  const out = [];
  let prevClose = null;
  for (const t of TX){
    if (t.balance === null) continue;
    const dep = num(t.deposit)  || 0;
    const wd  = num(t.withdraw) || 0;
    const implied = +(t.balance - (dep - wd)).toFixed(2);
    const open  = prevClose === null ? implied : prevClose;
    const close = t.balance;
    const gap   = +(close - open - (dep - wd)).toFixed(2);
    out.push({
      n: t.n, label: "#" + t.n, date: t.dateText || "Unknown",
      open, close,
      high: Math.max(open, close), low: Math.min(open, close),
      deposits: dep, withdrawals: wd,
      gap: Math.abs(gap) > 0.005 ? gap : 0
    });
    prevClose = close;
  }
  return out;
}

const CANDLES = buildCandles();

/* window (in transactions) for the blue moving-average line */
const MA_WINDOW = 9;

/* moving average of the running balance, per transaction */
const MA = CANDLES.map((c,i)=>{
  const from = Math.max(0, i-MA_WINDOW+1);
  let s = 0, n = 0;
  for (let k=from;k<=i;k++){ s += CANDLES[k].close; n++; }
  return s/n;
});

(function(){
  const svg = document.getElementById("chart");
  const tip = document.getElementById("tip");
  if (!CANDLES.length){ svg.innerHTML = '<text x="10" y="30" class="axlbl">No data</text>'; return; }

  const H = 330, PL = 74, PR = 18, PT = 14, PB = 34;
  let lo = Infinity, hi = -Infinity;
  CANDLES.forEach(c=>{ lo = Math.min(lo,c.low); hi = Math.max(hi,c.high); });
  const pad = (hi-lo)*0.08 || 10;
  lo = Math.max(0, lo-pad); hi = hi+pad;

  function draw(){
    const W = Math.max(720, svg.parentElement.clientWidth);
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("width", W);
    svg.setAttribute("height", H);
    svg.style.height = H+"px";

    const plotW = W - PL - PR;
    const step  = plotW / CANDLES.length;
    const bw    = Math.max(3, Math.min(22, step*0.6));
    const cx    = i => PL + step*i + step/2;
    const y     = v => PT + (1-(v-lo)/(hi-lo))*(H-PT-PB);

    let grid = "", labs = "";
    for (let i=0;i<=4;i++){
      const v = lo + (hi-lo)*i/4, yy = y(v);
      grid += `<line class="gl" x1="${PL}" y1="${yy.toFixed(1)}" x2="${W-PR}" y2="${yy.toFixed(1)}"/>`;
      labs += `<text class="axlbl" x="${PL-9}" y="${(yy+4).toFixed(1)}" text-anchor="end">${"$"+Math.round(v).toLocaleString()}</text>`;
    }

    let xlabels = "", body = "";
    CANDLES.forEach((c,i)=>{
      const up = c.close >= c.open;
      const x  = cx(i);
      const yt = y(Math.max(c.open,c.close)), yb = y(Math.min(c.open,c.close));
      const h  = Math.max(1.5, yb-yt);
      body += `<line class="wick" x1="${x.toFixed(1)}" y1="${y(c.high).toFixed(1)}" x2="${x.toFixed(1)}" y2="${y(c.low).toFixed(1)}"/>`;
      body += `<rect class="${up?"candle-up":"candle-dn"}" x="${(x-bw/2).toFixed(1)}" y="${yt.toFixed(1)}" width="${bw.toFixed(1)}" height="${h.toFixed(1)}"/>`;
      body += `<rect class="hit" data-i="${i}" x="${(x-step/2).toFixed(1)}" y="${PT}" width="${step.toFixed(1)}" height="${H-PT-PB}" fill="transparent"/>`;
    });

    /* label every Nth candle with its transaction number */
    const every = Math.max(1, Math.ceil(CANDLES.length/14));
    CANDLES.forEach((c,i)=>{
      if (i % every === 0 || i === CANDLES.length-1)
        xlabels += `<text class="axlbl" x="${cx(i).toFixed(1)}" y="${H-10}" text-anchor="middle">${c.label}</text>`;
    });

    /* blue moving-average line following the value of the holdings */
    const maPath = MA.map((v,i)=>({ i, x: cx(i), v }));
    const maD = maPath.map((p,i)=>(i?"L":"M")+p.x.toFixed(1)+" "+y(p.v).toFixed(1)).join(" ");
    const lastMa = maPath[maPath.length-1];
    const maLine =
      `<path class="mavg" d="${maD}"/>` +
      `<circle class="mavgdot" cx="${lastMa.x.toFixed(1)}" cy="${y(lastMa.v).toFixed(1)}" r="3"/>` +
      `<text class="avglbl" x="${lastMa.x.toFixed(1)}" y="${(y(lastMa.v)-9).toFixed(1)}" text-anchor="end">Moving avg ${money(lastMa.v)}</text>`;

    svg.innerHTML = grid + labs + body + maLine + xlabels;

    /* hover tooltips */
    const hits = svg.querySelectorAll(".hit");
    hits.forEach(el=>{
      el.addEventListener("mouseenter", ()=>{
        const c = CANDLES[+el.dataset.i];
        const up = c.close >= c.open;
        tip.innerHTML =
          `<div class="tt-t">Transaction ${c.n} &mdash; ${c.date}</div>` +
          `<div class="tt-r"><span>Opened at</span><span>${money(c.open)}</span></div>` +
          `<div class="tt-r"><span>Closed at</span><span>${money(c.close)}</span></div>` +
          `<div class="tt-r"><span>Change</span><span style="color:${up?"var(--up)":"var(--down)"}">${(c.close-c.open>=0?"+":"")+money(c.close-c.open)}</span></div>` +
          `<div class="tt-r"><span>Moving avg</span><span style="color:#1c4fd8">${money(MA[+el.dataset.i])}</span></div>` +
          (c.deposits  ? `<div class="tt-r"><span>Deposit</span><span>${money(c.deposits)}</span></div>`  : "") +
          (c.withdrawals?`<div class="tt-r"><span>Withdrawal</span><span>${money(c.withdrawals)}</span></div>`:"") +
          (c.gap ? `<div class="tt-r"><span>Unrecorded</span><span>${money(c.gap)}</span></div>` : "");
        const svgRect = svg.getBoundingClientRect();
        const wrapRect = svg.parentElement.getBoundingClientRect();
        const px = svgRect.left - wrapRect.left + cx(+el.dataset.i);
        const py = svgRect.top  - wrapRect.top  + y(c.high);
        tip.style.opacity = "1";
        const tw = tip.offsetWidth;
        tip.style.left = Math.max(0, Math.min(wrapRect.width - tw, px - tw/2)) + "px";
        tip.style.top  = Math.max(0, py - tip.offsetHeight - 10) + "px";
      });
    });
    svg.addEventListener("mouseleave", ()=>{ tip.style.opacity = "0"; });
  }

  draw();
  let t;
  window.addEventListener("resize", ()=>{ clearTimeout(t); t = setTimeout(draw,120); });
})();

/* ------------------------------------------------------------------ table */
const q = document.getElementById("q");
const filter = document.getElementById("filter");
const rows = document.getElementById("rows");
const count = document.getElementById("count");

function visible(){
  const term = q.value.trim().toLowerCase();
  const f = filter.value;
  return TX.filter(t=>{
    if (f==="in"  && num(t.deposit)  === null) return false;
    if (f==="out" && num(t.withdraw) === null) return false;
    if ((f==="2025" || f==="2026") && !(t.date && t.date.startsWith(f))) return false;
    if (term){
      const hay = [t.n,t.dateText,t.notes,t.silver,t.withdrawText,t.depositText,t.balanceText]
                  .join(" ").toLowerCase();
      if (!hay.includes(term)) return false;
    }
    return true;
  }).slice().reverse();          /* newest first */
}

function render(){
  const v = visible();
  count.textContent = v.length + " shown of " + TX.length;
  if (!v.length){
    rows.innerHTML = '<tr><td colspan="7" class="empty-msg">No transactions match.</td></tr>';
    return;
  }
  rows.innerHTML = v.map(t=>{
    const w = num(t.withdraw), d = num(t.deposit);
    const wCell = w === null
      ? (t.withdrawText ? '<span class="with">' + esc(t.withdrawText) + "</span>" : "&mdash;")
      : '<span class="with">' + money(w) + "</span>";
    const dCell = d === null
      ? (t.depositText ? '<span style="color:var(--gold)">' + esc(t.depositText) + "</span>" : "&mdash;")
      : '<span class="dep">' + money(d) + "</span>";
    return "<tr>"
      + '<td class="n">' + t.n + "</td>"
      + '<td class="date">' + esc(t.dateText || "—") + "</td>"
      + '<td class="r">' + wCell + "</td>"
      + '<td class="r">' + dCell + "</td>"
      + '<td class="r bal">' + money(t.balance) + "</td>"
      + '<td class="silver">' + esc(t.silver || "—") + "</td>"
      + '<td class="notes">' + esc(t.notes || "") + "</td>"
      + "</tr>";
  }).join("");
}

q.addEventListener("input", render);
filter.addEventListener("change", render);
document.getElementById("print").addEventListener("click", ()=>window.print());
render();
</script>
</body>
</html>
'''

HTML = HTML.replace("__DATA__", DATA).replace("__LOGO__", LOGO_URI)
OUT.write_text(HTML, encoding="utf-8")
print("wrote", OUT, f"{OUT.stat().st_size//1024} KiB")
