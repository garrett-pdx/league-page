<script>
	import { Awards } from '$lib/components'
	import HallOfFame from '$lib/Awards/HallOfFame.svelte';
	import { waitForAll } from '$lib/utils/helper';
	import LinearProgress from '@smui/linear-progress';

    export let data;
    const {awardsData, teamManagersData, leagueHistoryData} = data;
</script>

<style>
    .awards {
        display: block;
        margin: 30px auto;
		width: 95%;
		max-width: 1000px;
		position: relative;
		z-index: 1;
		overflow-y: hidden;
    }

	.loading {
		display: block;
		width: 85%;
		max-width: 500px;
		margin: 80px auto;
	}

	.nothingYet {
		display: block;
		width: 85%;
		max-width: 500px;
		margin: 80px auto;
		text-align: center;
	}
</style>

<div class="awards">
	{#await waitForAll(awardsData, teamManagersData, leagueHistoryData) }
		<div class="loading">
			<p>Retrieving awards data...</p>
			<LinearProgress indeterminate />
		</div>
	{:then [podiums, leagueTeamManagers, leagueHistory] }
		<!-- Plaque strip sits ABOVE the illustrated podiums rather than replacing them; the
		     podium scene is 379 lines of hand-tuned art with ten breakpoints. -->
		<HallOfFame {leagueHistory} {leagueTeamManagers} />

		{#each podiums as podium}
			<Awards {podium} {leagueTeamManagers} />
		{:else}
			<p class="nothingYet">No seasons have been completed yet, so no awards have been earned...</p>
		{/each}
	{:catch error}
		<!-- promise was rejected -->
		<p>Something went wrong: {error.message}</p>
	{/await}
</div>