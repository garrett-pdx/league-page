---
name: league-data
description: Refresh the league's dataset from Sleeper and produce the verified fact block for a week — scores, optimal lineups, benched points, efficiency, all-play records, rankings, head-to-head history and all-time leaderboards. Use this whenever you need current league numbers for any reason: before writing or publishing any league post, when asked "who's winning", "what did X score", "how many points did Y leave on the bench", "what's the head-to-head between A and B", "is that a record", or when league data looks stale. Also use it after a week completes to refresh and commit the dataset. league-recap and league-preview depend on this skill; run it first rather than querying Sleeper ad hoc.
---

# League data

Everything a post asserts has to come from here, and it has to be **re-derived at publish
time**: a number that was true when it was written is not the same thing as a number that is
true. Every wrong fact a league blog publishes was right at some earlier moment.

The league is whatever `league/league.json` names (`sleeperLeagueId`). Its own facts and quirks
are in `league/NOTES.md`; read that too.

## The fact block

```bash
python3 scripts/week-facts.py <week>              # human-readable table
python3 scripts/week-facts.py <week> --live       # also lists starters still on 0.0
python3 scripts/week-facts.py <week> --json       # machine-readable
python3 scripts/week-facts.py <week> --fixture D  # read matchups/rosters from D, no network
```

For each team: scored, optimal, benched, efficiency, all-play record, score rank. For each
game: margin, leader, what the trailer still needs. Plus the top started performances. The
optimal lineup is solved exactly for any roster shape (superflex, IDP, kickers, defenses, every
flex type) by `scripts/lineup.py`, the same solver the site uses.

**Fields that are easy to misread:**

- **`started` vs `optimal_lineup`.** `started` is who the manager played; `optimal_lineup` is
  the best legal lineup available. Writing "X started Y" off the optimal lineup invents a
  decision nobody made.
- **`best_benched` is not "players on the bench".** It is the best players the *optimal* lineup
  left out, which includes players started in the wrong slot. Never write "sat on his bench"
  from it; compare `started` with `optimal_lineup`.
- **`finished_benched` / `finished_efficiency`** grade only the slots whose player has finished.
  A starter whose game hasn't kicked off sits on 0.0, and the optimal lineup would swap him for
  any bench player who has already scored, charging the manager for a decision the week hasn't
  finished making. **For any team with a starter still to play, publish these instead of
  `benched` / `efficiency`.** With nobody pending they equal the regular figures exactly. The
  slot each pending player holds is read from Sleeper, never guessed.
- **`trailer_needs` is a floor when `leader_still_playing` is true.** Whatever the leader's
  pending players score raises the bar.
- **IR players are excluded from the optimal lineup**, since they couldn't legally start, but
  the IR list comes from *today's* rosters (see the traps).

The all-play record — what a team would be against everyone that week — is the number that
separates *beaten* from *unlucky*.

`--fixture` exists because Sleeper has no point-in-time endpoint: save `matchups.json` and
`rosters.json` into a directory to test against a past mid-week state. To rebuild a Monday after
the fact, zero **every** player on the Monday teams, bench included.

## History and fact-checking

```bash
python3 scripts/week-facts.py --h2h <handle A> <handle B>   # two separate arguments
python3 scripts/week-facts.py --history
```

`--history` prints all-time leaderboards: highest scores, highest losing scores, lowest scores,
most benched, closest finishes. Check every superlative against it, and count from the full data
rather than the printed top five: a count read off a truncated list is wrong more often than
not. `docs/league-lore.md` (from `npm run derive-narratives`) has ~300 more derived facts with
their definitions at the top.

`--h2h` gives the record, points each way and every meeting, including playoffs. It does not say
*which* meetings were playoff games. Before calling one a title game, a third-place game or a
consolation game, classify it from `static/data/league-history.json`:

- `brackets[season]["winners"]` / `["losers"]` hold the games. Round `r`'s week(s) depend on the
  season's `playoff_round_type` (0: one week per round from `playoff_week_start`; 1: the final
  is two weeks; 2: every round is two weeks), as `roundWeeks()` in `src/lib/Seasons/seasonData.js`
  computes. `t1`/`t2` are roster ids for that season.
- Winners bracket `p: 1` is the championship, `p: 3` third place, `p: 5` fifth. The losers bracket
  reuses `p`, so a `p: 1` there is never a final: with `playoff_type` 1 (consolation) it decides
  the place just after the playoff teams; with `playoff_type` 0 (toilet bowl) its `w` is the
  LOWER scorer and the game decides last place.

## Other sources worth knowing

- **Drafts and keepers:** `league-history.json` `drafts[season]` (every pick, `is_keeper`
  flagged; the `primary` draft is the season's own, a non-primary one is imported from another
  platform), and `keepers.json` (each keeper's cost and lineage).
- **Transaction history:** `static/data/transactions.json` keys adds and drops by **player id**,
  not name; count "the Nth time X has been on this roster" from the ids. **Filter
  `status == "complete"`**: failed waiver claims are recorded as adds too.
- **Unrostered players' production:**
  `https://api.sleeper.app/v1/stats/nfl/regular/<season>/<week>` returns every player's stat
  line. Its points use Sleeper's generic scoring, not this league's, so quote the stat line —
  catches, yards, touchdowns — never its points.
- **Weekly projections, for judging a start/sit call:**
  `python3 scripts/projections.py <week> "Player A" "Player B"` prints Sleeper's projection for
  that week rescored with this league's settings, and each player's projected rank at his
  position. This is what the manager saw when he set the lineup, so it is the fair test of
  whether a call was defensible. `--snapshot` saves the week's projections to
  `static/data/projections/` before kickoff; commit it, since Sleeper may not freeze old weeks.
- **The league's rules as Sleeper enforces them:** `python3 scripts/league-summary.py`.

## Refreshing the committed dataset

```bash
python3 scripts/pull-league-history.py    # Sleeper -> static/data/*.json (completed weeks only)
npm run derive-site-data                  # -> games.json + season-notes.json (the site's history pages)
npm run derive-narratives                 # -> narratives.json + docs/league-lore.md
```

Run it after a week completes and commit the diff (a scheduled GitHub Action can do this; see
`docs/setup.md`). The pages built on it show "through week N".

`derive-site-data` checks itself before writing anything: every record against Sleeper's, every
game mirrored, every week's best lineup at least what was scored. **A failure exits non-zero and
writes nothing** — that is a fault in the data or a format the engine doesn't handle, so read the
message rather than working around it. **Disagreements with Sleeper's settled figures** (a record
a game off, a season's potential points a few points out, usually a stat correction after
settlement or a player whose position has changed) are printed as warnings, with the
`league.json` override that would pin each one; `pipeline.strict` turns them into failures. A
records mismatch for the current season right after a week ends usually means Sleeper finalised
the week before its NFL calendar moved; re-pull later rather than editing anything.

`week-facts.py` reads live Sleeper for the current week, so a post doesn't strictly need the
pull, but `--history` reads only the committed files.

## Traps this data has sprung

Each of these has produced a wrong fact.

- **A mid-week pull must not commit a partial week.** The pull writes only weeks the NFL
  calendar has moved past (`nfl_state` in `league-history.json` records what it saw), so
  `--history` knows nothing about the week in progress. Use the live fact block for that week.
- **IR is read from today's rosters.** Recomputing a past week can count a player who was on IR
  *that* week and has since come off it. Don't re-quote a past week's efficiency from a later
  recompute without checking who was on IR then.
- **A scheduled-but-unplayed season looks completely real**: full rosters, genuine
  `matchup_id`s, every score 0.0. A season counts only once a point has been scored.
- **Every season carries an empty week 18** with `matchup_id: 0`. Treat a falsy `matchup_id` as
  "no fixture".
- **Keepers occupy draft slots.** Draft steals and busts must filter `is_keeper`.
- **Roster shape changes between seasons**; optimal-lineup maths reads `roster_positions` per
  season.
- **Median leagues** score a second result each regular-season week; `games.json` carries it in
  its `median` column and Sleeper's records include it. Head-to-head never does.
- **Orphaned rosters** (no owner) appear under a stand-in id `orphan-<season>-<roster>`.
- **`players.json` only holds players who have appeared in league history**; others fall back
  to the live `/players/nfl` dictionary (~5MB).

## Reading "who is still playing"

A game is flagged `MAYBE LIVE -- confirm` when the **trailing** team has a starter on exactly
0.0. That zero is ambiguous — a player whose game hasn't started, or one who played and scored
nothing — so **confirm each named player against the real NFL schedule**, and name the game.
The same ambiguity runs through `finished_*`: a starter who really finished on zero is treated
as pending, which flatters that manager. Confirm before publishing.

## Editing skill files

Don't write a dollar sign directly followed by a digit, or by the word ARGUMENTS, anywhere in a
SKILL.md: the skill loader treats those as argument placeholders and substitutes them. Write "29
dollars" or "a 29 bid" instead.
