#!/usr/bin/env python3
"""Every App Store link on the site carries a campaign name, so App Store Connect can count installs by where they
came from (Apps, the app, Analytics, Acquisition, Campaigns). The provider number and the names live here: the two
page tools read them from this file, and this script writes them into the pages kept by hand.

    python3 tools/campaign.py           write the links into index.html, press/, support/ and privacy/
    python3 tools/campaign.py --check   every page: each App Store link and each Smart App Banner carries both tokens
    python3 tools/campaign.py --links   a ready-made link for each place a post goes, as Markdown

A link is https://apps.apple.com/app/apple-store/id<app>?pt=<provider>&ct=<name>&mt=8. The provider number comes from
App Store Connect's own campaign link generator and from nowhere else; it is the same for every link. A name is at
most 30 characters. Apple shows a campaign only after five people have installed through it and a day has passed, so
the names are few on purpose: three for the site's own pages and one for each place a post goes.

A link to the daily page can also say where it was posted, as https://swanroad.app/daily/?from=hn: the page's App
Store button then carries that name (daily/puzzle.js), so the install counts for the post and not for the page."""
import html, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
APP_ID = "6821428315"
# From App Store Connect's campaign link generator (Analytics, Acquisition, Campaigns), read there on 2026-11-17.
PROVIDER = "128263881"

# The site's own pages.
SITE = "site"            # the home page, the devlog, support and privacy
DAILY = "webdaily"       # the daily puzzle page
PUZZLE = "puzzlelink"    # a numbered puzzle page, where a puzzle shared from the app lands
PRESS = "press"          # the press page, and the link in a press email

# One for each place a post goes. Add a line for a new place; the name is what App Store Connect will show.
CHANNELS = [
    ("applevis", "AppleVis forum post"),
    ("audiogames", "AudioGames.net forum post"),
    ("r-abstractgames", "Reddit, r/abstractgames"),
    ("r-iosgaming", "Reddit, r/iosgaming"),
    ("r-blind", "Reddit, r/blind"),
    ("hn", "Hacker News"),
    ("bgg", "BoardGameGeek"),
    ("youtube", "YouTube descriptions and Shorts"),
    (PRESS, "Press emails"),
    ("producthunt", "Product Hunt"),
    ("bluesky", "Bluesky"),
    ("linkedin", "LinkedIn"),
    ("friends", "Links sent to friends and testers"),
]
NAME = re.compile(r"[a-z0-9-]{1,30}")
PLAIN = f"https://apps.apple.com/app/id{APP_ID}"


def store(name):
    """The App Store link for a campaign name."""
    assert NAME.fullmatch(name), name
    return f"https://apps.apple.com/app/apple-store/id{APP_ID}?pt={PROVIDER}&ct={name}&mt=8" if PROVIDER else PLAIN


def href(name):
    """The same link, written for an HTML attribute."""
    return html.escape(store(name))


def banner(name, argument=None):
    """The content of a page's Smart App Banner tag. `argument` is the link the banner hands to the app."""
    parts = [f"app-id={APP_ID}"]
    if argument:
        parts.append(f"app-argument={argument}")
    if PROVIDER:
        parts.append(html.escape(f"affiliate-data=pt={PROVIDER}&ct={name}&mt=8"))
    return ", ".join(parts)


def name_for(page):
    """The campaign name a page's own links carry, from its path under the site's root."""
    if page.startswith("p/"):
        return PUZZLE
    if page.startswith("daily/"):
        return DAILY
    if page.startswith("press/"):
        return PRESS
    return SITE


LINK = re.compile(r'href="https://apps\.apple\.com/app/[^"]*id' + APP_ID + r'[^"]*"')
BANNER = re.compile(r'<meta name="apple-itunes-app" content="([^"]*)">')


def pages():
    for index in sorted(ROOT.rglob("index.html")):
        folder = index.parent.relative_to(ROOT)
        if not any(part.startswith(".") or part == "src" for part in folder.parts):
            yield index, ("" if str(folder) == "." else folder.as_posix() + "/")


def write_by_hand():
    """The pages no tool writes: their App Store links and banner tags, set from the names above."""
    for page in ("", "press/", "support/", "privacy/"):
        path = ROOT / page / "index.html"
        text = path.read_text()
        name = name_for(page)
        new = LINK.sub(lambda _: f'href="{href(name)}"', text)
        new, banners = BANNER.subn(lambda _: f'<meta name="apple-itunes-app" content="{banner(name)}">', new)
        assert banners == 1, (page, banners)
        if new != text:
            path.write_text(new)
        print(f"{page or 'index.html'}: {len(LINK.findall(new))} link(s) and the banner carry '{name}'")


def check():
    if not PROVIDER:
        sys.exit("campaign: no provider number yet, so every link is plain. Set PROVIDER in tools/campaign.py.")
    bad, links, banners = [], 0, 0
    for index, page in pages():
        text, name = index.read_text(), name_for(page)
        for found in LINK.findall(text):
            links += 1
            if html.unescape(found[6:-1]) != store(name):
                bad.append(f"{page or '/'}: link is {html.unescape(found[6:-1])}, expected the '{name}' link")
        tags = BANNER.findall(text)
        banners += len(tags)
        want = f"affiliate-data=pt={PROVIDER}&ct={name}&mt=8"
        if len(tags) != 1 or want not in html.unescape(tags[0]) or f"app-id={APP_ID}" not in tags[0]:
            bad.append(f"{page or '/'}: banner tag is {tags}, expected '{name}'")
        if "apps.apple.com/app/id" in text.replace('"installUrl":"' + PLAIN, ""):
            bad.append(f"{page or '/'}: a plain App Store link is left")
    for line in bad[:20]:
        print("  FAIL " + line)
    print(f"campaign: {links} links and {banners} banners on {sum(1 for _ in pages())} pages" + (f", {len(bad)} wrong" if bad else ", all carry their names"))
    sys.exit(1 if bad else 0)


def links():
    if not PROVIDER:
        sys.exit("campaign: no provider number yet. Set PROVIDER in tools/campaign.py.")
    print("| Where the post goes | Name in App Store Connect | App Store link | Daily puzzle link |")
    print("|---|---|---|---|")
    for name, where in CHANNELS:
        print(f"| {where} | `{name}` | {store(name)} | https://swanroad.app/daily/?from={name} |")


if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    elif "--links" in sys.argv:
        links()
    else:
        write_by_hand()
