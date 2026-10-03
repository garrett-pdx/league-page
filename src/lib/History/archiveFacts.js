/*
"From the archives" on the Trophy Room (ArchiveCard.svelte). Ours, not upstream's.

HAND-WRITTEN, and every figure was re-derived from static/data/ when it was written -- never
copied from docs/league-lore.md or a bio. Re-check them all at the end of each season (the
end-of-season checklist in the root CLAUDE.md says so).

Rules these follow, so a 2026 week can never make one false:
  - completed seasons only (2022-2025), or a fixed historic event;
  - any "most" or "widest" is scoped "through 2025";
  - fantasy facts only, and none that simply repeats a manager bio's "Mudd League:" line.

Shape: { label, text, season, managers, source }
  label     the small kicker above the fact
  text      an array of segments, rendered in order:
              'plain string'
              { m: '<user_id>', label: 'Kabroa' }   -> link to that manager's page
              { season: 2022 }                       -> link to /seasons/2022
            Segments rather than an HTML string, so nothing here is {@html}-injected.
  season    the season(s) the fact belongs to
  managers  user_ids named in it (Sleeper user_id == managerID in leagueInfo.js)
  source    where the numbers come from, for the person re-checking them
*/

const GURRET = '76909640692416512';
const TNT44 = '611697269254791168';
const MIKESTREINZ = '605683461667229696';
const TUCKER = '611664340277383168';
const PAULSLAATS = '870570674836656128';
const JONAH = '612407006212468736';
const KSHOYER = '611630747161358336';
const BBROWN16 = '999190763323944960';
const KABROA = '611649934390870016';
const MALSTOL = '850475150817234944';

export const archiveFacts = [
    {
        label: 'Origins',
        text: [
            'The league was founded on ESPN in 2021 and takes its name from Claremont-Mudd-Scripps, where at least some of the managers played college football together. Only the 2021 draft made the move to Sleeper for ',
            { season: 2022 },
            ', and it priced that season\'s 18 keepers.',
        ],
        season: [2022],
        managers: [],
        source: 'league-history.json drafts.2022 (non-primary 15-round draft dated 2022-06-25); keepers.json 2022 (18 rows, baseline "carried-over prior-season draft")',
    },
    {
        label: 'Closest finish',
        text: [
            'The two closest games through 2025 both involved ',
            { m: KABROA, label: 'Kabroa' },
            '. He lost to ',
            { m: JONAH, label: 'jonahcartwright' },
            ' 111.84 to 111.80 in week 10 of ',
            { season: 2022 },
            ', and beat ',
            { m: TNT44, label: 'TnT44' },
            ' 95.80 to 95.58 in week 15 of ',
            { season: 2025 },
            '.',
        ],
        season: [2022, 2025],
        managers: [KABROA, JONAH, TNT44],
        source: 'games.json, every game kind, seasons 2022-2025: smallest |pf - pa| (0.04, then 0.22)',
    },
    {
        label: 'Left on the bench',
        text: [
            'In a week 17 consolation game in ',
            { season: 2022 },
            ', ',
            { m: KABROA, label: 'Kabroa' },
            ' scored 69.60 and left 69.78 on his bench, the most through 2025. His best lineup would have scored 139.38; ',
            { m: MIKESTREINZ, label: 'mikestreinz' },
            ' won with 117.70.',
        ],
        season: [2022],
        managers: [KABROA, MIKESTREINZ],
        source: 'games.json max_pf - pf, nulls skipped, seasons 2022-2025',
    },
    {
        label: 'Title run',
        text: [
            { m: MALSTOL, label: 'malstol' },
            ' won the ',
            { season: 2025 },
            ' title by 3.08 in the semifinal, 129.06 to 125.98 over ',
            { m: GURRET, label: 'Gurret' },
            ', and by 52.78 in the final, 139.28 to 86.50 over ',
            { m: TUCKER, label: 'tuckersdumbteam' },
            ', who had arrived on six straight wins.',
        ],
        season: [2025],
        managers: [MALSTOL, GURRET, TUCKER],
        source: 'games.json 2025 weeks 16-17 (kind "playoff"); tuckersdumbteam 2025 results, W in weeks 11-16',
    },
    {
        label: 'Keeper',
        text: [
            { m: KSHOYER, label: 'kshoyer' },
            ' kept Jalen Hurts at a 12th-round cost in ',
            { season: 2022 },
            ' and an 11th in ',
            { season: 2023 },
            ', and got 782.88 points out of him in 31 starts. The second year ended with the title.',
        ],
        season: [2022, 2023],
        managers: [KSHOYER],
        source: 'keepers.json cost_round (2022 R12, 2023 R11); weeks.json starter points in fixture weeks, 406.58 (16 starts) + 376.30 (15)',
    },
    {
        label: 'Draft',
        text: [
            { m: BBROWN16, label: 'BBrown16' },
            ' took Travis Etienne 74th overall in the ',
            { season: 2025 },
            ' draft, in round 8, and got 213.50 points from him in 15 starts.',
        ],
        season: [2025],
        managers: [BBROWN16],
        source: 'league-history.json drafts.2025 primary (pick_no 74, round 8, is_keeper false); weeks.json starter points in fixture weeks',
    },
    {
        label: 'Blowout',
        text: [
            { m: MIKESTREINZ, label: 'mikestreinz' },
            ' beat ',
            { m: GURRET, label: 'Gurret' },
            ' 168.12 to 78.28 in week 12 of ',
            { season: 2023 },
            '. The margin, 89.84, is the widest through 2025.',
        ],
        season: [2023],
        managers: [MIKESTREINZ, GURRET],
        source: 'games.json, every game kind, seasons 2022-2025: largest |pf - pa|',
    },
    {
        label: 'Waiver wire',
        text: [
            { m: PAULSLAATS, label: 'paulslaats' },
            ' spent $75 of his $100 FAAB on Trevor Lawrence the week of the ',
            { season: 2022 },
            ' final, the biggest winning bid through 2025. Lawrence started the final and scored 3.48; paulslaats won the title anyway.',
        ],
        season: [2022],
        managers: [PAULSLAATS],
        source: 'transactions.json status "complete", largest faab (2022-12-28, week 16 leg); weeks.json 2022 week 17 starters; league-history.json seasons.2022.waiver_budget',
    },
];
