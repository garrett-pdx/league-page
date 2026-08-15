import {
    waitForAll,
    getLeagueRosters,
    getLeagueTeamManagers,
    getLeagueData,
    getLeagueTransactions,
    getAwards,
    getLeagueRecords,
    getLeagueHistory,
    managers as managersObj
} from '$lib/utils/helper';
export async function load({ url, fetch }) {
    if(!managersObj.length) return false;
    // getLeagueHistory takes SvelteKit's fetch so the static dataset also resolves during SSR.
    const managersInfo = waitForAll(
        getLeagueRosters(),
        getLeagueTeamManagers(),
        getLeagueData(),
        getLeagueTransactions(),
        getAwards(),
        getLeagueRecords(),
        getLeagueHistory(fetch),
    );

    const manager = url?.searchParams?.get('manager');

    const props = {
        manager: manager && manager < managersObj.length ? manager : -1,
        managers: managersObj,
        managersInfo
    }

    return props;
}