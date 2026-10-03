<script>
    /*
    The distribution chart: one strip per manager, one dot per row (a game, or a season), on a
    shared axis, strips sorted by median. Where a bar says who is best on average, this says how
    they get there: a wide strip is a boom-or-bust team, a tight one is steady.

    MARKS. Dots are laid out as a beeswarm (scale.js swarm()): each dot sits at its true value on
    the axis and is nudged up or down just enough not to cover another, so every game stays
    visible and nothing reshuffles between renders. The median is a heavy tick with a surface
    outline, and its number is printed under the manager's name. The middle half of the values
    (the interquartile range) is a faint band behind the dots, drawn only for a manager with five or
    more values -- a "quartile" of three games is not a thing. A hairline marks the median of
    everyone together, so a strip reads as above or below the league at a glance.

    COLOUR. One series, so no legend colours to decode: dots are neutral grey, and the one
    manager being looked at -- hovered, focused or tapped -- turns the accent blue, dots, median
    and band together. A single dot being inspected goes navy and larger.

    INTERACTION. Each strip is one real <button> 44px tall, so a row is easy to hit with a thumb
    and reachable by keyboard; nothing requires landing on a 7px dot. The pointer finds the NEAREST
    dot within 12px (mouse) or 22px (touch) of the pointer, and ignores the rest of the strip.
      * mouse: hovering a strip highlights it and, near a dot, shows that game; clicking a dot
        narrows the filters to that game's week (Lab's narrow()), clicking elsewhere on the strip
        narrows to that manager.
      * touch, or a narrow window: a tap selects the strip (and the dot, if one was close) and a
        readout under the chart gives the numbers, with buttons that do the narrowing. A tap never
        narrows by itself, so a misplaced finger costs nothing.
      * keyboard: a strip takes focus and highlights; Enter narrows to the manager.
    The table below the chart has every value and is the text alternative; the strips are named
    for a screen reader with their median and count, and the dots are hidden from it.
    */
    import { MEASURES, fmtMeasure, distribution } from './statLab.js';
    import { niceTicks, linear, tickText, swarm } from './scale.js';

    let {
        rows = [], measure, ds, labelOf, nameOf, narrow, narrowLabel, narrowManager, narrowManagerLabel,
        narrowScreen = false,
    } = $props();

    const ROW = 44;
    const PAD = 7;

    let plotW = $state(0);
    let activeUid = $state(null);
    let activeId = $state(null);
    let touch = $state(false);

    const def = $derived(MEASURES[measure]);
    const noun = $derived(ds === 'games' ? 'game' : 'season');
    const labelW = $derived(narrowScreen ? 72 : 124);
    const r = $derived(narrowScreen ? 3 : 3.5);

    const groups = $derived(distribution(rows, measure, nameOf));
    const all = $derived(groups.flatMap((g) => g.rows.map((x) => x[measure])).sort((a, b) => a - b));
    const leagueMedian = $derived(all.length ? (all[(all.length - 1) >> 1] + all[all.length >> 1]) / 2 : 0);

    const T = $derived(all.length
        ? niceTicks(all[0], all[all.length - 1], narrowScreen ? 5 : 7)
        : { ticks: [0, 1], lo: 0, hi: 1, step: 1 });
    // labels thin out to every other tick when the plot is too narrow to print them all
    const stride = $derived(plotW / Math.max(1, T.ticks.length - 1) < 38 ? 2 : 1);
    const X = $derived(linear([T.lo, T.hi], [PAD, Math.max(PAD + 1, plotW - PAD)]));

    // the swarm for every strip; y is an offset from the strip's centre line
    const laid = $derived(
        plotW
            ? groups.map((g) => {
                  const xs = g.rows.map((x) => X(x[measure]));
                  const ys = swarm(xs, r + 0.5, ROW / 2 - r - 3);
                  return {
                      ...g,
                      dots: g.rows.map((row, i) => ({ row, x: xs[i], y: ys[i] })),
                      band: g.n >= 8,
                  };
              })
            : []
    );

    const active = $derived(laid.find((g) => g.uid === activeUid) ?? null);
    const activeDot = $derived(active?.dots.find((d) => d.row.id === activeId) ?? null);
    const activeIx = $derived(laid.findIndex((g) => g.uid === activeUid));

    const medianOf = (g) => fmtMeasure(g.median, measure);
    const range = (g) => `${fmtMeasure(g.q1, measure)} to ${fmtMeasure(g.q3, measure)}`;

    /* ---- pointer ----------------------------------------------------------------------------- */

    const nearest = (e, g) => {
        const rect = e.currentTarget.querySelector('svg').getBoundingClientRect();
        const px = e.clientX - rect.left;
        const py = e.clientY - rect.top - ROW / 2;
        const reach = touch || narrowScreen ? 22 : 12;
        let best = null, bestD = reach * reach;
        for(const d of g.dots) {
            // a strip is wide and short, so a miss up or down counts for half a miss sideways
            const dd = (d.x - px) ** 2 + ((d.y - py) / 2) ** 2;
            if(dd < bestD) { bestD = dd; best = d.row.id; }
        }
        return best;
    };

    const sawTouch = (e) => { touch = e.pointerType !== 'mouse'; };

    const onmove = (e, g) => {
        sawTouch(e);
        if(touch) return;                 // selection on a phone happens on click, never on a scroll
        activeUid = g.uid;
        activeId = nearest(e, g);
    };
    const onleave = (e) => { if(e.pointerType === 'mouse') { activeUid = null; activeId = null; } };
    const onfocus = (g) => { if(!touch) { activeUid = g.uid; activeId = null; } };
    const onblur = () => { if(!touch && !narrowScreen) { activeUid = null; activeId = null; } };

    const onclick = (e, g) => {
        const id = e.detail === 0 ? null : nearest(e, g);       // detail 0: a keyboard activation
        if(touch || narrowScreen) {
            activeUid = g.uid;
            activeId = id;
            return;
        }
        const hit = id && g.dots.find((d) => d.row.id === id);
        if(hit) narrow(hit.row);
        else narrowManager(g.uid);
    };

    const showPanel = $derived((touch || narrowScreen) && active);

    const oppNote = (row) => (ds === 'games' && row.opponent_id ? ` vs ${nameOf(row.opponent_id)}` : '');

    const ariaSummary = $derived(
        `Distribution of ${ds === 'games' ? 'weekly' : 'season'} ${def.label.toLowerCase()}, ${groups.length} ` +
        `${groups.length === 1 ? 'manager' : 'managers'}, one dot per ${noun}, sorted by median` +
        (groups.length ? `, from ${nameOf(groups[0].uid)} at ${medianOf(groups[0])} to ${nameOf(groups[groups.length - 1].uid)} at ${medianOf(groups[groups.length - 1])}` : '') +
        `. Every value is in the table below.`
    );
</script>

<style>
    .wrap { position: relative; }

    .strip {
        appearance: none;
        display: grid;
        align-items: center;
        width: 100%;
        height: 44px;
        padding: 0;
        margin: 0;
        border: none;
        border-bottom: 1px solid var(--vizGridSoft);
        background: transparent;
        font: inherit;
        color: var(--vizInk);
        text-align: left;
        cursor: pointer;
        touch-action: pan-y;
    }

    .strip.on { background: var(--navy050); }
    .strip:focus-visible { outline: 2px solid var(--blueOne); outline-offset: -2px; }

    .who {
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-width: 0;
        padding: 0 6px 0 0.4em;
        line-height: 1.2;
    }

    .nm { font-size: 0.875rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .med { font-size: 0.8rem; color: var(--vizInk2); font-variant-numeric: tabular-nums; }
    .strip.on .nm { font-weight: 700; }

    /* the marks never take the pointer: they are swapped in and out as the pointer moves, and a
       press on an element that is gone by the release produces no click at all. The button is the
       target; nearest() finds the dot. */
    svg { display: block; overflow: visible; pointer-events: none; }
    .grid { stroke: var(--vizGrid); stroke-width: 1; shape-rendering: crispEdges; }
    .zero { stroke: var(--vizAxis); stroke-width: 1; shape-rendering: crispEdges; }
    .league { stroke: var(--vizAxis); stroke-width: 2; shape-rendering: crispEdges; }

    .band { fill: var(--vizBand); }
    .on .band { fill: var(--vizBandOn); }
    .dot { fill: var(--vizDot); stroke: var(--vizSurface); stroke-width: 1; }
    .on .dot { fill: var(--vizS1); }
    .dot.pick { fill: var(--navy700); stroke-width: 2; }
    .median { fill: var(--vizInk); stroke: var(--vizSurface); stroke-width: 1; }
    .on .median { fill: var(--navy700); }

    .axis { display: grid; align-items: start; }
    .axis svg { overflow: visible; }
    .tick { fill: var(--vizInk2); font-size: 12px; font-variant-numeric: tabular-nums; }
    .axisTitle { fill: var(--vizInk); font-size: 12px; font-weight: 500; }

    .tip {
        position: absolute;
        z-index: 2;
        padding: 0.45em 0.7em;
        background: var(--fff);
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusSm);
        box-shadow: var(--shadowCardHover);
        pointer-events: none;
        font-size: 0.85rem;
        white-space: nowrap;
        transform: translate(-50%, calc(-100% - 8px));
    }

    .tipHead { margin: 0 0 0.2em; font-weight: 700; }
    .tipRow { display: flex; gap: 0.5em; line-height: 1.5; }
    .tipRow strong { font-variant-numeric: tabular-nums; }
    .tipRow span { color: var(--vizInk2); }

    .panel {
        margin-top: 0.6em;
        padding: 0.6em 0.7em;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusSm);
        font-size: 0.875rem;
    }

    .narrowBtn {
        appearance: none;
        margin-top: 0.5em;
        min-height: 44px;
        width: 100%;
        border: none;
        border-radius: var(--radiusPill);
        background: var(--accentFill);
        color: #fff;
        font: inherit;
        font-weight: 500;
        cursor: pointer;
    }

    .narrowBtn.quiet { background: var(--fff); color: var(--accentInk); border: 1px solid var(--accentBorder); }

    .legend {
        display: flex;
        flex-wrap: wrap;
        gap: 4px 16px;
        margin: 0.6em 0 0;
        padding: 0;
        list-style: none;
        font-size: 0.8rem;
        color: var(--vizInk2);
    }

    .legend li { display: flex; align-items: center; gap: 6px; }
    .legend svg { flex: none; }

    .hint { margin: 0.4em 0 0; font-size: 0.8rem; color: var(--vizInk2); }
</style>

<div class="wrap" role="group" aria-label={ariaSummary}
    style="min-height: {groups.length * ROW + 40}px">
    {#each laid as g (g.uid)}
        <button
            type="button"
            class="strip"
            class:on={g.uid === activeUid}
            style="grid-template-columns: {labelW}px minmax(0, 1fr)"
            aria-label="{nameOf(g.uid)}: median {medianOf(g)} over {g.n} {noun}{g.n === 1 ? '' : 's'}{g.band ? `, middle half ${range(g)}` : ''}. {narrowManagerLabel(g.uid)}"
            onpointerenter={(e) => onmove(e, g)}
            onpointermove={(e) => onmove(e, g)}
            onpointerdown={sawTouch}
            onpointerleave={onleave}
            onfocus={() => onfocus(g)}
            onblur={onblur}
            onclick={(e) => onclick(e, g)}
        >
            <span class="who" aria-hidden="true">
                <span class="nm">{nameOf(g.uid)}</span>
                <span class="med">{medianOf(g)}</span>
            </span>
            <svg width={plotW} height={ROW} aria-hidden="true">
                {#each T.ticks as t}
                    <line class={t === 0 ? 'zero' : 'grid'} x1={X(t)} x2={X(t)} y1="0" y2={ROW} />
                {/each}
                <line class="league" x1={X(leagueMedian)} x2={X(leagueMedian)} y1="0" y2={ROW} />
                {#if g.band}
                    <rect class="band" x={X(g.q1)} y="6" width={Math.max(2, X(g.q3) - X(g.q1))} height={ROW - 12} rx="4" />
                {/if}
                {#each g.dots as d (d.row.id)}
                    {#if d.row.id !== activeId}
                        <circle class="dot" cx={d.x} cy={ROW / 2 + d.y} {r} />
                    {/if}
                {/each}
                <rect class="median" x={X(g.median) - 1.5} y="7" width="3" height={ROW - 14} rx="1" />
                {#if g.uid === activeUid && activeDot}
                    <circle class="dot pick" cx={activeDot.x} cy={ROW / 2 + activeDot.y} r={r + 2} />
                {/if}
            </svg>
        </button>
    {/each}

    <div class="axis" style="grid-template-columns: {labelW}px minmax(0, 1fr)">
        <span></span>
        <div bind:clientWidth={plotW}>
            {#if plotW}
                <svg width={plotW} height="40" aria-hidden="true">
                    {#each T.ticks as t, i}
                        {#if i % stride === 0}<text class="tick" x={X(t)} y="16" text-anchor="middle">{tickText(t, def.fmt, T.step)}</text>{/if}
                    {/each}
                    <text class="axisTitle" x={plotW / 2} y="34" text-anchor="middle">{def.label} →</text>
                </svg>
            {:else}
                <div style="height: 40px"></div>
            {/if}
        </div>
    </div>

    {#if active && activeDot && !touch && !narrowScreen}
        <div class="tip" style="left: {Math.min(Math.max(labelW + activeDot.x, 100), labelW + plotW - 100)}px; top: {activeIx * ROW + ROW / 2 + activeDot.y}px">
            <p class="tipHead">{labelOf(activeDot.row)}{oppNote(activeDot.row)}</p>
            <div class="tipRow"><strong>{fmtMeasure(activeDot.row[measure], measure)}</strong><span>{def.label}</span></div>
        </div>
    {/if}
</div>

{#if showPanel}
    <div class="panel" aria-live="polite">
        <p class="tipHead">{nameOf(active.uid)} · {active.n} {noun}{active.n === 1 ? '' : 's'}</p>
        <div class="tipRow"><strong>{medianOf(active)}</strong><span>median</span></div>
        {#if active.band}
            <div class="tipRow"><strong>{range(active)}</strong><span>middle half</span></div>
        {/if}
        <div class="tipRow"><strong>{fmtMeasure(active.lo, measure)} to {fmtMeasure(active.hi, measure)}</strong><span>lowest to highest</span></div>
        {#if activeDot}
            <p class="tipHead" style="margin-top: 0.6em">{labelOf(activeDot.row)}{oppNote(activeDot.row)}</p>
            <div class="tipRow"><strong>{fmtMeasure(activeDot.row[measure], measure)}</strong><span>{def.label}</span></div>
            <button type="button" class="narrowBtn" onclick={() => narrow(activeDot.row)}>{narrowLabel(activeDot.row)}</button>
        {/if}
        <button type="button" class="narrowBtn" class:quiet={!!activeDot} onclick={() => narrowManager(active.uid)}>{narrowManagerLabel(active.uid)}</button>
    </div>
{:else}
    <p class="hint">{narrowScreen ? 'Tap a row to inspect it, or tap near a dot to pick that game.' : `Hover a row to highlight it and a dot to inspect it; click a dot to narrow to that ${ds === 'games' ? 'week' : 'manager'}, or the row to narrow to the manager.`}</p>
{/if}

<ul class="legend" aria-hidden="true">
    <li><svg width="10" height="10"><circle cx="5" cy="5" r="3.5" fill="var(--vizDot)" /></svg>one {noun}</li>
    <li><svg width="6" height="16"><rect x="1.5" y="1" width="3" height="14" rx="1" fill="var(--vizInk)" /></svg>manager’s median, shown under the name</li>
    {#if laid.some((g) => g.band)}
        <li><svg width="18" height="14"><rect x="0" y="1" width="18" height="12" rx="3" fill="var(--vizBand)" stroke="var(--vizAxis)" /></svg>middle half</li>
    {/if}
    <li><svg width="6" height="16"><rect x="2" y="0" width="2" height="16" fill="var(--vizAxis)" /></svg>everyone’s median, {fmtMeasure(leagueMedian, measure)}</li>
</ul>
