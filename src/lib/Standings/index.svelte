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

    // Least important to most important (i.e. the most important [usually wins] goes last).
    // A key the standings do not carry (no divisions, say) is skipped by the sort below.
    const sortOrder = ["fptsAgainst", "divisionTies", "divisionWins", "fpts", "ties", "wins"];

    /*
    Columns, left to right. Ties and the division record appear only for a league that has them:
    a column of zeros on every row is noise, and on a phone it pushes the points off-screen.
    */
    const ALL_COLUMNS = [
        {name: "W", field: "wins"},
        {name: "T", field: "ties", when: "ties"},
        {name: "L", field: "losses"},
        {name: "Div W", field: "divisionWins", when: "divisions"},
        {name: "Div T", field: "divisionTies", when: "divisionTies"},
        {name: "Div L", field: "divisionLosses", when: "divisions"},
        {name: "FPTS", field: "fpts"},
        {name: "FPTS Against", field: "fptsAgainst"},
        {name: "Streak", field: "streak"},
    ];
    let columnOrder = ALL_COLUMNS.filter((c) => !c.when);
    const columnsFor = (rows) => {
        const has = {
            ties: rows.some((r) => r.ties > 0),
            divisions: rows.some((r) => r.divisionWins !== null && r.divisionWins !== undefined),
            divisionTies: rows.some((r) => r.divisionTies > 0),
        };
        return ALL_COLUMNS.filter((c) => !c.when || has[c.when]);
    };

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
            columnOrder = columnsFor(finalStandings);
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

    .standingsTable {
        max-width: 100%;
        overflow-x: auto;
        margin: 0.5em 0 5em;
    }

    /* The table scrolls inside its own container, with the Team column pinned. For position:
       sticky to work the scrolling box has to be the DataTable's own table container (the
       nearest ancestor with overflow), so the DataTable is capped at the page width instead of
       growing past it and leaving the outer div to scroll. */
    .standingsTable :global(.mdc-data-table) {
        max-width: 100%;
    }

    .standingsTable :global(th:first-child),
    .standingsTable :global(td:first-child) {
        position: sticky;
        left: 0;
        z-index: 1;
        background-color: var(--fff);
        box-shadow: 4px 0 4px -3px rgba(0, 0, 0, 0.18);
    }

    .standingsTable :global(.contrastRow td:first-child) {
        background-color: var(--f8f8f8);
    }

    @media (max-width: 700px) {
        .standingsTable :global(th:first-child),
        .standingsTable :global(td:first-child) {
            min-width: 130px;
            max-width: 150px;
            white-space: normal;
        }

        .standingsTable :global(th),
        .standingsTable :global(td) {
            padding: 0 8px;
        }
    }

    .errorMessage {
        text-align: center;
        color: var(--g555);
        margin: 3em auto;
    }
</style>

<!-- The page title ("Standings") is a PageHeader mounted in routes/standings/+page.svelte. In
     preseason LastSeason renders its own SectionHeading naming the season it is showing. -->
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
