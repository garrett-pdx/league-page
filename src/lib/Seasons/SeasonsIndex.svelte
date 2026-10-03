<script>
    /*
    The /seasons index: one card per season, newest first. Each card is a single link to that
    year's page, so the names inside it are plain text (a link inside a link is invalid HTML).

    Everything comes from the committed dataset -- final_standings for the podium, games.json for
    the top seed, season-notes for the best week -- through seasonCards() in seasonData.js.
    */
    import { waitForAll } from '$lib/utils/helper';
    import { managers } from '$lib/utils/leagueInfo';
    import Person from './Person.svelte';
    import { seasonCards, peopleLookup } from './seasonData';

    export let historyData, gamesData, notesData;

    const record = (r) => r.ties ? `${r.wins}-${r.losses}-${r.ties}` : `${r.wins}-${r.losses}`;
</script>

<style>
    .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(min(300px, 100%), 1fr));
        gap: 1.1rem;
        width: 94%;
        max-width: var(--pageMax);
        margin: 0 auto 4em;
        /* the six cards' height, reserved while the data loads so the footer doesn't jump */
        min-height: 60vh;
    }

    .card {
        display: flex;
        flex-direction: column;
        background-color: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        color: inherit;
        text-decoration: none;
        overflow: hidden;
        transition: box-shadow 0.18s ease, transform 0.18s ease;
    }

    @media (hover: hover) {
        .card:hover {
            box-shadow: var(--shadowCardHover);
            transform: translateY(-2px);
        }
    }

    .card:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }

    .top {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 0.5em;
        padding: 0.9rem 1.1rem 0.7rem;
        border-bottom: 1px solid var(--accentBorder);
    }

    .year {
        font-family: var(--fontDisplay);
        font-size: 2.1rem;
        font-weight: 600;
        line-height: 1;
        color: var(--navy700);
    }

    .tag {
        font-family: var(--fontDisplay);
        font-size: 0.8rem;
        font-weight: 500;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--g555);
        text-align: right;
    }

    .tag.live {
        color: var(--fff);
        background-color: var(--accentFill);
        border-radius: var(--radiusPill);
        padding: 0.25em 0.7em;
    }

    .champ {
        display: flex;
        align-items: center;
        gap: 0.75em;
        padding: 0.8rem 1.1rem;
        background-color: var(--goldFill);
        color: var(--goldOnFill);
    }

    .champ .label, .champ :global(.name) { color: var(--goldOnFill); }
    .champ :global(.name) {
        font-family: var(--fontDisplay);
        font-size: 1.25rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }

    .label {
        display: block;
        font-family: var(--fontDisplay);
        font-size: 0.75rem;
        font-weight: 500;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--g555);
        margin-bottom: 0.2em;
    }

    dl {
        margin: 0;
        padding: 0.4rem 1.1rem 1rem;
        display: grid;
        gap: 0.55rem;
    }

    dl div {
        display: grid;
        grid-template-columns: 6.6rem minmax(0, 1fr);
        align-items: center;
        gap: 0.5em;
    }

    dt {
        font-family: var(--fontDisplay);
        font-size: 0.8rem;
        font-weight: 500;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--g555);
    }

    dd {
        margin: 0;
        color: var(--g333);
        min-width: 0;
    }

    .num {
        font-variant-numeric: tabular-nums;
        color: var(--g555);
        white-space: nowrap;
    }

    .espn {
        padding: 0.9rem 1.1rem 1.1rem;
        color: var(--g444);
        line-height: 1.45;
        margin: 0;
    }

    .more {
        margin-top: auto;
        padding: 0.7rem 1.1rem;
        border-top: 1px solid var(--accentBorder);
        font-family: var(--fontDisplay);
        font-size: 0.85rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--accentInk);
    }

    .loading, .error {
        text-align: center;
        color: var(--g555);
        grid-column: 1 / -1;
    }
</style>

<div class="grid">
    {#await waitForAll(historyData, gamesData, notesData)}
        <p class="loading">Pulling the seasons out of the archive...</p>
    {:then [history, {games}, notes]}
        {@const people = peopleLookup(history, managers)}
        {#each seasonCards(history, games, notes) as card (card.year)}
            <a class="card" href="/seasons/{card.year}">
                <div class="top">
                    <span class="year">{card.year}</span>
                    {#if card.kind === 'progress'}
                        <span class="tag live">In progress{card.throughWeek ? ` · week ${card.throughWeek}` : ''}</span>
                    {:else if card.kind === 'espn'}
                        <span class="tag">ESPN · founding season</span>
                    {:else}
                        <span class="tag">Final</span>
                    {/if}
                </div>

                {#if card.kind === 'espn'}
                    <p class="espn">The league's first season, played on ESPN. Only the draft made the move to Sleeper; no standings or results survive.</p>
                {:else}
                    {#if card.champion}
                        <div class="champ">
                            <div>
                                <span class="label">Champion</span>
                                <Person person={people[card.champion]} size={40} link={false} />
                            </div>
                        </div>
                    {/if}
                    <dl>
                        {#if card.runnerUp}
                            <div><dt>Runner-up</dt><dd><Person person={people[card.runnerUp]} size={24} link={false} /></dd></div>
                        {/if}
                        {#if card.topSeed}
                            <div>
                                <dt>{card.kind === 'progress' ? 'Leader' : 'Top seed'}</dt>
                                <dd><Person person={people[card.topSeed.user_id]} size={24} link={false} /> <span class="num">{record(card.topSeed)}</span></dd>
                            </div>
                        {/if}
                        {#if card.bestWeek}
                            <div>
                                <dt>Best week{card.kind === 'progress' ? ' so far' : ''}</dt>
                                <dd><Person person={people[card.bestWeek.user_id]} size={24} link={false} /> <span class="num">{card.bestWeek.points.toFixed(2)} · wk {card.bestWeek.week}</span></dd>
                            </div>
                        {/if}
                    </dl>
                {/if}
                <span class="more">{card.kind === 'espn' ? 'The 2021 draft' : `The ${card.year} season`} →</span>
            </a>
        {/each}
    {:catch error}
        <p class="error">The archive wouldn't open: {error.message}</p>
    {/await}
</div>
