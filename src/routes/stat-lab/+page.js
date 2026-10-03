import { getLeagueGames, getLeagueHistory } from '$lib/utils/helper';

/*
Stat Lab reads the two committed files only -- no Sleeper calls -- so every number agrees with
Standings, Rivalry and the Seasons pages. Both promises are returned unawaited, as everywhere
else, so the page header renders straight away.

This load() deliberately never reads `url`. Every control lives in the query string, and
SvelteKit re-runs a load() that touched url.searchParams on every goto(); not touching it keeps
a filter change a pure client-side re-render.
*/
export function load({ fetch }) {
    return {
        gamesData: getLeagueGames(fetch),
        historyData: getLeagueHistory(fetch),
    };
}
