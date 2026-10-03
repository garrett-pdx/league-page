<script>
    /*
    A season's extremes: the three highest and lowest single-team scores (season-notes), the
    biggest blowout and the closest game (every played game, playoffs included), the best and
    worst season-long lineup efficiency (lineupTotals over the regular season: points scored over
    the best legal lineup's points), and each team's MVP -- the top scorer in its starting lineup.

    extremes   seasonExtremes() output
    lineups    lineupTotals() output, best first
    mvps       seasonMvps() output: {user_id: {name, pos, points, starts}}
    order      user_ids in table order, for the MVP list
    */
    import Person from './Person.svelte';

    export let extremes;
    export let lineups = [];
    export let mvps = {};
    export let order = [];
    export let people;
    export let partial = false;

    const KIND = {playoff: 'playoffs', placement: 'third-place game', consolation: 'consolation'};
    const where = (g) => `Week ${g.week}${KIND[g.kind] ? `, ${KIND[g.kind]}` : ''}`;
    const pct = (n) => `${(n * 100).toFixed(1)}%`;

    $: best = lineups[0];
    $: worst = lineups.length > 1 ? lineups[lineups.length - 1] : null;
</script>

<style>
    .tiles {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(min(300px, 100%), 1fr));
        gap: 1rem;
        width: 94%;
        max-width: var(--pageMax);
        margin: 0 auto 2em;
    }

    .tile {
        background-color: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        padding: 0.9rem 1rem 0.8rem;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .label {
        font-family: var(--fontDisplay);
        font-size: 0.8rem;
        font-weight: 500;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--g555);
    }

    .value {
        font-family: var(--fontDisplay);
        font-size: 2rem;
        font-weight: 600;
        line-height: 1.05;
        color: var(--navy700);
    }

    .sub {
        font-size: 0.875rem;
        color: var(--g555);
        line-height: 1.35;
    }

    .also {
        margin: 0.3rem 0 0;
        padding: 0.4rem 0 0;
        border-top: 1px solid var(--eee);
        list-style: none;
        font-size: 0.875rem;
        color: var(--g444);
    }

    .also li {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.5em;
    }

    .num { font-variant-numeric: tabular-nums; white-space: nowrap; }

    .mvps {
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

    .mvps li {
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr) auto;
        align-items: center;
        gap: 0.6rem;
        padding: 0.3rem 0.9rem;
        border-bottom: 1px solid var(--eee);
        min-height: 48px;
        box-sizing: border-box;
    }

    .mvps li:last-child { border-bottom: none; }

    .player { min-width: 0; line-height: 1.25; }
    .player strong { font-weight: 500; color: var(--g111); }
    .pos { font-size: 0.8rem; color: var(--g555); margin-left: 0.3em; }
    .starts { display: block; font-size: 0.8rem; color: var(--g555); }

    .mvpTitle {
        font-family: var(--fontDisplay);
        font-size: 0.85rem;
        font-weight: 500;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--g555);
        text-align: center;
        margin: 0 0 0.6em;
    }

    @media (max-width: 480px) {
        .mvps li { grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.2fr) auto; padding: 0.3rem 0.6rem; gap: 0.45rem; }
    }
</style>

<div class="tiles">
    {#if extremes.high.length}
        {@const top = extremes.high[0]}
        <div class="tile">
            <span class="label">Highest score{partial ? ' so far' : ''}</span>
            <span class="value num">{top.points.toFixed(2)}</span>
            <Person person={people[top.user_id]} size={26} />
            <span class="sub">{where(top)}, against {people[top.opponent_id]?.first}</span>
            <ul class="also">
                {#each extremes.high.slice(1) as w}
                    <li><span>{people[w.user_id]?.first}, wk {w.week}</span><span class="num">{w.points.toFixed(2)}</span></li>
                {/each}
            </ul>
        </div>
    {/if}
    {#if extremes.low.length}
        {@const bottom = extremes.low[0]}
        <div class="tile">
            <span class="label">Lowest score{partial ? ' so far' : ''}</span>
            <span class="value num">{bottom.points.toFixed(2)}</span>
            <Person person={people[bottom.user_id]} size={26} />
            <span class="sub">{where(bottom)}, against {people[bottom.opponent_id]?.first}</span>
            <ul class="also">
                {#each extremes.low.slice(1) as w}
                    <li><span>{people[w.user_id]?.first}, wk {w.week}</span><span class="num">{w.points.toFixed(2)}</span></li>
                {/each}
            </ul>
        </div>
    {/if}
    {#if extremes.blowout}
        {@const g = extremes.blowout}
        <div class="tile">
            <span class="label">Biggest blowout</span>
            <span class="value num">{g.margin.toFixed(2)}</span>
            <Person person={people[g.user_id]} size={26} />
            <span class="sub">beat {people[g.opponent_id]?.first} <span class="num">{g.pf.toFixed(2)}–{g.pa.toFixed(2)}</span>. {where(g)}.</span>
        </div>
    {/if}
    {#if extremes.closest}
        {@const g = extremes.closest}
        <div class="tile">
            <span class="label">Closest game</span>
            <span class="value num">{g.margin.toFixed(2)}</span>
            <Person person={people[g.user_id]} size={26} />
            <span class="sub">beat {people[g.opponent_id]?.first} <span class="num">{g.pf.toFixed(2)}–{g.pa.toFixed(2)}</span>. {where(g)}.</span>
        </div>
    {/if}
    {#if best}
        <div class="tile">
            <span class="label">Sharpest lineups</span>
            <span class="value num">{pct(best.efficiency)}</span>
            <Person person={people[best.user_id]} size={26} />
            <span class="sub">Points scored as a share of the best legal lineup's, over the regular season. Left <span class="num">{best.bench.toFixed(2)}</span> on the bench.</span>
        </div>
    {/if}
    {#if worst}
        <div class="tile">
            <span class="label">Least efficient lineups</span>
            <span class="value num">{pct(worst.efficiency)}</span>
            <Person person={people[worst.user_id]} size={26} />
            <span class="sub">Left <span class="num">{worst.bench.toFixed(2)}</span> points on the bench over the regular season.</span>
        </div>
    {/if}
</div>

{#if order.some((uid) => mvps[uid])}
    <h4 class="mvpTitle">Each team's MVP{partial ? ' so far' : ''}</h4>
    <ol class="mvps">
        {#each order.filter((uid) => mvps[uid]) as uid (uid)}
            {@const m = mvps[uid]}
            <li>
                <Person person={people[uid]} size={26} short />
                <span class="player">
                    <strong>{m.name}</strong><span class="pos">{m.pos}</span>
                    <span class="starts">{m.starts} {m.starts === 1 ? 'start' : 'starts'}</span>
                </span>
                <span class="num">{m.points.toFixed(1)}</span>
            </li>
        {/each}
    </ol>
{/if}
