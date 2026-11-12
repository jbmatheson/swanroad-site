#!/usr/bin/env python3
"""Writes p/<id>/index.html for every puzzle in the app's book, and daily/index.html: the pages a shared link lands on
for someone without the app. usage: python3 tools/puzzle_pages.py <path to the app's puzzles.json>"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
N = 7
GLYPH = {"1": "⚪", "2": "🔶", "3": "🔷"}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Swan Road</title>
<meta name="description" content="{description}">
<link rel="canonical" href="https://swanroad.app/{path}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title} · Swan Road">
<meta property="og:description" content="{description}">
<meta property="og:image" content="https://swanroad.app/assets/shot-puzzle.jpg">
<meta property="og:url" content="https://swanroad.app/{path}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0b1a2b">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/icon-32.png">
<link rel="apple-touch-icon" href="/assets/icon-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&display=swap" rel="stylesheet">
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
  nav a:hover {{ color: var(--ink); }}
  main {{ max-width: 680px; margin: 0 auto; padding: 48px 16px 72px; text-align: center; }}
  h1 {{ font-family: var(--serif); font-weight: 600; font-size: clamp(32px, 5vw, 44px); line-height: 1.1; margin: 0 0 6px; }}
  p {{ margin: 0 0 14px; }}
  .muted {{ color: var(--muted); }}
  a {{ color: var(--accent); }}
  .board {{ font-size: clamp(22px, 6vw, 34px); line-height: 1.15; letter-spacing: .02em; margin: 28px auto; white-space: pre; font-family: var(--sans); }}
  .btn {{ display: inline-flex; align-items: center; gap: 10px; margin: 18px 0 8px; padding: 14px 22px; border-radius: 14px; background: var(--accent); color: #0b1a2b; font-weight: 600; text-decoration: none; }}
  .btn svg {{ width: 22px; height: 22px; }}
</style>
</head>
<body>
<header class="top"><div class="wrap"><a class="brand" href="/"><img src="/assets/icon-64.png" alt="" width="32" height="32">Swan Road</a><nav><a href="/#how">How it plays</a><a href="/support/">Support</a><a href="/privacy/">Privacy</a></nav></div></header>
<main>
  <h1>{title}</h1>
  <p class="muted">{subtitle}</p>
{board}
  <p>{brief}</p>
  <a class="btn" href="https://apps.apple.com/app/id6821428315"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M16.4 12.6c0-2.5 2-3.6 2.1-3.7-1.2-1.7-3-1.9-3.6-2-1.5-.2-3 .9-3.8.9-.8 0-2-.9-3.2-.9-1.7 0-3.2 1-4.1 2.5-1.8 3.1-.5 7.6 1.3 10.1.9 1.2 1.9 2.6 3.2 2.5 1.3-.1 1.8-.8 3.3-.8s2 .8 3.3.8c1.4 0 2.2-1.2 3.1-2.5 1-1.4 1.4-2.8 1.4-2.9-.1 0-2.9-1.1-3-4zM13.9 5.3c.7-.8 1.2-2 1-3.1-1 0-2.2.7-2.9 1.5-.6.7-1.2 1.9-1 3 1.1.1 2.2-.6 2.9-1.4z"/></svg>Get it on the App Store</a>
  <p class="muted">With the app installed, this link opens the puzzle there.</p>
</main>
</body>
</html>
"""

def board(cells):
    rows = []
    for r in range(N):
        row = ""
        for c in range(N):
            v = cells[r * N + c]
            row += GLYPH.get(v) or ("🟨" if r == 0 else "⬛" if r == N - 1 else "🟦")
        rows.append(row)
    return '  <div class="board" aria-label="the starting position">' + "\n".join(rows) + "</div>"

def write(path, **fields):
    out = ROOT / path / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(PAGE.format(path=path + "/", **fields))

puzzles = json.load(open(sys.argv[1]))["puzzles"]
for p in puzzles:
    seat = "Light" if p["toMove"] == 0 else "Dark"
    other = "Dark" if seat == "Light" else "Light"
    moves = "one move" if p["n"] == 1 else f"{p['n']} moves"
    write(f"p/{p['id']}",
          title=f"Puzzle {p['id']}",
          subtitle=f"Collect in {p['n']} · {seat} to move",
          description=f"Swan Road puzzle {p['id']}: force a pearl onto {seat}’s shore within {moves}, whatever {other} does.",
          board=board(p["cells"]),
          brief=f"{seat} to move. Force a pearl onto {seat}’s shore within {moves}, whatever {other} does. Anchors pull, pearls drift one square a turn toward the strongest pull, and a pearl that reaches a shore is collected.")
write("daily",
      title="Today’s puzzle",
      subtitle="A new one every day, the same for everyone",
      description="Swan Road sets one puzzle a day: force a pearl onto your shore in a few moves, whatever the other side does.",
      board="",
      brief="Swan Road sets one puzzle a day, the same for everyone: force a pearl onto your shore in one to four moves, whatever the other side does. Solve it daily to keep a streak.")
print(f"wrote {len(puzzles)} puzzle pages and daily/")
