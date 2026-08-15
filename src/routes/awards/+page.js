import { getAwards, getLeagueTeamManagers, getLeagueHistory } from '$lib/utils/helper';

export async function load({ fetch }) {
    const awardsData = getAwards();
    const teamManagersData = getLeagueTeamManagers();
    // getLeagueHistory takes SvelteKit's fetch so the static dataset resolves during SSR too.
    const leagueHistoryData = getLeagueHistory(fetch);

    return {
        awardsData,
        teamManagersData,
        leagueHistoryData,
    };
}
