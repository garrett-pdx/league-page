---
name: mudd-preview
description: Write and publish The Mudd Report's midweek edition for the league blog — written Wednesday or Thursday before the next NFL week kicks off, covering how Monday night settled the previous week, the waiver and FAAB results, the current standings, a preview of every upcoming matchup with its head-to-head history, and which managers have players in the Thursday night game. Use this whenever asked for the midweek post, the week-ahead preview, "preview next week", "who plays who", a waiver-wire writeup, a Thursday-night exposure rundown, or a recap once the previous week is fully final. Handles the whole job: pulls fresh data, drafts in the league's house voice, fact-checks every claim against final data and league history, then publishes to Contentful.
---

# The Mudd Report — midweek edition

Written Wednesday or Thursday, after the previous week is completely final and before the next
one starts. It does three jobs in one piece: **settle** last week, **report** the waiver
aftermath, and **preview** what's coming, ending on the Thursday night game.

The previous week is closed here. Where the Monday edition trades on suspense, this one trades
on consequence — what the results actually did to everyone, and who has to answer for it.

## Before drafting

1. **Re-derive last week from final data.** Use the `mudd-data` skill:
   ```bash
   python3 scripts/week-facts.py <last_week>
   ```
   **Do not reuse figures from the Monday post.** Monday night moves scores, and moving one
   score reorders every ranking built on it. This is the single most important instruction in
   this skill; see the fact check below for what it cost.
2. **Pull the waiver results.**
   ```bash
   curl -s "https://api.sleeper.app/v1/league/1312235880743706624/transactions/<week>"
   ```
   Waivers run after the week's games, so claims for the upcoming week usually land in the
   *previous* week's bucket. Check both. Each has `type` (waiver / free_agent / trade),
   `status` (complete / failed) and `settings.waiver_bid`.
   **Failed bids are the best content in the dataset** — they show who wanted a player and
   lost, which is invisible in Sleeper's own UI.
3. **Get the upcoming schedule and standings.**
   ```bash
   curl -s "https://api.sleeper.app/v1/league/1312235880743706624/matchups/<next_week>"
   curl -s "https://api.sleeper.app/v1/league/1312235880743706624/rosters"
   ```
   Rosters carry `settings.waiver_budget_used` for remaining FAAB — refetch after waivers run,
   because a stale snapshot shows everyone at $0 spent.
4. **Get head-to-head history for every upcoming matchup.**
   ```bash
   python3 scripts/week-facts.py --h2h <A> <B>
   ```
5. **Find the Thursday game and who is exposed.** Sleeper has no schedule endpoint, so look up
   the actual TNF matchup for that week, then scan rosters for players on either team and note
   who is starting them.
6. **Read `docs/mudd-voice.md`** before writing a word of prose.

## Structure

```
# THE MUDD REPORT — WEEK N PREVIEW
*<day> <date> · Week N-1 in the books · <TNF matchup and time>*

<standfirst: three clauses, ending on the matchup that matters most>

---

## MONDAY NIGHT SETTLED IT
<how the live games resolved; who needed what and got or didn't get it>

### The cruelest thing that happened to anybody
<the single worst beat of the week, with the what-if arithmetic>

## THE WAIVER WIRE
<the contested claim as a table; then the cheap ones; total FAAB spent>

## THE TABLE
<standings: W-L and points for>

## WEEK N
### <matchup> — <angle>
<history, current form, what's at stake; one sub-section per game>

## THURSDAY NIGHT — <matchup, time>
<table of who is starting whom; then the storylines inside the game>

---
<closing line>
```

## What makes this edition land

**A bidding war is a story.** Who bid, who won, what they paid, and who lost — as a table. The
gap between the winning and losing bid says something about both managers.

**Previews need history or they're just a schedule.** A matchup feels inevitable when you know
one manager is 5-1 in it and has outscored the other by 116 points. Lead with the record, then
current form, then what's at stake.

**The rivalry games carry extra weight.** Each manager has a designated rival in
`leagueInfo.js`, set from real head-to-head data. Those matchups get named as such.

**Thursday exposure is genuinely useful.** Six of ten managers having a starter in one game
matters, and when both sides of an upcoming matchup have a player in it, the week effectively
starts Thursday. Say so.

**Early standings are misleading and that's the point.** A 1-0 team with the lowest winning
score and a 0-1 team with the fourth-best score are both worth naming.

## Before publishing — the two checks

**History check.** Verify every superlative against
`python3 scripts/week-facts.py --history`. "Best losing score in league history" was written
once and was actually *fourteenth* — the record belonged to someone else entirely, and that
someone turned out to be the better story anyway. Unverifiable claims get cut, not softened.

**Fact check against final data.** This edition's defining failure mode, stated plainly: the
Week 2 2026 post reused Week 1 figures from the Monday post. Monday night had moved them.
**Ten claims were wrong**, and a reader caught it before the writer did.

So re-run `week-facts.py` and check the draft against it line by line:

- **Rankings above all.** "Second-highest scorer", "fourth-best score", "three of the five
  losing teams" — every one of these changed after Monday night. Recompute each.
- **Direction.** That post's intro sent the league's highest scorer into a game against "the
  only team that has ever handled him" when he was in fact 5-1 *over* them. Reversed records
  read perfectly and are completely false.
- **Efficiency and benched points move too.** A bench player scoring on Monday night changes
  the optimal lineup, and therefore the benched total.
- **Roster membership.** Confirm a player is on the roster you're attributing him to. One post
  put a running back on a manager's bench a week after he'd been dropped.
- **FAAB.** Refetch rosters; a pre-waiver snapshot reports everyone at full budget.

## Publishing

**The title must end in `PREVIEW`.** Both editions cover the same week number, and
`publish-article.mjs` matches on title to decide between updating and creating. Titling this
post `WEEK N` would silently overwrite the Monday `WEEK N RECAP` rather than publish a second
post. The two titles are:

| Edition | Title |
| --- | --- |
| Monday | `THE MUDD REPORT — WEEK N RECAP` |
| Midweek | `THE MUDD REPORT — WEEK N PREVIEW` |

```bash
node scripts/publish-article.mjs docs/articles/<season>-w<week>-preview.md \
  --type Recap --author Gurret --featured --dry-run
```

Dry run, check the block counts, then publish without the flag. It updates in place on a title
match, so corrections go to the live post instead of creating a second copy.

Then **unfeature the previous post** -- `HomePost.svelte` takes the first `featured` entry and
`getBlogPosts` requests no explicit order, so leaving two featured makes the home page
undefined rather than merely untidy.

Then verify on the site: tables rendered as tables, no literal Markdown, and — because this is
read on phones — no horizontal scrolling. Keep cells short; numeric columns don't wrap.
