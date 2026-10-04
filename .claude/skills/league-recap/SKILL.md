---
name: league-recap
description: Write and publish the league blog's weekly recap — the in-progress Monday edition written before Monday Night Football, covering the weekend's results, the team of the week, lineup efficiency, benched points, schedule luck, injuries, and which managers still have players live in the Monday game. Use this whenever asked for the Monday post, the weekly recap, "write up this week", "how did everyone do", a Monday-night-still-alive rundown, or a recap while games are still outstanding. Handles the whole job end to end: pulls fresh data, drafts in the league's house voice, fact-checks every claim against Sleeper and league history, then publishes.
---

# The weekly recap (Monday edition)

Written Monday, before the Monday night game. The hook is that the week **is not over**: some
matchups are decided, some are not, and specific people are sitting on specific players who can
still change their week. A post that reads like a settled recap has missed it.

The blog's name, title format, draft location, author and category for this edition are in
`league/voice.md`. If that file is missing or doesn't cover something, ask the commissioner
rather than inventing it.

**Target: a five-minute read**, about 1,150 words of prose at most, tables not counted. Cut
before you polish.

## Before drafting

1. **Get the numbers** with the `league-data` skill: `python3 scripts/week-facts.py <week> --live`.
   Read its notes on `finished_*`, `best_benched` and `trailer_needs` before using any of them.
2. **Confirm who is actually live.** A starter on 0.0 is ambiguous. Look up the real Monday game
   and check each named player is in it.
3. **Read `docs/writing.md`, then `league/voice.md`.** The first is the craft; the second is
   this league's voice, names and running bits.
4. **Read the last two published posts** in the drafts directory. Their stories are spent: a
   story gets one full telling, and after that a single line only if it has a new consequence.
5. **Get the history:** `--history` for superlatives, `--h2h` for any game worth a paragraph.

## Structure

```
# <TITLE, as league/voice.md sets it>
*<day> <date> · <n> of <m> games final · <N> min read*

## THE SCOREBOARD
<one bold line per matchup, LIVE / decided / final; one sentence under each>

## <THE RIVALRY GAME, if designated rivals met>

## TEAM OF THE WEEK — <manager>
## THE LOWLIGHT REEL
## LINEUP EFFICIENCY          <table: team / bench / eff%, worst last>
## SCHEDULE LUCK              <all-play table, then ROBBED and GOT AWAY WITH IT>
## THE INJURY WARD
## STILL ALIVE TONIGHT — <matchup, time>

---
<closing line>
```

Drop any section the week didn't earn. In a best-ball league, lineup efficiency is always 100%:
drop that section. In a median league, say who won or lost their median game too.

## What makes this edition land

**The still-alive section is the reason it's Monday.** Name the game, the players, the points
needed, and whether it's plausible. The trailer needs *strictly more* than the margin
(`trailer_needs` is margin + 0.01). If the leader also has someone in the game, that number is
only the floor: the real bar is the trailer's player *beating the leader's* by the margin. When
several live games run through one NFL game, say so; it's the best line of the night.

**Efficiency separates bad luck from bad management.** But **grade only finished slots**: for
any team with a starter still to play, use `finished_benched` / `finished_efficiency`, and say
above the table that unfinished slots aren't counted.

**Never call a start/sit call a mistake without checking that week's projections**
(`scripts/projections.py`). The optimal lineup is hindsight. A manager who started every
projected pick and was beaten by his own bench got it right and was punished for it; that is the
true story and the better one.

**Schedule luck sorts the complaints.** A team with a strong all-play record that loses got
robbed; a weak all-play team that wins should keep quiet. Name both, and count carefully before
calling anything "the luckiest ever".

**A rivalry game gets its own section.** Each manager's designated rival is `rival.userId` in
`league/league.json`. When two rivals meet, give the series: the record, who has led it and for
how long, every margin (the ladder of margins in order is a strong device), the biggest scores
inside it, and where this result ranks.

**The injury ward is the one section with no data behind it.** Search for current news and
attribute it. Check depth from `rosters` when a starter goes down, and name real free-agent
replacements. Report injuries straight; the comedy belongs to lineup decisions.

## Before publishing: the checks

**History check.** Every "most ever", "first time", "lowest since" is verified against
`--history` or a direct query, counting from the full data. Unverifiable claims are cut.

**Repetition check.** `python3 scripts/repeat-check.py <draft>` lists every figure and every
six-word phrase the draft shares with the previous two posts (prose only). A callback with a new
consequence stays; a re-telling goes. Shared phrases should be zero.

**Numbers check.** Re-run `week-facts.py` and confirm every figure still matches: table cells,
player scores, and whether each player was actually started or benched.

**Classes that break even when every number is right:**

- **Tense — its own pass.** Read the draft asking only *which games does this say are over?*
  For each, confirm the trailer has nobody left. A live game is only ever *leading*, *ahead*,
  *on course* — and so is anything riding on a live score: a record, "top score of the week",
  "team of the week". Labels and closing lines compress, and compression is where the hedge
  gets dropped.
- **Rankings** — "second-highest", "three of the five" — silently wrong after one more game.
- **Direction** — head-to-head records read fluently when reversed. Confirm who leads whom.
- **Counts** — compute them. Don't read them off a truncated leaderboard.
- **Player ownership** — confirm the player is on that roster now.

## Publishing

1. **Reading time, last.** After the final edit, `python3 scripts/reading-time.py <draft>` and end
   the dateline with its `· N min read` (prose only, 230 words a minute, rounded up).
2. **Publish** with the author, category and featured flag from `league/voice.md`:
   ```bash
   node scripts/publish-article.mjs <draft> --type <category> --author <sleeper username> --featured --dry-run
   ```
   Check the output, then drop `--dry-run`.
   - **Markdown blog** (`blog.backend` "markdown"): this writes `league/posts/<slug>.md`.
     Commit and push it; the deploy publishes it. Re-running with the same slug updates it.
   - **Contentful**: this creates the entry, or updates the one whose title matches.
   The home page shows the newest featured post, so the previous one needs no unfeaturing.
3. **Verify live at phone width**: tables render as tables, no literal Markdown, and
   `document.documentElement.scrollWidth` equals `clientWidth`.

**Correcting a published post.** Fix the text and republish; if a published *fact* changed, add
an italic correction note at the bottom saying what it said and what's true. Rewording needs no
note. Don't change a published post's slug: it is a URL people have shared.

## A note on timing

This post is a snapshot, and the dateline says so ("15 of 16 games final"). That keeps it honest
later, but it also means **its numbers are never a source for anything written afterwards**.
The midweek preview re-derives everything from final data.
