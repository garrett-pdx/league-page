<script>
    /*
    A manager's finish in every completed season, each linking to that season's archive page.
    Mounted under the Career Stats tiles in Managers/Manager.svelte.

    finishes   getManagerCareer(...).finishes: [{season, place}], oldest first, completed
               seasons only (final_standings never holds an unplayed one)
    */
    import { ordinal } from '$lib/utils/helper';

    export let finishes = [];
</script>

<style>
    .finishes {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 0.4rem;
        margin: 0.8em 0 0;
        padding: 0;
        list-style: none;
    }

    a {
        display: inline-flex;
        align-items: center;
        gap: 0.4em;
        min-height: 44px;
        padding: 0 0.9em;
        box-sizing: border-box;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusPill);
        background-color: var(--fff);
        color: var(--navy700);
        text-decoration: none;
        font-size: 0.9rem;
        font-variant-numeric: tabular-nums;
    }

    .year { color: var(--g555); }
    .place { font-weight: 700; }

    .champ {
        background-color: var(--goldFill);
        border-color: var(--goldFill);
        color: var(--goldOnFill);
    }

    .champ .year { color: var(--goldOnFill); }

    @media (hover: hover) {
        a:hover { background-color: var(--navy050); }
        a.champ:hover { background-color: var(--goldFill); text-decoration: underline; }
    }

    a:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }
</style>

{#if finishes.length}
    <ul class="finishes" aria-label="Finish by season">
        {#each finishes as f (f.season)}
            <li>
                <a href="/seasons/{f.season}" class:champ={f.place === 1}>
                    <span class="year">{f.season}</span>
                    <span class="place">{f.place === 1 ? 'Champion' : ordinal(f.place)}</span>
                </a>
            </li>
        {/each}
    </ul>
{/if}
