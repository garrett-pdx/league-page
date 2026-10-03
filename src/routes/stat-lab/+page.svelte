<script>
    import { PageHeader } from '$lib/Design';
    import StatLab from '$lib/StatLab/StatLab.svelte';

    let { data } = $props();
</script>

<PageHeader title="Stat Lab" intro="Every game since 2022. Filter it, sort it, chart it, and send the link to the group chat." />

<StatLab gamesData={data.gamesData} historyData={data.historyData} />
