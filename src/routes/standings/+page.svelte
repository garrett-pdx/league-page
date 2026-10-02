<script>
	import { Standings } from '$lib/components'
	import { PageHeader } from '$lib/Design';
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
</style>

<PageHeader title="Standings" intro="Wins first, then points scored. The table does not take requests." />

<div class="holder">
	<Standings {standingsData} {leagueTeamManagersData} {leagueHistoryData} />

	<!-- Under the table, not inside it: Standings/index.svelte is upstream's. -->
	<ScheduleLuck {standingsData} {matchupsData} {leagueTeamManagersData} {nflStateData} {gamesData} />
</div>
