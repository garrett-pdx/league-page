/*
Readers for three small committed files in static/data/, used by the Seasons archive
(src/routes/seasons):

    season-notes.json   per-season trades, top scorers, high and low weeks   (~4 KB gzipped)
    keepers.json        every keeper with its cost and the rule check         (~32 KB)
    players.json        player_id -> {n: name, p: position, t: team}          (~20 KB)

Same pattern as leagueHistory.js and leagueGames.js: one static fetch per file, memoized for the
session, no Sleeper calls. A rejection is never memoized. Pass SvelteKit's `fetch` from a load()
so the call also works during SSR.

Ours, not upstream's. See static/data/README.md for the shapes.
*/

const cache = {};

const loadOnce = (url, servFetch) => {
    if(cache[url]) return cache[url];

    const doFetch = servFetch || fetch;

    cache[url] = doFetch(url)
        .then((res) => {
            if(!res.ok) throw new Error(`${url}: ${res.status} ${res.statusText}`);
            return res.json();
        })
        .catch((err) => {
            delete cache[url];
            throw err;
        });

    return cache[url];
}

/** Resolves to {generated, seasons: {<year>: {through_week, trades, top_scorers, high_weeks, low_weeks}}} */
export const getSeasonNotes = (servFetch) => loadOnce('/data/season-notes.json', servFetch);

/** Resolves to {generated, keepers: {<year>: [row]}} -- rows sorted by pick number */
export const getKeepers = (servFetch) => loadOnce('/data/keepers.json', servFetch);

/** Resolves to {<player_id>: {n, p, t}}. Covers every player in every committed draft. */
export const getDataPlayers = (servFetch) => loadOnce('/data/players.json', servFetch);
