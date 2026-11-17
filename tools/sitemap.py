#!/usr/bin/env python3
"""Writes sitemap.xml: every page of the site, found by its index.html. robots.txt points search engines at it.
Run it after adding or removing a page, which the other two tools do: python3 tools/sitemap.py"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://swanroad.app/"
# Read first, in this order; everything else follows by path, the numbered puzzles in number order.
FIRST = ["", "daily/", "devlog/", "press/", "support/", "privacy/"]


def order(path):
    if path in FIRST:
        return (0, FIRST.index(path), "")
    head, _, rest = path.partition("/")
    number = rest.strip("/")
    return (1, 0, head) + ((int(number),) if head == "p" and number.isdigit() else (0, rest))


pages = []
for index in ROOT.rglob("index.html"):
    folder = index.parent.relative_to(ROOT)
    if any(part.startswith(".") or part == "src" for part in folder.parts):
        continue
    pages.append("" if str(folder) == "." else folder.as_posix() + "/")
pages.sort(key=order)

lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
lines += [f"  <url><loc>{SITE}{page}</loc></url>" for page in pages]
lines.append("</urlset>")
(ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n")
print(f"sitemap: {len(pages)} pages")
