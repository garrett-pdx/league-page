/*
Reader for static/data/games.json -- one row per team per game, every completed week since 2022 --
plus the pure functions every history page computes from it: Schedule luck on Standings, the
head-to-head grid on Rivalry, the Seasons archive and Stat Lab. All four read the same rows
through the same filters, so they cannot disagree with each other.

games.json is built offline by scripts/derive-site-data.py, which handles the dataset's traps
(the fictional week 18, unplayed weeks that look real, playoff games told apart by week number)
and checks every regular-season record against Sleeper before writing. See
static/data/README.md for the file format.

Everything below the loader is pure: no Svelte, no stores, no fetch. Node can import and test it
directly.

A row, as every function here takes and returns it:

    {season, week, user_id, opponent_id, pf, pa, result, kind}

    season       number (2022), unlike league-history.json's string keys
    result       "W" | "L" | "T", from this team's side
    kind         "regular" | "playoff" | "placement" | "consolation"

Each game appears twice, once from each side.
*/

const GAMES_URL = '/data/games.json';

let gamesPromise = null;

/**
 * Decode the columnar file into row objects.
 * Exported for tests; pages should call getLeagueGames().
 */
export const decodeGames = (raw) => {
    const col = {};
    raw.columns.forEach((name, i) => { col[name] = raw.data[i]; });

    const games = new Array(raw.count);
    for(let i = 0; i < raw.count; i++) {
        const row = {
            season: col.season[i],
            week: col.week[i],
            user_id: raw.managers[col.manager[i]],
            opponent_id: raw.managers[col.opponent[i]],
            pf: col.pf[i],
            pa: col.pa[i],
            result: col.result[i],
            kind: raw.kinds[col.kind[i]],
        };
        // Only present if the max_pf self-check passed; today it does not, see the README.
        if(col.max_pf) row.max_pf = col.max_pf[i];
        games[i] = row;
    }

    return {
        generated: raw.generated,
        // {season, week}: the last completed week -- the "data through week N" stamp
        through: raw.through,
        nflState: raw.nfl_state,
        managers: raw.managers,
        games,
    };
}

/**
 * Fetch, decode and memoize games.json. Resolves to {generated, through, nflState, managers, games}.
 * Pass SvelteKit's `fetch` from a load() so the call also works during SSR.
 */
export const getLeagueGames = (servFetch) => {
    if(gamesPromise) return gamesPromise;

    const doFetch = servFetch || fetch;

    gamesPromise = doFetch(GAMES_URL)
        .then((res) => {
            if(!res.ok) throw new Error(`league games: ${res.status} ${res.statusText}`);
            return res.json();
        })
        .then(decodeGames)
        .catch((err) => {
            // Never memoize a rejection -- a transient failure would otherwise poison the
            // cache for the rest of the session.
            gamesPromise = null;
            throw err;
        });

    return gamesPromise;
}

const asSet = (v) => {
    if(v === null || v === undefined) return null;
    const list = Array.isArray(v) ? v : [v];
    return list.length ? new Set(list.map(String)) : null;
}

/**
 * Narrow a list of rows. Every option is optional; absent or empty means "no filter".
 *
 *   seasons    number(s) or string(s): [2024, 2025]
 *   managers   user_id(s): rows FROM these managers' side
 *   kinds      kind(s): ['regular'], or ['playoff', 'placement'] for "Playoffs"
 *   weekRange  [from, to], inclusive; either end may be null
 *   opponent   user_id(s): rows AGAINST these managers
 *
 * Don't filter by manager before allPlay() -- see there.
 */
export const filterGames = (games, {seasons, managers, kinds, weekRange, opponent} = {}) => {
    const s = asSet(seasons);
    const m = asSet(managers);
    const k = asSet(kinds);
    const o = asSet(opponent);
    const [from, to] = weekRange || [];

    return games.filter((g) =>
        (!s || s.has(String(g.season))) &&
        (!m || m.has(g.user_id)) &&
        (!k || k.has(g.kind)) &&
        (!o || o.has(g.opponent_id)) &&
        (from === null || from === undefined || g.week >= from) &&
        (to === null || to === undefined || g.week <= to)
    );
}

const winsOf = (r) => r.wins + r.ties / 2;

/**
 * All-play: each week, every team is scored against every OTHER team that played that week, not
 * just its opponent. Returns one entry per manager, sorted by all-play % (best first):
 *
 *   {user_id, games, wins, losses, ties,             the real record in these rows
 *    allPlayWins, allPlayLosses, allPlayTies,
 *    allPlayPct,                                    (W + T/2) / all-play games
 *    expectedWins,                                  sum over weeks of that week's all-play share
 *    luck}                                          (wins + ties/2) - expectedWins
 *
 * A tie, real or all-play, counts as half a win. With ten teams expectedWins is exactly
 * allPlayPct x games; summing week by week keeps it right when a week has fewer teams.
 *
 * The comparison pool is whatever rows you pass, so pass WHOLE WEEKS: filter by season, kind or
 * week range, never by manager, then pick managers out of the result. Normally kinds:
 * ['regular'] -- only eight teams play in a playoff week, and the four who didn't would simply
 * be missing from it. Across the league each week's luck sums to zero.
 */
export const allPlay = (games) => {
    const weeks = new Map();
    for(const g of games) {
        const key = `${g.season}-${g.week}`;
        if(!weeks.has(key)) weeks.set(key, []);
        weeks.get(key).push(g);
    }

    const out = {};
    const entry = (uid) => out[uid] || (out[uid] = {
        user_id: uid, games: 0, wins: 0, losses: 0, ties: 0,
        allPlayWins: 0, allPlayLosses: 0, allPlayTies: 0,
        allPlayPct: null, expectedWins: 0, luck: 0,
    });

    for(const rows of weeks.values()) {
        for(const g of rows) {
            const e = entry(g.user_id);
            e.games++;
            if(g.result === 'W') e.wins++;
            else if(g.result === 'L') e.losses++;
            else e.ties++;

            let w = 0, l = 0, t = 0;
            for(const other of rows) {
                if(other.user_id === g.user_id) continue;
                if(g.pf > other.pf) w++;
                else if(g.pf < other.pf) l++;
                else t++;
            }
            e.allPlayWins += w;
            e.allPlayLosses += l;
            e.allPlayTies += t;
            if(w + l + t) e.expectedWins += (w + t / 2) / (w + l + t);
        }
    }

    for(const e of Object.values(out)) {
        const n = e.allPlayWins + e.allPlayLosses + e.allPlayTies;
        e.allPlayPct = n ? (e.allPlayWins + e.allPlayTies / 2) / n : null;
        e.luck = winsOf(e) - e.expectedWins;
    }

    return Object.values(out).sort((a, b) => (b.allPlayPct ?? -1) - (a.allPlayPct ?? -1));
}

/**
 * Head-to-head for every ordered pair of managers who met in these rows:
 *
 *   h2h[a][b] = {games, wins, losses, ties, pf, pa}    a's record against b
 *
 * Both directions are present, mirrored. A pair that never met has no entry. `kinds` filters
 * first (default: all), e.g. {kinds: ['regular']} or {kinds: ['playoff', 'placement']}.
 * A manager's row summed across opponents equals standingsFrom() on the same rows.
 */
export const headToHead = (games, {kinds} = {}) => {
    const rows = kinds ? filterGames(games, {kinds}) : games;
    const out = {};
    for(const g of rows) {
        const mine = out[g.user_id] || (out[g.user_id] = {});
        const r = mine[g.opponent_id] || (mine[g.opponent_id] = {games: 0, wins: 0, losses: 0, ties: 0, pf: 0, pa: 0});
        r.games++;
        if(g.result === 'W') r.wins++;
        else if(g.result === 'L') r.losses++;
        else r.ties++;
        r.pf += g.pf;
        r.pa += g.pa;
    }
    for(const opps of Object.values(out)) {
        for(const r of Object.values(opps)) {
            r.pf = round2(r.pf);
            r.pa = round2(r.pa);
        }
    }
    return out;
}

/**
 * A standings table from whatever rows you pass, sorted by win % (ties as half), then points for:
 *
 *   [{user_id, games, wins, losses, ties, winPct, pf, pa}]
 *
 * For a season's regular-season table pass filterGames(games, {seasons: [y], kinds: ['regular']}).
 * Note this is not Sleeper's tie-break order -- it has no notion of divisions or head-to-head.
 */
export const standingsFrom = (games) => {
    const out = {};
    for(const g of games) {
        const r = out[g.user_id] || (out[g.user_id] = {user_id: g.user_id, games: 0, wins: 0, losses: 0, ties: 0, winPct: null, pf: 0, pa: 0});
        r.games++;
        if(g.result === 'W') r.wins++;
        else if(g.result === 'L') r.losses++;
        else r.ties++;
        r.pf += g.pf;
        r.pa += g.pa;
    }
    const rows = Object.values(out);
    for(const r of rows) {
        r.pf = round2(r.pf);
        r.pa = round2(r.pa);
        r.winPct = r.games ? winsOf(r) / r.games : null;
    }
    return rows.sort((a, b) => (b.winPct - a.winPct) || (b.pf - a.pf));
}

const round2 = (n) => Math.round(n * 100) / 100;

/**
 * The current season's games in the same row shape, from the site's LIVE Sleeper data rather
 * than games.json, so Standings' luck column can never lag the live table beside it.
 *
 * Inputs, all already loaded by the usual helpers (each memoized in a store):
 *
 *   matchupsData        the resolved value of getLeagueMatchups():
 *                       {year, week, regularSeasonLength,
 *                        matchupWeeks: [{week, matchups: {matchup_id: [{roster_id, starters,
 *                                                                       points: number[]}]}}]}
 *                       `points` there is the per-STARTER array; a team's score is its sum.
 *   leagueTeamManagers  the resolved value of getLeagueTeamManagers(); roster IDs become user_ids
 *                       through teamManagersMap[year][roster_id].managers[0], the roster's owner
 *                       for THIS season (roster IDs mean nothing across seasons).
 *   nflState            the resolved value of getNflState().
 *   throughWeek         optional. Include weeks <= this only. Pass the number of games in the
 *                       live Standings table (max wins + losses + ties over its rows) to pin the
 *                       luck numbers to exactly what that table counts.
 *
 * Only completed weeks: while the NFL regular season is running, a week counts once the NFL
 * week has moved past it (week < nflState.week) -- the week in progress has real points for the
 * games already played and is not a result. Before kickoff and in the offseason, a week counts
 * if anybody scored in it, which is every week of a finished season and none of an unstarted
 * one. Weeks with nobody scoring never count; matchup_id 0/null is never a game.
 *
 * getLeagueMatchups() loads regular-season weeks only, so every row is kind 'regular'. It also
 * drops Sleeper's custom_points, so a commissioner-overridden week (none yet this season) would
 * show the computed score here and the override in games.json.
 *
 * From a page:
 *
 *   // +page.js load() -- unawaited, as everywhere else
 *   matchupsData: getLeagueMatchups(),
 *   leagueTeamManagersData: getLeagueTeamManagers(),
 *   nflStateData: getNflState(),
 *
 *   // component
 *   {#await Promise.all([matchupsData, leagueTeamManagersData, nflStateData])}
 *   {:then [matchups, teamManagers, nflState]}
 *       <AllPlayTable rows={allPlay(liveSeasonGames({matchupsData: matchups,
 *           leagueTeamManagers: teamManagers, nflState}))} />
 *   {/await}
 */
export const liveSeasonGames = ({matchupsData, leagueTeamManagers, nflState, throughWeek = null}) => {
    if(!matchupsData?.matchupWeeks || !leagueTeamManagers?.teamManagersMap || !nflState) return [];

    const year = parseInt(matchupsData.year);
    const rosters = leagueTeamManagers.teamManagersMap[year] || {};
    const stateSeason = parseInt(nflState.season);

    const weekComplete = (week, scored) => {
        if(!scored) return false;
        if(throughWeek !== null && throughWeek !== undefined && week > throughWeek) return false;
        if(year < stateSeason) return true;
        if(year > stateSeason) return false;
        if(nflState.season_type === 'regular') return week < nflState.week;
        return true;    // 'post', or 'pre'/'off' with points on the board
    };

    const rows = [];
    for(const {week, matchups} of matchupsData.matchupWeeks) {
        const teams = [];
        for(const [matchupID, pair] of Object.entries(matchups || {})) {
            // getLeagueMatchups keys by matchup_id as given, so a non-fixture is "0" or "null"
            if(!Number(matchupID) || !pair || pair.length !== 2) continue;
            teams.push(pair.map((t) => ({
                user_id: rosters[t.roster_id]?.managers?.[0] ?? null,
                pf: round2((t.points || []).reduce((sum, p) => sum + (p || 0), 0)),
            })));
        }
        const scored = teams.some((pair) => pair.some((t) => t.pf > 0));
        if(!weekComplete(week, scored)) continue;

        for(const [a, b] of teams) {
            if(!a.user_id || !b.user_id) continue;
            for(const [me, them] of [[a, b], [b, a]]) {
                rows.push({
                    season: year,
                    week,
                    user_id: me.user_id,
                    opponent_id: them.user_id,
                    pf: me.pf,
                    pa: them.pf,
                    result: me.pf > them.pf ? 'W' : me.pf < them.pf ? 'L' : 'T',
                    kind: 'regular',
                });
            }
        }
    }
    return rows;
}
