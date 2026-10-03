import { getLeagueHistory, getLeagueGames, getSeasonNotes } from '$lib/utils/helper';

// The Seasons archive index. Three static files from static/data/, all memoised and unawaited,
// so the header renders at once and the cards fill in. No Sleeper calls.
export async function load({ fetch }) {
    return {
        historyData: getLeagueHistory(fetch),
        gamesData: getLeagueGames(fetch),
        notesData: getSeasonNotes(fetch),
    };
}
