---
name: mudd-monday
description: Write and publish The Mudd Report's Monday edition for the league blog — the in-progress recap written before Monday Night Football, covering the weekend's results, the team of the week, lineup efficiency, benched points, schedule luck, injuries, and which managers still have players live in the Monday game. Use this whenever asked for the Monday post, the weekly recap, "write up this week", "how did everyone do", a Monday-night-still-alive rundown, or a recap while games are still outstanding. Handles the whole job end to end: pulls fresh data, drafts in the league's house voice, fact-checks every claim against Sleeper and league history, then publishes to Contentful.
---

# The Mudd Report — Monday edition

Written Monday, before the Monday night game kicks off. The hook is that the week **is not
over**: some matchups are decided, one or two are not, and specific people are sitting on
specific players who can still change their season.

That tension is the whole edition. A post that reads like a settled recap has missed it.

## Before drafting

1. **Get the numbers.** Use the `mudd-data` skill:
   ```bash
   python3 scripts/week-facts.py <week> --live
   ```
   `--live` flags starters still on 0.0. Treat it as a lead, not a fact — it cannot tell a
   player whose game has not started from one who scored nothing. Confirm against the real NFL
   schedule and name the game.
2. **Read `docs/mudd-voice.md`.** It defines the voice and, more usefully, the moves that work.
3. **Check what's happened before.** `--history` and `--h2h` give the all-time context that
   turns a result into a story.

## Structure

Adapt to the week, but this shape has worked twice:

```
# THE MUDD REPORT — WEEK N RECAP
*Monday <date> · <n> of <m> games final · <N> min read*

<standfirst: the week in three clauses, one of them the live game>

---

## THE SCOREBOARD
<one line per matchup, bold, with LIVE or final; a sentence under each>

## TEAM OF THE WEEK — <manager>
<top score, efficiency, what they got right, one historical barb>

## THE LOWLIGHT REEL
<benched points, started zeros, the what-if that stings most>

## LINEUP EFFICIENCY
<table: scored / benched / efficiency, worst last -- four columns max, see below>

## SCHEDULE LUCK
<all-play table, then ROBBED and GOT AWAY WITH IT>

## THE INJURY WARD
<real injury news, who it hurts, waiver names worth a look -- needs outside sources, see below>

## STILL ALIVE TONIGHT — <matchup, time>
<who needs what from whom, and why it is or isn't likely>

---
<closing line>
```

## What makes this edition land

**The "needs" number.** For a live matchup, the trailing manager needs *strictly more* than
the margin — at two decimals that is margin + 0.01. `week-facts.py` computes `trailer_needs`
for exactly this. Getting it right is the difference between "needs 21.12" (a tie) and "needs
21.13" (a win).

**A pending starter is not a benching, and the optimal lineup cannot tell the difference.**
A starter whose game has not kicked off sits on 0.0, so `best_lineup` cheerfully replaces him
with any bench player who has already scored — and charges the manager for it. In Week 2 of
2026 this hit five of ten teams, and the entire 11.00 "benched" on tuckersdumbteam was Xavier
Worthy standing in for a receiver who had not played yet. Published as-is it read as a
judgement on a decision the week had not finished making.

On a Monday, grade only the slots whose player has finished: keep each pending starter in his
slot and optimise the rest over players who have actually played. Sanity-check the result —
every manager with nobody pending must come out unchanged, and if they don't, the calculation
is ignoring slot eligibility. Corrected, kshoyer went from 95.2% to a perfect 100%.

**Do not call a start/sit decision a mistake without checking the ranks.** The optimal lineup
is pure hindsight. It says nothing about whether a call was defensible when it was made, and a
post that treats the two as the same thing is just bullying whoever got unlucky. Check the
market before writing the barb — FantasyCalc values live in
`~/Desktop/ff_keeper/public/value-snapshot.json`, keyed by Sleeper id, and this league's config
is `numQbs=1, numTeams=10, ppr=0.5`.

Kabroa's Week 2 lineup was written up as four bad calls. He had in fact started the
higher-ranked player at all four slots — 49 over 147, 60 over 103, 86 over 177, 119 over 129 —
and his bench simply went off. "He got it right and was punished for it" is both the true
story and the better one.

**Efficiency is the spine.** Scored versus optimal is the one number that separates bad luck
from bad management, and this league's managers care about it more than the result. Order the
table worst-last so it ends on the disaster.

**Schedule luck sorts the complaints.** The all-play record tells you who was beaten and who
was merely unlucky. A team that goes 6-3 against the field and loses got robbed; a team that
goes 2-7 and wins should keep quiet. Both are worth naming.

**The injury ward is the one section with no data behind it.** Sleeper exposes `reserve` (who
is on IR) and nothing about why, and no committed file carries injury status or free-agent
availability. Everything else in this post is derived; this part needs real reporting -- search
for current injury news, and attribute it. If you cannot source it, write the IR moves you can
see from `rosters` and leave the speculation out.

**Keep tables to four columns.** `docs/mudd-voice.md` caps them there because these are read on
a 375px phone. For efficiency, scored / benched / efficiency is enough -- quote the optimal
figure in prose where it matters rather than adding a fifth column.

**The still-alive section is the reason it's Monday.** Name the game, the players, the points
needed, and whether it's plausible. If someone's own bench player is starting against them,
that's the story.

## Before publishing — the two checks

These are not optional, and the second one exists because it was learned the hard way.

**History check.** Every claim of the form "most ever", "first time", "league record", "worst
since" gets verified against `python3 scripts/week-facts.py --history` or a direct query over
`static/data/weeks.json`. If it cannot be verified, cut it. In the Week 1 post, a benched-points
record and a prior-year figure were both wrong — the record belonged to a different week and
the figure to a different manager.

**Fact check against final data.** Re-run `week-facts.py` immediately before publishing and
confirm every number in the draft still matches. Then walk the draft and check each of these
by hand, because they are the classes that break:

- **Rankings** — "second-highest", "fourth-best", "three of the five". These are right when
  written and silently wrong after one more game.
- **Direction** — head-to-head records read fluently when reversed. Confirm who leads whom.
- **Counts** — "four teams left points on the bench that would have changed the result" is a
  claim with an answer; compute it.
- **Player ownership** — check the player is actually on that roster now. Rosters churn.
- **Tense, and it is its own check.** Every number in the Week 2 2026 post verified — every
  score, every table cell, every ranking — and the post still said a man had *won* a matchup
  it had itself labelled **LIVE** four paragraphs earlier. A numeric check cannot catch this,
  because no number is wrong.

  So after the numbers pass, read the draft again asking only: *which games does this claim are
  over?* For each one, confirm the trailer has nobody left. That post asserted a win in four
  places — the standfirst ("won anyway"), the lowlight reel ("He won. He won because…"), a
  section label ("GOT AWAY WITH IT"), and the closing line ("Brenden **has** the lowest winning
  score in league history") — and a reader caught it.

  A live game is only ever *leading*, *ahead*, *on course*, or *could own by midnight*. The same
  applies to any record riding on a live score: provisional until the last player is off the
  field. Watch section labels and closing lines especially — both compress, and compression is
  where the hedge gets dropped.

## Publishing

**Add the reading time last.** After the final edit, run

```bash
python3 scripts/reading-time.py docs/articles/<season>-w<week>-monday.md
```

and put its figure at the end of the dateline, as `· N min read`. Do it after the fact check,
not before: corrections change the length, and a stale estimate is a small wrong number sitting
at the very top of the post. The script counts prose only -- tables are scanned, not read, so
their cells are left out -- at 230 words a minute, rounded up.

**The title must end in `RECAP`.** Both editions cover the same week number, and
`publish-article.mjs` matches on title to decide between updating and creating. Titling this
post `WEEK N` would silently overwrite the midweek `WEEK N PREVIEW` instead of publishing a
second post -- the live article would be replaced, with no warning and no second entry. The
two titles are:

| Edition | Title |
| --- | --- |
| Monday | `THE MUDD REPORT — WEEK N RECAP` |
| Midweek | `THE MUDD REPORT — WEEK N PREVIEW` |

```bash
node scripts/publish-article.mjs docs/articles/<season>-w<week>-monday.md \
  --type Recap --author Gurret --featured --dry-run
```

Dry run first to see the block counts and catch a conversion problem. Then drop `--dry-run`.
It updates in place if a post with that title already exists, so re-running after an edit
corrects the live post rather than duplicating it.

Then **unfeature the previous week's post**, or the home page has two featured posts to choose
between and picks whichever Contentful returns first. `HomePost.svelte` takes the first
`featured` entry it sees and `getBlogPosts` requests no explicit order, so this is genuinely
undefined rather than merely untidy.

Afterwards, confirm on the live site that the tables rendered as tables and nothing arrived as
literal Markdown.

## A note on timing

This post is a snapshot and should say so in the standfirst ("15 of 16 games final"). That
stamp is what makes it honest later — but it also means **its numbers are never a source for
anything written afterwards**. The midweek preview re-derives everything from final data.
