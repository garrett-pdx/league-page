---
name: mudd-monday
description: Write and publish The Mudd Report's Monday edition for the league blog — the in-progress recap written before Monday Night Football, covering the weekend's results, the team of the week, lineup efficiency, benched points, schedule luck, injuries, and which managers still have players live in the Monday game. Use this whenever asked for the Monday post, the weekly recap, "write up this week", "how did everyone do", a Monday-night-still-alive rundown, or a recap while games are still outstanding. Handles the whole job end to end: pulls fresh data, drafts in the league's house voice, fact-checks every claim against Sleeper and league history, then publishes to Contentful.
---

# The Mudd Report — Monday edition

Written Monday, before the Monday night game. The hook is that the week **is not over**: some
matchups are decided, some are not, and specific people are sitting on specific players who can
still change their week. A post that reads like a settled recap has missed it.

**Target: a five-minute read** — about 1,150 words of prose at most, tables not counted. The
Week 2 2026 edition ran to ten minutes. Cut before you polish.

## Before drafting

1. **Get the numbers** with the `mudd-data` skill: `python3 scripts/week-facts.py <week> --live`.
   Read its `mudd-data` notes on `finished_*`, `best_benched` and `trailer_needs` before using
   any of them — each has been misread once.
2. **Confirm who is actually live.** A starter on 0.0 is ambiguous. Look up the real Monday
   game and check each named player is in it.
3. **Read `docs/mudd-voice.md`.** It defines the voice, and the rules that keep it honest.
4. **Get the history.** `--history` for superlatives; `--h2h` for any game worth a paragraph.

## Structure

```
# THE MUDD REPORT — WEEK N RECAP
*Monday <date> · <n> of <m> games final · <N> min read*

## THE SCOREBOARD
<one bold line per matchup, LIVE / decided / final; one sentence under each>

## <THE RIVALRY GAME, if designated rivals met — see below>

## TEAM OF THE WEEK — <manager>
## THE LOWLIGHT REEL
## LINEUP EFFICIENCY          <table: team / bench / eff%, worst last>
## SCHEDULE LUCK              <all-play table, then ROBBED and GOT AWAY WITH IT>
## THE INJURY WARD
## STILL ALIVE TONIGHT — <matchup, time>

---
<closing line>
```

No standfirst: the dateline and the scoreboard already say what the week was. Drop any section
the week didn't earn.

## What makes this edition land

**The still-alive section is the reason it's Monday.** Name the game, the players, the points
needed, and whether it's plausible. The trailer needs *strictly more* than the margin —
`trailer_needs` is margin + 0.01. If the leader also has someone in the game, that number is
only the floor: in Week 2 of 2026 malstol "needed 25.37 from Skattebo" while Kyren Williams was
still to play for paulslaats, so the real bar was Skattebo *beating Williams* by 25.37. When
three live games all run through one NFL game, say so; it's the best line of the night.

**Efficiency is the spine** — it separates bad luck from bad management, and this league cares
about it more than results. But **grade only finished slots**: for any team with a starter
still to play, use `finished_benched` / `finished_efficiency`, and say above the table that
unfinished slots aren't counted. Publishing the raw figures in Week 2 of 2026 charged five
managers for players who hadn't kicked off, and needed a correction.

**Never call a start/sit call a mistake without checking the ranks.** The optimal lineup is
hindsight. Kabroa's Week 2 2026 lineup was first written up as four bad calls; he had started
the higher-ranked player at every slot and his bench simply went off. "He got it right and was
punished for it" was the true story and the better one. See the market-rank source in
`mudd-data`.

**Schedule luck sorts the complaints.** A 6-3 all-play team that loses got robbed; a 2-7 team
that wins should keep quiet. Name both — and count carefully before calling a win "the
luckiest ever" (1-8 wins had happened nine times before).

**A rivalry game gets its own section.** Each manager's designated rival is in `leagueInfo.js`.
When two rivals meet, a one-line result undersells it. Give the series: the record, who has led
it and for how long, every margin (the ladder of margins in order is a strong device), the
biggest scores inside it, and where this result ranks — "the closest these two have ever
played" landed far better than "decided by 1.82".

**The injury ward is the one section with no data behind it.** Search for current news and
attribute it. Check QB depth from `rosters` when a quarterback goes down — "the only
quarterback on his roster" is a fact worth stating — and name real free-agent replacements.
Report actual injuries straight; the comedy belongs to lineup decisions.

**Tables: four columns at most**, read on a 375px phone. Keep names short in cells.

## Before publishing — the checks

**History check.** Every "most ever", "first time", "lowest since" gets verified against
`--history` or a direct query, counting from the full data. Unverifiable claims are cut, not
softened.

**Numbers check.** Re-run `week-facts.py` and confirm every figure in the draft still matches:
table cells, player scores, and whether each player was actually started or benched.

**Classes that break even when every number is right:**

- **Tense — its own pass.** Read the draft asking only *which games does this say are over?*
  For each, confirm the trailer has nobody left. The Week 2 2026 post called a man the winner of
  a game it had labelled LIVE, in four places: the standfirst, the lowlight reel, a section
  label ("GOT AWAY WITH IT") and the closing line. A live game is only ever *leading*, *ahead*,
  *on course*. The same goes for anything riding on a live score: a record, "top score of the
  week", "team of the week", "closest game of the week". Tucker took top score *and* team of the
  week off Jonah on that Monday night with one Davante Adams game. Labels and closing lines
  compress, and compression is where the hedge gets dropped.
- **Rankings** — "second-highest", "three of the five" — silently wrong after one more game.
- **Direction** — head-to-head records read fluently when reversed. Confirm who leads whom.
- **Counts** — compute them. Don't read them off a truncated leaderboard.
- **Player ownership** — confirm the player is on that roster now.

## Publishing

1. **Reading time, last.** After the final edit run
   `python3 scripts/reading-time.py docs/articles/<season>-w<week>-monday.md` and end the
   dateline with its `· N min read`. It counts prose only, tables excluded, at 230 words a
   minute rounded up. Corrections change the length, so never estimate before the checks.
2. **Title ends in `RECAP`.** `publish-article.mjs` matches on title to decide between updating
   and creating, and both editions share a week number. A bare `WEEK N` would silently overwrite
   the midweek `WEEK N PREVIEW`.
3. **Publish.**
   ```bash
   node scripts/publish-article.mjs docs/articles/<season>-w<week>-monday.md \
     --type Recap --author Gurret --featured --dry-run
   ```
   Check the block counts, then drop `--dry-run`. It updates in place on a title match.
   Republishing any other post: omit `--featured`, or it goes back on the home page.
4. **Unfeature the previous post.** `HomePost.svelte` shows the first `featured` entry and
   `getBlogPosts` requests no order, so two featured posts make the home page undefined.
5. **Verify live at phone width** — tables render as tables, no literal Markdown, and
   `document.documentElement.scrollWidth` equals `clientWidth`.

**Correcting a published post.** Fix the text, and if a published *fact* changed, add an italic
correction note at the bottom saying what it said and what's true. Trims and rewording need no
note. To rename a post, change the title on the entry through the management API — republishing
under a new title creates a duplicate and orphans the old entry.

## A note on timing

This post is a snapshot, and the dateline says so ("15 of 16 games final"). That stamp keeps it
honest later, but it also means **its numbers are never a source for anything written
afterwards**. The midweek preview re-derives everything from final data.
