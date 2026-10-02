import { leagueID } from "$lib/utils/leagueInfo"
import { waitForAll } from "$lib/utils/helperFunctions/multiPromise"
import { json, error } from '@sveltejs/kit';

/*
Unrostered QB/RB/WR/TE with their depth-chart slot, for /free-agents.

League-specific; not upstream's. Kept separate from fetch_players_info on purpose: that payload is
upstream's and sits in localStorage for 24h, while who is free and who is hurt has to be fresh.

Three things this encodes, all verified against live data:

  * Sleeper's depth_chart_order is per team+position (WRs share one sequence across LWR/RWR/SWR)
    and has gaps and the odd duplicate (SF RB 1,2,4,6). We sort and assign a dense rank rather
    than trusting the raw number.
  * Sleeper cannot say who is out for the SEASON -- IR only means four games, and there is no
    return date. ESPN's core API carries a projected returnDate per injury (season-ending ones get
    a date past the season, e.g. 2027-02-15). Players whose return lands after the fantasy title
    week are dropped BEFORE ranking, so the next man up takes their slot.
  * Sleeper's espn_id is mostly null for fringe players, so we fall back to a name+team match
    against ESPN's team rosters. Any ESPN failure fails OPEN: the player stays, with Sleeper's
    injury badge. A third-party outage must not empty the page.

/players/nfl is ~15MB; the cache header below is what keeps that (and the ESPN fan-out) off
every page view.

REFRESH: the page's Refresh button asks for ?fresh=<unix minute>. Vercel's CDN caches each URL
separately, so a new minute misses the cache and pulls fresh -- but only the current minute (+/-1
for clock skew and requests that straddle the boundary) is accepted. Anything else is a 400 before
any fetching, so nobody can force a 15MB pull per request with random values: with three valid
values at any moment, the whole site gets at most ~3 fresh pulls a minute however many people
click (in practice one -- honest clients all send the current minute).
*/

const POSITIONS = ['QB', 'RB', 'WR', 'TE'];
const INJURED = ['IR', 'PUP', 'Out', 'Sus', 'DNR', 'NA', 'Doubtful'];
const ESPN_TEAM = { WAS: 'WSH' }; // Sleeper abbreviation -> ESPN, where they differ

const getJSON = async (url) => {
    const res = await fetch(url, {compress: true});
    if(!res.ok) throw new Error(`${res.status} ${url}`);
    return res.json();
}

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
        const teamsData = await getJSON('https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams');
        const teamIDs = {};
        for(const {team} of teamsData.sports[0].leagues[0].teams) teamIDs[team.abbreviation] = team.id;

        const needed = [...new Set(unknown.map(p => ESPN_TEAM[p.team] ?? p.team))].filter(t => teamIDs[t]);
        const rosters = await pool(needed, 16, (t) => getJSON(`https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/${teamIDs[t]}/roster`));
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
        const list = await getJSON(`https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/${season}/athletes/${ids[pid]}/injuries?limit=1`);
        if(!list.items?.length) return null;
        const injury = await getJSON(list.items[0].$ref.replace('http://', 'https://'));
        return injury.details?.returnDate ?? null;
    });

    const out = {};
    pids.forEach((pid, i) => { if(dates[i]) out[pid] = dates[i]; });
    return out;
}

export async function GET({ url, setHeaders }) {
    const fresh = url.searchParams.get('fresh');
    if(fresh != null) {
        const minute = Math.floor(Date.now() / 60000);
        if(!/^\d+$/.test(fresh) || Math.abs(parseInt(fresh) - minute) > 1) {
            throw error(400, 'Stale refresh token');
        }
    }

    let nflState, leagueData, rosters, playerData, seasonStats, trending;
    try {
        [nflState, leagueData, rosters, playerData] = await waitForAll(
            getJSON('https://api.sleeper.app/v1/state/nfl'),
            getJSON(`https://api.sleeper.app/v1/league/${leagueID}`),
            getJSON(`https://api.sleeper.app/v1/league/${leagueID}/rosters`),
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

    const rostered = new Set();
    for(const roster of rosters) {
        for(const key of ['players', 'reserve', 'taxi']) {
            for(const id of roster[key] ?? []) rostered.add(id);
        }
    }

    const candidates = Object.values(playerData).filter(p => p.active && p.team && POSITIONS.includes(p.position));

    // Season-ending check, free agents only -- a rostered player's slot still counts for ranking.
    const injuredFAs = candidates.filter(p => !rostered.has(p.player_id) && INJURED.includes(p.injury_status));
    let returnDates = {};
    try {
        returnDates = await getReturnDates(injuredFAs, nflState.season);
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
        if(rostered.has(p.player_id) || seasonOver(p)) continue;
        const stats = seasonStats[p.player_id];
        const player = {
            id: p.player_id,
            n: p.full_name ?? `${p.first_name} ${p.last_name}`,
            pos: p.position,
            t: p.team,
            depth: depth[p.player_id] ?? null,
        };
        if(p.depth_chart_position && p.depth_chart_position != p.position) player.slot = p.depth_chart_position;
        if(p.injury_status) player.is = p.injury_status;
        if(returnDates[p.player_id]) player.ret = returnDates[p.player_id];
        if(stats?.tm_off_snp) player.snap = Math.round(100 * (stats.off_snp ?? 0) / stats.tm_off_snp);
        if(trend[p.player_id]) player.trend = trend[p.player_id];
        if(p.search_rank && p.search_rank < 9999999) player.rank = p.search_rank; // 9999999 = unranked
        players.push(player);
    }

    setHeaders({'cache-control': fresh != null
        ? 'public, s-maxage=60'
        : 'public, s-maxage=900, stale-while-revalidate=3600'});
    return json({
        updated: new Date().toISOString(),
        cutoff,
        players,
    });
}
