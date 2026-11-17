# Name

The game is **Swan Road**: two words, no apostrophe, no extra s. That holds everywhere: pages, the devlog, the press kit, commit messages, file names and links. `.githooks/name-check` blocks any other form on commit and on push; a fresh clone needs `git config core.hooksPath .githooks` once.

# Footer

Every page ends with the same footer, and it lives in one place: `tools/footer.py`. Never edit a page's footer by
hand. Change it there, run `python3 tools/footer.py` (the pages kept by hand), then the two page tools
(`tools/puzzle_pages.py`, `tools/devlog.py`). `python3 tools/footer.py --check` fails if any page differs.
