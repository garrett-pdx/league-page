<script>
    import { onMount } from 'svelte';
    import LinearProgress from '@smui/linear-progress';
    import { allPlay, filterGames, liveSeasonGames } from '$lib/utils/helper';
    import AllPlayTable from './AllPlayTable.svelte';

    /*
    Schedule luck for /standings. Mounted in routes/standings/+page.svelte rather than inside
    Standings/index.svelte, so the upstream component keeps its shape.

    TWO MODES, picked the same way the Standings component picks its own:

      LIVE        standingsData resolved to a table. The rows are built from Sleeper's live
                  matchups (liveSeasonGames), NOT from games.json, because games.json is only as
                  fresh as the last data refresh and this table sits right beside one that is
                  live. `throughWeek` is the most games any team has in that live table, so the
                  two can never disagree about how many weeks they count.

      PRESEASON   standingsData resolved to nothing: there is no current-season table. Show the
                  last season in games.json instead, regular season only, labelled as last
                  season -- the same fallback LastSeason.svelte makes for the standings.
    */
    export let standingsData, matchupsData, leagueTeamManagersData, nflStateData, gamesData;

    let loading = true;
    let loadError = false;
    let rows = [];
    let season = null;
    let eyebrow = null;
    let leagueTeamManagers = null;

    onMount(async () => {
        // games.json is only read in preseason; keep a failed fetch from surfacing unhandled.
        Promise.resolve(gamesData).catch(() => {});

        try {
            const standings = await standingsData;

            if(!standings) {
                // Preseason. The live matchups fetch was started by load() regardless; mark it as
                // handled so a failure there is not reported as an unhandled rejection.
                Promise.resolve(matchupsData).catch(() => {});

                const [games, ltm] = await Promise.all([gamesData, leagueTeamManagersData]);
                leagueTeamManagers = ltm;
                // "Last season" is the latest one BEFORE the league's current season. games.json
                // only holds completed weeks, so this is the newest finished year.
                const current = parseInt(ltm.currentSeason);
                const seasons = games.games.filter((g) => g.kind === 'regular' && (!current || g.season < current)).map((g) => g.season);
                if(seasons.length) {
                    season = Math.max(...seasons);
                    rows = allPlay(filterGames(games.games, {seasons: [season], kinds: ['regular']}));
                    eyebrow = `Last season, ${season}`;
                }
                loading = false;
                return;
            }

            const [matchups, ltm, nflState] = await Promise.all([matchupsData, leagueTeamManagersData, nflStateData]);
            leagueTeamManagers = ltm;
            season = parseInt(matchups.year);

            const counts = Object.values(standings.standingsInfo).map((s) => (s.wins || 0) + (s.losses || 0) + (s.ties || 0));
            const throughWeek = Math.max(0, ...counts);

            rows = throughWeek > 0
                ? allPlay(liveSeasonGames({matchupsData: matchups, leagueTeamManagers: ltm, nflState, throughWeek}))
                : [];
            eyebrow = `${season} season, through week ${throughWeek}`;
            loading = false;
        } catch(err) {
            console.error(err);
            loadError = true;
            loading = false;
        }
    });
</script>

<style>
    .loading {
        display: block;
        width: 85%;
        max-width: 500px;
        margin: 40px auto 80px;
    }

    /* Below 1200px this sits under the standings table, which is still loading too. A second
       spinner there was on screen, and got thrown down the page when the table landed (layout
       shift 0.57 at 375px). The table's own spinner says the page is working; this one waits
       for the side-by-side layout, where nothing sits above it. */
    @media (max-width: 1199px) {
        .loading { display: none; }
    }

    .errorMessage {
        text-align: center;
        color: var(--g555);
        margin: 2em auto 4em;
    }
</style>

{#if loadError}
    <p class="errorMessage">Schedule luck could not be loaded. Try refreshing the page.</p>
{:else if loading}
    <div class="loading">
        <p>Working out who had the easy schedule...</p>
        <LinearProgress indeterminate />
    </div>
{:else if rows.length}
    <AllPlayTable {rows} {leagueTeamManagers} {season} {eyebrow} />
{/if}
