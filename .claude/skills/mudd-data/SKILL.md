---
name: mudd-data
description: Refresh the Mudd League dataset from Sleeper and produce the verified fact block for a week — scores, optimal lineups, benched points, efficiency, all-play records, rankings, head-to-head history and all-time leaderboards. Use this whenever you need current league numbers for any reason: before writing or publishing any league post, when asked "who's winning", "what did X score", "how many points did Y leave on the bench", "what's the head-to-head between A and B", "is that a record", or when league data looks stale. Also use it after a week completes to commit the refreshed dataset. Both mudd-monday and mudd-preview depend on this skill; run it first rather than querying Sleeper ad hoc.
---

# Mudd League data

Everything a post asserts has to come from here, and it has to be **re-derived at publish
time**: a number that was true when it was written is not the same thing as a number that is
true. Every wrong fact this blog has published was right at some earlier moment.

## The fact block

```bash
python3 scripts/week-facts.py <week>              # human-readable table
python3 scripts/week-facts.py <week> --live       # also lists starters still on 0.0
python3 scripts/week-facts.py <week> --json       # machine-readable
python3 scripts/week-facts.py <week> --fixture D  # read matchups/rosters from D, no network
```

For each team: scored, optimal, benched, efficiency, all-play record, score rank. For each
game: margin, leader, what the trailer still needs. Plus the top started performances.

**Fields that have each been misread once:**

- **`started` vs `optimal_lineup`.** `started` is who the manager played; `optimal_lineup` is
  the best legal lineup available. Writing "X started Y" off the optimal lineup invents a
  decision nobody made.
- **`best_benched` is not "players on the bench".** It is the best players the *optimal*
  lineup left out, which includes players who were started in the wrong slot. Never write "sat
  on his bench" from it; compare `started` with `optimal_lineup`.
- **`finished_benched` / `finished_efficiency`** grade only the slots whose player has
  finished. A starter whose game hasn't kicked off sits on 0.0, and the optimal lineup swaps
  him for any bench player who has already scored — charging the manager for a decision the
  week hasn't finished making. **For any team with a starter still to play, publish these
  instead of `benched` / `efficiency`.** The text output prints them in their own block. With
  nobody pending they equal the regular figures exactly. The slot each pending player holds is
  read from Sleeper, never guessed: a hand calculation that assumed Kyren Williams was in an RB
  slot, when he was in FLEX, put a wrong number in the Week 2 2026 recap.
- **`trailer_needs` is a floor when `leader_still_playing` is true.** Whatever the leader's
  pending players score raises the bar; the text output says so under the game.
- **IR players are excluded from the optimal lineup**, since they couldn't legally start — but
  the IR list comes from *today's* rosters (see traps).

The all-play record — what a team would be against everyone that week — is the number that
separates *beaten* from *unlucky*, and most of what a weekly post argues about.

`--fixture` exists because Sleeper has no point-in-time endpoint. To test against a past
mid-week state, save `matchups.json` and `rosters.json` into a directory. To rebuild a Monday
after the fact, zero **every** player on the two Monday teams, bench included — zeroing only the
pending starters leaves their bench teammates' Monday points in the pool.

## History and fact-checking

```bash
python3 scripts/week-facts.py --h2h Gurret mikestreinz   # two separate arguments
python3 scripts/week-facts.py --history
```

`--history` prints all-time leaderboards: highest scores, highest losing scores, lowest scores,
most benched, closest finishes. Check every superlative against it, and count from the full
data rather than the printed top five: "eight managers have won at 1-8" was written off a
truncated list, and the true answer was nine times, by six managers.

`--h2h` gives the record, points each way and every meeting, including playoffs. It does not
say *which* meetings were playoff games. Before calling one a title game, third-place game or
consolation game, classify it from `static/data/league-history.json`:

- `brackets[season]["winners"]` / `["losers"]` hold the games; round `r` is played in week
  `playoff_week_start + r - 1` (16 and 17 in every season so far), and `t1`/`t2` are roster
  ids — get each manager's roster id for that week from `weeks.json`.
- Winners bracket `p: 1` is the championship and `p: 3` the third-place game. The losers bracket
  reuses `p`, so a `p: 1` there is a consolation placement game, not a final. Getting that
  wrong once turned a fifth-place game into a "title game".

## Other sources worth knowing

- **Who drafted a player:** `static/data/draft-2026.json`, `all_picks` — round, pick and
  manager. It made the Week 3 2026 preview's best story: a manager paying 29 FAAB dollars for a
  receiver he had drafted and cut for nothing.
- **Transaction history:** `static/data/transactions.json` keys adds and drops by **player
  id**, not name. Count "the Nth time X has been on this roster" from the ids — a
  "third stint" was published that was really a second.
- **Unrostered players' production:**
  `https://api.sleeper.app/v1/stats/nfl/regular/<season>/<week>` returns every player's stat
  line. Its points use Sleeper's generic half-PPR, not this league's scoring (six-point passing
  touchdowns), so quote the stat line — catches, yards, touchdowns — never its points.
- **Market ranks, for judging a start/sit call:**
  `~/Desktop/ff_keeper/public/value-snapshot.json` (FantasyCalc, keyed by Sleeper id; use the
  `numQbs=1, numTeams=10, ppr=0.5` entry). It is a preseason snapshot, so say "ranked Nth in
  August", not "ranked Nth".

## Refreshing the committed dataset

```bash
python3 scripts/pull-league-history.py    # rewrites static/data/*.json
npm run derive-narratives                 # rebuilds narratives.json + docs/league-lore.md
```

Run it after a week completes and commit the diff; it also picks up in-season rookies, who
otherwise print as raw ids. `week-facts.py` reads live Sleeper for the current week, so a post
doesn't strictly need the pull — but `--history` reads only the committed files.

## Traps this data has already sprung

Each of these produced a wrong fact once.

- **A mid-week pull commits a partial week.** Pulled on a Monday, `weeks.json` holds the
  current week with Monday's players on 0.0, and `--history` treats those scores as final. Any
  superlative touching the current week is provisional until it's re-pulled after Monday night.
- **IR is read from today's rosters.** Recomputing a past week can count a player who was on IR
  *that* week and has since come off it — Alec Pierce's 8.10 from BBrown16's Week 1 2026 IR slot
  re-entered his optimal lineup when the week was recomputed later. Don't re-quote a past
  week's efficiency from a later recompute without checking who was on IR then.
- **A scheduled-but-unplayed season looks completely real** — ten rosters, genuine
  `matchup_id`s, every score 0.0. `season_played()` requires a point to have been scored.
- **Every season carries a fictional week 18** with `matchup_id: 0`. Treat falsy `matchup_id`
  as "no fixture".
- **Keepers occupy draft slots.** Draft steals and busts must filter `is_keeper`.
- **Roster shape changes between seasons** (14 spots in 2025, 13 in 2026); optimal-lineup maths
  reads `roster_positions` per season.
- **`players.json` only holds players who have appeared in league history**; others fall back
  to the live `/players/nfl` dictionary (~5MB).

## Reading "who is still playing"

A game is flagged `MAYBE LIVE -- confirm` when the **trailing** team has a starter on exactly
0.0. That zero is ambiguous — it is equally a player whose game hasn't started and one who
played and scored nothing — so **confirm each named player against the real NFL schedule**,
and name the game. In Week 1 of 2026 all five games were flagged and two were already over.

The same ambiguity runs through `finished_*`: a starter who really did finish on zero is
treated as pending, which flatters that manager. Confirm before publishing.

## Editing these skill files

Don't write a dollar sign directly followed by a digit or by the word ARGUMENTS anywhere in a
SKILL.md. The skill loader treats those as argument placeholders and substitutes them, so
"everyone at [dollar-zero] spent" once rendered as "everyone at Week spent". Write "29 dollars"
or "a 29 bid" instead.
