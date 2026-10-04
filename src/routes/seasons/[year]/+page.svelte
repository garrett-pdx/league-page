<script>
    import { PageHeader } from '$lib/Design';
    import SeasonPage from '$lib/Seasons/SeasonPage.svelte';
    import PreSleeperSeason from '$lib/Seasons/PreSleeperSeason.svelte';
    import { archiveYears, isComplete } from '$lib/Seasons/seasonData';
    import { preSleeperSeasons } from '$lib/utils/leagueInfo';

    export let data;

    // Reactive, and keyed below: following the previous/next links reuses this component with
    // new data, and every child computes from `year` once, on mount.
    $: ({year, history, gamesData, notesData, keepersData, playersData, leagueTeamManagersData} = data);
    $: years = archiveYears(history, preSleeperSeasons);
    // A pre-Sleeper season (league.json history.preSleeper) with no Sleeper season of its own.
    $: pre = history.seasons?.[String(year)] ? null : preSleeperSeasons.find((s) => s.season === year);
    $: newer = years.find((y, i) => years[i + 1] === year);
    $: older = years[years.indexOf(year) + 1];

    $: intro = pre
        ? (pre.intro || `Played on ${pre.platform}, before the league came to Sleeper.`)
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
        color: var(--brand700);
        font-family: var(--fontDisplay);
        letter-spacing: 0.06em;
        text-transform: uppercase;
        text-decoration: none;
    }

    @media (hover: hover) {
        .pager a:hover { background-color: var(--brand050); }
    }

    .pager a:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }

    .spacer { flex: 1; }
</style>

<PageHeader title="{year} Season" {intro} />

{#key year}
    {#if pre}
        <PreSleeperSeason {pre} {history} {playersData} />
    {:else}
        <SeasonPage {year} {history} {gamesData} {notesData} {keepersData} {playersData} {leagueTeamManagersData} />
    {/if}
{/key}

<nav class="pager" aria-label="Other seasons">
    {#if older}<a href="/seasons/{older}" rel="prev">← {older}</a>{:else}<span class="spacer"></span>{/if}
    <a href="/seasons">All seasons</a>
    {#if newer}<a href="/seasons/{newer}" rel="next">{newer} →</a>{:else}<span class="spacer"></span>{/if}
</nav>
