---
name: mudd-preview
description: Write and publish The Mudd Report's midweek edition for the league blog — written Wednesday or Thursday before the next NFL week kicks off, covering how Monday night settled the previous week, the waiver and FAAB results, the current standings, a preview of every upcoming matchup with its head-to-head history, and which managers have players in the Thursday night game. Use this whenever asked for the midweek post, the week-ahead preview, "preview next week", "who plays who", a waiver-wire writeup, a Thursday-night exposure rundown, or a recap once the previous week is fully final. Handles the whole job: pulls fresh data, drafts in the league's house voice, fact-checks every claim against final data and league history, then publishes to Contentful.
---

# The Mudd Report — midweek edition

Written Wednesday or Thursday, after the previous week is final and before the next one
starts. Three jobs: **settle** last week, **report** the waiver aftermath, **preview** what's
coming, ending on the Thursday night game. Where the Monday edition trades on suspense, this
one trades on consequence.

**It must be published before Thursday kickoff** — the Thursday section is worthless after. If
it's late, still do the whole job, but check the clock before promising "tonight".

**Target: a five-minute read** — about 1,150 words of prose at most, tables not counted. The
Week 3 2026 preview went out at 1,420 words of prose, which was too long; the trimmed version
is 880. One paragraph per matchup preview.

## Before drafting

1. **Refresh the dataset, then re-derive last week from final data** (`mudd-data` skill):
   ```bash
   python3 scripts/pull-league-history.py && npm run derive-narratives
   python3 scripts/week-facts.py <last_week>
   ```
   The pull replaces the partial week a Monday pull committed. **Never reuse figures from the
   Monday post** — Monday night moves scores, and one moved score reorders every ranking built
   on it. The Week 2 2026 preview reused them and shipped ten wrong claims.
2. **Waivers**, for both the finished week and the upcoming one — claims usually land in the
   finished week's bucket:
   ```bash
   curl -s "https://api.sleeper.app/v1/league/1312235880743706624/transactions/<week>"
   ```
   **Failed bids are the best content in the dataset**: they show who wanted a player and lost.
   Then find the story behind the contested player: who drafted him and when he was cut
   (`draft-2026.json`, `transactions.json`), and what he's done since (the stats endpoint in
   `mudd-data` — quote stat lines, not its points).
3. **Standings and FAAB** from `/rosters` — refetch *after* waivers run, or everyone shows
   nothing spent.
4. **Head-to-head for every upcoming game:** `week-facts.py --h2h <A> <B>`. Classify any old
   playoff meeting from the brackets before describing it (`mudd-data` has the method).
5. **The Thursday game and who's exposed.** Sleeper has no schedule endpoint: look up the real
   TNF game, then check each roster's *current* week starters (`/matchups/<next_week>`) for
   players on either team. Starters, not just rostered players.
6. **Read `docs/mudd-voice.md`** before writing prose.

## Structure

```
# THE MUDD REPORT — WEEK N PREVIEW
*<day> <date> · Week N-1 in the books · <TNF game and time> · <N> min read*

## MONDAY NIGHT SETTLED IT
<what the live games needed and got; records that became final>
### The cruelest thing that happened to anybody
<the single worst beat, with the what-if arithmetic>

## THE WAIVER WIRE
<contested claim as a table, the story behind it, then the other moves in a line each>

## THE TABLE
<standings table: team / W-L / PF; two sentences on what's misleading about it>

## WEEK N
<optional one-line hook that runs across several games>
### <matchup> — <angle>
<one paragraph: record, then current form, then what's at stake>

## THURSDAY NIGHT — <matchup, time>
<table of who starts whom; one or two storylines>

---
<closing line>
```

No standfirst — the dateline and first section do that job.

## What makes this edition land

**A bidding war is a story, and the best one is usually in the history.** paulslaats paying 29
dollars for Denzel Boston was a bid; paulslaats paying 29 dollars for a receiver he had drafted
and cut for nothing three weeks earlier was the lead of the waiver section. Check the draft and
the transaction log for every contested player.

**Previews need history or they're just a schedule.** Lead with the record, then form, then
stakes. Records you'd put in a headline — "the highest score in league history came in this
fixture" — are worth the history query.

**Say plainly when a fact is about the past.** "The three highest scores in league history were
all posted in fixtures being played this week" read as though they'd been posted this week.
Name the year and the pairing: "Streinz scored 193.04 against TnT44 in 2023."

**Rivalry games get their own section.** When designated rivals (`leagueInfo.js`) meet, give
the series properly: record, who has led it and for how long, the margins, the biggest scores
inside it.

**The cruelest beat needs the ranks, not just the arithmetic.** A bench player who would have
won the game only indicts the manager if starting him was a defensible call at the time. Check
the market ranks (`mudd-data`) before writing it as a mistake; when the manager made the
sensible call and lost anyway, that's the crueler story.

**Thursday exposure matters when it's one-sided.** Say how many managers start someone
tonight, and whether any of their opponents do. Lineups change until lock: re-check them
immediately before publishing and stamp the table "as of Thursday afternoon".

**Early standings are misleading, and that's the point.** Two sentences, not a paragraph.

## Before publishing — the checks

**History check.** Every superlative against `--history`, counted from full data.
Unverifiable claims are cut.

**Numbers check.** Re-run `week-facts.py` and check the draft line by line. Then the classes
that break even when every number is right:

- **Counts in a category — count them all.** The Week 3 2026 draft called two teams "the only
  unbeaten teams" when three were 2-0, said four managers had a Monday-night starter when five
  did, and called kshoyer the best of the winless teams when he had the fewest points of the
  three.
- **"Nth time" claims** — count from `transactions.json` by player id. "Goff's third stint on
  Gurret's roster" was a second.
- **Direction** — the Week 2 2026 preview had the league's highest scorer facing "the only team
  that has ever handled him" when he was 5-1 *over* them. Confirm who leads every series.
- **Rankings, efficiency, benched points** — all move on Monday night. Recompute.
- **Roster membership and FAAB** — confirm against a post-waiver `/rosters` fetch.
- **Tense** — last week is final; this week hasn't happened. Anything about Thursday is "as of".

## Publishing

1. **Reading time, last:** `python3 scripts/reading-time.py docs/articles/<season>-w<week>-preview.md`,
   and end the dateline with `· N min read`. Prose only, tables excluded, 230 words a minute
   rounded up. Re-run after every edit.
2. **Title ends in `PREVIEW`.** `publish-article.mjs` matches on title, and both editions share
   a week number; a bare `WEEK N` would silently overwrite the Monday `WEEK N RECAP`.
3. **Publish.**
   ```bash
   node scripts/publish-article.mjs docs/articles/<season>-w<week>-preview.md \
     --type Recap --author Gurret --featured --dry-run
   ```
   Check the block counts, then drop `--dry-run`. Republishing any other post: omit
   `--featured`.
4. **Unfeature the previous post** — `HomePost.svelte` shows the first `featured` entry, and
   `getBlogPosts` requests no order.
5. **Verify live at phone width**: tables render, no literal Markdown, no horizontal scroll.

**Correcting a published post:** fix it, and add an italic correction note at the bottom when a
published fact changed. Trims and rewording need no note. Rename through the management API,
never by republishing under a new title.
