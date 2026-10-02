import { leagueID } from "$lib/utils/leagueInfo"
import { waitForAll } from "$lib/utils/helperFunctions/multiPromise"
import { json, error } from '@sveltejs/kit';
import { REFRESH_WINDOW_MS, currentRefreshWindow } from '$lib/FreeAgents/refreshWindow';

/*
Every QB/RB/WR/TE with their depth-chart slot, for /free-agents. Free agents by default; rostered
players are included too, carrying their owner (`own`, a user_id, resolved through `owners` to a
Sleeper handle), and the page's "Show rostered" toggle decides whether they appear. The endpoint
kept its name when rostered players were added, to avoid churn.

League-specific; not upstream's. Kept separate from fetch_players_info on purpose: that payload is
upstream's and sits in localStorage for 24h, while who is free and who is hurt has to be fresh.

Three things this encodes, all verified against live data:

  * Sleeper's depth_chart_order is per team+position (WRs share one sequence across LWR/RWR/SWR)
    and has gaps and the odd duplicate (SF RB 1,2,4,6). We sort and assign a dense rank rather
    than trusting the raw number.
  * Sleeper cannot say who is out for the SEASON -- IR only means four games, and there is no
    return date. ESPN's core API carries a projected returnDate per injury (season-ending ones get
    a date past the season, e.g. 2027-02-15). Players whose return lands after the fantasy title
    week are dropped BEFORE ranking, so the next man up takes their slot. This applies to
    rostered players too: an out-for-the-season player is hidden and holds no slot, whoever owns
    him.
  * Sleeper's espn_id is mostly null for fringe players, so we fall back to a name+team match
    against ESPN's team rosters. Any ESPN failure fails OPEN: the player stays, with Sleeper's
    injury badge. A third-party outage must not empty the page.

/players/nfl is ~15MB; the cache header below is what keeps that (and the ESPN fan-out) off
every page view.

REFRESH: the page's Refresh button asks for ?fresh=<window>, where a window is REFRESH_WINDOW_MS
(5 min, in $lib/FreeAgents/refreshWindow.js). Vercel's CDN caches each URL separately, so a new
window misses the cache and pulls fresh -- but only the current window (+/-1 for clock skew and
requests that straddle the boundary) is accepted. Anything else is a 400 before any fetching, so
nobody can force a 15MB pull per request with random values: in practice the whole site gets one
fresh pull per window however many people click (three at the very most).
*/

const POSITIONS = ['QB', 'RB', 'WR', 'TE'];
const INJURED = ['IR', 'PUP', 'Out', 'Sus', 'DNR', 'NA', 'Doubtful'];
const ESPN_TEAM = { WAS: 'WSH' }; // Sleeper abbreviation -> ESPN, where they differ

/*
Every outbound request has a time limit. Without one, a single stalled request out of the ~60
this makes (Sleeper plus the ESPN fan-out) left the whole response hanging with no answer -- seen
both locally and on the live site. ESPN gets less time per call, and the whole ESPN step a
deadline of its own, past which it fails open like any other ESPN failure.
*/
const SLEEPER_TIMEOUT = 20000;
const ESPN_TIMEOUT = 8000;
const ESPN_DEADLINE = 15000;

const getJSON = async (url, timeout = SLEEPER_TIMEOUT) => {
    const res = await fetch(url, {compress: true, signal: AbortSignal.timeout(timeout)});
    if(!res.ok) throw new Error(`${res.status} ${url}`);
    return res.json();
}
const getESPN = (url) => getJSON(url, ESPN_TIMEOUT);

const withDeadline = (promise, ms, label) => Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error(`${label} took over ${ms}ms`)), ms)),
]);

// run fn over items with at most `limit` in flight
const pool = async (items, limit, fn) => {
    const out = new Array(items.length);
    let next = 0;
    const worker = async () => {
        while(next < items.length) {
            const i = next++;
            out[i] = await fn(items[i]).catch(() => null);
        }
    }
    await Promise.all(Array.from({length: Math.min(limit, items.length)}, worker));
    return out;
}

const normName = (s) => s.toLowerCase()
    .replace(/\b(jr|sr|ii|iii|iv|v)\b\.?/g, '')
    .replace(/[^a-z]/g, '');

// Last day (Tuesday) of the league's championship week.
const seasonCutoff = (nflState, leagueData) => {
    const playoffStart = parseInt(leagueData.settings.playoff_week_start);
    const rounds = Math.ceil(Math.log2(parseInt(leagueData.settings.playoff_teams) || 4));
    const titleWeek = playoffStart + rounds - 1;
    const start = new Date(`${nflState.season_start_date}T00:00:00Z`);
    start.setUTCDate(start.getUTCDate() + 7 * (titleWeek - 1) + 6);
    return start.toISOString().slice(0, 10);
}

// sleeper player_id -> ESPN returnDate (YYYY-MM-DD), for the injured players given
const getReturnDates = async (injured, season) => {
    const ids = {};
    const unknown = [];
    for(const p of injured) {
        if(p.espn_id) ids[p.player_id] = String(p.espn_id);
        else unknown.push(p);
    }

    if(unknown.length) {
        const teamsData = await getESPN('https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams');
        const teamIDs = {};
        for(const {team} of teamsData.sports[0].leagues[0].teams) teamIDs[team.abbreviation] = team.id;

        const needed = [...new Set(unknown.map(p => ESPN_TEAM[p.team] ?? p.team))].filter(t => teamIDs[t]);
        const rosters = await pool(needed, 16, (t) => getESPN(`https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/${teamIDs[t]}/roster`));
        const byTeam = {};
        needed.forEach((t, i) => {
            byTeam[t] = (rosters[i]?.athletes ?? []).flatMap(g => g.items);
        });

        for(const p of unknown) {
            const name = normName(p.full_name ?? '');
            const hits = (byTeam[ESPN_TEAM[p.team] ?? p.team] ?? []).filter(a => normName(a.fullName) == name);
            if(hits.length == 1) ids[p.player_id] = hits[0].id;
        }
    }

    const pids = Object.keys(ids);
    const dates = await pool(pids, 16, async (pid) => {
        const list = await getESPN(`https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/${season}/athletes/${ids[pid]}/injuries?limit=1`);
        if(!list.items?.length) return null;
        const injury = await getESPN(list.items[0].$ref.replace('http://', 'https://'));
        return injury.details?.returnDate ?? null;
    });

    const out = {};
    pids.forEach((pid, i) => { if(dates[i]) out[pid] = dates[i]; });
    return out;
}

export async function GET({ url, setHeaders }) {
    const fresh = url.searchParams.get('fresh');
    if(fresh != null) {
        if(!/^\d+$/.test(fresh) || Math.abs(parseInt(fresh) - currentRefreshWindow()) > 1) {
            throw error(400, 'Stale refresh token');
        }
    }

    let nflState, leagueData, rosters, users, playerData, seasonStats, trending;
    try {
        [nflState, leagueData, rosters, users, playerData] = await waitForAll(
            getJSON('https://api.sleeper.app/v1/state/nfl'),
            getJSON(`https://api.sleeper.app/v1/league/${leagueID}`),
            getJSON(`https://api.sleeper.app/v1/league/${leagueID}/rosters`),
            getJSON(`https://api.sleeper.app/v1/league/${leagueID}/users`),
            getJSON('https://api.sleeper.app/v1/players/nfl'),
        );
    } catch (err) {
        console.error(err);
        throw error(502, 'Could not reach Sleeper');
    }
    // nice-to-haves: the page works without either
    [seasonStats, trending] = await waitForAll(
        getJSON(`https://api.sleeper.app/v1/stats/nfl/regular/${nflState.season}`).catch(() => ({})),
        getJSON('https://api.sleeper.app/v1/players/nfl/trending/add?lookback_hours=48&limit=200').catch(() => []),
    );

    const owner = {};   // player_id -> owner user_id
    for(const roster of rosters) {
        for(const key of ['players', 'reserve', 'taxi']) {
            for(const id of roster[key] ?? []) owner[id] = roster.owner_id;
        }
    }
    const owners = {};  // user_id -> Sleeper handle
    for(const user of users) owners[user.user_id] = user.display_name;

    const candidates = Object.values(playerData).filter(p => p.active && p.team && POSITIONS.includes(p.position));

    // Season-ending check for everyone, rostered or not
    const injured = candidates.filter(p => INJURED.includes(p.injury_status));
    let returnDates = {};
    try {
        returnDates = await withDeadline(getReturnDates(injured, nflState.season), ESPN_DEADLINE, 'ESPN injury lookup');
    } catch (err) {
        console.error('ESPN injury lookup failed, showing all injured players', err);
    }
    const cutoff = seasonCutoff(nflState, leagueData);
    const seasonOver = (p) => (returnDates[p.player_id] ?? '') > cutoff;

    // dense depth rank per team+position, after dropping the season-ending
    const depth = {};
    const groups = {};
    for(const p of candidates) {
        if(p.depth_chart_order == null || seasonOver(p)) continue;
        (groups[`${p.team}|${p.position}`] ??= []).push(p);
    }
    for(const group of Object.values(groups)) {
        group.sort((a, b) => a.depth_chart_order - b.depth_chart_order || (a.search_rank ?? 1e9) - (b.search_rank ?? 1e9));
        group.forEach((p, i) => { depth[p.player_id] = i + 1; });
    }

    const trend = {};
    for(const t of trending) trend[t.player_id] = t.count;

    const players = [];
    for(const p of candidates) {
        if(seasonOver(p)) continue;
        const stats = seasonStats[p.player_id];
        const player = {
            id: p.player_id,
            n: p.full_name ?? `${p.first_name} ${p.last_name}`,
            pos: p.position,
            t: p.team,
            depth: depth[p.player_id] ?? null,
        };
        if(owner[p.player_id]) player.own = owner[p.player_id];
        if(p.depth_chart_position && p.depth_chart_position != p.position) player.slot = p.depth_chart_position;
        if(p.injury_status) player.is = p.injury_status;
        if(returnDates[p.player_id]) player.ret = returnDates[p.player_id];
        if(stats?.tm_off_snp) player.snap = Math.round(100 * (stats.off_snp ?? 0) / stats.tm_off_snp);
        if(trend[p.player_id]) player.trend = trend[p.player_id];
        if(p.search_rank && p.search_rank < 9999999) player.rank = p.search_rank; // 9999999 = unranked
        players.push(player);
    }

    setHeaders({'cache-control': fresh != null
        ? `public, s-maxage=${REFRESH_WINDOW_MS / 1000}`
        : 'public, s-maxage=900, stale-while-revalidate=3600'});
    return json({
        updated: new Date().toISOString(),
        cutoff,
        owners,
        players,
    });
}
