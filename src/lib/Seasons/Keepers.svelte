<script>
    /*
    Every keeper in a season with what he cost, from keepers.json. A keeper occupies the draft
    slot he costs, so the round shown IS the cost. The note says where that cost came from:
    the round he went in last season's primary draft, one round dearer when the same manager
    keeps him again, and the last round when he went undrafted (constitution 4.2-4.4).

    For 2022 "last season" is the carried-over 2021 ESPN draft, which keepers.json marks as the
    baseline; that is the one place the carried-over draft legitimately prices anything.
    */
    import Person from './Person.svelte';

    export let rows = [];
    export let year;
    export let players = {};
    export let people;

    $: prevLabel = rows[0]?.baseline?.startsWith('carried-over') ? `${year - 1} (ESPN)` : `${year - 1}`;

    const note = (r, prev) => {
        const base = r.previous_season_round ? `Round ${r.previous_season_round} in ${prev}` : `Undrafted in ${prev}`;
        return r.kept_by_same_manager_last_season ? `${base} · kept again (+1 round)` : base;
    };
</script>

<style>
    .list {
        width: 94%;
        max-width: 760px;
        margin: 0 auto 1.5em;
        padding: 0;
        list-style: none;
        background-color: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        overflow: hidden;
    }

    li {
        display: grid;
        grid-template-columns: 3.4rem minmax(0, 1.3fr) minmax(0, 1fr);
        align-items: center;
        gap: 0.6rem;
        padding: 0.35rem 0.9rem;
        border-bottom: 1px solid var(--eee);
        min-height: 52px;
        box-sizing: border-box;
    }

    li:last-child { border-bottom: none; }

    .cost {
        font-family: var(--fontDisplay);
        font-weight: 600;
        color: var(--navy700);
        text-align: center;
        line-height: 1.05;
    }

    .cost small {
        display: block;
        font-size: 0.75rem;
        font-weight: 500;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--g555);
    }

    .player { min-width: 0; line-height: 1.25; }
    .player strong { font-weight: 500; color: var(--g111); }
    .pos { font-size: 0.8rem; color: var(--g555); margin-left: 0.3em; }

    .note {
        display: block;
        font-size: 0.8rem;
        color: var(--g555);
    }

    .by { min-width: 0; font-size: 0.9rem; }

    @media (max-width: 480px) {
        li { grid-template-columns: 2.8rem minmax(0, 1fr) minmax(0, 0.75fr); gap: 0.45rem; padding: 0.35rem 0.6rem; }
    }
</style>

<ol class="list">
    {#each rows as r (r.player_id)}
        <li>
            <span class="cost"><small>Round</small>{r.cost_round}</span>
            <span class="player">
                <strong>{players[r.player_id]?.n ?? 'Unknown player'}</strong><span class="pos">{players[r.player_id]?.p ?? ''}</span>
                <span class="note">{note(r, prevLabel)}</span>
            </span>
            <span class="by"><Person person={people[r.user_id]} size={22} short /></span>
        </li>
    {/each}
</ol>
