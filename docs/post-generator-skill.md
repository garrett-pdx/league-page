# Plan: the `mudd-post` skill

A project skill that drafts the three weekly blog posts described in [blog.md](blog.md).
**Not built yet.** This is the design so it can be picked up cold.

The goal is not "an AI writes the blog." It is: every number in a post is computed from
the league's own data, the writing is a thin layer on top, and nobody has to remember what
happened in week 6.

## Where it lives

`.claude/skills/mudd-post/SKILL.md`, committed to the repo. `.gitignore` deliberately
ignores only `.claude/worktrees/` and `.claude/settings.local.json` so skills stay shared —
if that ever widens back to `.claude/`, this skill silently stops being version controlled.

Invoked as `/mudd-post`, with the edition inferred from the current day and overridable:
`/mudd-post tuesday`, `/mudd-post friday`, `/mudd-post sunday`, plus `--week N --season YYYY`
for backfilling or testing against a finished season.

## The hard rule

**Every factual claim must come from a query, not from recall.** Scores, margins, bench
points, FAAB amounts, records, streaks — all computed, all traceable. The skill should
refuse to assert a number it did not derive. This is the single thing that determines
whether the posts are trustworthy, and it is also the failure mode a language model falls
into most naturally.

A concrete guard: the skill emits a `facts` block (JSON) first, then writes prose that may
only reference values present in that block. Easy to eyeball, easy to test.

## Data sources

In season, live Sleeper is authoritative for the current week; `static/data/` is
authoritative for history.

| Need | Source |
| --- | --- |
| Current week and season phase | `GET /v1/state/nfl` |
| This week's scores, rosters, per-player points | `GET /v1/league/{id}/matchups/{week}` |
| This week's adds/drops/FAAB, including failed bids | `GET /v1/league/{id}/transactions/{week}` |
| Current rosters and FAAB remaining | `GET /v1/league/{id}/rosters` |
| Player names, positions, teams | `static/data/players.json`, refreshed by the puller |
| Head-to-head history, all-time context | `static/data/weeks.json` |
| Records, final standings, champions | `static/data/league-history.json` |
| Keeper cost of a player being added | `static/data/keepers.json` |
| Ownership history ("he's been dropped three times") | `static/data/ownership.json` |
| Manager real names | `src/lib/utils/leagueInfo.js` |

Note `players.json` only contains players who have appeared in league history. A brand-new
waiver pickup will be missing until `scripts/pull-league-history.py` runs again — the skill
must fall back to `GET /v1/players/nfl` for unknown ids rather than printing a raw id.

## The computations worth building once

These are the recurring beats. Each should be a small, testable function, not prose
improvised per week.

- **Bench regret.** For each roster: highest-scoring benched player vs the lowest-scoring
  starter at a slot he was eligible for. Report the swap and the point delta.
- **Would it have mattered.** Recompute the matchup with the optimal legal lineup. The
  interesting cases are *lost while leaving enough on the bench to win* and *won despite
  leaving the most on the bench* — that second one is the funnier stat and nobody tracks it.
- **Streamers missed.** Free agents (rostered by nobody that week) who outscored a started
  player at the same position. Cross-reference `transactions` to see who *almost* had them.
- **Waiver outcomes.** Who bid, who won, what they paid, and — from `status: "failed"` —
  who wanted the same player and lost. Failed bids are the best content in the dataset and
  are invisible in Sleeper's own UI.
- **Roster holes.** Given `roster_positions` and current rosters, which teams are starting
  a player below replacement at a position, ranked. This is what turns a generic waiver
  list into "which manager needs them most."
- **Still alive.** For the Sunday post: starters whose NFL game has not finished, the
  current margin, and the points needed. Requires per-player game status, not just points.
- **Unlikely.** Margin percentiles against all 72 played weeks in `weeks.json`; flag
  results in the tails. "Third-closest game in league history" beats "a close one."

## Output

Draft to a file first — `drafts/<season>-w<week>-<edition>.md` — never straight to
publish. Publishing is a separate, explicit step.

Contentful's rich text is awkward to author programmatically. Two options, decide when
building: write Markdown for a human to paste, or use the Content Management API
(`VITE_CONTENTFUL_ACCESS_TOKEN`, already needed for comments) to create an unpublished
`blog_post` entry the commissioner reviews and publishes. The second is better if this is
going to run unattended; it also keeps the author field consistent.

## Voice

Dry, specific, short. The league is ten people who played college football together, so
the register is a group chat rather than a broadcast. Name managers by real name — they
are all in `leagueInfo.js` now. Never manufacture drama the numbers don't support; the
numbers are usually funnier. No jokes written by a person is the entire point of this
skill, but a bad joke is worse than none.

## Scheduling, later

Once the skill is reliable, `/loop` or a scheduled task can run it Tuesday, Friday and
Sunday night. Don't schedule it until a few weeks have been generated and read by a human
first — an unattended generator that quietly starts citing wrong numbers is worse than no
blog.

## Build order

1. The `facts` extractor for one edition (Tuesday is the richest and most forgiving).
2. Bench regret and "would it have mattered" — the two beats that make the post worth
   reading.
3. Prose layer with the facts-block constraint.
4. Friday and Sunday editions, which reuse most of the same computations.
5. Contentful publishing.
6. Scheduling.
