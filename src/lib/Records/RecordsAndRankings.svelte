<script>
    import Button, { Group, Label } from '@smui/button';
    import { generateGraph, gotoManager, round } from '$lib/utils/helper';

  	import DataTable, { Head, Body, Row, Cell } from '@smui/data-table';
	import RecordTeam from './RecordTeam.svelte';
	import BarChart from '$lib/BarChart.svelte';

    export let key, tradesData, waiversData, weekRecords, weekLows, seasonLongRecords, seasonLongLows, showTies, winPercentages, fptsHistories, lineupIQs, prefix, blowouts, closestMatchups, allTime=false, leagueTeamManagers;

    let graphs = [];
    let curTable = 0;
    let curGraph = 0;

    let iqOffset = 0;
    let tables = [
        "Win Percentages",
        "Points",
        "Transactions",
    ]

    const year = allTime ? null : prefix;

    /*
    Sortable columns, for the four RANKING tables only.

    The six record tables above are deliberately NOT sortable. Each of those is a top-N list
    defined by its own metric -- "Single Week Scoring Records" IS points descending -- and its
    rank column is positional, so re-sorting would renumber rank into nonsense.

    Here re-ranking is the entire point: "who leads on points per game" is a different and
    equally legitimate question from "who leads on total points", and the rank column
    renumbering to match the chosen column is correct rather than misleading.

    Sorting only ever applies to numeric columns. Manager is left alone -- the cell renders a
    component, and the name it displays lives in leagueTeamManagers rather than on the row.
    */
    let sorts = {};

    const sortRanking = (table, field) => {
        const cur = sorts[table];
        // A newly picked column starts descending: for every stat in these tables the big end
        // is the interesting one. Clicking the already-active column flips direction.
        const dir = cur && cur.field === field ? -cur.dir : -1;
        sorts = {...sorts, [table]: {field, dir}};
    }

    /*
    All three helpers take the sort state as an explicit argument rather than closing over it.
    That is not style -- it is required. Svelte 4 reactivity tracks only what a reactive
    statement or template expression references SYNTACTICALLY, so `$: x = sortRows(rows, 'fpts')`
    does not depend on `sorts` just because sortRows reads it, and `{arrow(sorts, 'fpts','fptsFor')}`
    never re-runs when `sorts` is reassigned. Written that way the tables silently never sorted:
    clicks registered, state updated, nothing re-rendered. Passing `sorts` in makes the
    dependency visible to the compiler.
    */

    // Returns a sorted COPY -- these arrays are props, and sorting in place would also
    // reorder the bar charts built from the same data.
    /*
    Compare numerically whenever both sides parse as numbers.

    Not every stat on these rows is a JS number -- the derived ones (points per game, win
    percentage, lineup IQ) arrive as strings from toFixed(). A plain `a > b` therefore compares
    them lexicographically, which silently sorts "95.62" above "111.65" because "9" > "1".
    Points Against sorted correctly while Points Per Game did not, which is exactly what a
    string/number split looks like.
    */
    const compare = (a, b) => {
        const an = typeof a === 'number' ? a : parseFloat(a);
        const bn = typeof b === 'number' ? b : parseFloat(b);
        if(!Number.isNaN(an) && !Number.isNaN(bn)) return an - bn;
        return String(a).localeCompare(String(b));
    }

    const sortRows = (rows, table, sortState) => {
        const sort = sortState[table];
        if(!sort || !rows) return rows;
        return [...rows].sort((a, b) => {
            const c = compare(a[sort.field], b[sort.field]);
            if(c === 0) return 0;
            return c > 0 ? sort.dir : -sort.dir;
        });
    }

    const ariaSort = (sortState, table, field) => {
        const sort = sortState[table];
        if(!sort || sort.field !== field) return 'none';
        return sort.dir === -1 ? 'descending' : 'ascending';
    }

    const arrow = (sortState, table, field) => {
        const sort = sortState[table];
        if(!sort || sort.field !== field) return '';
        return sort.dir === -1 ? '▼' : '▲';
    }

    $: sortedLineupIQs = sortRows(lineupIQs, 'iq', sorts);
    $: sortedWinPercentages = sortRows(winPercentages, 'win', sorts);
    $: sortedFptsHistories = sortRows(fptsHistories, 'fpts', sorts);
    $: sortedTransactions = sortRows(transactions, 'trans', sorts);

    const changeTable = (newGraph) => {
        switch (newGraph) {
            case 0 - iqOffset:
            case (4 + (99 * iqOffset)):
                curTable = 0;
                break;
            case 1 - iqOffset:
            case 2 - iqOffset:
                curTable = 1 - iqOffset;
                break;
            case 3 - iqOffset:
                curTable = 2 - iqOffset;
                break;
            case 5 - (2 * iqOffset):
            case 6 - (2 * iqOffset):
                curTable = 3 - iqOffset;
                break;
            default:
                curTable = 0;
                break;
        }
    }

    const changeGraph = (newTable) => {
        switch (newTable) {
            case 0 - iqOffset:
                if(curGraph == 0 || curGraph == 4) {
                    break;
                }
                curGraph = 0;
                break;
            case 1 - iqOffset:
                if(curGraph == 1 - iqOffset || curGraph == 2 - iqOffset) {
                    break;
                }
                curGraph = 1 - iqOffset;
                break;
            case 2 - iqOffset:
                curGraph = 3 - iqOffset;
                break;
            case 3 - iqOffset:
                if(curGraph == 5 - (2 * iqOffset) || curGraph == 6 - (2 * iqOffset)) {
                    break;
                }
                curGraph = 5 - (2 * iqOffset);
                break;
            default:
                curGraph = 0;
                break;
        }
    }

    const setGraphs = (wD) => {
        const lineupIQGraph = {
            stats: lineupIQs,
            x: "Lineup IQ",
            stat: "%",
            header: "Manager Lineup IQ",
            field: "iq",
            short: "Lineup IQ"
        }

        const potentialPointsGraph = {
            stats: lineupIQs,
            x: "Points",
            stat: "",
            header: "Potential Points vs Points",
            field: "potentialPoints",
            secondField: "fpts",
            short: "Potential Points"
        }

        const winsGraph = {
            stats: winPercentages,
            x: "Wins",
            stat: "",
            header: "Team Wins",
            field: "wins",
            short: "Wins"
        }

        const winPercentagesGraph = {
            stats: winPercentages,
            x: "Win Percentage",
            stat: "%",
            header: "Team Win Percentages",
            field: "percentage",
            short: "Win Percentage"
        }

        const fptsHistoriesGraph = {
            stats: fptsHistories,
            x: "Fantasy Points",
            stat: "",
            header: "Team Fantasy Points",
            field: "fptsFor",
            short: "Fantasy Points"
        }

        const tradesGraph = {
            stats: tradesData,
            x: "# of trades",
            stat: "",
            header: "Number of Trades Managers Have Made",
            field: "trades",
            short: "Trades"
        }

        const waiversGraph = {
            stats: wD,
            x: "# of Waiver Moves",
            stat: "",
            header: "Waivers Moves Managers Have Made",
            field: "waivers",
            short: "Waivers"
        }
        const gs = [];

        if(lineupIQs[0]?.potentialPoints) {
            gs.push(generateGraph(lineupIQGraph, year));
        }
        gs.push(generateGraph(winsGraph, year, 5));
        gs.push(generateGraph(winPercentagesGraph, year));
        gs.push(generateGraph(fptsHistoriesGraph, year));
        if(lineupIQs[0]?.potentialPoints) {
            gs.push(generateGraph(potentialPointsGraph, year, 10, 0));
        }
        if(key == "regularSeasonData") {
            gs.push(generateGraph(tradesGraph, year));
            gs.push(generateGraph(waiversGraph, year));
        }

        curGraph = 0;
        graphs = gs;
    }

    const setTransactionsAndGraphs = (wD) => {
        if(wD[0].rosterID) {
            for(let i = 1; i <= waiversData.length; i++) {
                if(!tradesData.find(t => t.rosterID == i)) {
                    tradesData.push({
                        rosterID: i,
                        trades: 0,
                    })
                }
            }
        }
        if(wD[0].managerID) {
            for(const userID in leagueTeamManagers.users) {
                if(!tradesData.find(t => t.managerID == userID)) {
                    tradesData.push({
                        managerID: userID,
                        trades: 0,
                    })
                }
            }
        }
        const transactions = [];

        for(const w of wD) {
            let trades = 0;
            if(tradesData[0].managerID) {
                trades = tradesData.find(t => t.managerID == w.managerID)?.trades || 0;
            } else if(tradesData[0].rosterID) {
                trades = tradesData.find(t => t.rosterID == w.rosterID)?.trades || 0;
            }
            const waivers = w.waivers;
            transactions.push({
                rosterID: w.rosterID,
                managerID: w.managerID,
                trades,
                waivers,
            })
        }

        setGraphs(wD)
        return transactions;
    }

    const setTables = (lIQs) => {
        const t = [
            "Win Percentages",
            "Points",
        ]
        if(key == "regularSeasonData") {
            t.push("Transactions")
        }
        if(!lIQs[0]?.potentialPoints) {
            iqOffset = 1;
        } else {
            t.unshift('Lineup IQs');
        }
        tables = t
    }

    $: transactions =  setTransactionsAndGraphs(waiversData)
    $: changeTable(curGraph);
    $: changeGraph(curTable);
    $: setTables(lineupIQs)
    
    let innerWidth;

</script>

<svelte:window bind:innerWidth={innerWidth} />

<style>
    :global(.headerPrimary) {
        background-color: var(--headerPrimary);
        text-align: center;
    }

    .italic {
        display: block;
        font-style: italic;
        font-size: 0.9em;
        color: var(--g999);
    }

    :global(.recordTable) {
        box-shadow: var(--shadowCard);
        margin: 2em;
        /* Without this the table's intrinsic width wins and the whole PAGE scrolls sideways
           on a phone -- measured 388px of content in a 375px viewport, with 449 elements
           past the right edge. MDC already gives .mdc-data-table__table-container its own
           overflow-x: auto, so capping the outer box moves the scroll inside the table
           where it belongs instead of breaking the layout. */
        max-width: 100%;
        box-sizing: border-box;
    }

    @media (max-width: 600px) {
        /* 2em each side leaves too little room for the narrowest tables to lay out */
        :global(.recordTable) {
            margin: 1.5em 0;
        }
    }

    :global(.rankingTable) {
        display: table;
        box-shadow: var(--shadowCard);
        margin: 2em auto 0.5em;
    }

    .fullFlex {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-around;
        margin: 3em auto 5em;
    }

    /* Sortable ranking headers. A real <button> inside the th rather than a click handler on
       the th itself, so keyboard operation and focus come for free -- the same reason the
       constitution's table of contents is buttons rather than clickable headings. */
    :global(.rankingTable .sortBtn) {
        background: none;
        border: none;
        padding: 0;
        margin: 0;
        font: inherit;
        color: inherit;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 0.3em;
        white-space: nowrap;
    }

    :global(.rankingTable .sortBtn:hover) {
        color: var(--accentInk);
    }

    :global(.rankingTable .sortBtn:focus-visible) {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
        border-radius: var(--radiusXs);
    }

    /* Reserve the arrow's width at all times so activating a column does not reflow the
       header row and shift the other columns sideways. */
    :global(.rankingTable .arrow) {
        display: inline-block;
        min-width: 0.75em;
        font-size: 0.8em;
        line-height: 1;
        color: var(--accentInk);
    }

    .rankingHolder {
        display: block;
        width: 100%;
        overflow-x: hidden;
    }

    .subTitle {
        font-style: italic;
        /* was 0.7em #888: grey at 3.54:1, below AA, at the smallest size on the page.
           --g555 measures 7.46:1 on white, and 0.8em keeps it subordinate without shrinking
           it past legibility. */
        font-size: 0.8em;
        color: var(--g555);
        line-height: 1.2em;
    }

    h4 {
        text-align: center;
        margin: 2em 0 1em;
    }

    .rankingTableWrapper {
        width: 25%;
    }

    .rankingInner {
        position: relative;
        display: flex;
        flex-wrap: nowrap;
        width: 400%;
		transition: margin-left 0.8s;
    }

    .buttonHolder {
        text-align: center;
        margin: 2em 0 4em;
    }

    :global(.cellName) {
        cursor: pointer;
        line-height: 1.2em;
        padding-left: 8px;
    }

    :global(.differentialName) {
        padding: 0.7em 0;
    }

    :global(.rank) {
        padding-right: 0;
    }

    .vs {
        padding-left: 0.6em;
        margin: 0.5em 0;
    }

    :global(.mdc-data-table__cell, .mdc-data-table__header-cell) {
        border-bottom-color: var(--borderOverride);
    }

    /* Start button resizing */

    @media (max-width: 540px) {
        :global(.buttonHolder .selectionButtons) {
            font-size: 0.6em;
        }
    }

    @media (max-width: 415px) {
        :global(.buttonHolder .selectionButtons) {
            font-size: 0.5em;
            padding: 0 6px;
            height: 30px;
        }
    }

    @media (max-width: 315px) {
        :global(.buttonHolder .selectionButtons) {
            font-size: 0.45em;
            padding: 0 3px;
        }
    }

    @media (max-width: 265px) {
        :global(.buttonHolder .selectionButtons) {
            font-size: 0.4em;
            padding: 0 2px;
            height: 24px;
            min-width: 40px;
        }
    }

    /* End button resizing */

    /* Start record table resizing */

    @media (max-width: 510px) {
        :global(.recordTable th) {
            font-size: 0.8em;
            padding: 1px 12px;
        }
        :global(.recordTable td) {
            font-size: 0.8em;
            padding: 1px 12px;
        }

        .vsRecord {
            margin: .6em 0;
        }
    }

    @media (max-width: 480px) {
        :global(.rank) {
            padding: 1px 0 1px 5px !important;
        }
        :global(.rank) {
            padding: 1px 0 1px 5px !important;
        }
    }

    @media (max-width: 460px) {
        :global(.recordTable th) {
            font-size: 0.6em;
            padding: 1px 12px;
        }
        :global(.recordTable td) {
            font-size: 0.6em;
            padding: 1px 12px;
        }
    }

    @media (max-width: 365px) {
        :global(.recordTable th) {
            font-size: 0.5em;
            padding: 1px 8px;
        }
        :global(.recordTable td) {
            font-size: 0.5em;
            padding: 1px 8px;
        }
    }

    @media (max-width: 265px) {
        :global(.recordTable th) {
            font-size: 0.4em;
            padding: 1px 5px;
        }
        :global(.recordTable td) {
            font-size: 0.4em;
            padding: 1px 5px;
        }
    }

    /* END record table resizing */

    /* Start ranking table resizing */

    @media (max-width: 570px) {
        :global(.rankingTable th) {
            font-size: 0.8em;
            max-width: 110px;
            white-space: break-spaces;
            padding: 1px 12px;
        }
        :global(.rankingTable td) {
            font-size: 0.8em;
            max-width: 110px;
            white-space: break-spaces;
            padding: 1px 12px;
        }
    }

    @media (max-width: 410px) {
        :global(.rankingTable th) {
            font-size: 0.6em;
            max-width: 90px;
            white-space: break-spaces;
            padding: 1px 12px;
        }
        :global(.rankingTable td) {
            font-size: 0.6em;
            max-width: 90px;
            white-space: break-spaces;
            padding: 1px 12px;
        }
    }

    @media (max-width: 340px) {
        :global(.rankingTable th) {
            font-size: 0.55em;
            max-width: 80px;
            white-space: break-spaces;
            padding: 1px 6px;
        }
        :global(.rankingTable td) {
            font-size: 0.55em;
            max-width: 80px;
            white-space: break-spaces;
            padding: 1px 6px;
        }
    }

    /* END ranking table resizing */
</style>

<h4>{prefix} Records</h4>

<div class="fullFlex">
    {#if weekRecords && weekRecords.length}
        <DataTable class="recordTable">
            <Head>
                <Row class="rTableHeader">
                    <Cell class="header headerPrimary" colspan=4>{prefix} {key == "playoffData" ? "Playoff " : ""}Single Week Scoring Records</Cell>
                </Row>
                <Row>
                    <Cell class="header rank"></Cell>
                    <Cell class="header">Manager</Cell>
                    <Cell class="header">Week</Cell>
                    <Cell class="header">Total Points</Cell>
                </Row>
            </Head>
            <Body>
                {#each weekRecords as leagueWeekRecord, ix}
                    <Row>
                        <Cell class="rank">{ix + 1}</Cell>
                        <Cell class="cellName" onclick={() => gotoManager({year: leagueWeekRecord.year || prefix, leagueTeamManagers, rosterID: leagueWeekRecord.rosterID})}>
                            <RecordTeam {leagueTeamManagers} rosterID={leagueWeekRecord.rosterID} year={allTime ? leagueWeekRecord.year : prefix} />
                        </Cell>
                        <Cell>{allTime ? leagueWeekRecord.year + " " : "" }{key == "regularSeasonData" ? "Week " : ""}{leagueWeekRecord.week}</Cell>
                        <Cell>{round(leagueWeekRecord.fpts)}</Cell>
                    </Row>
                {/each}
            </Body>
        </DataTable>
    {/if}

    {#if weekLows && weekLows.length}
        <DataTable class="recordTable">
            <Head>
                <Row>
                    <Cell class="header headerPrimary" colspan=4>{prefix} {key == "playoffData" ? "Playoff " : ""}Single Week Scoring Lows</Cell>
                </Row>
                <Row>
                    <Cell class="header rank"></Cell>
                    <Cell class="header">Manager</Cell>
                    <Cell class="header">Week</Cell>
                    <Cell class="header">Total Points</Cell>
                </Row>
            </Head>
            <Body>
                {#each weekLows as leagueWeekLow, ix}
                    <Row>
                        <Cell class="rank">{ix + 1}</Cell>
                        <Cell class="cellName" onclick={() => gotoManager({year: leagueWeekLow.year || prefix, leagueTeamManagers, rosterID: leagueWeekLow.rosterID})}>
                            <RecordTeam {leagueTeamManagers} rosterID={leagueWeekLow.rosterID} year={allTime ? leagueWeekLow.year : prefix} />
                        </Cell>
                        <Cell>{allTime ? leagueWeekLow.year + " " : "" }{key == "regularSeasonData" ? "Week " : ""}{leagueWeekLow.week}</Cell>
                        <Cell>{round(leagueWeekLow.fpts)}</Cell>
                    </Row>
                {/each}
            </Body>
        </DataTable>
    {/if}

    {#if allTime && key == "regularSeasonData"}
        <DataTable class="recordTable">
            <Head>
                <Row>
                    <Cell class="header headerPrimary" colspan=5>All-Time Highest Season Points<span class="italic">Ranked by PPG</span></Cell>
                </Row>
                <Row>
                    <Cell class="header rank"></Cell>
                    <Cell class="header">Manager</Cell>
                    <Cell class="header">Year</Cell>
                    <Cell class="header">Total Points</Cell>
                    <Cell class="header">PPG</Cell>
                </Row>
            </Head>
            <Body>
                {#each seasonLongRecords as mostSeasonLongPoint, ix}
                    <Row>
                        <Cell class="rank">{ix + 1}</Cell>
                        <Cell class="cellName" onclick={() => gotoManager({year: mostSeasonLongPoint.year, leagueTeamManagers, rosterID: mostSeasonLongPoint.rosterID})}>
                            <RecordTeam {leagueTeamManagers} rosterID={mostSeasonLongPoint.rosterID} year={mostSeasonLongPoint.year} />
                        </Cell>
                        <Cell>{mostSeasonLongPoint.year}</Cell>
                        <Cell>{round(mostSeasonLongPoint.fpts)}</Cell>
                        <Cell>{mostSeasonLongPoint.fptsPerGame}</Cell>
                    </Row>
                {/each}
            </Body>
        </DataTable>
    {/if}
    
    {#if allTime && key == "regularSeasonData"}
        <DataTable class="recordTable">
            <Head>
                <Row>
                    <Cell class="header headerPrimary" colspan=5>All-Time Lowest Season Points<span class="italic">Ranked by PPG</span></Cell>
                </Row>
                <Row>
                    <Cell class="header rank"></Cell>
                    <Cell class="header">Manager</Cell>
                    <Cell class="header">Year</Cell>
                    <Cell class="header">Total Points</Cell>
                    <Cell class="header">PPG</Cell>
                </Row>
            </Head>
            <Body>
                {#each seasonLongLows as leastSeasonLongPoint, ix}
                    <Row>
                        <Cell class="rank">{ix + 1}</Cell>
                        <Cell class="cellName" onclick={() => gotoManager({year: leastSeasonLongPoint.year, leagueTeamManagers, rosterID: leastSeasonLongPoint.rosterID})}>
                            <RecordTeam {leagueTeamManagers} rosterID={leastSeasonLongPoint.rosterID} year={leastSeasonLongPoint.year} />
                        </Cell>
                        <Cell>{leastSeasonLongPoint.year}</Cell>
                        <Cell>{round(leastSeasonLongPoint.fpts)}</Cell>
                        <Cell>{leastSeasonLongPoint.fptsPerGame}</Cell>
                    </Row>
                {/each}
            </Body>
        </DataTable>
    {/if}

    {#if blowouts && blowouts.length}
        <DataTable class="recordTable">
            <Head>
                <Row>
                    <Cell class="header headerPrimary" colspan=4>{prefix} Largest {key == "playoffData" ? "Playoff " : ""}Blowouts</Cell>
                </Row>
                <Row>
                    <Cell class="header rank"></Cell>
                    <Cell class="header">Matchup</Cell>
                    <Cell class="header">Week</Cell>
                    <Cell class="header">Differential</Cell>
                </Row>
            </Head>
            <Body>
                {#each blowouts as blowout, ix}
                    <Row>
                        <Cell class="rank">{ix + 1}</Cell>
                        <Cell class="cellName differentialName">
                            <div class="vsRecord">
                                <div onclick={() => gotoManager({year: blowout.year || prefix, leagueTeamManagers, rosterID: blowout.home.rosterID})}>
                                    <RecordTeam {leagueTeamManagers} rosterID={blowout.home.rosterID} year={allTime ? blowout.year : prefix} compressed={true} points={round(blowout.home.fpts)} />
                                </div>
                                <p class="vs">
                                    vs
                                </p>
                                <div onclick={() => gotoManager({year: blowout.year || prefix, leagueTeamManagers, rosterID: blowout.away.rosterID})}>
                                    <RecordTeam {leagueTeamManagers} rosterID={blowout.away.rosterID} year={allTime ? blowout.year : prefix} compressed={true} points={round(blowout.away.fpts)} />
                                </div>
                            </div>
                        </Cell>
                        <Cell>{allTime ? blowout.year + " " : "" }{key == "regularSeasonData" ? "Week " : ""}{blowout.week}</Cell>
                        <Cell>{round(blowout.differential)}</Cell>
                    </Row>
                {/each}
            </Body>
        </DataTable>
    {/if}

    {#if closestMatchups && closestMatchups.length}
        <DataTable class="recordTable">
            <Head>
                <Row>
                    <Cell class="header headerPrimary" colspan=4>{prefix} Narrowest {key == "playoffData" ? "Playoff " : ""}Wins</Cell>
                </Row>
                <Row>
                    <Cell class="header rank"></Cell>
                    <Cell class="header">Matchup</Cell>
                    <Cell class="header">Week</Cell>
                    <Cell class="header">Differential</Cell>
                </Row>
            </Head>
            <Body>
                {#each closestMatchups as closestMatchup, ix}
                    <Row>
                        <Cell class="rank">{ix + 1}</Cell>
                        <Cell class="cellName differentialName">
                            <div class="vsRecord">
                                <div onclick={() => gotoManager({year: closestMatchup.year || prefix, leagueTeamManagers, rosterID: closestMatchup.home.rosterID})}>
                                    <RecordTeam {leagueTeamManagers} rosterID={closestMatchup.home.rosterID} year={allTime ? closestMatchup.year : prefix} compressed={true} points={round(closestMatchup.home.fpts)} />
                                </div>
                                <p class="vs">
                                    vs
                                </p>
                                <div onclick={() => gotoManager({year: closestMatchup.year || prefix, leagueTeamManagers, rosterID: closestMatchup.away.rosterID})}>
                                    <RecordTeam {leagueTeamManagers} rosterID={closestMatchup.away.rosterID} year={allTime ? closestMatchup.year : prefix} compressed={true} points={round(closestMatchup.away.fpts)} />
                                </div>
                            </div>
                        </Cell>
                        <Cell>{allTime ? closestMatchup.year + " " : "" }{key == "regularSeasonData" ? "Week " : ""}{closestMatchup.week}</Cell>
                        <Cell>{round(closestMatchup.differential)}</Cell>
                    </Row>
                {/each}
            </Body>
        </DataTable>
    {/if}
</div>

<h4>{prefix} {key == "playoffData" ? "Playoff " : ""}Rankings</h4>

{#if graphs.length}
    <BarChart {graphs} bind:curGraph={curGraph} {leagueTeamManagers} />
{/if}

<div class="rankingHolder">
    <div class="rankingInner" style="margin-left: -{100 * curTable}%;">
        {#if lineupIQs[0]?.potentialPoints}
            <div class="rankingTableWrapper">
                <DataTable class="rankingTable">
                    <Head>
                        <Row>
                            <Cell class="header headerPrimary" colspan=5>
                                {prefix} {key == "playoffData" ? "Playoff " : ""}Lineup IQ Rankings
                                <div class="subTitle">
                                    The percentage of potential points each manager has captured
                                </div>
                            </Cell>
                        </Row>
                        <Row>
                            <Cell class="header"></Cell>
                            <Cell class="header">Manager</Cell>
                            <Cell class="header" aria-sort={ariaSort(sorts, 'iq', 'iq')}>
                                <button type="button" class="sortBtn" onclick={() => sortRanking('iq', 'iq')}>Lineup IQ<span class="arrow">{arrow(sorts, 'iq', 'iq')}</span></button>
                            </Cell>
                            <Cell class="header" aria-sort={ariaSort(sorts, 'iq', 'fpts')}>
                                <button type="button" class="sortBtn" onclick={() => sortRanking('iq', 'fpts')}>Points<span class="arrow">{arrow(sorts, 'iq', 'fpts')}</span></button>
                            </Cell>
                            <Cell class="header" aria-sort={ariaSort(sorts, 'iq', 'potentialPoints')}>
                                <button type="button" class="sortBtn" onclick={() => sortRanking('iq', 'potentialPoints')}>Potential Points<span class="arrow">{arrow(sorts, 'iq', 'potentialPoints')}</span></button>
                            </Cell>
                        </Row>
                    </Head>
                    <Body>
                        {#each sortedLineupIQs as lineupIQ, ix}
                            <Row>
                                <Cell>{ix + 1}</Cell>
                                <Cell class="cellName" onclick={() => gotoManager({year: lineupIQ.year || prefix, leagueTeamManagers, managerID: lineupIQ.managerID, rosterID: lineupIQ.rosterID})}>
                                    <RecordTeam {leagueTeamManagers} managerID={lineupIQ.managerID} rosterID={lineupIQ.rosterID} year={allTime ? lineupIQ.year : prefix} />
                                </Cell>
                                <Cell>{lineupIQ.iq}%</Cell>
                                <Cell>{round(lineupIQ.fpts)}</Cell>
                                <Cell>{round(lineupIQ.potentialPoints)}</Cell>
                            </Row>
                        {/each}
                    </Body>
                </DataTable>
            </div>
        {/if}

        <div class="rankingTableWrapper">
            <DataTable class="rankingTable">
                <Head>
                    <Row>
                        <Cell class="header headerPrimary" colspan=6>{prefix} {key == "playoffData" ? "Playoff " : ""}Win Percentages Rankings</Cell>
                    </Row>
                    <Row>
                        <Cell class="header"></Cell>
                        <Cell class="header">Manager</Cell>
                        <Cell class="header" aria-sort={ariaSort(sorts, 'win', 'percentage')}>
                            <button type="button" class="sortBtn" onclick={() => sortRanking('win', 'percentage')}>Win %<span class="arrow">{arrow(sorts, 'win', 'percentage')}</span></button>
                        </Cell>
                        <Cell class="header" aria-sort={ariaSort(sorts, 'win', 'wins')}>
                            <button type="button" class="sortBtn" onclick={() => sortRanking('win', 'wins')}>Wins<span class="arrow">{arrow(sorts, 'win', 'wins')}</span></button>
                        </Cell>
                        {#if showTies}
                            <Cell class="header" aria-sort={ariaSort(sorts, 'win', 'ties')}>
                                <button type="button" class="sortBtn" onclick={() => sortRanking('win', 'ties')}>Ties<span class="arrow">{arrow(sorts, 'win', 'ties')}</span></button>
                            </Cell>
                        {/if}
                        <Cell class="header" aria-sort={ariaSort(sorts, 'win', 'losses')}>
                            <button type="button" class="sortBtn" onclick={() => sortRanking('win', 'losses')}>Losses<span class="arrow">{arrow(sorts, 'win', 'losses')}</span></button>
                        </Cell>
                    </Row>
                </Head>
                <Body>
                    {#each sortedWinPercentages as winPercentage, ix}
                        <Row>
                            <Cell>{ix + 1}</Cell>
                            <Cell class="cellName" onclick={() => gotoManager({year: winPercentage.year || prefix, leagueTeamManagers, rosterID: winPercentage.rosterID, managerID: winPercentage.managerID})}>
                                <RecordTeam {leagueTeamManagers} managerID={winPercentage.managerID} rosterID={winPercentage.rosterID} year={allTime ? winPercentage.year : prefix} />
                            </Cell>
                            <Cell>{winPercentage.percentage}%</Cell>
                            <Cell>{winPercentage.wins}</Cell>
                            {#if showTies}
                                <Cell>{winPercentage.ties}</Cell>
                            {/if}
                            <Cell>{winPercentage.losses}</Cell>
                        </Row>
                    {/each}
                </Body>
            </DataTable>
        </div>

        <div class="rankingTableWrapper">
            <DataTable class="rankingTable">
                <Head>
                    <Row>
                        <Cell class="header headerPrimary" colspan=5>
                            {prefix} {key == "playoffData" ? "Playoff " : ""}Fantasy Points Rankings
                        </Cell>
                    </Row>
                    <Row>
                        <Cell class="header"></Cell>
                        <Cell class="header">Manager</Cell>
                        <Cell class="header" aria-sort={ariaSort(sorts, 'fpts', 'fptsFor')}>
                            <button type="button" class="sortBtn" onclick={() => sortRanking('fpts', 'fptsFor')}>Points For<span class="arrow">{arrow(sorts, 'fpts', 'fptsFor')}</span></button>
                        </Cell>
                        <Cell class="header" aria-sort={ariaSort(sorts, 'fpts', 'fptsAgainst')}>
                            <button type="button" class="sortBtn" onclick={() => sortRanking('fpts', 'fptsAgainst')}>Points Against<span class="arrow">{arrow(sorts, 'fpts', 'fptsAgainst')}</span></button>
                        </Cell>
                        <Cell class="header" aria-sort={ariaSort(sorts, 'fpts', 'fptsPerGame')}>
                            <button type="button" class="sortBtn" onclick={() => sortRanking('fpts', 'fptsPerGame')}>Points Per Game<span class="arrow">{arrow(sorts, 'fpts', 'fptsPerGame')}</span></button>
                        </Cell>
                    </Row>
                </Head>
                <Body>
                    {#each sortedFptsHistories as fptsHistory, ix}
                        <Row>
                            <Cell>{ix + 1}</Cell>
                            <Cell class="cellName" onclick={() => gotoManager({year: fptsHistory.year || prefix, leagueTeamManagers, rosterID: fptsHistory.rosterID, managerID: fptsHistory.managerID})}>
                                <RecordTeam {leagueTeamManagers} managerID={fptsHistory.managerID} rosterID={fptsHistory.rosterID} year={allTime ? fptsHistory.year : prefix} />
                            </Cell>
                            <Cell>{round(fptsHistory.fptsFor)}</Cell>
                            <Cell>{round(fptsHistory.fptsAgainst)}</Cell>
                            <Cell>{round(fptsHistory.fptsPerGame)}</Cell>
                        </Row>
                    {/each}
                </Body>
            </DataTable>
        </div>

        <div class="rankingTableWrapper">
            <DataTable class="rankingTable">
                <Head>
                    <Row>
                        <Cell class="header headerPrimary" colspan=4>
                            {prefix} Transaction Totals
                        </Cell>
                    </Row>
                    <Row>
                        <Cell class="header"></Cell>
                        <Cell class="header">Manager</Cell>
                        <Cell class="header" aria-sort={ariaSort(sorts, 'trans', 'trades')}>
                            <button type="button" class="sortBtn" onclick={() => sortRanking('trans', 'trades')}>Trades<span class="arrow">{arrow(sorts, 'trans', 'trades')}</span></button>
                        </Cell>
                        <Cell class="header" aria-sort={ariaSort(sorts, 'trans', 'waivers')}>
                            <button type="button" class="sortBtn" onclick={() => sortRanking('trans', 'waivers')}>Waivers<span class="arrow">{arrow(sorts, 'trans', 'waivers')}</span></button>
                        </Cell>
                    </Row>
                </Head>
                <Body>
                    {#each sortedTransactions as transaction, ix}
                        <Row>
                            <Cell>{ix + 1}</Cell>
                            <Cell class="cellName" onclick={() => gotoManager({year: transaction.year || prefix, leagueTeamManagers, rosterID: transaction.rosterID, managerID: transaction.managerID})}>
                                <RecordTeam {leagueTeamManagers} managerID={transaction.managerID} rosterID={transaction.rosterID} year={allTime ? transaction.year : prefix} />
                            </Cell>
                            <Cell>{transaction.trades}</Cell>
                            <Cell>{transaction.waivers}</Cell>
                        </Row>
                    {/each}
                </Body>
            </DataTable>
        </div>

    </div>
</div>

<div class="buttonHolder">
    <Group variant="outlined">
        {#each tables as table, ix}
            <Button class="selectionButtons" onclick={() => curTable = ix} variant="{curTable == ix ? "raised" : "outlined"}">
                <Label>{table}</Label>
            </Button>
        {/each}
    </Group>
</div>