<script>
    /*
    Draft picks laid out by round: one card per round, one line per pick. Used for a season's
    first three rounds and for the whole 2021 (ESPN) draft.

    rounds    earlyRounds() output: [[pick, ...], ...] -- picks as stored in league-history.json
    teams     picks per round, for the "1.04" pick label
    players   players.json: {player_id: {n, p, t}}
    people    peopleLookup() output
    */
    import Person from './Person.svelte';

    export let rounds = [];
    export let teams = 10;
    export let players = {};
    export let people;

    const label = (p) => `${p.round}.${String(p.pick_no - (p.round - 1) * teams).padStart(2, '0')}`;
</script>

<style>
    .rounds {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(290px, 100%), 1fr));
        gap: 1rem;
        width: 94%;
        max-width: var(--pageMax);
        margin: 0 auto 1.5em;
    }

    .round {
        background-color: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        overflow: hidden;
    }

    h4 {
        margin: 0;
        padding: 0.45rem 0.9rem;
        font-family: var(--fontDisplay);
        font-size: 0.85rem;
        font-weight: 500;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--g555);
        background-color: var(--navy050);
    }

    ol {
        list-style: none;
        margin: 0;
        padding: 0;
    }

    li {
        display: grid;
        grid-template-columns: 2.6rem minmax(0, 1fr) minmax(0, 0.9fr);
        align-items: center;
        gap: 0.5rem;
        padding: 0 0.9rem;
        border-top: 1px solid var(--eee);
        min-height: 44px;
    }

    .pick {
        font-variant-numeric: tabular-nums;
        color: var(--g555);
        font-size: 0.9rem;
    }

    .player { min-width: 0; line-height: 1.2; }
    .player strong { font-weight: 500; color: var(--g111); }

    .pos {
        font-size: 0.8rem;
        color: var(--g555);
        margin-left: 0.3em;
    }

    .keeper {
        display: inline-block;
        margin-left: 0.4em;
        padding: 0.05em 0.45em;
        border-radius: var(--radiusXs);
        background-color: var(--accentFill);
        color: var(--fff);
        font-size: 0.75rem;
        letter-spacing: 0.04em;
        vertical-align: 0.1em;
    }

    .by { min-width: 0; font-size: 0.9rem; }
</style>

<div class="rounds">
    {#each rounds as picks, r}
        <section class="round">
            <h4>Round {picks[0]?.round ?? r + 1}</h4>
            <ol>
                {#each picks as p (p.pick_no)}
                    <li>
                        <span class="pick">{label(p)}</span>
                        <span class="player">
                            <strong>{players[p.player_id]?.n ?? 'Unknown player'}</strong><span class="pos">{players[p.player_id]?.p ?? ''}</span>{#if p.is_keeper}<span class="keeper">Keeper</span>{/if}
                        </span>
                        <span class="by"><Person person={people[p.picked_by]} size={22} short /></span>
                    </li>
                {/each}
            </ol>
        </section>
    {/each}
</div>
