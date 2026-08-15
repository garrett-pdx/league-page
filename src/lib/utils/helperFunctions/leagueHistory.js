/*
Reader for static/data/league-history.json -- the first thing in the site to touch the
committed dataset. Everything else fetches Sleeper live.

Why this file exists at all: Sleeper's API exposes the podium and the toilet bowl, and nothing
else. getAwards() can tell you who came 1st, 2nd, 3rd and last; it cannot tell you who came 6th,
because that is not a bracket result. `final_standings` in the dataset IS derived from the
brackets (plus regular-season record for the two teams in neither), so it is the only source for
a full 1-10 placement, and therefore the only way to show a manager's best and worst finish.

It also keys on user_id rather than roster_id, which sidesteps the trap that roster IDs are only
meaningful within a season.

One static 114 KB fetch, memoized for the session. No Sleeper calls.
*/

const HISTORY_URL = '/data/league-history.json';

let historyPromise = null;

/**
 * Fetch and memoize the league history dataset.
 * Pass SvelteKit's `fetch` from a load() so the call also works during SSR.
 */
export const getLeagueHistory = (servFetch) => {
    if(historyPromise) return historyPromise;

    const doFetch = servFetch || fetch;

    historyPromise = doFetch(HISTORY_URL)
        .then((res) => {
            if(!res.ok) throw new Error(`league history: ${res.status} ${res.statusText}`);
            return res.json();
        })
        .catch((err) => {
            // Never memoize a rejection -- a transient failure would otherwise poison the
            // cache for the rest of the session.
            historyPromise = null;
            throw err;
        });

    return historyPromise;
}

const ORDINALS = ['th', 'st', 'nd', 'rd'];

/** 1 -> "1st", 2 -> "2nd", 11 -> "11th" */
export const ordinal = (n) => {
    if(n === null || n === undefined) return null;
    const v = Math.abs(n) % 100;
    return `${n}${ORDINALS[(v - 20) % 10] || ORDINALS[v] || ORDINALS[0]}`;
}

/**
 * Career summary for one manager, derived from the dataset.
 * Returns null when the manager is not in the history at all.
 */
export const getManagerCareer = (history, managerID) => {
    if(!history || !managerID) return null;

    const manager = history.managers?.[managerID];
    if(!manager) return null;

    const career = manager.career || {};
    const wins = career.wins || 0;
    const losses = career.losses || 0;
    const ties = career.ties || 0;
    const games = wins + losses + ties;

    /*
    career.seasons_played counts every season the manager holds a roster, which includes the
    CURRENT one before a single game is played -- in 2026 that record is 0-0 and would make a
    four-season manager read as five. Count seasons that actually happened instead.
    */
    const seasonsPlayed = Object.values(manager.records || {})
        .filter((r) => (r.wins || 0) + (r.losses || 0) + (r.ties || 0) > 0)
        .length;

    // final_standings only contains completed seasons, so there is no 2026 row to exclude here.
    const finishes = [];
    for(const [season, table] of Object.entries(history.final_standings || {})) {
        const row = table.find((r) => r.user_id === managerID);
        if(row) finishes.push({season, place: row.place});
    }
    finishes.sort((a, b) => Number(a.season) - Number(b.season));

    /*
    `finishes` is sorted oldest-first, and <= / >= mean a tie resolves to the LATER season --
    Garrett finished 3rd in both 2022 and 2025, and the recent one is the interesting one.
    */
    const best = finishes.length
        ? finishes.reduce((a, b) => (b.place <= a.place ? b : a))
        : null;
    const worst = finishes.length
        ? finishes.reduce((a, b) => (b.place >= a.place ? b : a))
        : null;

    return {
        handle: manager.handle,
        teamNames: manager.team_names || [],
        wins,
        losses,
        ties,
        games,
        record: ties ? `${wins}-${losses}-${ties}` : `${wins}-${losses}`,
        winPct: games ? wins / games : null,
        pointsFor: career.points_for || 0,
        pointsAgainst: career.points_against || 0,
        ppg: games ? (career.points_for || 0) / games : null,
        seasonsPlayed,
        finishes,
        best,
        worst,
        championships: finishes.filter((f) => f.place === 1).length,
    };
}
