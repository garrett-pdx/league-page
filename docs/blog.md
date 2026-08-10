# The Mudd League blog

Three posts a week, written against the league's own data. This file is the spec for
what each post contains and what it takes to turn the blog on.

## Status: blocked on Contentful

`enableBlog` in `src/lib/utils/leagueInfo.js` is still `false`. Upstream's blog reads from
[Contentful](https://contentful.com) — there is no file-based post option in the template —
so the account has to exist before the flag can flip. The free tier covers this easily.

**Setup, once:**

1. Create a free Contentful account and a space.
2. Add a content model with ID **`blog_post`**. Upstream's field spec is in
   [TRAINING_WHEELS.md](../TRAINING_WHEELS.md#iii-add-a-blog) — follow it exactly, the IDs
   are matched by string. Use each author's **Sleeper username** in the author field.
3. Add a second content model with ID **`blog_comment`**, fields `blogID`, `comment`,
   `author` (`src/routes/api/addBlogComments/[id]/+server.js` writes exactly these).
4. Create two API keys: a **Content Delivery** token (read) and a **Content Management**
   token (write — needed only for comments).
5. Set three environment variables locally in a gitignored `.env`, and in Vercel's project
   settings for production:
   - `VITE_CONTENTFUL_SPACE`
   - `VITE_CONTENTFUL_CLIENT_ACCESS_TOKEN` (delivery)
   - `VITE_CONTENTFUL_ACCESS_TOKEN` (management)
6. Flip `enableBlog = true`.

The Blog tab is already hidden while the flag is false (`NavLarge.svelte:122`,
`NavSmall.svelte:75`), so nothing is broken in the meantime.

## The three weekly posts

### Tuesday — the recap

Last week, settled. Scores, and then the things people actually argue about.

- Final scores and margins; the blowout and the nail-biter.
- **Start/sit decisions made.** Who benched a player who outscored their starter, by how
  much, and whether it cost them the matchup.
- **What could have happened.** Optimal lineup vs actual, per team: who would have won on
  a different lineup, and who won *despite* leaving the most on the bench.
- **Streamers missed.** Free agents who outscored rostered starters at the same position.
- The unlikely thing that happened anyway.
- Top news and injuries.
- **Waiver prospects, and which manager needs them most** — matched against each roster's
  actual hole, not a generic top-10 list.

### Friday — Thursday recap and the week ahead

- Thursday night result and what it did to the matchups already in progress.
- **Who got the waivers they needed** and what they paid; who got outbid.
- Who still has an empty or injured starting slot heading into Sunday.
- The fantasy matchups to watch, and the NFL games that decide them.

### Sunday night — after the late games

- Every fantasy matchup, summarised.
- **Who still has players left**, and exactly what they need on Monday to win or lose.
- Anything already mathematically settled.

## Most of this is derivable, and that matters

Three posts a week is roughly 150 a year. Hand-writing all of it will not survive
October. The good news is that `static/data/` plus the live Sleeper API already answers
most of the recurring questions mechanically:

| Post element | Source |
| --- | --- |
| Scores, margins, per-player points | `weeks.json`, or live `/matchups/{week}` |
| Bench points vs starter points | `players_points` minus `starters_points` |
| Optimal lineup, "what could have happened" | `potential_points` vs `points_for` |
| Who got which waiver, and for how much | `transactions.json` / live transactions |
| Failed bids — who wanted a player and lost | transactions with `status: "failed"` |
| Roster holes by position | roster + `roster_positions` |
| Head-to-head history for a matchup | `weeks.json`, all seasons |
| Keeper implications of an add | `keepers.json` |

Not derivable from Sleeper: NFL news and injuries (the `/api/fetch_serverside_news` feed
covers some), the NFL schedule for "which games to watch", and every actual joke.

The sane split is a generator that drafts the factual skeleton — scores, bench regrets,
FAAB spend, who needs what — leaving the commentary to a person. That is a real build and
has not been started; it is not required to launch the blog.
