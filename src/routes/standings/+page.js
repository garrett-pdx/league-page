import { getLeagueStandings, getLeagueTeamManagers, getLeagueHistory, getLeagueMatchups, getNflState, getLeagueGames } from '$lib/utils/helper';

export async function load({ fetch }) {

    const standingsData = getLeagueStandings();
    const leagueTeamManagersData = getLeagueTeamManagers();
    // Only used in preseason, to show last season's final table instead of a blank page.
    // Memoised and SSR-safe; takes SvelteKit's fetch so the static dataset resolves server-side.
    const leagueHistoryData = getLeagueHistory(fetch);

    // For Schedule luck (src/lib/History). The live matchups and NFL state feed the current
    // season's table; games.json is the preseason fallback. All three are memoised and unawaited.
    const matchupsData = getLeagueMatchups();
    const nflStateData = getNflState();
    const gamesData = getLeagueGames(fetch);

    return {
        standingsData,
        leagueTeamManagersData,
        leagueHistoryData,
        matchupsData,
        nflStateData,
        gamesData,
    };
}
