#!/usr/bin/env python3
"""Builds the devlog from Markdown: devlog/src/<slug>.md becomes devlog/<slug>/index.html, and devlog/index.html lists
the posts. A post starts with a header block:

    title: Why the pearls drift
    date: 2026-11-10
    description: One sentence for the index and the link preview.
    published: false

Only published posts are written and listed; --drafts includes the rest for a local look. Run from anywhere:
    uv run --with markdown python3 tools/devlog.py [--drafts]
"""
import pathlib, re, shutil, sys

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "devlog" / "src", ROOT / "devlog"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Swan Road</title>
<meta name="description" content="{description}">
<link rel="canonical" href="https://swanroad.app/{path}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title} · Swan Road">
<meta property="og:description" content="{description}">
<meta property="og:image" content="https://swanroad.app/assets/social.jpg">
<meta property="og:url" content="https://swanroad.app/{path}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0b1a2b">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/icon-32.png">
<link rel="apple-touch-icon" href="/assets/icon-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&display=swap" rel="stylesheet">
<style>
  :root {{ --bg: #0b1a2b; --ink: #eef3f8; --muted: #a7b6c6; --accent: #7fd4ea; --sand: #e4d6b2; --card: #132b49; --line: rgba(255,255,255,.08);
          --serif: "Fraunces", "Iowan Old Style", "Palatino", Georgia, serif; --sans: -apple-system, "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink); font: 18px/1.65 var(--sans); -webkit-font-smoothing: antialiased; }}
  img {{ display: block; max-width: 100%; height: auto; }}
  header.top {{ position: sticky; top: 0; z-index: 10; backdrop-filter: blur(14px); background: rgba(11,26,43,.72); border-bottom: 1px solid var(--line); }}
  header.top .wrap {{ max-width: 1080px; margin: 0 auto; padding: 0 16px; display: flex; align-items: center; justify-content: space-between; height: 60px; }}
  .brand {{ display: flex; align-items: center; gap: 10px; color: var(--ink); text-decoration: none; font-family: var(--serif); font-size: 20px; font-weight: 600; }}
  .brand img {{ width: 32px; height: 32px; border-radius: 8px; }}
  nav a {{ color: var(--muted); text-decoration: none; margin-left: 20px; font-size: 15px; }}
  nav a:hover {{ color: var(--ink); }}
  @media (max-width: 640px) {{ nav a:not(:last-child) {{ display: none; }} }}
  main {{ max-width: 720px; margin: 0 auto; padding: 48px 16px 72px; }}
  h1 {{ font-family: var(--serif); font-weight: 600; font-size: clamp(32px, 5vw, 44px); line-height: 1.1; margin: 0 0 6px; }}
  h2 {{ font-family: var(--serif); font-weight: 600; font-size: 26px; margin: 40px 0 10px; color: var(--sand); }}
  h3 {{ font-family: var(--serif); font-weight: 600; font-size: 20px; margin: 26px 0 6px; }}
  p, li {{ margin: 0 0 14px; }}
  .muted {{ color: var(--muted); }}
  a {{ color: var(--accent); }}
  ul, ol {{ padding-left: 22px; }}
  blockquote {{ margin: 0 0 14px; padding: 14px 18px; background: var(--card); border: 1px solid var(--line); border-radius: 14px; }}
  blockquote p:last-child {{ margin: 0; }}
  code {{ font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 16px; background: var(--card); padding: 1px 6px; border-radius: 6px; }}
  .post {{ padding: 18px 0; border-bottom: 1px solid var(--line); }}
  .post h2 {{ margin: 0 0 4px; font-size: 24px; }}
  .post h2 a {{ color: var(--ink); text-decoration: none; }}
  .post h2 a:hover {{ color: var(--accent); }}
  .post .muted {{ font-size: 15px; }}
  footer {{ border-top: 1px solid var(--line); padding: 28px 16px 48px; color: var(--muted); font-size: 15px; text-align: center; }}
  footer a {{ color: var(--muted); margin: 0 8px; }}
</style>
</head>
<body>
<header class="top"><div class="wrap"><a class="brand" href="/"><img src="/assets/icon-64.png" alt="" width="32" height="32">Swan Road</a><nav><a href="/#how">How it plays</a><a href="/devlog/">Devlog</a><a href="/press/">Press</a><a href="/support/">Support</a></nav></div></header>
<main>
"""
FOOT = """</main>
<footer>
  <div><a href="https://mouseandchisel.com">Made by Mouse &amp; Chisel</a></div>
  <div><a href="/support/">Support</a><a href="/privacy/">Privacy policy</a><a href="/press/">Press</a><a href="/devlog/">Devlog</a></div>
</footer>
</body>
</html>
"""


def read(path):
    text = path.read_text(encoding="utf-8")
    head, body = text.split("\n\n", 1)
    meta = dict(line.split(":", 1) for line in head.splitlines())
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    meta["published"] = meta.get("published", "false").lower() == "true"
    meta["slug"] = path.stem
    return meta, body


def nice(date):
    y, m, d = date.split("-")
    return f"{int(d)} {['January','February','March','April','May','June','July','August','September','October','November','December'][int(m) - 1]} {y}"


def main(drafts=False):
    posts = [read(p) for p in sorted(SRC.glob("*.md"))]
    posts = [(m, b) for m, b in posts if m["published"] or drafts]
    posts.sort(key=lambda mb: mb[0]["date"], reverse=True)
    for d in OUT.iterdir():
        if d.is_dir() and d.name != "src": shutil.rmtree(d)
    for m, body in posts:
        html = markdown.markdown(body, extensions=["smarty"])
        page = HEAD.format(title=m["title"], description=m["description"], path=f"devlog/{m['slug']}/")
        page += f"<p class=\"muted\">{nice(m['date'])}{'' if m['published'] else ' · draft'}</p>\n<h1>{m['title']}</h1>\n{html}\n"
        page += "<p class=\"muted\"><a href=\"/devlog/\">All posts</a></p>\n" + FOOT
        (OUT / m["slug"]).mkdir(parents=True); (OUT / m["slug"] / "index.html").write_text(page, encoding="utf-8")
    index = HEAD.format(title="Devlog", description="Notes from making Swan Road: the rules, the computer opponent, the name, the details.", path="devlog/")
    index += "<h1>Devlog</h1>\n<p class=\"muted\">Notes from making the game, one a week from launch.</p>\n"
    for m, _ in posts:
        index += (f"<div class=\"post\"><h2><a href=\"/devlog/{m['slug']}/\">{m['title']}</a></h2>"
                  f"<p class=\"muted\">{nice(m['date'])}{'' if m['published'] else ' · draft'}</p><p>{m['description']}</p></div>\n")
    if not posts: index += "<p>The first post comes with the launch.</p>\n"
    (OUT / "index.html").write_text(index + FOOT, encoding="utf-8")
    print(f"devlog: {len(posts)} post(s) written")


if __name__ == "__main__":
    main(drafts="--drafts" in sys.argv[1:])
