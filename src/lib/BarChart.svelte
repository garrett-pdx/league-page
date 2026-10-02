<script>
    import { SegmentedControl } from '$lib/Design';
	import Bar from './Bar.svelte';

    export let graphs, leagueTeamManagers, curGraph = 0;

    const colors = [
        "--barChartOne",
        "--barChartTwo",
        "--barChartThree",
        "--barChartFour",
        "--barChartFive",
        "--barChartSix",
    ];

    // note that due to changig to horizontal, yMin and yMax are now used as xMin and xMax
    $: xMin = graphs[curGraph].secondStats.length > 0 ? graphs[curGraph].xMin/3 : graphs[curGraph].xMin;
    $: xMax = graphs[curGraph].xMax;
    $: stats = graphs[curGraph].stats;
    $: secondStats = graphs[curGraph].secondStats;
    $: managerIDs = graphs[curGraph].managerIDs;
    $: rosterIDs = graphs[curGraph].rosterIDs;
    $: labels = graphs[curGraph].labels;
    $: header = graphs[curGraph].header;
    $: year = graphs[curGraph].year;
    $: graphOptions = graphs.map((graph, ix) => ({value: ix, label: graph.short}));
</script>

<style>
    .chartWrapper {
		background-color: var(--fff);
        padding: 1em 0 0.5em;
        margin: 0 auto;
        max-width: 950px;
        box-shadow: var(--shadowCard);
    }

    .barChart {
        display: block;
        position: relative;
        width: 100%;
        height: 100%;
    }

    h6 {
        /* This is the chart's title, so it stays a real heading -- but headings now inherit the
           condensed display face, and with no size of its own it took MDC's headline6 at 20px
           in Oswald 400, which reads as body copy that happens to be narrow. Size and track it
           deliberately instead. Every other heading in the app does the same; MDC's stock scale
           is not usable as-is. */
        font-family: var(--fontDisplay);
        font-size: 1.05em;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--navy700);
        width: 100%;
        text-align: center;
        margin: 0 0 1em;
    }

    .buttonHolderG {
        text-align: center;
        margin: 1em 0 2em;
        padding: 0 12px;
    }

    @media (max-width: 1000px) {
        .chartWrapper {
            max-width: 95%;
        }
    }
    @media (max-width: 850px) {
        .chartWrapper {
            max-width: 100%;
        }
    }
</style>

<h6>{header}</h6>
<div class="chartWrapper">
    <div class="barChart" >
        {#each managerIDs as managerID, ix}
            <Bar {leagueTeamManagers} {managerID} rosterID={rosterIDs[ix]} {xMin} {xMax} stat={stats[ix]} secondStat={secondStats[ix]} {year} label={labels.stat} color={colors[ix % colors.length]} />
        {/each}
    </div>
</div>

{#if graphs.length > 1}
    <div class="buttonHolderG">
        <SegmentedControl options={graphOptions} bind:value={curGraph} ariaLabel="Chart" />
    </div>
{/if}
