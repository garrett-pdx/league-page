import { getLeagueStandings, getLeagueTeamManagers, getLeagueHistory } from '$lib/utils/helper';

export async function load({ fetch }) {

    const standingsData = getLeagueStandings();
    const leagueTeamManagersData = getLeagueTeamManagers();
    // Only used in preseason, to show last season's final table instead of a blank page.
    // Memoised and SSR-safe; takes SvelteKit's fetch so the static dataset resolves server-side.
    const leagueHistoryData = getLeagueHistory(fetch);

    return {
        standingsData,
        leagueTeamManagersData,
        leagueHistoryData,
    };
}
