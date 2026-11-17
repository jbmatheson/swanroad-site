#!/usr/bin/env python3
"""Builds the devlog from Markdown: devlog/src/<slug>.md becomes devlog/<slug>/index.html, and devlog/index.html lists
the posts. A post starts with a header block:

    title: Why the pearls drift
    date: 2026-11-10
    description: One sentence for the index and the link preview.
    published: false
    updated: 2026-11-17        (optional: the day a published post was last added to)

Only published posts are written and listed; --drafts includes the rest for a local look. Every post ends with the
same closing block: the daily puzzle and the App Store, then the other posts. devlog/feed.xml is an Atom feed of the published posts. Run
from anywhere:
    uv run --with markdown python3 tools/devlog.py [--drafts]
"""
import html as htmllib, json, pathlib, re, shutil, sys

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "devlog" / "src", ROOT / "devlog"
SITE = "https://swanroad.app/"
STORE = "https://apps.apple.com/app/id6821428315"
FEED = '<link rel="alternate" type="application/atom+xml" title="Swan Road devlog" href="/devlog/feed.xml">\n'

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
<meta name="apple-itunes-app" content="app-id=6821428315">
{extra}<link rel="icon" type="image/png" sizes="32x32" href="/assets/icon-32.png">
<link rel="apple-touch-icon" href="/assets/icon-180.png">
<link rel="preload" href="/assets/fonts/fraunces-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts/fraunces.css">
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
  @media (max-width: 640px) {{ nav a:not(:last-child):not(.cta) {{ display: none; }} }}
  @media (max-width: 380px) {{ nav a:not(.cta) {{ display: none; }} }}
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
  .play {{ margin: 44px 0 0; padding: 18px 20px 20px; background: var(--card); border: 1px solid var(--line); border-radius: 14px; }}
  .play p:last-child {{ margin: 0; }}
  .btn {{ display: inline-block; padding: 12px 20px; border-radius: 12px; background: var(--accent); color: #0b1a2b; font-weight: 600; text-decoration: none; }}
  footer {{ border-top: 1px solid var(--line); padding: 28px 16px 48px; color: var(--muted); font-size: 15px; text-align: center; }}
  footer a {{ color: var(--muted); margin: 0 8px; }}
</style>
</head>
<body>
<header class="top"><div class="wrap"><a class="brand" href="/"><img src="/assets/icon-64.png" alt="" width="32" height="32">Swan Road</a><nav><a class="cta" href="/daily/">Daily puzzle</a><a href="/#how">How it plays</a><a href="/devlog/">Devlog</a><a href="/press/">Press</a><a href="/support/">Support</a></nav></div></header>
<main>
"""
FOOT = """</main>
<footer>
  <div><a href="https://mouseandchisel.com" target="_blank" rel="noopener">Made by Mouse &amp; Chisel Games</a></div>
  <div><a href="/daily/">Daily puzzle</a><a href="/support/">Support</a><a href="/privacy/">Privacy policy</a><a href="/press/">Press</a><a href="/devlog/">Devlog</a></div>
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


# What every post ends with: the way to play, for a reader who arrived at a post and knows nothing else of the game.
PLAY = """<aside class="play">
<p><strong>Play it.</strong> <a href="/daily/">Today’s puzzle plays in your browser</a>, with nothing to install. Swan Road is free on the App Store for iPhone and iPad, with no ads and no account.</p>
<p><a class="btn" href="{store}">Get it on the App Store</a></p>
</aside>
"""


def dated(m):
    """The line under a post's title: the day it was published, and the day it was last added to if it has one."""
    line = nice(m["date"])
    if m.get("updated") and m["updated"] != m["date"]:
        line += f" · updated {nice(m['updated'])}"
    return line + ("" if m["published"] else " · draft")


def article(m):
    """What search engines are told a post is."""
    data = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": m["title"], "description": m["description"],
            "datePublished": m["date"], "dateModified": m.get("updated") or m["date"],
            "url": f"{SITE}devlog/{m['slug']}/", "image": f"{SITE}assets/social.jpg",
            "author": {"@type": "Organization", "name": "Mouse & Chisel Games", "url": "https://mouseandchisel.com"},
            "publisher": {"@type": "Organization", "name": "Mouse & Chisel Games", "url": "https://mouseandchisel.com"}}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>\n"


def feed(posts):
    """An Atom feed of the published posts, newest first, each with its whole text."""
    x = htmllib.escape
    newest = max((m.get("updated") or m["date"]) for m, _ in posts)
    out = ['<?xml version="1.0" encoding="utf-8"?>', '<feed xmlns="http://www.w3.org/2005/Atom">',
           "  <title>Swan Road devlog</title>", "  <subtitle>Notes from making the game.</subtitle>",
           f'  <link href="{SITE}devlog/"/>', f'  <link rel="self" href="{SITE}devlog/feed.xml"/>',
           f"  <id>{SITE}devlog/</id>", f"  <updated>{newest}T12:00:00Z</updated>", "  <author><name>Mouse &amp; Chisel Games</name><uri>https://mouseandchisel.com</uri></author>"]
    for m, body in posts:
        url = f"{SITE}devlog/{m['slug']}/"
        out += ["  <entry>", f"    <title>{x(m['title'])}</title>", f'    <link href="{url}"/>', f"    <id>{url}</id>",
                f"    <published>{m['date']}T12:00:00Z</published>", f"    <updated>{(m.get('updated') or m['date'])}T12:00:00Z</updated>",
                f"    <summary>{x(m['description'])}</summary>", f'    <content type="html">{x(body)}</content>', "  </entry>"]
    out.append("</feed>")
    (OUT / "feed.xml").write_text("\n".join(out) + "\n", encoding="utf-8")


def main(drafts=False):
    posts = [read(p) for p in sorted(SRC.glob("*.md"))]
    posts = [(m, b) for m, b in posts if m["published"] or drafts]
    posts.sort(key=lambda mb: (mb[0]["date"], mb[0].get("order", "")), reverse=True)
    for d in OUT.iterdir():
        if d.is_dir() and d.name != "src": shutil.rmtree(d)
    rendered = []
    for m, body in posts:
        html = markdown.markdown(body, extensions=["smarty"])
        rendered.append((m, html))
        page = HEAD.format(title=m["title"], description=m["description"], path=f"devlog/{m['slug']}/", extra=FEED + article(m))
        page += f"<p class=\"muted\">{dated(m)}</p>\n<h1>{m['title']}</h1>\n{html}\n"
        page += PLAY.format(store=STORE)
        others = [o for o, _ in posts if o["slug"] != m["slug"]]
        if others:
            page += "<h2>More from the devlog</h2>\n<ul>\n" + "".join(
                f"<li><a href=\"/devlog/{o['slug']}/\">{o['title']}</a>: {o['description']}</li>\n" for o in others) + "</ul>\n"
        page += "<p class=\"muted\"><a href=\"/devlog/\">All posts</a></p>\n" + FOOT
        (OUT / m["slug"]).mkdir(parents=True); (OUT / m["slug"] / "index.html").write_text(page, encoding="utf-8")
    index = HEAD.format(title="Devlog", description="Notes from making Swan Road: the rules, the computer opponent, the name, the details.", path="devlog/", extra=FEED)
    index += "<h1>Devlog</h1>\n<p class=\"muted\">Notes from making the game, one a week from launch. <a href=\"/devlog/feed.xml\">Feed</a></p>\n"
    for m, _ in posts:
        index += (f"<div class=\"post\"><h2><a href=\"/devlog/{m['slug']}/\">{m['title']}</a></h2>"
                  f"<p class=\"muted\">{dated(m)}</p><p>{m['description']}</p></div>\n")
    if not posts: index += "<p>The first post comes with the launch.</p>\n"
    (OUT / "index.html").write_text(index + FOOT, encoding="utf-8")
    published = [(m, h) for m, h in rendered if m["published"]]
    if published: feed(published)
    print(f"devlog: {len(posts)} post(s) written")


if __name__ == "__main__":
    main(drafts="--drafts" in sys.argv[1:])
