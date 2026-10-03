<script>
    /*
    Stat Lab's entry point: waits for the two data files, then hands them to Lab, which holds
    everything synchronous. The pending block reserves most of a screen so the page doesn't jump
    when the controls and chart arrive.
    */
    import LinearProgress from '@smui/linear-progress';
    import Lab from './Lab.svelte';

    let { gamesData, historyData } = $props();
</script>

<style>
    .pending {
        min-height: 80vh;
        width: 85%;
        max-width: 500px;
        margin: 40px auto 0;
        text-align: center;
        color: var(--g555);
    }
</style>

{#await Promise.all([gamesData, historyData])}
    <div class="pending">
        <p>Loading every game since 2022…</p>
        <LinearProgress indeterminate />
    </div>
{:then [games, history]}
    <Lab {games} {history} />
{:catch error}
    <p class="pending">Stat Lab couldn’t load its data: {error.message}</p>
{/await}
