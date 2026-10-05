# The Mudd League: notes for agents

This league's facts, decisions and quirks. The engine's own guide is the root `CLAUDE.md`; this
file is everything specific to the Mudd League. Facts here were true when written; re-derive any
number from `static/data/` before quoting it.

## The site

- **Live at [muddleague.site](https://muddleague.site)** (bought through Vercel, which runs its
  DNS); `mudd-league.vercel.app` serves the same site, so old links still work. Every push to
  `master` deploys.
- **Displayed as "The Mudd League."** Sleeper names it "Mudd Keeper League"; the display name
  deliberately differs. Don't "correct" it to match the API.
- The name traces to **Claremont-Mudd-Scripps**, where at least some of the managers played
  college football together. Founded in 2021 on ESPN, moved to Sleeper for 2022; the founding
  year is on the seal, in the home page and in the constitution — keep them in step.
- **Blog:** The Mudd Report, on Contentful with the read-only delivery token. Comments are off
  (the league doesn't want them, and the management token that writing them needs must never
  be a `VITE_` variable). `CONTENTFUL_MANAGEMENT_TOKEN`, used only by `publish-article.mjs`, lives
  only in the local `.env`, never in Vercel. Voice and publishing details: `league/voice.md`.
  Drafts of every published post are in `league/drafts/`.
- **The home page copy was approved by Garrett on 2026-10-03.**
- **Optional manager fields are unset** (`favoriteTeam`, `preferredContact`, `fantasyStart`,
  `philosophy`, `tradingScale`, `favoritePlayer`, `valuePosition`); the managers have been asked
  for them (`docs/site-todo.md`). Unset fields are simply hidden.
- **Rivals** are five pairings from a maximum-weight matching over head-to-head history
  (frequency, closeness, stakes); `scripts/suggest-rivals.py` reproduces three of the five with
  its default weights, and the configured ones stand. Jordan Leonard's rival is "The Field".
- `pipeline.strict` is on: this league pins every disagreement with Sleeper in `overrides`.

## The league (verified against the Sleeper API 2026-08-09)

- 10 teams. Keeper league, **not dynasty**. Scoring 0.5 PPR, 6-point passing TDs. Starters QB,
  RB, RB, WR, WR, TE, FLEX, FLEX; 5 bench, 2 IR (6 bench through 2025; the league voted 7–3 to cut
  it, and the draft from 14 rounds to 13, for 2026). Playoffs: 4 teams from week 16; a
  consolation bracket decides 5th–8th. FAAB, a 100-dollar budget. Trade deadline week 12.
- Sleeper league IDs, newest first (the site needs only the current one):
  | Season | League ID |
  | --- | --- |
  | 2026 (current) | `1312235880743706624` |
  | 2025 | `1257452519521517570` |
  | 2024 | `1124503476031041536` |
  | 2023 | `982140218121711616` |
  | 2022 (first) | `819042960179077120` |
- **Champions:** 2022 `paulslaats`, 2023 `kshoyer`, 2024 `BBrown16`, 2025 `malstol`.
- **Keepers:** 2 per team. Cost = the round the player was drafted last year, +1 round of
  inflation when the *same manager* keeps him again, undrafted players cost the final round
  (`keepers.rule` in league.json). Two rules the league decided in the constitution that the
  keeper draft board predates: when two keepers owe the same round the *manager chooses* which
  moves up, and draft picks trade **one for one**.
- **The same-round collision rule diverges from the keeper draft board on purpose.** The board
  resolves it by player rank (its own `CLAUDE.md` calls that a tool-author guess). Garrett has
  accepted the divergence — the board is a planning aid, the constitution governs — so don't
  "fix" the board to match, and don't file it as a bug.

## Managers (`managerID` / `userId` is the Sleeper `user_id`, never a roster ID)

| Roster | Handle | user_id | Team name (2026-10-03) |
| --- | --- | --- | --- |
| 1 | Gurret (Garrett — repo owner / commissioner) | `76909640692416512` | Slim Pickens 👱‍♀️💋🎀✨ |
| 2 | TnT44 | `611697269254791168` | — |
| 3 | mikestreinz | `605683461667229696` | Tupac on da bench |
| 4 | tuckersdumbteam | `611664340277383168` | — |
| 5 | paulslaats | `870570674836656128` | Street Clothes |
| 6 | jonahcartwright | `612407006212468736` | StepBurrow I'm Stuck |
| 7 | kshoyer | `611630747161358336` | — |
| 8 | BBrown16 | `999190763323944960` | Straight Miss Pissles |
| 9 | Kabroa | `611649934390870016` | #FREEJT |
| 10 | malstol | `850475150817234944` | Ben's Beautiful Johnsons |

Team names are a snapshot; the site reads them live.

- **One former manager.** `JJJet` (`860365948673204224`) is **Jordan Leonard**: 2022 only, 5-10,
  9th, replaced by `BBrown16` in 2023. Listed last in `managers`; the Managers page puts him in
  the Moratorium automatically.
- `Football_Team` (`612343067143389184`) is **not** a former manager: in the 2022 user list but
  never held a roster. The engine filters never-rostered accounts out on its own.
- **The hand-maintained 2025 standings had 5th and 6th swapped** (BBrown16 won the consolation
  final over mikestreinz). The keeper draft board still carries the swapped copy in
  `~/Desktop/ff_keeper/src/ui/rosters.ts`; fix it there, or have it read `final_standings`.

## Bios: where the numbers come from

Every manager's bio is built from their `cmsathletics.org` roster page, at Garrett's direction.

- **The school's site contradicts itself**: prose bio copy and Statistics tables disagree.
  League policy, set by Garrett: when they conflict, use whichever sounds better — but the
  number must appear somewhere on the school's own page; never invent a third.
- **Two facts confirmed by Garrett that the source can't back up:** `Kabroa` is Kanoa
  Gilliland, and Jonah Cartwright attended **Harvey Mudd** (the CMS site has it wrong). Don't
  rewrite either against the website.
- Scraping those pages needs the browser: the Statistics tab (`#ui-id-3`) populates
  client-side, so a plain fetch reports no statistics. Offensive linemen genuinely have empty
  career tables.
- Each active bio's "Mudd League:" line is a fantasy fact scoped to "2022 to 2025"; extend the
  scope at season's end. Malcolm's bio says "Reigning champion." — true only until the next
  title game.

## The history dataset

- **2022 has two drafts on the same league, and one isn't a 2022 draft.** The 14-round draft of
  2022-09-04 is the real season draft (`primary`). The 15-round one dated 2022-06-25 is the 2021
  ESPN draft, imported (`history.preSleeper[0].importedDraftId`); it's the baseline 2022's
  keeper costs price against. Only that draft survives of 2021: no standings, results or
  champion.
- **71 of 75 keepers match the cost rules exactly.** The four that don't: DeVonta Smith 2024
  (tuckersdumbteam, R8 held instead of inflating to R7), De'Von Achane 2024 (BBrown16, R13 rather
  than R11), Amon-Ra St. Brown 2025 (mikestreinz, R4 — inflated despite a change of manager) and
  Brian Thomas 2025 (jonahcartwright, R7 rather than R9). Probably commissioner adjustments;
  ask before treating them as precedent.
- **One commissioner override:** 2024 week 8, tuckersdumbteam 137.74 v BBrown16 122.54
  (computed 150.34 to 148.74). Official scores use the override.
- **Pinned corrections** (`overrides` in league.json): two post-settlement stat corrections
  (2023 jonahcartwright v Gurret, 2024 Kabroa v tuckersdumbteam), and the positions Sleeper
  allowed Taysom Hill (TE in 2022, QB/TE from 2023) and Travis Hunter (WR in 2025). With them,
  all 50 manager-seasons reproduce Sleeper's potential points to the cent.
- `static/data/draft-2026.json` (`all_picks`: round, pick and manager) and `docs/draft-2026.md`
  come from the one-off `scripts/derive-draft-report.py`.
- Projection snapshots in `static/data/projections/` start at Week 4 2026 (captured Thursday
  4:18 PT). **Sleeper does rewrite past weeks' projections**: by Monday of Week 4, almost every
  player's Week 4 projection had drifted from the Thursday snapshot, and players hurt on Sunday
  (Barkley, Chase, McConkey) had been reset to 0. Grade start/sit calls from the snapshot.

## Companion project (different repo, different purpose)

`~/Desktop/ff_keeper` → [garrett-pdx/keeper-draft-board](https://github.com/garrett-pdx/keeper-draft-board),
live at <https://garrett-pdx.github.io/keeper-draft-board/>: a separate Vite/TypeScript app for
the keeper draft (keeper cost maths, ADP, the draft board). It has its own `CLAUDE.md`. The two
projects share a league, not a codebase; don't copy code between them. The site links to it from
`links` in league.json (the League menu and /resources) and from `home.md` and the constitution.

## Season-specific checklist items

- **Preseason:** swap the 4for4 FAAB guide in `links.elsewhere` (its URL is the season's own
  article, so it goes stale every year).
- **End of season:** besides the `league-season` skill's steps, update the Champions line above
  and the career figures in `league/voice.md`.

## Other docs in this repo about this league

`docs/site-todo.md`, `docs/revamp-log.md`, `docs/plan-site-todo.md`, `docs/plan-history-pages.md`,
`docs/blog.md`, `docs/post-generator-skill.md`, `docs/draft-2026.md`, and `docs/league-lore.md`
(generated). `docs/plan-open-source.md` is the plan for turning this site into the open-source
template.
