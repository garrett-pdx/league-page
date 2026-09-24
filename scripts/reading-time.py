#!/usr/bin/env python3
"""
Reading-time estimate for a Mudd Report article, for the "· N min read" in its dateline.

  python3 scripts/reading-time.py docs/articles/2026-w3-preview.md

Counts the words a reader actually sees: the title is dropped (it is its own field on the
site), table divider rows and Markdown punctuation are stripped, and table cells count as
words. Divides by 230 words a minute and rounds UP, because these posts are dense with
tables and scores, which read slower than prose -- the Week 3 2026 preview was 1,496 words,
6.5 minutes at 230, and published as 7.

Run it last, after every edit. The number goes stale the moment the article changes length.
"""
import math
import re
import sys

WPM = 230


def count_words(md):
    body = md.split("\n", 1)[1] if "\n" in md else ""
    body = re.sub(r"^\|\s*-+.*$", "", body, flags=re.M)   # table divider rows
    body = re.sub(r"[*#|`>_]", " ", body)                  # Markdown punctuation
    # A stale "· N min read" must not count itself.
    body = re.sub(r"·\s*\d+\s*min read", " ", body)
    return sum(1 for w in re.findall(r"[\w$.'’%-]+", body) if re.search(r"\w", w))


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python3 scripts/reading-time.py <article.md>")
    words = count_words(open(sys.argv[1], encoding="utf-8").read())
    minutes = max(1, math.ceil(words / WPM))
    print(f"{words} words -> {minutes} min read")


if __name__ == "__main__":
    main()
