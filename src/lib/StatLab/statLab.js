/*
Stat Lab's data layer: datasets, measures, presets and the URL scheme. Pure -- no Svelte, no
fetch -- so Node can import it and check its numbers directly:

    node --input-type=module -e "import * as s from './src/lib/StatLab/statLab.js'; ..."

Everything is computed from games.json (through leagueGames.js) plus league-history.json's
final_standings, so every number here agrees with Standings, Rivalry and the Seasons pages.

THE PIPELINE
    annotateGames(games)   once per load: every row gains its week's all-play record and its
                           expected wins, scored against EVERY team that played that week. Done
                           on whole weeks, before any filter, which is the rule allPlay() states:
                           never filter by manager first.
    filterGames(...)       the user's filters; the annotation rides along on each row.
    buildRows(...)         one row per game, per manager-season, or per manager career. Summing
                           the annotated rows gives all-play and luck for exactly the games kept,
                           so a Seasons row on regular-season weeks equals allPlay() on that season.

URL SCHEME (every control; defaults are left out, so a bare /stat-lab is the default view)
    ds      games | seasons | managers                     dataset          (seasons)
    m       measure key, see MEASURES                       the measure      (per dataset)
    x       measure key                                     scatter x axis   (pf, or pa when m=pf)
    chart   bar | line | scatter | dist                    chart            (bar)
    type    regular | playoffs | all                        game type        (regular)
    season  2024,2025                                       seasons          (all)
    mgr     gurret,kabroa  -- Sleeper handles, lowercased   managers         (all)
    opp     malstol                                         opponents        (any)
    wk      1-14, 5-, -3                                    week range       (all)
    sort    a column key                                    table sort       (the measure)
    dir     asc | desc                                      sort direction   (the measure's own)
    top     10 | 25 | all                                   bars shown       (10)
    min     a game count, 0 = show everything               minimum games    (derived: defaultMin())
            Seasons and Careers only. Absent means "the default for this view", which is worked out
            from the data (see defaultMin), so it is never written down; any other value, including
            0, is written.
*/
import { filterGames, allPlay } from '../utils/helperFunctions/leagueGames.js';

export const DATASETS = [
    { value: 'games', label: 'Games', one: 'one team’s score in one week' },
    { value: 'seasons', label: 'Seasons', one: 'one manager’s season' },
    { value: 'managers', label: 'Careers', one: 'one manager’s career' },
];

export const CHARTS = [
    { value: 'bar', label: 'Bar' },
    { value: 'line', label: 'Line' },
    { value: 'scatter', label: 'Scatter' },
    { value: 'dist', label: 'Distribution' },
];

export const GAME_TYPES = [
    { value: 'regular', label: 'Regular', kinds: ['regular'] },
    { value: 'playoffs', label: 'Playoffs', kinds: ['playoff', 'placement'] },
    { value: 'all', label: 'All', kinds: null },
];

const ALL = ['games', 'seasons', 'managers'];
const AGG = ['seasons', 'managers'];

/*
fmt:    pts (2 dp) | pct (1 dp) | signed (2 dp, always signed) | int | place
low:    true where a smaller number is better (the default sort runs ascending)
diverge: signed measures, drawn either side of zero
*/
export const MEASURES = {
    pf:         { label: 'Points for', short: 'PF', fmt: 'pts', ds: ALL,
                  desc: 'Points scored. Seasons and careers add up every game kept by the filters.' },
    pa:         { label: 'Points against', short: 'PA', fmt: 'pts', ds: ALL,
                  desc: 'Points the opponent scored.' },
    margin:     { label: 'Margin', short: 'Margin', fmt: 'signed', ds: ALL, diverge: true,
                  desc: 'Points for minus points against.' },
    ppg:        { label: 'Points per game', short: 'PPG', fmt: 'pts', ds: AGG,
                  desc: 'Points for divided by games played, so a short season compares fairly.' },
    winPct:     { label: 'Win %', short: 'Win %', fmt: 'pct', ds: AGG,
                  desc: 'Wins, with a tie as half a win, over games played.' },
    allPlayPct: { label: 'All-play %', short: 'All-play', fmt: 'pct', ds: ALL,
                  desc: 'The record against every team that played that week, not just the opponent. For one game, the share of the other teams outscored.' },
    luck:       { label: 'Luck', short: 'Luck', fmt: 'signed', ds: AGG, diverge: true,
                  desc: 'Real wins minus the wins the all-play record says were earned. Positive means the schedule helped.' },
    sd:         { label: 'Spread (SD)', short: 'SD', fmt: 'pts', ds: AGG,
                  desc: 'The standard deviation of weekly scores. High is boom or bust; low is steady.' },
    maxPf:      { label: 'Max points', short: 'Max', fmt: 'pts', ds: ALL,
                  desc: 'The best legal lineup from the whole roster. Matches Sleeper’s potential points to the cent. Not counted for the 2024 week 8 commissioner-override game.' },
    bench:      { label: 'Bench points', short: 'Bench', fmt: 'pts', ds: ALL,
                  desc: 'Max points minus points scored: what a perfect lineup would have added.' },
    eff:        { label: 'Lineup efficiency', short: 'Eff.', fmt: 'pct', ds: ALL,
                  desc: 'Points scored as a share of max points. 100% is a perfect lineup.' },
    finish:     { label: 'Final place', short: 'Finish', fmt: 'place', ds: ['seasons'], low: true,
                  desc: 'Where the season ended, from the playoff brackets. Blank for a season still being played.' },
    titles:     { label: 'Titles', short: 'Titles', fmt: 'int', ds: ['managers'],
                  desc: 'Championships won in the selected seasons.' },
};

export const DEFAULT_MEASURE = { games: 'pf', seasons: 'winPct', managers: 'winPct' };

export const measuresFor = (ds) =>
    Object.entries(MEASURES).filter(([, m]) => m.ds.includes(ds)).map(([key, m]) => ({ key, ...m }));

/**
 * A distribution needs several values per manager: games (one dot a week) or seasons (one dot a
 * season). A career is one value per manager, so there is nothing to spread; and a final place
 * or a title count is a handful of integers stacked on each other, which says nothing a bar
 * doesn't.
 */
export const distOk = (ds, m) => ds !== 'managers' && !['finish', 'titles'].includes(m);

export const chartsFor = (ds, m) =>
    CHARTS.map((c) => ({
        ...c,
        disabled: (c.value === 'line' && ds === 'managers') || (c.value === 'dist' && !distOk(ds, m)),
    }));

/* ---- formatting -------------------------------------------------------------------------- */

const MINUS = '−';
const ORD = ['th', 'st', 'nd', 'rd'];
const ordinal = (n) => {
    const v = n % 100;
    return `${n}${ORD[(v - 20) % 10] || ORD[v] || ORD[0]}`;
};

export const fmt = (value, kind) => {
    if(value === null || value === undefined || Number.isNaN(value)) return '—';
    switch(kind) {
        case 'pts':
            return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        case 'pct':
            return `${(value * 100).toFixed(1)}%`;
        case 'signed': {
            const v = Math.round(value * 100) / 100;
            if(v === 0) return '0.00';
            return `${v > 0 ? '+' : MINUS}${Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }
        case 'place':
            return ordinal(value);
        default:
            return String(value);
    }
};

export const fmtMeasure = (value, key) => fmt(value, MEASURES[key]?.fmt);

export const record = (w, l, t) => (t ? `${w}-${l}-${t}` : `${w}-${l}`);

/* ---- annotation -------------------------------------------------------------------------- */

/**
 * Give every row its week's all-play record and expected wins. Uses allPlay() one week at a
 * time over every team that played that week -- ten in a regular-season week, eight in a
 * playoff week (the two teams outside both brackets sit it out).
 */
export const annotateGames = (games) => {
    const weeks = new Map();
    for(const g of games) {
        const key = `${g.season}-${g.week}`;
        if(!weeks.has(key)) weeks.set(key, []);
        weeks.get(key).push(g);
    }
    const out = [];
    for(const rows of weeks.values()) {
        const byUser = {};
        for(const e of allPlay(rows)) byUser[e.user_id] = e;
        for(const g of rows) {
            const e = byUser[g.user_id];
            const n = e.allPlayWins + e.allPlayLosses + e.allPlayTies;
            out.push({
                ...g,
                apW: e.allPlayWins,
                apL: e.allPlayLosses,
                apT: e.allPlayTies,
                expected: e.expectedWins,
                allPlayPct: n ? (e.allPlayWins + e.allPlayTies / 2) / n : null,
            });
        }
    }
    return out;
};

/* ---- datasets ---------------------------------------------------------------------------- */

const round2 = (n) => Math.round(n * 100) / 100;

const gameRow = (g) => {
    const hasMax = g.max_pf !== null && g.max_pf !== undefined;
    return {
        id: `${g.season}-${g.week}-${g.user_id}`,
        user_id: g.user_id,
        season: g.season,
        week: g.week,
        opponent_id: g.opponent_id,
        gameKind: g.kind,
        result: g.result,
        pf: g.pf,
        pa: g.pa,
        margin: round2(g.pf - g.pa),
        apW: g.apW, apL: g.apL, apT: g.apT,
        allPlayPct: g.allPlayPct,
        maxPf: hasMax ? g.max_pf : null,
        bench: hasMax ? round2(g.max_pf - g.pf) : null,
        eff: hasMax && g.max_pf ? g.pf / g.max_pf : null,
    };
};

const aggregate = (rows) => {
    let wins = 0, losses = 0, ties = 0, pf = 0, pa = 0, apW = 0, apL = 0, apT = 0, expected = 0;
    let lineupGames = 0, lineupPf = 0, maxPf = 0;
    const scores = [];
    const seasons = new Set();
    for(const g of rows) {
        if(g.result === 'W') wins++;
        else if(g.result === 'L') losses++;
        else ties++;
        pf += g.pf;
        pa += g.pa;
        apW += g.apW; apL += g.apL; apT += g.apT;
        expected += g.expected;
        scores.push(g.pf);
        seasons.add(g.season);
        if(g.max_pf !== null && g.max_pf !== undefined) {
            lineupGames++;
            lineupPf += g.pf;
            maxPf += g.max_pf;
        }
    }
    const games = rows.length;
    const mean = games ? pf / games : null;
    // population SD: the spread of the scores actually played, not an estimate of anything
    const sd = games > 1 ? Math.sqrt(scores.reduce((s, x) => s + (x - mean) ** 2, 0) / games) : null;
    const apN = apW + apL + apT;
    return {
        games, wins, losses, ties,
        pf: round2(pf), pa: round2(pa), margin: round2(pf - pa),
        ppg: mean,
        winPct: games ? (wins + ties / 2) / games : null,
        apW, apL, apT,
        allPlayPct: apN ? (apW + apT / 2) / apN : null,
        expected,
        luck: games ? wins + ties / 2 - expected : null,
        sd,
        maxPf: lineupGames ? round2(maxPf) : null,
        bench: lineupGames ? round2(maxPf - lineupPf) : null,
        eff: lineupGames && maxPf ? lineupPf / maxPf : null,
        seasonCount: seasons.size,
        seasonSet: seasons,
    };
};

const placeOf = (history, season, uid) =>
    history?.final_standings?.[String(season)]?.find((p) => p.user_id === uid)?.place ?? null;

/**
 * The filtered table for a dataset. `games` must already be annotated.
 * Rows carry `id`, `user_id`, the dataset's identity fields, and every measure.
 */
export const buildRows = (games, history, state) => {
    const kinds = GAME_TYPES.find((t) => t.value === state.type)?.kinds ?? null;
    const kept = filterGames(games, {
        seasons: state.season,
        managers: state.mgrIds,
        kinds,
        weekRange: state.wk,
        opponent: state.oppIds,
    });

    if(state.ds === 'games') return kept.map(gameRow);

    const groups = new Map();
    for(const g of kept) {
        const key = state.ds === 'seasons' ? `${g.season}-${g.user_id}` : g.user_id;
        if(!groups.has(key)) groups.set(key, []);
        groups.get(key).push(g);
    }

    const out = [];
    for(const [key, rows] of groups) {
        const a = aggregate(rows);
        const uid = rows[0].user_id;
        if(state.ds === 'seasons') {
            const season = rows[0].season;
            const { seasonSet, ...rest } = a;
            out.push({ id: key, user_id: uid, season, ...rest, finish: placeOf(history, season, uid) });
        } else {
            const { seasonSet, ...rest } = a;
            let titles = 0;
            for(const s of seasonSet) if(placeOf(history, s, uid) === 1) titles++;
            out.push({ id: key, user_id: uid, ...rest, titles });
        }
    }
    return out;
};

/* ---- minimum games ----------------------------------------------------------------------- */

/*
Why a minimum: a rate over three games is noise that looks like signal. The three-week 2026
seasons beat every full season on win %, and Jordan Leonard's 2-0 against malstol topped "who
owns whom". Seasons and careers below the threshold are hidden (and counted, so the page can say
so); Games has no minimum, a game is a game.

The default is worked out from the data in view rather than fixed per dataset, because "enough
games" depends on what is being looked at: a regular season is 15 games but a playoff run is
2 and a single week is 1, so a flat "5" would hide every playoff season and every filtered view.
So: a fraction of the most games any row in view has, capped.

    Seasons                 a third, up to 5     15-game regular seasons -> 5, so 3-game 2026 drops out
    Careers                 a third, up to 10    63-game careers -> 10; only a one-season career is near it
    opponent-filtered       2/5, up to 4         a pair meets ~9 times; Jordan's 2 games drop out

A result of 1 or less is 0 (nothing hidden): playoffs, one season in progress, a single week.
`maxGames` is the largest `games` among the rows before any minimum is applied.
*/
const MIN_PROFILE = {
    seasons: { frac: 1 / 3, cap: 5 },
    managers: { frac: 1 / 3, cap: 10 },
    versus: { frac: 0.4, cap: 4 },
};

export const defaultMin = (ds, hasOpponent, maxGames) => {
    if(ds === 'games') return 0;
    const { frac, cap } = hasOpponent ? MIN_PROFILE.versus : MIN_PROFILE[ds];
    // the small epsilon keeps 15 * (1/3) from rounding up to 6 on floating-point noise
    const n = Math.min(cap, Math.ceil(maxGames * frac - 1e-9));
    return n <= 1 ? 0 : n;
};

/** Seasons and careers with fewer than `min` games are dropped; games rows are never filtered. */
export const applyMin = (rows, ds, min) => (ds === 'games' || !min ? rows : rows.filter((r) => r.games >= min));

/* ---- distribution ------------------------------------------------------------------------ */

/** Linear-interpolated quantile of an ascending array (Excel's QUARTILE.INC, numpy's default). */
export const quantile = (sorted, p) => {
    if(!sorted.length) return null;
    const h = (sorted.length - 1) * p;
    const lo = Math.floor(h);
    const hi = Math.ceil(h);
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (h - lo);
};

/**
 * One group per manager: every row's value of `key`, with the median and quartiles, sorted by
 * median (highest first; ties by name via `nameOf` when given). Rows with no value are left out.
 */
export const distribution = (rows, key, nameOf = (u) => u) => {
    const by = new Map();
    for(const r of rows) {
        const v = r[key];
        if(v === null || v === undefined || Number.isNaN(v)) continue;
        if(!by.has(r.user_id)) by.set(r.user_id, []);
        by.get(r.user_id).push(r);
    }
    const groups = [];
    for(const [uid, rs] of by) {
        const vals = rs.map((r) => r[key]).sort((a, b) => a - b);
        groups.push({
            uid, rows: rs, n: vals.length,
            median: quantile(vals, 0.5), q1: quantile(vals, 0.25), q3: quantile(vals, 0.75),
            lo: vals[0], hi: vals[vals.length - 1],
        });
    }
    return groups.sort((a, b) => b.median - a.median || String(nameOf(a.uid)).localeCompare(String(nameOf(b.uid))));
};

/* ---- sorting ----------------------------------------------------------------------------- */

/** Columns other than measures that the table can sort by. */
export const IDENTITY_SORTS = ['name', 'season', 'week', 'record', 'allPlay', 'opponent'];

export const defaultDir = (key) => (MEASURES[key]?.low || ['name', 'opponent'].includes(key) ? 'asc' : 'desc');

/**
 * Sort rows and give each a competition rank (1, 2, 2, 4) on the sort key. Nulls always sink.
 * `nameOf(uid)` resolves the name and opponent columns.
 */
export const sortRows = (rows, key, dir, nameOf) => {
    const value = (r) => {
        switch(key) {
            case 'name': return nameOf(r.user_id);
            case 'opponent': return nameOf(r.opponent_id);
            case 'season': return r.season * 100 + (r.week ?? 0);
            case 'week': return r.week;
            case 'record': return r.winPct ?? (r.result === 'W' ? 1 : r.result === 'T' ? 0.5 : 0);
            case 'allPlay': return r.allPlayPct;
            default: return r[key];
        }
    };
    const sign = dir === 'asc' ? 1 : -1;
    const tagged = rows.map((r) => ({ r, v: value(r) }));
    tagged.sort((a, b) => {
        const an = a.v === null || a.v === undefined, bn = b.v === null || b.v === undefined;
        if(an || bn) return an - bn;
        if(typeof a.v === 'string') return sign * a.v.localeCompare(b.v);
        if(a.v !== b.v) return sign * (a.v - b.v);
        // stable, readable tie-break: newest first, then name
        return (b.r.season ?? 0) - (a.r.season ?? 0) || (b.r.week ?? 0) - (a.r.week ?? 0);
    });
    let prev, rank = 0;
    return tagged.map(({ r, v }, i) => {
        if(i === 0 || v !== prev) rank = i + 1;
        prev = v;
        return { ...r, rank: v === null || v === undefined ? null : rank };
    });
};

/* ---- URL state --------------------------------------------------------------------------- */

const list = (v) => (v ? v.split(',').map((s) => s.trim()).filter(Boolean) : []);

/**
 * Read the view from the page address. `ctx` = {seasons: number[], handles: {handle: uid}}
 * validates against the data; anything unknown falls back to the default rather than erroring,
 * so an old or hand-edited link still opens something sensible.
 */
export const parseState = (params, ctx) => {
    const get = (k) => params.get(k);
    const ds = DATASETS.some((d) => d.value === get('ds')) ? get('ds') : 'seasons';

    const valid = (k) => MEASURES[k]?.ds.includes(ds);
    const m = valid(get('m')) ? get('m') : DEFAULT_MEASURE[ds];
    let x = valid(get('x')) ? get('x') : 'pf';
    if(x === m) x = m === 'pf' ? 'pa' : 'pf';

    let chart = CHARTS.some((c) => c.value === get('chart')) ? get('chart') : 'bar';
    if(chart === 'line' && ds === 'managers') chart = 'bar';
    if(chart === 'dist' && !distOk(ds, m)) chart = 'bar';

    const type = GAME_TYPES.some((t) => t.value === get('type')) ? get('type') : 'regular';

    const season = list(get('season')).map(Number).filter((s) => ctx.seasons.includes(s)).sort();

    const handles = (k) => list(get(k)).map((h) => h.toLowerCase()).filter((h) => ctx.handles[h]);
    const mgr = handles('mgr');
    const opp = handles('opp');

    let wk = [null, null];
    const wkRaw = get('wk');
    if(wkRaw && /^\d*-\d*$/.test(wkRaw)) {
        const [a, b] = wkRaw.split('-').map((v) => (v === '' ? null : Number(v)));
        wk = [a, b];
        if(a !== null && b !== null && a > b) wk = [b, a];
    }

    const sortable = (k) => valid(k) || IDENTITY_SORTS.includes(k);
    const sort = sortable(get('sort')) ? get('sort') : m;
    const dir = ['asc', 'desc'].includes(get('dir')) ? get('dir') : defaultDir(sort);

    const top = ['10', '25', 'all'].includes(get('top')) ? get('top') : '10';

    // null means "the default for this view"; 1 is the same as 0 (every row has a game)
    const minRaw = get('min');
    const min = minRaw !== null && /^\d{1,3}$/.test(minRaw) ? (Number(minRaw) <= 1 ? 0 : Number(minRaw)) : null;

    return {
        ds, m, x, chart, type, season, mgr, opp, wk, sort, dir, top, min,
        mgrIds: mgr.map((h) => ctx.handles[h]),
        oppIds: opp.map((h) => ctx.handles[h]),
    };
};

/** The query string for a state, leaving out every default. Keys are written in a fixed order. */
export const serializeState = (s) => {
    const p = new URLSearchParams();
    if(s.ds !== 'seasons') p.set('ds', s.ds);
    if(s.m !== DEFAULT_MEASURE[s.ds]) p.set('m', s.m);
    if(s.chart !== 'bar') p.set('chart', s.chart);
    if(s.chart === 'scatter' && s.x !== (s.m === 'pf' ? 'pa' : 'pf')) p.set('x', s.x);
    if(s.type !== 'regular') p.set('type', s.type);
    if(s.season?.length) p.set('season', [...s.season].sort().join(','));
    if(s.mgr?.length) p.set('mgr', s.mgr.join(','));
    if(s.opp?.length) p.set('opp', s.opp.join(','));
    if(s.wk && (s.wk[0] !== null || s.wk[1] !== null)) p.set('wk', `${s.wk[0] ?? ''}-${s.wk[1] ?? ''}`);
    if(s.sort && s.sort !== s.m) p.set('sort', s.sort);
    if(s.sort && s.dir !== defaultDir(s.sort)) p.set('dir', s.dir);
    if(s.chart === 'bar' && s.top !== '10') p.set('top', s.top);
    if(s.ds !== 'games' && s.min !== null && s.min !== undefined) p.set('min', String(s.min));
    return p.toString();
};

/* ---- presets ----------------------------------------------------------------------------- */

/**
 * The starting points shown as chips. `ctx` = {currentSeason, finished, champion}: `finished`
 * lists the seasons with final standings; the champion is the latest finished season's winner,
 * by handle, so "Who owns whom" never names a stale champ.
 * Each preset is a full query string, so it is also exactly the link it produces.
 */
export const presets = ({ currentSeason, finished = [], champion }) => [
    { id: 'luck', label: 'Luckiest seasons', query: 'm=luck' },
    { id: 'weeks', label: 'Biggest weeks ever', query: 'ds=games&type=all' },
    { id: 'pfpa', label: `Points for vs. against, ${currentSeason}`, query: `m=pa&chart=scatter&season=${currentSeason}` },
    // every weekly score, one strip per manager: spread is the width of the strip. Games, so the
    // 2026 weeks count as the games they are; no minimum applies and none is needed.
    { id: 'boom', label: 'Boom or bust', query: 'ds=games&chart=dist' },
    { id: 'bench', label: 'Who left the most on the bench', query: 'm=bench' },
    ...(champion ? [{ id: 'owns', label: 'Who owns whom', query: `ds=managers&type=all&opp=${champion}` }] : []),
];

/**
 * Quadrant captions for a scatter, keyed `${x}|${y}`, in the order
 * [top-left, top-right, bottom-left, bottom-right]. Pairs not listed get generic captions.
 */
export const QUADRANTS = {
    'pf|pa': ['Outscored', 'Shootouts', 'Low-scoring', 'In control'],
    'ppg|sd': ['Erratic', 'Boom', 'Steady, low', 'Steady, high'],
    'allPlayPct|winPct': ['Lucky', 'Earned it', 'Deserved it', 'Unlucky'],
    'allPlayPct|luck': ['Lucky', 'Good and lucky', 'Bad and unlucky', 'Unlucky'],
    'pf|bench': ['Wasted bench', 'Deep roster', 'Thin roster', 'Sharp lineups'],
};

export const quadrantLabels = (x, y) => {
    const known = QUADRANTS[`${x}|${y}`];
    if(known) return known;
    const X = MEASURES[x].short, Y = MEASURES[y].short;
    // a lower-is-better measure is drawn upside down (1st at the top), so its words swap too
    const [top, bottom] = MEASURES[y].low ? ['low', 'high'] : ['high', 'low'];
    return [`Low ${X}, ${top} ${Y}`, `High ${X}, ${top} ${Y}`, `Low ${X}, ${bottom} ${Y}`, `High ${X}, ${bottom} ${Y}`];
};
