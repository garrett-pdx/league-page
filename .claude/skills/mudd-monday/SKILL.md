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
# THE MUDD REPORT — WEEK N
*Monday <date> · <n> of <m> games final*

<standfirst: the week in three clauses, one of them the live game>

---

## THE SCOREBOARD
<one line per matchup, bold, with LIVE or final; a sentence under each>

## TEAM OF THE WEEK — <manager>
<top score, efficiency, what they got right, one historical barb>

## THE LOWLIGHT REEL
<benched points, started zeros, the what-if that stings most>

## LINEUP EFFICIENCY
<table: scored / optimal / benched / efficiency, worst last>

## SCHEDULE LUCK
<all-play table, then ROBBED and GOT AWAY WITH IT>

## THE INJURY WARD
<real injury news, who it hurts, waiver names worth a look>

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

**Efficiency is the spine.** Scored versus optimal is the one number that separates bad luck
from bad management, and this league's managers care about it more than the result. Order the
table worst-last so it ends on the disaster.

**Schedule luck sorts the complaints.** The all-play record tells you who was beaten and who
was merely unlucky. A team that goes 6-3 against the field and loses got robbed; a team that
goes 2-7 and wins should keep quiet. Both are worth naming.

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

## Publishing

```bash
node scripts/publish-article.mjs docs/articles/<season>-w<week>-monday.md \
  --type Recap --author Gurret --featured --dry-run
```

Dry run first to see the block counts and catch a conversion problem. Then drop `--dry-run`.
It updates in place if a post with that title already exists, so re-running after an edit
corrects the live post rather than duplicating it.

Afterwards, confirm on the live site that the tables rendered as tables and nothing arrived as
literal Markdown.

## A note on timing

This post is a snapshot and should say so in the standfirst ("15 of 16 games final"). That
stamp is what makes it honest later — but it also means **its numbers are never a source for
anything written afterwards**. The midweek preview re-derives everything from final data.
