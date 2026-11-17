#!/usr/bin/env python3
"""The footer every page ends with, kept in one place so the pages cannot drift apart. The page tools
(puzzle_pages.py, devlog.py) read it from here; this script writes it into the pages kept by hand.

    python3 tools/footer.py           write the footer into index.html, press/, privacy/ and support/
    python3 tools/footer.py --check   every page on the site carries exactly this footer and its styles

To change the footer, change it here, run this script, then run the two page tools."""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BY_HAND = ("", "press/", "privacy/", "support/")

HTML = """<footer>
  <div class="links"><a href="/daily/">Daily puzzle</a><a href="/devlog/">Devlog</a><a href="/support/">Support</a><a href="/privacy/">Privacy policy</a><a href="/press/">Press</a><a href="mailto:jim@mouseandchisel.com">Contact us</a></div>
  <div>© 2026 <a href="https://mouseandchisel.com" target="_blank" rel="noopener">Mouse &amp; Chisel Games</a>. Swan Road (<i lang="ang">swanrād</i>) is an Old English kenning for the sea, from <i>Beowulf</i>.</div>
</footer>"""

# Every page defines --line, --muted and --ink. The links sit in a wrapping row, so a narrow phone breaks between
# links and never inside one.
CSS = """  footer { border-top: 1px solid var(--line); padding: 36px 16px 48px; color: var(--muted); font-size: 15px; text-align: center; }
  footer > div { line-height: 2; }
  footer .links { display: flex; flex-wrap: wrap; justify-content: center; gap: 0 20px; }
  footer > div:last-child { margin-top: 12px; font-size: 14px; line-height: 1.6; opacity: .75; }
  footer > div:last-child a { text-decoration: underline; white-space: normal; }
  footer a { color: var(--muted); text-decoration: none; white-space: nowrap; }
  footer a:hover { color: var(--ink); }"""

MARKUP = re.compile(r"<footer>.*?</footer>", re.S)
STYLES = re.compile(r"(?:^[ \t]*footer\b[^\n]*\n)+", re.M)


def pages():
    for index in sorted(ROOT.rglob("index.html")):
        folder = index.parent.relative_to(ROOT)
        if not any(part.startswith(".") or part == "src" for part in folder.parts):
            yield index, ("" if str(folder) == "." else folder.as_posix() + "/")


def write_by_hand():
    for page in BY_HAND:
        path = ROOT / page / "index.html"
        text = path.read_text(encoding="utf-8")
        new, blocks = MARKUP.subn(lambda _: HTML, text)
        new, rules = STYLES.subn(lambda _: CSS + "\n", new)
        assert blocks == 1 and rules == 1, (page, blocks, rules)
        if new != text:
            path.write_text(new, encoding="utf-8")
        print(f"{page or 'index.html'}: {'written' if new != text else 'already current'}")


def check():
    bad, count = [], 0
    for index, page in pages():
        text = index.read_text(encoding="utf-8")
        count += 1
        if text.count(HTML) != 1 or text.count("<footer") != 1:
            bad.append(f"{page or '/'}: the footer is not the one in tools/footer.py")
        if text.count(CSS) != 1 or len(STYLES.findall(text)) != 1:
            bad.append(f"{page or '/'}: the footer's styles are not the ones in tools/footer.py")
    for line in bad[:20]:
        print("  FAIL " + line)
    print(f"footer: {count} pages" + (f", {len(bad)} wrong" if bad else ", all the same"))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    check() if "--check" in sys.argv else write_by_hand()
