<script>
    /*
    A season's table: final places 1-10 from final_standings (finalTable() in seasonData.js), or,
    for a season still being played, the regular-season standings so far (regularStandings()).
    Each row carries the regular-season record, points for and against, and the playoff seed.

    rows      finalTable() or regularStandings() output
    people    peopleLookup() output
    final     true: the first column is the final place; false: the current rank
    */
    import Person from './Person.svelte';

    export let rows = [];
    export let people;
    export let final = true;

    const record = (r) => r.ties ? `${r.wins}-${r.losses}-${r.ties}` : `${r.wins}-${r.losses}`;
    const pts = (n) => n?.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) ?? '';
</script>

<style>
    .table {
        width: 94%;
        max-width: 760px;
        margin: 0 auto 1.5em;
        background-color: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        overflow: hidden;
    }

    .row {
        display: grid;
        grid-template-columns: 2.2rem minmax(0, 1fr) 3.6rem 5.4rem 5.4rem 3.4rem;
        align-items: center;
        gap: 0.5rem;
        padding: 0.45rem 0.9rem;
        min-height: 48px;
        box-sizing: border-box;
        border-bottom: 1px solid var(--accentBorder);
    }

    .row:last-child { border-bottom: none; }

    .head {
        min-height: 0;
        padding-top: 0.6rem;
        padding-bottom: 0.6rem;
        font-family: var(--fontDisplay);
        font-size: 0.75rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--g555);
        background-color: var(--navy050);
    }

    .place {
        font-family: var(--fontDisplay);
        font-weight: 600;
        font-size: 1.15rem;
        color: var(--navy700);
        text-align: center;
    }

    .champ { background-color: #fdf6e3; }
    .champ .place {
        background-color: var(--goldFill);
        color: var(--goldOnFill);
        border-radius: var(--radiusCircle);
        width: 1.9rem;
        height: 1.9rem;
        line-height: 1.9rem;
        font-size: 1rem;
    }

    /* the line between the playoff teams and the rest */
    .cut { border-bottom: 2px solid var(--navy400); }

    .num {
        font-variant-numeric: tabular-nums;
        text-align: right;
        color: var(--g444);
        white-space: nowrap;
    }

    .head .num { color: var(--g555); }

    .team { min-width: 0; font-weight: 500; }

    @media (max-width: 560px) {
        .row {
            grid-template-columns: 1.9rem minmax(0, 1fr) 3rem 4.4rem;
            gap: 0.4rem;
            padding: 0.45rem 0.6rem;
        }
        .pa, .seed { display: none; }
        .champ .place { width: 1.7rem; height: 1.7rem; line-height: 1.7rem; }
    }
</style>

<div class="table" role="table" aria-label={final ? 'Final standings' : 'Standings so far'}>
    <div class="row head" role="row">
        <span role="columnheader" class="place-h">{final ? 'Fin' : 'Rk'}</span>
        <span role="columnheader">Team</span>
        <span role="columnheader" class="num">W-L</span>
        <span role="columnheader" class="num">PF</span>
        <span role="columnheader" class="num pa">PA</span>
        <span role="columnheader" class="num seed">Seed</span>
    </div>
    {#each rows as row, i (row.user_id)}
        <div class="row" class:champ={final && row.place === 1} class:cut={i === 3} role="row">
            <span class="place" role="cell">{final ? row.place : i + 1}</span>
            <span class="team" role="cell"><Person person={people[row.user_id]} size={30} /></span>
            <span class="num" role="cell">{record(row)}</span>
            <span class="num" role="cell">{pts(row.pf)}</span>
            <span class="num pa" role="cell">{pts(row.pa)}</span>
            <span class="num seed" role="cell">{row.seed ?? i + 1}</span>
        </div>
    {/each}
</div>
