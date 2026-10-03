import { error } from '@sveltejs/kit';
import {
    getLeagueHistory,
    getLeagueGames,
    getSeasonNotes,
    getKeepers,
    getDataPlayers,
    getLeagueTeamManagers,
} from '$lib/utils/helper';
import { archiveYears } from '$lib/Seasons/seasonData';

/*
One season's page. The one deliberate exception to "return unawaited promises": the history file
is awaited, because whether this year exists decides between a page and a real 404, and only
load() can send a 404 status. It is a single small static file from our own origin, memoised for
the session, and every other source stays unawaited.
*/
export async function load({ params, fetch }) {
    const year = Number(params.year);
    if(!/^\d{4}$/.test(params.year)) error(404, 'No such season');

    const history = await getLeagueHistory(fetch);
    if(!archiveYears(history).includes(year)) error(404, `No ${params.year} season on record`);

    return {
        year,
        history,
        title: `${year} Season`,
        gamesData: getLeagueGames(fetch),
        notesData: getSeasonNotes(fetch),
        keepersData: getKeepers(fetch),
        playersData: getDataPlayers(fetch),
        // Sleeper, and slow (it walks every season): only the all-play table waits on it.
        leagueTeamManagersData: getLeagueTeamManagers(),
    };
}
