<script>
    /*
    Standings by week: each team's rank after every regular-season week, one line per team.

    The form is EMPHASIS, not a ten-colour legend: ten categorical hues is past what anyone can
    tell apart, so every line is a recessive grey and the one team being looked at is drawn in
    navy, on top, with dots. Identity never rests on colour -- the end of every line carries the
    team's name, the buttons underneath name the selected team in words, and the same numbers
    are in a table behind the "Show as a table" control.

    Pointing works on the nearest point, not on the 2px line: the pointer snaps to the nearest
    week, and the team whose rank row is nearest the pointer at that week lights up. A tap
    selects it; the buttons do the same from the keyboard.

    Drawn at the container's real pixel width (bind:clientWidth), not a scaled viewBox, so the
    labels stay 12px+ at 375px instead of shrinking with the drawing.

    Props:
      ranksData   ranksByWeek() output: {weeks, ranks: {uid: [rank...]}, records: {uid: [...]}}
      people      peopleLookup() output
      selected    the user_id drawn in navy by default (the champion, or the leader)
    */
    import { Disclosure } from '$lib/Design';

    export let ranksData;
    export let people;
    export let selected = null;

    let width = 0;
    let hoverTeam = null;
    let hoverWeek = null;      // index into weeks

    $: ({weeks, ranks, records} = ranksData);
    $: teams = Object.keys(ranks);
    $: n = teams.length;
    $: last = weeks.length - 1;
    // final order, top to bottom, for the buttons and the table
    $: order = [...teams].sort((a, b) => ranks[a][last] - ranks[b][last]);

    $: narrow = width < 520;
    $: padL = 26;
    $: padR = narrow ? 76 : 150;
    $: padT = 14;
    $: padB = 30;
    $: rowH = narrow ? 27 : 32;
    $: plotW = Math.max(60, width - padL - padR);
    $: height = padT + (n - 1) * rowH + padB;
    $: step = weeks.length > 1 ? plotW / (weeks.length - 1) : 0;
    $: x = (i) => padL + (weeks.length > 1 ? i * step : plotW / 2);
    $: y = (rank) => padT + (rank - 1) * rowH;
    // label every week when there is room, otherwise the odd weeks (1, 3 ... 15: a 15-week
    // season still labels its last week)
    $: tickEvery = step >= 24 ? 1 : 2;

    $: active = hoverTeam || selected;

    const path = (list, xf, yf) => list.map((r, i) => `${i ? 'L' : 'M'}${xf(i).toFixed(1)},${yf(r).toFixed(1)}`).join('');

    const ord = (k) => {
        const v = k % 100;
        return k + (['th', 'st', 'nd', 'rd'][(v - 20) % 10] || ['th', 'st', 'nd', 'rd'][v] || 'th');
    };

    function locate(event) {
        const svg = event.currentTarget;
        const box = svg.getBoundingClientRect();
        const px = event.clientX - box.left;
        const py = event.clientY - box.top;
        const i = weeks.length > 1 ? Math.round((px - padL) / step) : 0;
        const wi = Math.min(last, Math.max(0, i));
        const rank = Math.min(n, Math.max(1, Math.round((py - padT) / rowH) + 1));
        const uid = teams.find((t) => ranks[t][wi] === rank) || null;
        return {wi, uid};
    }

    function onMove(event) {
        if(event.pointerType === 'touch') return;
        const {wi, uid} = locate(event);
        hoverWeek = wi;
        hoverTeam = uid;
    }

    function onLeave() {
        hoverWeek = null;
        hoverTeam = null;
    }

    function onTap(event) {
        const {wi, uid} = locate(event);
        hoverWeek = wi;
        if(uid) selected = uid;
        hoverTeam = null;
    }

    // the readout under the chart: the active team at the hovered week, or at the end
    $: readWeek = hoverWeek ?? last;
    $: activeRanks = active ? ranks[active] : null;
    $: best = activeRanks ? Math.min(...activeRanks) : null;
    $: worst = activeRanks ? Math.max(...activeRanks) : null;
</script>

<style>
    .chart {
        width: 94%;
        max-width: 860px;
        margin: 0 auto;
        background-color: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        padding: 1rem 0.75rem 0.75rem;
        box-sizing: border-box;
    }

    .plot { width: 100%; }

    svg {
        display: block;
        touch-action: manipulation;
        cursor: crosshair;
        user-select: none;
    }

    .grid { stroke: var(--eee); stroke-width: 1; }
    .cross { stroke: var(--g999); stroke-width: 1; }

    .axis {
        font-family: var(--fontBody);
        font-size: 12px;
        fill: var(--g555);
        font-variant-numeric: tabular-nums;
    }

    .line {
        fill: none;
        stroke: #b8c3d1;
        stroke-width: 1.5;
        stroke-linejoin: round;
        stroke-linecap: round;
    }

    .line.on {
        stroke: var(--navy700);
        stroke-width: 2.5;
    }

    .dot {
        fill: var(--navy700);
        stroke: var(--fff);
        stroke-width: 2;
    }

    .end {
        font-family: var(--fontBody);
        font-size: 12px;
        fill: var(--g555);
    }

    .end.on {
        fill: var(--navy700);
        font-weight: 700;
    }

    @media (min-width: 521px) {
        .end { font-size: 14px; }
    }

    .readout {
        min-height: 2.9em;
        margin: 0.6rem 0.25rem 0;
        color: var(--g444);
        line-height: 1.4;
        text-align: center;
    }

    .readout strong { color: var(--navy700); }

    .picker {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 0.4rem;
        margin: 0.8rem 0 0;
        padding: 0;
        list-style: none;
    }

    .picker button {
        min-height: 44px;
        min-width: 44px;
        padding: 0 0.85em;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusPill);
        background-color: var(--fff);
        color: var(--navy700);
        font: inherit;
        font-size: 0.9rem;
        cursor: pointer;
    }

    .picker button[aria-pressed='true'] {
        background-color: var(--accentFill);
        border-color: var(--accentFill);
        color: var(--fff);
    }

    @media (hover: hover) {
        .picker button:hover { background-color: var(--navy050); }
        .picker button[aria-pressed='true']:hover { background-color: var(--navy600); }
    }

    .picker button:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }

    .tableWrap {
        overflow-x: auto;
        margin: 0 auto;
        max-width: 100%;
    }

    table {
        border-collapse: collapse;
        margin: 0 auto;
        font-variant-numeric: tabular-nums;
        background-color: var(--fff);
    }

    th, td {
        padding: 0.4em 0.5em;
        text-align: center;
        border-bottom: 1px solid var(--eee);
        font-size: 14px;
        white-space: nowrap;
    }

    th { font-weight: 500; color: var(--g555); }

    th.team {
        text-align: left;
        position: sticky;
        left: 0;
        background-color: var(--fff);
    }
</style>

<div class="chart">
    <div class="plot" bind:clientWidth={width}>
        {#if width}
            <!-- The buttons below are the keyboard route to the same selection. -->
            <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
            <svg
                {width}
                {height}
                role="img"
                aria-label="Rank after each week, one line per team. Use the buttons below the chart to pick a team, or open the table for every number."
                onpointermove={onMove}
                onpointerleave={onLeave}
                onclick={onTap}
            >
                <!-- rank rows and the axis -->
                {#each Array(n) as _, r}
                    <line class="grid" x1={padL} x2={padL + plotW} y1={y(r + 1)} y2={y(r + 1)} />
                    <text class="axis" x={padL - 8} y={y(r + 1)} dy="0.35em" text-anchor="end">{r + 1}</text>
                {/each}
                {#each weeks as w, i}
                    {#if i % tickEvery === 0}
                        <text class="axis" x={x(i)} y={height - 8} text-anchor="middle">{w}</text>
                    {/if}
                {/each}

                {#if hoverWeek !== null}
                    <line class="cross" x1={x(hoverWeek)} x2={x(hoverWeek)} y1={padT - 6} y2={y(n) + 6} />
                {/if}

                <!-- the context lines first, then the active one on top -->
                {#each teams as uid (uid)}
                    {#if uid !== active}
                        <path class="line" d={path(ranks[uid], x, y)} />
                    {/if}
                {/each}
                {#if active && ranks[active]}
                    <path class="line on" d={path(ranks[active], x, y)} />
                    {#each ranks[active] as r, i}
                        <circle class="dot" cx={x(i)} cy={y(r)} r={i === readWeek ? 5.5 : 4} />
                    {/each}
                {/if}

                <!-- every line ends in its team's name; final ranks are distinct, so no two collide -->
                {#each teams as uid (uid)}
                    <text class="end" class:on={uid === active} x={padL + plotW + 10} y={y(ranks[uid][last])} dy="0.35em">
                        {narrow ? people[uid]?.first : people[uid]?.name}
                    </text>
                {/each}
            </svg>
        {:else}
            <div style="height: {padT + 9 * 27 + padB}px"></div>
        {/if}
    </div>

    <p class="readout" aria-live="polite">
        {#if active && activeRanks}
            <strong>{people[active]?.name}</strong>: {ord(activeRanks[readWeek])} after week {weeks[readWeek]}
            ({records[active][readWeek]}).
            Best {ord(best)}, worst {ord(worst)}.
        {:else}
            Point at a line, or pick a team.
        {/if}
    </p>

    <ul class="picker" aria-label="Highlight a team">
        {#each order as uid (uid)}
            <li>
                <button type="button" aria-pressed={uid === selected} onclick={() => (selected = uid)}>
                    {people[uid]?.first}
                </button>
            </li>
        {/each}
    </ul>
</div>

<Disclosure label="Show as a table" openLabel="Hide the table">
    <div class="tableWrap">
        <table>
            <thead>
                <tr>
                    <th class="team" scope="col">Team</th>
                    {#each weeks as w}<th scope="col">Wk {w}</th>{/each}
                </tr>
            </thead>
            <tbody>
                {#each order as uid (uid)}
                    <tr>
                        <th class="team" scope="row">{people[uid]?.name}</th>
                        {#each ranks[uid] as r}<td>{r}</td>{/each}
                    </tr>
                {/each}
            </tbody>
        </table>
    </div>
</Disclosure>
