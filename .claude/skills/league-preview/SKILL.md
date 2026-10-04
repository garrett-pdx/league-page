---
name: league-preview
description: Write and publish the league blog's midweek preview — written Wednesday or Thursday before the next NFL week kicks off, covering the waiver and FAAB results, the current standings, a preview of every upcoming matchup with its head-to-head history, and which managers have players in the Thursday night game. Use this whenever asked for the midweek post, the week-ahead preview, "preview next week", "who plays who", a waiver-wire writeup, a Thursday-night exposure rundown, or a recap once the previous week is fully final. Handles the whole job: pulls fresh data, drafts in the league's house voice, fact-checks every claim against final data and league history, then publishes.
---

# The midweek preview

Written Wednesday or Thursday, after the previous week is final and before the next one starts.
It looks **forward**: the waiver aftermath, the standings, a preview of every game, ending on
the Thursday night game.

The blog's name, title format, draft location, author and category for this edition are in
`league/voice.md`. If something isn't covered there, ask rather than invent.

**It does not recap last week.** The Monday edition already did, and most readers read both. If
a Monday result changes a story going forward (a record now within reach, a team falling to
0-3), it gets one clause inside the preview it affects. Last week can still supply a lead, but
only a story no post has told.

**It must be published before Thursday kickoff**; the Thursday section is worthless after.

**Target: a five-minute read**, about 1,150 words of prose at most, tables not counted. One
paragraph per matchup.

## Before drafting

1. **Refresh the dataset, then re-derive last week from final data** (`league-data` skill):
   ```bash
   python3 scripts/pull-league-history.py && npm run derive-site-data && npm run derive-narratives
   python3 scripts/week-facts.py <last_week>
   ```
   **Never reuse figures from the Monday post**: Monday night moves scores, and one moved score
   reorders every ranking built on it.
2. **Waivers**, for both the finished week and the upcoming one (claims usually land in the
   finished week's bucket): `https://api.sleeper.app/v1/league/<sleeperLeagueId>/transactions/<week>`.
   **Failed bids are the best content in the dataset**: they show who wanted a player and lost.
   Find the story behind a contested player: who drafted him and when he was cut (the drafts in
   `league-history.json`, `transactions.json`), and what he has done since (quote stat lines).
3. **Standings and FAAB** from `/rosters`, refetched *after* waivers run.
4. **Head-to-head for every upcoming game:** `week-facts.py --h2h <A> <B>`. Classify any old
   playoff meeting from the brackets before describing it (`league-data` has the method).
5. **The Thursday game and who's exposed.** Sleeper has no schedule endpoint: look up the real
   TNF game, then check each roster's *current* week starters (`/matchups/<next_week>`) for
   players on either team. Starters, not just rostered players.
6. **Snapshot the coming week's projections** before Thursday kickoff and commit the file:
   `python3 scripts/projections.py <next_week> --snapshot`.
7. **Read `docs/writing.md`, then `league/voice.md`.**
8. **Read the last two published posts**, especially the Monday recap, which covered the same
   week. Its stories are spent.

## Structure

```
# <TITLE, as league/voice.md sets it>
*<day> <date> · Week N-1 in the books · <TNF game and time> · <N> min read*

## <AN UNTOLD STORY FROM LAST WEEK, if there is one — fresh heading every week>
## THE WAIVER WIRE
<contested claim as a table, the story behind it, then the other moves in a line each>
## THE TABLE
<standings table: team / W-L / PF; two sentences on what's misleading about it>
## WEEK N
### <matchup> — <angle>
<one paragraph: record, then current form, then what's at stake>
## THURSDAY NIGHT — <matchup, time>
<table of who starts whom; one or two storylines>

---
<closing line>
```

In a league with divisions, the table groups or marks them; in a median league, the record is
Sleeper's (median results included) and the text says so.

## What makes this edition land

**A bidding war is a story, and the best one is usually in the history.** A manager paying big
for a player he drafted and cut for nothing three weeks earlier is the lead of the waiver
section. Check the draft and the transaction log for every contested player.

**Previews need history or they're just a schedule.** Lead with the record, then form, then
stakes.

**Say plainly when a fact is about the past.** Name the year and the pairing.

**Rivalry games get their own section** (`rival.userId` in league.json): record, who has led it
and for how long, the margins, the biggest scores inside it.

**A what-if needs that week's projections, not just the arithmetic.** A bench player who would
have won the game only indicts the manager if starting him was a defensible call at the time.

**Thursday exposure matters when it's one-sided.** Say how many managers start someone tonight,
and whether their opponents do. Lineups change until lock: re-check immediately before publishing
and stamp the table "as of Thursday afternoon".

**Early standings are misleading, and that's the point.** Two sentences, not a paragraph.

## Before publishing: the checks

**History check.** Every superlative against `--history`, counted from full data. Unverifiable
claims are cut.

**Repetition check.** `python3 scripts/repeat-check.py <draft>`: aim for zero shared figures and
zero shared phrases. A shared figure survives only inside a genuinely new story; a Monday result
restated with its outcome is a recap and goes.

**Numbers check.** Re-run `week-facts.py` and check the draft line by line. Then:

- **Counts in a category — count them all.** "The only unbeaten teams" when there were three.
- **"Nth time" claims** — count from `transactions.json` by player id.
- **Direction** — confirm who leads every series.
- **Rankings, efficiency, benched points** — all move on Monday night. Recompute.
- **Roster membership and FAAB** — confirm against a post-waiver `/rosters` fetch.
- **Tense** — last week is final; this week hasn't happened. Anything about Thursday is "as of".

## Publishing

1. **Reading time, last:** `python3 scripts/reading-time.py <draft>`; end the dateline with
   `· N min read`. Re-run after every edit.
2. **Publish** with the author, category and featured flag from `league/voice.md`:
   ```bash
   node scripts/publish-article.mjs <draft> --type <category> --author <sleeper username> --featured --dry-run
   ```
   Check the output, then drop `--dry-run`. Markdown blog: commit and push the
   `league/posts/<slug>.md` it writes. Contentful: it creates or updates the entry.
3. **Verify live at phone width**: tables render, no literal Markdown, no horizontal scroll.

**Correcting a published post:** fix it, republish, and add an italic correction note at the
bottom when a published fact changed.
