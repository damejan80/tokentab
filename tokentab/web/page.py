"""The dashboard as one self-contained HTML string: styles, markup and a little
vanilla JS that fetches /api/report and draws it. No build, no framework, no
network — it opens even with the network unplugged, which is the whole point of
a local tool.

Look: a paper invoice. Warm cream stock, ink-blue figures, one oxblood-red accent
used sparingly. The grand total sits in a bordered "amount due" block; every row
uses dot leaders instead of bars. It's a document, not a terminal.
"""

PAGE_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>tokentab</title>
<style>
  :root {
    --stock: #f6f2e9;
    --stock-line: #ece5d6;
    --ink: #1f2a44;
    --ink-soft: #5c6474;
    --ink-faint: #9a9384;
    --rule: #d9d0bd;
    --stamp: #9c2b28;
    --stamp-soft: #b8514d;
    --pos: #2f5d50;
    /* system stacks only — the tool stays fully offline, no font CDN */
    --serif: "Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
    --mono: ui-monospace, "SF Mono", "SFMono-Regular", Menlo, "DejaVu Sans Mono", Consolas, monospace;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    background: #e8e2d4;
    color: var(--ink);
    font-family: var(--mono);
    font-size: 13.5px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    padding: 40px 18px 70px;
  }

  .bill {
    max-width: 720px;
    margin: 0 auto;
    background: var(--stock);
    border: 1px solid var(--rule);
    /* faint horizontal ledger lines, like ruled accounting paper */
    background-image: repeating-linear-gradient(
      var(--stock) 0, var(--stock) 33px, var(--stock-line) 33px, var(--stock-line) 34px
    );
    box-shadow: 0 30px 60px -34px rgba(40,34,20,0.55);
    padding: 0;
  }
  .inner { padding: 40px 46px 44px; }

  /* ---- letterhead ---- */
  .head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 2px solid var(--ink);
    padding-bottom: 16px;
  }
  .head .mark {
    font-family: var(--serif);
    font-size: 27px;
    font-weight: 600;
    letter-spacing: -0.4px;
    color: var(--ink);
    line-height: 1;
  }
  .head .tag {
    font-size: 11px;
    color: var(--ink-soft);
    letter-spacing: 0.4px;
    margin-top: 7px;
  }
  .head .meta {
    text-align: right;
    font-size: 11px;
    color: var(--ink-soft);
    line-height: 1.7;
  }
  .head .meta b { color: var(--ink); font-weight: 500; }
  .head .no {
    font-family: var(--serif);
    font-size: 13px;
    color: var(--stamp);
    letter-spacing: 1px;
  }

  /* ---- period selector: looks like form checkboxes on a slip ---- */
  .periods {
    display: flex;
    gap: 0;
    margin: 22px 0 8px;
    border: 1px solid var(--rule);
    background: rgba(255,255,255,0.35);
    width: fit-content;
  }
  .periods button {
    font-family: var(--mono);
    font-size: 11.5px;
    letter-spacing: 0.5px;
    color: var(--ink-soft);
    background: transparent;
    border: 0;
    border-right: 1px solid var(--rule);
    padding: 7px 15px;
    cursor: pointer;
    transition: background .12s, color .12s;
  }
  .periods button:last-child { border-right: 0; }
  .periods button:hover { color: var(--ink); background: rgba(255,255,255,0.5); }
  .periods button[aria-current="true"] {
    color: var(--stock);
    background: var(--ink);
    font-weight: 500;
  }

  /* ---- amount-due block: the bottom line, but up top ---- */
  .due {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border: 1.5px solid var(--ink);
    padding: 18px 22px;
    margin: 16px 0 30px;
    background: rgba(255,255,255,0.4);
  }
  .due .lab {
    font-size: 11px;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--ink-soft);
  }
  .due .lab b { display: block; color: var(--ink); font-weight: 500; margin-top: 6px; font-size: 12.5px; letter-spacing: 0.3px; }
  .due .amt {
    font-family: var(--serif);
    font-size: 46px;
    font-weight: 600;
    color: var(--ink);
    letter-spacing: -1px;
    line-height: 0.9;
    font-variant-numeric: tabular-nums;
  }
  .due .amt .cur { color: var(--stamp); font-size: 26px; vertical-align: 6px; margin-right: 1px; }

  /* ---- sections ---- */
  section { margin: 26px 0; }
  h2 {
    font-family: var(--serif);
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.5px;
    color: var(--ink);
    margin: 0 0 12px;
    padding-bottom: 5px;
    border-bottom: 1px solid var(--rule);
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }
  h2 .hint { font-family: var(--mono); font-size: 10.5px; font-weight: 400; letter-spacing: 1px; color: var(--ink-faint); text-transform: uppercase; }

  /* dot-leader line item */
  .item { display: flex; align-items: baseline; padding: 4px 0; gap: 4px; }
  .item .n { color: var(--ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 60%; }
  .item .n em { font-style: normal; color: var(--ink-faint); font-size: 11px; margin-left: 6px; }
  .item .dots {
    flex: 1;
    border-bottom: 1px dotted var(--ink-faint);
    transform: translateY(-3px);
    min-width: 20px;
    opacity: 0.7;
  }
  .item .v { font-variant-numeric: tabular-nums; color: var(--ink); white-space: nowrap; }
  .item .v small { color: var(--ink-faint); margin-left: 8px; font-size: 11px; }

  /* per-day ledger table */
  .ledger { width: 100%; border-collapse: collapse; font-size: 12.5px; }
  .ledger td { padding: 4px 0; border-bottom: 1px solid var(--stock-line); }
  .ledger .d { color: var(--ink-soft); width: 96px; }
  .ledger .g { padding: 0 10px; }
  .ledger .g i { display: inline-block; height: 8px; background: var(--stamp-soft); vertical-align: middle; }
  .ledger .a { text-align: right; color: var(--ink); font-variant-numeric: tabular-nums; width: 74px; }

  /* ---- footer stamp ---- */
  .foot {
    margin-top: 34px;
    padding-top: 16px;
    border-top: 2px solid var(--ink);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .foot .note { font-size: 10.5px; color: var(--ink-soft); line-height: 1.6; max-width: 60%; }
  .stamp {
    border: 2px solid var(--stamp);
    color: var(--stamp);
    font-family: var(--serif);
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 6px 12px;
    transform: rotate(-5deg);
    opacity: 0.85;
    white-space: nowrap;
  }

  .empty { color: var(--ink-soft); text-align: center; padding: 34px 0; font-style: italic; }
  .loading { color: var(--ink-faint); text-align: center; padding: 60px 0; letter-spacing: 2px; }
  @media (max-width: 560px) {
    .inner { padding: 28px 22px; }
    .head { flex-direction: column; gap: 12px; }
    .head .meta { text-align: left; }
    .due { flex-direction: column; align-items: flex-start; gap: 12px; }
  }
</style>
</head>
<body>
  <div class="bill">
    <div class="inner">
      <div class="head">
        <div>
          <div class="mark">tokentab</div>
          <div class="tag">statement of AI coding usage</div>
        </div>
        <div class="meta">
          <div class="no" id="stmt-no">NO. —</div>
          <div>issued <b id="issued">—</b></div>
          <div>account <b>this machine</b></div>
        </div>
      </div>

      <div class="periods" id="periods">
        <button data-p="today">Today</button>
        <button data-p="week" aria-current="true">7 days</button>
        <button data-p="30days">30 days</button>
        <button data-p="month">Month</button>
        <button data-p="all">All</button>
      </div>

      <div id="body"><div class="loading">preparing statement…</div></div>

      <div class="foot">
        <div class="note">Read from local session logs. Nothing leaves this machine. Prices are best-effort — treat them as a guide, not a receipt.</div>
        <div class="stamp">local copy</div>
      </div>
    </div>
  </div>

<script>
const $ = (s, r=document) => r.querySelector(s);

const money = n => {
  if (n >= 1000) return Math.round(n).toLocaleString("en-US");
  if (n >= 1) return n.toFixed(2);
  if (n === 0) return "0.00";
  return n.toFixed(3);
};
const toks = n => {
  if (n >= 1e9) return (n/1e9).toFixed(2)+"B";
  if (n >= 1e6) return (n/1e6).toFixed(1)+"M";
  if (n >= 1e3) return (n/1e3).toFixed(1)+"K";
  return String(n);
};
const dollars = n => "$" + money(n);
const labels = { claude:"Claude Code", codex:"Codex", gemini:"Gemini CLI", cursor:"Cursor" };
const label = k => labels[k] || k;
const tokensOf = t => t.input + t.output + t.cacheRead + t.cacheWrite;

// a tidy statement number derived from the date, so it feels like a real doc
function stmtNo() {
  const d = new Date();
  return "NO. " + d.getFullYear() + "-" +
    String(d.getMonth()+1).padStart(2,"0") + String(d.getDate()).padStart(2,"0");
}
function today() {
  return new Date().toLocaleDateString("en-US", { year:"numeric", month:"short", day:"numeric" });
}

async function load(p) {
  for (const b of document.querySelectorAll("#periods button"))
    b.setAttribute("aria-current", b.dataset.p === p ? "true" : "false");
  $("#body").innerHTML = '<div class="loading">preparing statement…</div>';
  try {
    const r = await fetch("/api/report?period=" + p);
    draw(await r.json());
  } catch (e) {
    $("#body").innerHTML = '<div class="empty">Couldn\'t read the statement — is the server still running?</div>';
  }
}

function items(rows, nameFn, valFn) {
  if (!rows.length) return '<div class="empty">nothing recorded</div>';
  return rows.map(r =>
    '<div class="item"><span class="n">' + nameFn(r) + '</span>'
    + '<span class="dots"></span>'
    + '<span class="v">' + valFn(r) + '</span></div>'
  ).join("");
}

function draw(rep) {
  const t = rep.totals;
  if (!t.calls) {
    $("#body").innerHTML = '<div class="empty">No charges for this period.<br>Nothing ran, or no supported tool has logs yet.</div>';
    return;
  }
  const cacheHit = (t.cacheHitRate*100).toFixed(1) + "%";
  const totalTok = tokensOf(t.tokens);

  const due =
    '<div class="due">'
    + '<div class="lab">total spend<b>' + t.calls.toLocaleString() + ' calls · '
      + toks(totalTok) + ' tokens · ' + cacheHit + ' cached</b></div>'
    + '<div class="amt"><span class="cur">$</span>' + money(t.cost) + '</div>'
    + '</div>';

  const tool = '<section><h2>By tool <span class="hint">share</span></h2>'
    + items(rep.byTool,
        r => label(r.label),
        r => dollars(r.cost) + '<small>' + Math.round(r.cost/t.cost*100) + '%</small>')
    + '</section>';

  const model = '<section><h2>Models <span class="hint">tokens</span></h2>'
    + items(rep.byModel.slice(0,8),
        r => r.label,
        r => dollars(r.cost) + '<small>' + toks(r.tokens) + '</small>')
    + '</section>';

  const proj = rep.byProject.length > 1
    ? '<section><h2>Projects</h2>'
      + items(rep.byProject.slice(0,8), r => r.label, r => dollars(r.cost))
      + '</section>'
    : '';

  const act = '<section><h2>By activity <span class="hint">share</span></h2>'
    + items(rep.byActivity,
        r => r.label,
        r => dollars(r.cost) + '<small>' + Math.round(r.cost/t.cost*100) + '%</small>')
    + '</section>';

  let days = '';
  if (rep.byDay.length > 1) {
    const max = Math.max(...rep.byDay.map(d => d.cost), 0.0001);
    const rows = rep.byDay.slice(-14).map(d => {
      const w = Math.max(3, Math.round(d.cost/max*180));
      return '<tr><td class="d">' + d.date + '</td>'
        + '<td class="g"><i style="width:'+w+'px"></i></td>'
        + '<td class="a">' + dollars(d.cost) + '</td></tr>';
    }).join("");
    days = '<section><h2>Daily entries</h2><table class="ledger">' + rows + '</table></section>';
  }

  $("#body").innerHTML = due + tool + model + proj + act + days;
}

$("#stmt-no").textContent = stmtNo();
$("#issued").textContent = today();
$("#periods").addEventListener("click", e => {
  const b = e.target.closest("button");
  if (b) load(b.dataset.p);
});
load("week");
</script>
</body>
</html>"""


def render_page() -> str:
    return PAGE_HTML
