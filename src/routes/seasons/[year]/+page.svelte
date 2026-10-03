<script>
    import { PageHeader } from '$lib/Design';
    import SeasonPage from '$lib/Seasons/SeasonPage.svelte';
    import EspnSeason from '$lib/Seasons/EspnSeason.svelte';
    import { archiveYears, isComplete, FOUNDING_SEASON } from '$lib/Seasons/seasonData';

    export let data;

    // Reactive, and keyed below: following the previous/next links reuses this component with
    // new data, and every child computes from `year` once, on mount.
    $: ({year, history, gamesData, notesData, keepersData, playersData, leagueTeamManagersData} = data);
    $: years = archiveYears(history);
    $: newer = years.find((y, i) => years[i + 1] === year);
    $: older = years[years.indexOf(year) + 1];

    $: intro = year === FOUNDING_SEASON
        ? 'The founding season, on ESPN. The draft is all that made it to Sleeper.'
        : isComplete(history, year)
            ? 'The table, the bracket, the draft and the trades, as they finished.'
            : 'Still being played. This is the archive copy, through the last completed week.';
</script>

<style>
    .pager {
        display: flex;
        justify-content: space-between;
        gap: 0.5rem;
        width: 94%;
        max-width: var(--pageMax);
        margin: 2.5rem auto 3rem;
    }

    .pager a {
        display: inline-flex;
        align-items: center;
        min-height: 44px;
        padding: 0 1.1em;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusPill);
        background-color: var(--fff);
        color: var(--navy700);
        font-family: var(--fontDisplay);
        letter-spacing: 0.06em;
        text-transform: uppercase;
        text-decoration: none;
    }

    @media (hover: hover) {
        .pager a:hover { background-color: var(--navy050); }
    }

    .pager a:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }

    .spacer { flex: 1; }
</style>

<PageHeader title="{year} Season" {intro} />

{#key year}
    {#if year === FOUNDING_SEASON}
        <EspnSeason {history} {playersData} />
    {:else}
        <SeasonPage {year} {history} {gamesData} {notesData} {keepersData} {playersData} {leagueTeamManagersData} />
    {/if}
{/key}

<nav class="pager" aria-label="Other seasons">
    {#if older}<a href="/seasons/{older}" rel="prev">← {older}</a>{:else}<span class="spacer"></span>{/if}
    <a href="/seasons">All seasons</a>
    {#if newer}<a href="/seasons/{newer}" rel="next">{newer} →</a>{:else}<span class="spacer"></span>{/if}
</nav>
