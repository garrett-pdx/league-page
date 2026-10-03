<script>
	import { Awards } from '$lib/components'
	import HallOfFame from '$lib/Awards/HallOfFame.svelte';
	import { waitForAll } from '$lib/utils/helper';
	import LinearProgress from '@smui/linear-progress';
	import { PageHeader, Disclosure } from '$lib/Design';

    export let data;
    const {awardsData, teamManagersData, leagueHistoryData} = data;
</script>

<style>
    .awards {
        display: block;
        margin: 30px auto;
		width: 95%;
		max-width: var(--pageMax);
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

<PageHeader title="Trophy Room" intro="Champions, podiums and toilet bowl losers, kept permanently." />

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

		<!-- The latest season is the page; the other years fold away. Four seasons of podiums were
		     7,000px of scrolling, and the Hall of Fame above already carries the whole history. -->
		{#if podiums.length}
			<Awards podium={podiums[0]} {leagueTeamManagers} />
			{#if podiums.length > 1}
				<Disclosure label="Show earlier seasons" openLabel="Hide earlier seasons">
					{#each podiums.slice(1) as podium}
						<Awards {podium} {leagueTeamManagers} />
					{/each}
				</Disclosure>
			{/if}
		{:else}
			<p class="nothingYet">No seasons have been completed yet, so no awards have been earned...</p>
		{/if}
	{:catch error}
		<!-- promise was rejected -->
		<p>Something went wrong: {error.message}</p>
	{/await}
</div>