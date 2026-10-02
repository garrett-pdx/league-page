<script>
	import LinearProgress from '@smui/linear-progress';
	import { Rivalry } from '$lib/components'
	import { PageHeader } from '$lib/Design';
	import HeadToHeadGrid from '$lib/History/HeadToHeadGrid.svelte';
	import { waitForAll } from '$lib/utils/helper';

	export let data;
	const {
        leagueTeamManagerData,
        playersData,
        transactionsData,
        recordsData,
        gamesData,
    } = data;

    /*
    Reactive, unlike the rest of the destructuring above: the head-to-head grid links to
    /rivalry?player_one=..&player_two=.. from this same page, and SvelteKit keeps the component
    alive across that navigation. A plain const would still hold the first pair.
    */
    $: playerOne = data.playerOne;
    $: playerTwo = data.playerTwo;
</script>

<style>
	.holder {
		position: relative;
		z-index: 1;
	}
	/* where the grid's links land; clear of the sticky 61px phone bar */
	#compare {
		scroll-margin-top: 70px;
	}
	.loading {
		display: block;
		width: 85%;
		max-width: 500px;
		margin: 80px auto;
	}
</style>

<PageHeader title="Rivalry" intro="Pick any two managers. The history is already in the books." />

<div class="holder">
	<HeadToHeadGrid {gamesData} leagueTeamManagersData={leagueTeamManagerData} />

	<div id="compare"></div>
	{#await waitForAll(leagueTeamManagerData, playersData, transactionsData, recordsData)}
		<div class="loading">
			<p>Gathering information...</p>
			<br />
			<LinearProgress indeterminate />
		</div>
	{:then [leagueTeamManagers, playersInfo, transactionsInfo, recordsInfo]}
		<!-- promise was fulfilled -->
		<Rivalry {leagueTeamManagers} {playersInfo} {transactionsInfo} {recordsInfo} {playerOne} {playerTwo} />
	{:catch error}
		<!-- promise was rejected -->
		<p>Something went wrong: {error.message}</p>
	{/await}
</div>
