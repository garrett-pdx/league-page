#!/usr/bin/env python3
"""
What does a draft repeat from the posts just before it?

  python3 scripts/repeat-check.py docs/articles/2026-w4-preview.md        # vs the previous 2
  python3 scripts/repeat-check.py docs/articles/2026-w4-preview.md --last 3

Two editions a week cover overlapping ground, and a reader who reads both should not be told
the same thing twice. The Week 4 2026 preview re-ran the Week 3 recap's lead almost verbatim --
paulslaats's perfect lineup, 148.38, the second-highest losing score, BBrown16's 148.74 --
under a new heading.

Compares prose only (tables are reference, and standings repeat by design) and reports:

  * every two-decimal figure the draft shares with an earlier post, with the draft's sentence.
    Aim for zero: a figure survives only inside a genuinely new story. Restating how Monday's
    live games turned out ("he needed 16.45 and got 8.50") is a recap of the recap, and the
    league asked for those to go;
  * every phrase of six or more words the draft shares with an earlier post -- the stock
    lines and devices that make a series read like a template.

Posts are ordered by the "WEEK N RECAP/PREVIEW" in their title: for the same week, the
preview comes before the recap.
"""
import argparse
import glob
import os
import re

ARTICLES = os.path.join(os.path.dirname(__file__), "..", "docs", "articles")


def order_key(path):
    title = open(path, encoding="utf-8").readline()
    m = re.search(r"WEEK (\d+)(?: (RECAP|PREVIEW))?", title)
    if not m:
        return (-1, 0)                       # preseason and anything untitled sorts first
    return (int(m.group(1)), 0 if m.group(2) == "PREVIEW" else 1)


def prose(path):
    lines = open(path, encoding="utf-8").read().split("\n")[1:]   # drop the title
    keep = [l for l in lines if not l.lstrip().startswith("|")]   # drop tables
    text = "\n".join(keep)
    text = re.sub(r"^\*.*min read\*$", "", text, flags=re.M)      # dateline
    text = re.sub(r"\*Correction:.*?\*", "", text, flags=re.S)    # correction notes
    return text


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def words(text):
    return re.findall(r"[a-z0-9’'.$-]+", re.sub(r"[*_#`]", " ", text.lower()))


def ngrams(ws, n):
    return {" ".join(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("--last", type=int, default=2)
    ap.add_argument("--n", type=int, default=6, help="phrase length in words")
    a = ap.parse_args()

    draft = os.path.abspath(a.draft)
    others = sorted((p for p in glob.glob(os.path.join(ARTICLES, "*.md"))
                     if os.path.abspath(p) != draft and order_key(p) < order_key(draft)),
                    key=order_key)[-a.last:]
    if not others:
        print("no earlier posts to compare against")
        return

    d_text = prose(draft)
    d_sents = sentences(d_text)
    d_grams = ngrams(words(d_text), a.n)

    for p in reversed(others):
        o_text = prose(p)
        title = open(p, encoding="utf-8").readline().strip("# \n")
        shared_figs = sorted(set(re.findall(r"\d+\.\d\d", d_text)) & set(re.findall(r"\d+\.\d\d", o_text)),
                             key=float, reverse=True)
        shared_grams = sorted(d_grams & ngrams(words(o_text), a.n))
        print(f"=== vs {title} ({os.path.basename(p)})")
        print(f"  figures in both: {len(shared_figs)}")
        for f in shared_figs:
            where = next((s for s in d_sents if f in s), "")
            print(f"    {f:>8}  {where[:110]}")
        # Collapse overlapping n-grams into runs so a repeated sentence prints once.
        runs, cur = [], []
        dw = words(d_text)
        for i in range(len(dw) - a.n + 1):
            g = " ".join(dw[i:i + a.n])
            if g in shared_grams:
                cur = cur + [dw[i + a.n - 1]] if cur else dw[i:i + a.n]
            elif cur:
                runs.append(" ".join(cur)); cur = []
        if cur:
            runs.append(" ".join(cur))
        print(f"  phrases of {a.n}+ words in both: {len(runs)}")
        for r in runs:
            print(f"    \"{r}\"")
        print()


if __name__ == "__main__":
    main()
