<script>
	import { Standings } from '$lib/components'
	import { PageHeader, SectionHeading } from '$lib/Design';
	import ScheduleLuck from '$lib/History/ScheduleLuck.svelte';

	export let data;
	const {standingsData, leagueTeamManagersData, leagueHistoryData, matchupsData, nflStateData, gamesData} = data;
</script>

<style>
	.holder {
		position: relative;
		z-index: 1;
		text-align: center;
	}

	/* Below 1200px the two tables stack, as they always have. Above it they sit side by side:
	   the standings are 550px wide and the schedule luck table 760px, and stacked on a 1440px
	   screen they were two different-width strips down the middle. */
	.pairHeading { display: none; }

	@media (min-width: 1200px) {
		.pair {
			display: grid;
			grid-template-columns: minmax(0, 5fr) minmax(0, 6fr);
			align-items: start;
			gap: 0 2rem;
			width: 96%;
			max-width: var(--pageMaxWide);
			margin: 0 auto;
		}

		/* The luck column opens with a heading; the standings column gets a twin so the tables
		   start on the same line. */
		.pairHeading { display: block; }
	}
</style>

<PageHeader title="Standings" intro="Wins first, then points scored. The table does not take requests." />

<div class="holder">
	<div class="pair">
		<div>
			<div class="pairHeading"><SectionHeading level={3}>The table</SectionHeading></div>
			<Standings {standingsData} {leagueTeamManagersData} {leagueHistoryData} />
		</div>

		<!-- Under the table, not inside it: Standings/index.svelte is upstream's. -->
		<div>
			<ScheduleLuck {standingsData} {matchupsData} {leagueTeamManagersData} {nflStateData} {gamesData} />
		</div>
	</div>
</div>
