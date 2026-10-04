<script>
    import { PageHeader } from '$lib/Design';
    import { pageIntro } from '$lib/utils/leagueInfo';
    import StatLab from '$lib/StatLab/StatLab.svelte';

    let { data } = $props();
</script>

<PageHeader title="Stat Lab" intro={pageIntro('stat-lab')} />

<StatLab gamesData={data.gamesData} historyData={data.historyData} />
