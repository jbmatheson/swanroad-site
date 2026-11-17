#!/usr/bin/env python3
"""Writes p/<id>/index.html for every puzzle in the app's book, and daily/index.html: the pages a shared link lands on
for someone without the app. usage: python3 tools/puzzle_pages.py <path to the app's puzzles.json>

The daily page plays today's puzzle in the browser, and only today's. daily/puzzle.js holds the rules and picks the
day's puzzle the way the app does, from the book this script writes into the page. So when the app's book changes,
run this again, then `python3 tools/check_daily.py <path to swanroad-sim>` to prove the page still plays every puzzle
the way the simulator does, and `python3 tools/sitemap.py`. The numbered pages stay pictures: the archive is the app's."""
import json, pathlib, sys
import campaign, footer

ROOT = pathlib.Path(__file__).resolve().parent.parent
N = 7
GLYPH = {"1": "⚪", "2": "🔶", "3": "🔷"}

STORE = """<a class="btn" href="@HREF@"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M16.4 12.6c0-2.5 2-3.6 2.1-3.7-1.2-1.7-3-1.9-3.6-2-1.5-.2-3 .9-3.8.9-.8 0-2-.9-3.2-.9-1.7 0-3.2 1-4.1 2.5-1.8 3.1-.5 7.6 1.3 10.1.9 1.2 1.9 2.6 3.2 2.5 1.3-.1 1.8-.8 3.3-.8s2 .8 3.3.8c1.4 0 2.2-1.2 3.1-2.5 1-1.4 1.4-2.8 1.4-2.9-.1 0-2.9-1.1-3-4zM13.9 5.3c.7-.8 1.2-2 1-3.1-1 0-2.2.7-2.9 1.5-.6.7-1.2 1.9-1 3 1.1.1 2.2-.6 2.9-1.4z"/></svg>Get it on the App Store</a>"""

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="https://swanroad.app/{path}">
<meta property="og:type" content="website">
<meta property="og:title" content="{page_title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="https://swanroad.app/assets/{image}">
<meta property="og:url" content="https://swanroad.app/{path}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0b1a2b">
<meta name="apple-itunes-app" content="{banner}">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/icon-32.png">
<link rel="apple-touch-icon" href="/assets/icon-180.png">
<link rel="preload" href="/assets/fonts/fraunces-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts/fraunces.css">
<style>
  :root {{ --bg: #0b1a2b; --ink: #eef3f8; --muted: #a7b6c6; --accent: #7fd4ea; --sand: #e4d6b2; --line: rgba(255,255,255,.08);
          --serif: "Fraunces", "Iowan Old Style", "Palatino", Georgia, serif; --sans: -apple-system, "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink); font: 17px/1.6 var(--sans); -webkit-font-smoothing: antialiased; }}
  header.top {{ position: sticky; top: 0; backdrop-filter: blur(14px); background: rgba(11,26,43,.72); border-bottom: 1px solid var(--line); }}
  header.top .wrap {{ max-width: 1080px; margin: 0 auto; padding: 0 16px; display: flex; align-items: center; justify-content: space-between; height: 60px; }}
  .brand {{ display: flex; align-items: center; gap: 10px; color: var(--ink); text-decoration: none; font-family: var(--serif); font-size: 20px; font-weight: 600; }}
  .brand img {{ width: 32px; height: 32px; border-radius: 8px; }}
  nav a {{ color: var(--muted); text-decoration: none; margin-left: 20px; font-size: 15px; }}
  nav a:hover, nav a[aria-current] {{ color: var(--ink); }}
  @media (max-width: 640px) {{ nav a:not(:last-child):not(.cta) {{ display: none; }} }}
  @media (max-width: 380px) {{ nav a:not(.cta) {{ display: none; }} }}
  main {{ max-width: 680px; margin: 0 auto; padding: 48px 16px 72px; text-align: center; }}
  h1 {{ font-family: var(--serif); font-weight: 600; font-size: clamp(32px, 5vw, 44px); line-height: 1.1; margin: 0 0 6px; }}
  p {{ margin: 0 0 14px; }}
  .muted {{ color: var(--muted); }}
  a {{ color: var(--accent); }}
  .board {{ font-size: clamp(22px, 6vw, 34px); line-height: 1.15; letter-spacing: .02em; margin: 28px auto; white-space: pre; font-family: var(--sans); }}
  .btn {{ display: inline-flex; align-items: center; gap: 10px; margin: 18px 0 8px; padding: 14px 22px; border-radius: 14px; background: var(--accent); color: #0b1a2b; font-weight: 600; text-decoration: none; }}
  .btn svg {{ width: 22px; height: 22px; }}
{footer_css}
{style}</style>
{head}</head>
<body>
<header class="top"><div class="wrap"><a class="brand" href="/"><img src="/assets/icon-64.png" alt="" width="32" height="32">Swan Road</a><nav><a class="cta" href="/daily/"{current}>Daily puzzle</a><a href="/#how">How it plays</a><a href="/support/">Support</a><a href="/privacy/">Privacy</a></nav></div></header>
<main>
{main}</main>
{footer}
</body>
</html>
"""

# A numbered puzzle: the position as a picture, and the way to the app.
PUZZLE_MAIN = """  <h1>{title}</h1>
  <p class="muted">{subtitle}</p>
{board}
  <p>{brief}</p>
  {store}
  <p class="muted">With the app installed, this link opens the puzzle there.</p>
  <p class="muted">No iPhone to hand? <a href="/daily/">Play today’s puzzle in your browser</a>.</p>
"""

# Today's puzzle, playable. Everything a search engine or a browser without scripts reads is written here; puzzle.js
# fills in the board and takes the fallback paragraph away.
DAILY_MAIN = """  <h1>Today’s Swan Road puzzle</h1>
  <p class="muted" id="sub">A free daily strategy puzzle, the same for everyone</p>
  <div id="game" hidden>
    <div class="bar" id="bar0"></div>
    <div class="grid" id="board" role="group" aria-label="The board: seven rows of seven squares. Light’s shore is the top row, Dark’s the bottom."></div>
    <div class="bar" id="bar1"></div>
    <p class="status" id="status" role="status"></p>
    <p class="sr" id="log" aria-live="polite"></p>
    <div class="controls" id="controls">
      <button type="button" class="ctl" id="reset">Reset</button>
      <button type="button" class="ctl" id="lift">Lift</button>
      <button type="button" class="ctl" id="cancel">Cancel</button>
      <button type="button" class="ctl go" id="confirm">Confirm</button>
    </div>
    <p class="muted small" id="stuck" hidden>Stuck? In the app this puzzle comes with a hint.</p>
    <div class="after" id="after" hidden>
      <p id="after-text">That was one position. In the app the other side fights back: four computer opponents, a friend across the table or online, and a daily game with a leaderboard. This puzzle is there every day too, with a hint when you want one and a streak to keep.</p>
      <button type="button" class="ctl" id="share">Share your result</button>
    </div>
  </div>
  <p id="fallback">Swan Road sets one puzzle a day, the same for everyone: force a pearl onto your shore in one to four moves, whatever the other side does. With scripts on, it plays right here.</p>
  @STORE@
  <p class="muted small">Free to download, no ads, no account. If you have the app, this link opens the puzzle there.</p>

  <section>
    <h2>How the puzzle works</h2>
    <ol class="rules">
      <li><strong>Your move.</strong> Place an anchor from your hand on any empty square, step one of your anchors to a square next to it, or lift one back into your hand.</li>
      <li><strong>Anchors pull.</strong> Every anchor pulls the pearls in its row and column: by 3 from the next square, 2 from two squares away, 1 from three. A pearl in between blocks the pull, and both sides’ anchors pull alike.</li>
      <li><strong>Pearls drift.</strong> After each move every pearl slides one square the way it is pulled hardest. Opposite pulls subtract, and when up-and-down equals left-and-right the pearl stays where it is.</li>
      <li><strong>Shores collect.</strong> A pearl that reaches a shore row is collected: Light’s shore is the top row, Dark’s the bottom. A pearl that slides onto an anchor sends that anchor back to its owner’s hand.</li>
    </ol>
    <p>The puzzle gives you one to four moves to force a pearl onto your shore, whatever the other side answers. Each puzzle has exactly one first move that works.</p>
    <p>The whole game runs on the same rules. <a href="/devlog/why-the-pearls-drift/">Why the pearls drift</a> sets them out, with the reasons for each.</p>
  </section>

  <section>
    <h2>Questions</h2>
    <h3>Is the daily puzzle free?</h3>
    <p>Yes. It plays in your browser with no account and no ads. The game itself is free on the App Store for iPhone and iPad; one optional purchase, Swan Road Complete, adds the 9×9 board, the full puzzle archive and more.</p>
    <h3>When does the puzzle change?</h3>
    <p>At midnight where you are. Everyone gets the same puzzle on the same day, here and in the app.</p>
    <h3>Can I play earlier puzzles?</h3>
    <p>In the app. Its archive holds eighty puzzles, from one move deep to four; the first three of each length are free and the rest come with Swan Road Complete. This page plays today’s puzzle only.</p>
    <h3>What is Swan Road?</h3>
    <p><a href="/">Swan Road</a> is a two-player abstract strategy board game. Five pearls lie between two shores; anchors pull, pearls drift and the tide rises, and the first to pull three pearls home wins. Play the computer at four levels, a friend on one device or online, and a daily game with a leaderboard.</p>
    <h3>Does this page keep anything about me?</h3>
    <p>Your browser remembers which days you solved the puzzle, so the page can say so when you come back. Nothing is sent anywhere. On an iPhone or iPad the page plays three daily puzzles and then hands you to the app, where the daily puzzle is free.</p>
  </section>
  <script type="application/json" id="book">@BOOK@</script>
  <script src="/daily/puzzle.js" defer></script>
"""

DAILY_STYLE = """  header.top { z-index: 10; }
  h2 { font-family: var(--serif); font-weight: 600; font-size: 26px; line-height: 1.2; margin: 56px 0 14px; color: var(--sand); }
  h3 { font-size: 17px; font-weight: 600; margin: 22px 0 4px; }
  section { text-align: left; }
  section h2 { text-align: center; }
  .small { font-size: 15px; text-wrap: balance; }
  .sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
  .rules { margin: 0 0 14px; padding-left: 22px; }
  .rules li { margin: 0 0 10px; }
  #game { max-width: 440px; margin: 26px auto 0; }
  .bar { display: flex; align-items: center; gap: 10px; padding: 8px 2px; font-size: 15px; color: var(--muted); }
  .bar .who { display: flex; align-items: center; gap: 8px; color: var(--ink); font-family: var(--serif); font-size: 18px; font-weight: 600; margin-right: auto; }
  .bar .chip { width: 24px; height: 24px; border-radius: 6px; display: inline-flex; align-items: center; justify-content: center; }
  .bar .chip svg { width: 16px; height: 16px; }
  .bar .you { font: 600 11px/1 var(--sans); letter-spacing: .04em; text-transform: uppercase; color: var(--accent); border: 1px solid var(--accent); border-radius: 6px; padding: 3px 6px; }
  .bar .pearls { display: inline-flex; gap: 5px; }
  .bar .pearls span { width: 14px; height: 14px; border-radius: 50%; border: 1.5px solid var(--muted); }
  .bar .pearls span.got { border-color: #dff6ff; background: radial-gradient(circle at 35% 30%, #fff, #bfeeff); }
  .grid { position: relative; display: grid; grid-template-columns: repeat(7, 1fr); gap: 1px; aspect-ratio: 1; background: rgba(255,255,255,.1);
          border: 1px solid rgba(255,255,255,.14); border-radius: 14px; overflow: hidden; touch-action: manipulation; }
  .cell { appearance: none; border: 0; padding: 0; margin: 0; border-radius: 0; cursor: pointer; background: #0f2439; color: inherit; font: inherit; -webkit-tap-highlight-color: transparent; }
  .cell.alt { background: #122840; }
  .cell.shore-light { background: #cdbf97; }
  .cell.shore-dark { background: #16181d; }
  .cell.selected { box-shadow: inset 0 0 0 3px var(--accent); }
  .cell.pending { box-shadow: inset 0 0 0 2px rgba(127,212,234,.55); }
  .cell.refused { box-shadow: inset 0 0 0 3px #ff8578; }
  .cell:focus-visible { outline: 3px solid #fff; outline-offset: -3px; position: relative; z-index: 3; }
  .grid.still .cell { cursor: default; }
  .pieces { position: absolute; inset: 0; pointer-events: none; z-index: 2; }
  .piece { position: absolute; left: 0; top: 0; width: calc(100% / 7); height: calc(100% / 7); display: flex; align-items: center; justify-content: center;
           transform: translate(calc(var(--c) * 100%), calc(var(--r) * 100%)); transition: transform .5s cubic-bezier(.3,.7,.3,1); }
  .piece > span { transition: opacity .28s ease, transform .28s ease; }
  .piece.gone > span { opacity: 0; transform: scale(.5); }
  .orb { width: 58%; height: 58%; border-radius: 50%; background: radial-gradient(circle at 35% 30%, #fff 0, #e9f8ff 38%, #a9d2e8 100%); box-shadow: 0 0 14px rgba(191,242,255,.65), 0 2px 4px rgba(0,0,0,.35); }
  .tile { width: 66%; height: 66%; border-radius: 24%; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,.4); }
  .tile svg { width: 64%; height: 64%; }
  .light .tile, .chip.light { background: #dbd6c7; color: #4d4841; }
  .dark .tile, .chip.dark { background: #333847; color: #bfd9f2; border: 1px solid rgba(191,217,242,.28); }
  .ghost .tile { opacity: .6; outline: 2px dashed var(--accent); outline-offset: 2px; }
  .leaving .tile { opacity: .3; }
  .arriving .tile { animation: land .3s ease-out; }
  @keyframes land { from { transform: scale(.55); opacity: 0; } to { transform: none; opacity: 1; } }
  .grid.jolt { animation: jolt .28s linear; }
  @keyframes jolt { 18% { transform: translateX(10px); } 40% { transform: translateX(-8px); } 62% { transform: translateX(5px); } 84% { transform: translateX(-3px); } }
  .status { min-height: 3.2em; margin: 12px 0 10px; padding: 8px 12px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
  .status.wrong { color: #ff8578; background: rgba(255,133,120,.12); font-weight: 600; }
  .status.solved { color: var(--accent); background: rgba(127,212,234,.12); font-weight: 600; }
  .controls { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
  .ctl { appearance: none; border: 0; min-height: 46px; padding: 0 18px; border-radius: 12px; background: rgba(255,255,255,.09); color: var(--ink); font: 600 16px var(--sans); cursor: pointer; }
  .ctl.go { background: var(--accent); color: #0b1a2b; flex: 1 1 110px; }
  .ctl:disabled { opacity: .38; cursor: default; }
  .ctl:focus-visible, .btn:focus-visible { outline: 3px solid #fff; outline-offset: 2px; }
  .after { margin: 18px 0 0; padding: 16px 16px 14px; border: 1px solid var(--line); border-radius: 14px; background: rgba(255,255,255,.04); }
  .after p { margin: 0 0 12px; }
  [hidden] { display: none !important; }
  @media (prefers-reduced-motion: reduce) { .piece, .piece > span { transition: none; } .arriving .tile, .grid.jolt { animation: none; } }
"""

DAILY_DESCRIPTION = "Play today’s Swan Road puzzle free in your browser. Place an anchor, watch the pearls drift, and force one onto your shore. A new strategy puzzle every day."

# What search engines are told the page is. No rating appears here until the App Store has one to quote.
DAILY_DATA = {
    "@context": "https://schema.org",
    "@type": ["VideoGame", "WebApplication"],
    "name": "Swan Road daily puzzle",
    "url": "https://swanroad.app/daily/",
    "description": DAILY_DESCRIPTION,
    "image": "https://swanroad.app/assets/social.jpg",
    "genre": ["Puzzle", "Strategy", "Board game"],
    "gamePlatform": ["Web browser", "iOS"],
    "applicationCategory": "GameApplication",
    "operatingSystem": "Any",
    "inLanguage": "en",
    "isAccessibleForFree": True,
    "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    "author": {"@type": "Organization", "name": "Mouse & Chisel Games", "url": "https://mouseandchisel.com"},
    "installUrl": "https://apps.apple.com/app/id6821428315",
}

def embed(value):
    """JSON that is safe inside a script element."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

def board(cells):
    rows = []
    for r in range(N):
        row = ""
        for c in range(N):
            v = cells[r * N + c]
            row += GLYPH.get(v) or ("🟨" if r == 0 else "⬛" if r == N - 1 else "🟦")
        rows.append(row)
    return '  <div class="board" aria-label="the starting position">' + "\n".join(rows) + "</div>"

def store_button(name):
    """The App Store button, carrying a campaign name (tools/campaign.py)."""
    return STORE.replace("@HREF@", campaign.href(name))

def write(path, link, name, **fields):
    out = ROOT / path / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    fields.setdefault("style", "")
    fields.setdefault("head", "")
    fields.setdefault("current", "")
    fields.setdefault("image", "shot-puzzle.jpg")
    out.write_text(PAGE.format(path=path + "/", banner=campaign.banner(name, f"https://swanroad.app/{link}"),
                               footer_css=footer.CSS, footer=footer.HTML, **fields))

book = json.load(open(sys.argv[1]))
puzzles = book["puzzles"]
for p in puzzles:
    seat = "Light" if p["toMove"] == 0 else "Dark"
    other = "Dark" if seat == "Light" else "Light"
    moves = "one move" if p["n"] == 1 else f"{p['n']} moves"
    write(f"p/{p['id']}", f"p/{p['id']}", campaign.PUZZLE,
          page_title=f"Puzzle {p['id']} · Swan Road",
          description=f"Swan Road puzzle {p['id']}: force a pearl onto {seat}’s shore within {moves}, whatever {other} does.",
          main=PUZZLE_MAIN.format(
              title=f"Puzzle {p['id']}",
              subtitle=f"Collect in {p['n']} · {seat} to move",
              board=board(p["cells"]),
              brief=f"{seat} to move. Force a pearl onto {seat}’s shore within {moves}, whatever {other} does. Anchors pull, pearls drift one square a turn toward the strongest pull, and a pearl that reaches a shore is collected.",
              store=store_button(campaign.PUZZLE)))

# The page needs what the app's Puzzle type reads and no more, in the book's order: the day's puzzle is a position in it.
keep = ("id", "n", "toMove", "turn", "cells", "supply", "score", "tree")
web_book = {"version": book.get("version", 1), "puzzles": [{k: p[k] for k in keep} for p in puzzles]}
write("daily", "daily", campaign.DAILY,
      page_title="Daily strategy puzzle, free online · Swan Road",
      description=DAILY_DESCRIPTION,
      image="social.jpg",
      current=' aria-current="page"',
      style=DAILY_STYLE,
      head='<script type="application/ld+json">' + embed(DAILY_DATA) + "</script>\n",
      main=DAILY_MAIN.replace("@STORE@", store_button(campaign.DAILY)).replace("@BOOK@", embed(web_book)))
print(f"wrote {len(puzzles)} puzzle pages and daily/")
