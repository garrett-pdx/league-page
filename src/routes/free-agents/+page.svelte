<script>
	import LinearProgress from '@smui/linear-progress';
    import FreeAgents from '$lib/FreeAgents/FreeAgents.svelte';

	export let data;
	const {freeAgents, extras} = data;
</script>

<style>
	.main {
		position: relative;
		z-index: 1;
	}
    .loading {
        display: block;
        width: 85%;
        max-width: 500px;
        margin: 80px auto;
    }
</style>

<div class="main">
    {#await Promise.all([freeAgents, extras])}
        <div class="loading">
            <p>Checking every depth chart in the league...</p>
            <LinearProgress indeterminate />
        </div>
    {:then [faData, [playersData, nflState]]}
        <FreeAgents {faData} playersInfo={playersData} {nflState} />
    {:catch error}
        <p>Something went wrong: {error.message}</p>
    {/await}
</div>
