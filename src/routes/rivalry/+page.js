import { getLeagueTeamManagers, loadPlayers, getLeagueTransactions, getLeagueRecords, getLeagueGames } from '$lib/utils/helper';

export async function load({url, fetch}) {

    const playerOne = url?.searchParams?.get('player_one');
    const playerTwo = url?.searchParams?.get('player_two');

    return {
        leagueTeamManagerData: getLeagueTeamManagers(),
        playersData: loadPlayers(fetch),
        transactionsData: getLeagueTransactions(),
        recordsData: getLeagueRecords(),
        // for the head-to-head grid: the committed game table, a small static file
        gamesData: getLeagueGames(fetch),
        playerOne,
        playerTwo,
    };
}