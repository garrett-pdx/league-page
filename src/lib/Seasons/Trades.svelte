<script>
    /*
    A season's completed trades, from season-notes.json. Each side lists what that team
    RECEIVED. Pre-draft trades are filed under week 1, which is why one can move this year's picks.
    */
    import Person from './Person.svelte';

    export let trades = [];
    export let people;

    const pick = (p) => {
        const from = people[p.original_owner]?.first;
        return `${p.season} round ${p.round} pick${from ? ` (${from}'s)` : ''}`;
    };

    const when = (t) => {
        const d = new Date(`${t.date}T12:00:00Z`);
        const date = isNaN(d) ? t.date : d.toLocaleDateString('en-US', {month: 'short', day: 'numeric', timeZone: 'UTC'});
        return `Week ${t.week} · ${date}`;
    };
</script>

<style>
    .trades {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(min(320px, 100%), 1fr));
        gap: 1rem;
        width: 94%;
        max-width: var(--pageMax);
        margin: 0 auto 1.5em;
        padding: 0;
        list-style: none;
    }

    .trade {
        background-color: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        overflow: hidden;
    }

    .when {
        display: block;
        padding: 0.4rem 0.9rem;
        font-family: var(--fontDisplay);
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--g555);
        background-color: var(--navy050);
    }

    .side {
        padding: 0.3rem 0.9rem 0.6rem;
        border-top: 1px solid var(--eee);
    }

    .gets {
        font-size: 0.8rem;
        color: var(--g555);
        margin-left: 0.3em;
    }

    ul {
        margin: 0.1rem 0 0;
        padding-left: 1.2em;
        color: var(--g333);
        line-height: 1.45;
    }

    .pos { font-size: 0.8rem; color: var(--g555); margin-left: 0.25em; }

    .none {
        text-align: center;
        color: var(--g555);
        margin: 0 auto 1.5em;
    }
</style>

{#if trades.length}
    <ol class="trades">
        {#each trades as t (t.id)}
            <li class="trade">
                <span class="when">{when(t)}</span>
                {#each t.teams as side}
                    <div class="side">
                        <Person person={people[side.user_id]} size={26} /><span class="gets">received</span>
                        <ul>
                            {#each side.players as p}<li>{p.name}<span class="pos">{p.pos}</span></li>{/each}
                            {#each side.picks as p}<li>{pick(p)}</li>{/each}
                            {#if side.faab}<li>${side.faab} FAAB</li>{/if}
                            {#if !side.players.length && !side.picks.length && !side.faab}<li>Nothing</li>{/if}
                        </ul>
                    </div>
                {/each}
            </li>
        {/each}
    </ol>
{:else}
    <p class="none">No trades. Ten managers, a whole season, and nobody could agree on anything.</p>
{/if}
