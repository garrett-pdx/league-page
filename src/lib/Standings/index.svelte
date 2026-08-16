<script>
    import { leagueName, round } from '$lib/utils/helper';
	import { getTeamFromTeamManagers } from '$lib/utils/helperFunctions/universalFunctions';
  	import DataTable, { Head, Body, Row, Cell } from '@smui/data-table';
	import LinearProgress from '@smui/linear-progress';
    import { onMount } from 'svelte';
    import Standing from './Standing.svelte';

    import LastSeason from './LastSeason.svelte';

    export let standingsData, leagueTeamManagersData, leagueHistoryData = null;

    // Resolved only for the preseason branch; the live path never touches it.
    let leagueHistory = null;
    let preseasonTeamManagers = null;

    // Least important to most important (i.e. the most important [usually wins] goes last)
    // Edit this to match your leagues settings
    const sortOrder = ["fptsAgainst", "divisionTies", "divisionWins", "fpts", "ties", "wins"];

    // Column order from left to right
    const columnOrder = [{name: "W", field: "wins"}, {name: "T", field: "ties"}, {name: "L", field: "losses"}, {name: "Div W", field: "divisionWins"}, {name: "Div T", field: "divisionTies"}, {name: "Div L", field: "divisionLosses"}, {name: "FPTS", field: "fpts"}, {name: "FPTS Against", field: "fptsAgainst"}, {name: "Streak", field: "streak"}]

    let loading = true;
    let preseason = false;
    let loadError = false;
    let standings, year, leagueTeamManagers;
    onMount(async () => {
        /*
        Every promise here was awaited bare, with nothing catching a rejection -- a Sleeper
        timeout or 500 threw inside onMount and left `loading` stuck true forever, on a
        top-level nav item. Same fix as MatchupsAndBrackets.svelte; see the note there.
        */
        try {
            const asyncStandingsData = await standingsData;
            if(!asyncStandingsData) {
                /*
                Preseason. getLeagueStandings() returns nothing until the season has games, and
                this branch used to end at a one-line "no standings yet" -- on a top-level nav
                item, for about seven months of the year. Fall back to the last completed season.
                */
                preseasonTeamManagers = await leagueTeamManagersData;
                leagueHistory = leagueHistoryData ? await leagueHistoryData : null;
                loading = false;
                preseason = true;
                return;
            }
            const {standingsInfo, yearData} = asyncStandingsData;
            leagueTeamManagers = await leagueTeamManagersData;
            year = yearData;

            let finalStandings = Object.keys(standingsInfo).map((key) => standingsInfo[key]);

            for(const sortType of sortOrder) {
                if(!finalStandings[0][sortType] && finalStandings[0][sortType] != 0) {
                    continue;
                }
                finalStandings = [...finalStandings].sort((a,b) => b[sortType] - a[sortType]);
            }

            standings = finalStandings;
            loading = false;
        } catch(err) {
            console.error(err);
            loadError = true;
            loading = false;
        }
    })

    let innerWidth;

</script>

<svelte:window bind:innerWidth={innerWidth} />

<style>
    .loading {
        display: block;
        width: 85%;
        max-width: 500px;
        margin: 80px auto;
    }

    :global(.center) {
        text-align: center;
    }

    :global(.wrappable) {
        white-space: normal;
        line-height: 1.2em;
    }

    h1 {
        font-size: 2.2em;
        line-height: 1.3em;
        margin: 1.5em 0 2em;
    }

    .standingsTable {
        max-width: 100%;
        overflow-x: scroll;
        margin: 0.5em 0 5em;
    }

    .errorMessage {
        text-align: center;
        color: var(--g555);
        margin: 3em auto;
    }
</style>

<!-- In preseason LastSeason renders its own SectionHeading for the season it is showing, so a
     second "2026 Standings" title above an obviously-2025 table would just be wrong. -->
{#if !preseason && !loadError}
    <h1>{year ?? ''} {leagueName} Standings</h1>
{/if}

{#if loadError}
    <p class="errorMessage">Something went wrong loading standings. Try refreshing the page.</p>
{:else if loading}
    <!-- promise is pending -->
    <div class="loading">
        <p>Loading Standings...</p>
        <LinearProgress indeterminate />
    </div>
{:else if preseason}
    <LastSeason {leagueHistory} leagueTeamManagers={preseasonTeamManagers} />
{:else}
    <div class="standingsTable">
        <DataTable table$aria-label="League Standings" >
            <Head> <!-- Team name  -->
                <Row>
                    <Cell class="center">Team</Cell>
                    {#each columnOrder as column}
                        <Cell class="center wrappable">{column.name}</Cell>
                    {/each}
                </Row>
            </Head>
            <Body>
                <!-- 	Standing	 -->
                {#each standings as standing}
                    <Standing {columnOrder} {standing} {leagueTeamManagers} team={getTeamFromTeamManagers(leagueTeamManagers, standing.rosterID)} />
                {/each}
            </Body>
        </DataTable>
    </div>
{/if}
