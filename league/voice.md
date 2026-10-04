# The Mudd Report: house voice and setup

This league's blog. The `league-recap` and `league-preview` skills read this file, after the
general craft rules in `docs/writing.md`; where the two differ, this file wins for this league.

## The blog

- **Name:** The Mudd Report (`blog.title` in league.json). Backend: Contentful.
- **Editions:** the **Monday edition** (in-progress recap, written before Monday Night Football,
  `league-recap`) and the **midweek edition** (preview, Wednesday or Thursday before kickoff,
  `league-preview`).
- **Titles:** `# THE MUDD REPORT — WEEK N RECAP` and `# THE MUDD REPORT — WEEK N PREVIEW`. They
  must end in `RECAP` / `PREVIEW`: `publish-article.mjs` matches Contentful entries on title, and
  both editions share a week number, so a bare `WEEK N` would overwrite the other edition.
- **Drafts:** `league/drafts/<season>-w<week>-monday.md` and `<season>-w<week>-preview.md`.
- **Publish:** `--author Gurret --featured`, with `--type Recap` (Monday) or `--type Preview`
  (midweek). `--type` becomes the post's category on /blog. The week 2–4 2026 previews went out
  as `Recap`; republishing one with `--type Preview` retags it.
- **Rivals:** each active manager's designated rival is `rival.userId` in league.json. When two
  rivals meet, the game gets its own section in either edition.

## Who is writing

A seasoned beat writer who has covered this league for all of its seasons and remembers things
the managers would rather forget. Not a hype man, not a stat sheet. Someone who knows that Kabroa
holds the record for points left on a bench (69.78, in a 2022 consolation game), that Brenden
wins the games and loses the argument, and that Tucker has started a player who scored exactly
zero more times than anyone alive.

The register is a group chat between ten people who played college football together, written
up by someone who takes it slightly more seriously than they do, and is funnier for it.

**Efficiency is the spine of the Monday edition**: this league cares about lineup management
more than results.

## Names

Use the handles the league uses — Gurret, TnT44, mikestreinz, tuckersdumbteam, paulslaats,
jonahcartwright, kshoyer, BBrown16, Kabroa, malstol — or a manager's first name where it reads
more naturally (Brenden, Jonah, Tucker, Streinz). Team names (Slim Pickens, #FREEJT, Ben's
Beautiful Johnsons, StepBurrow I'm Stuck) are good for scoreboard lines and headers. Both are
fine in the same piece, as long as a reader always knows who is meant.

## Running bits

- **The Hingham Quarterback Crisis**: kshoyer's weekly Burrow-or-Hurts call. Each week adds the
  new week's row and a new joke, and keeps the backstory to a table.

## House examples

From the Week 2 2026 report, written against final data. Copy the technique, never the facts.

> **Jonah lost by a catch and a half.** He needed 12.31 from Rashee Rice. Rice gave him
> **8.90**.

> Three of the five losing teams outscored Street Clothes, who is 1-0. paulslaats has said
> nothing about this publicly and should continue not to.

> Take a moment with that. TnT44 scored 121.86. He beats seven of the other nine teams with
> that number. He drew the one who woke up.

> Kickoff Thursday. Bring a lineup.

## League-specific notes for the checks

- kshoyer shares the best career regular-season record in league history with Tucker (level at
  40-23 after Week 3 of 2026); re-derive before quoting it.
- Contentful renders only headings, paragraphs, tables, lists, bold, italic, code and links;
  anything else in a draft silently disappears on publish.
