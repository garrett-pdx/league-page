<script>
    /*
    A measure over time, one line per manager: weeks for the Games dataset (a continuous
    timeline when several seasons are selected), seasons for the Seasons dataset.

    COLOUR. Up to four managers get the first four categorical slots, each with a legend entry and
    an end label. Five or more would need hues past what stays distinguishable, so instead every
    line is a quiet grey and the one being inspected turns blue -- emphasis rather than a rainbow.
    Either way, hovering (or tapping) a line highlights it and dims the rest, and the legend
    buttons pin a highlight.

    Slots go by the managers' order in leagueInfo among those shown, so the same selection always
    gets the same colours.

    INSPECTING. A crosshair snaps to the nearest week or season; the readout lists every manager's
    value there, highest first. With a mouse it floats beside the crosshair and a click narrows the
    filters to the highlighted manager (or, for games, that week). On a phone a tap inspects, and
    the readout sits under the chart with a button that narrows.
    */
    import { MEASURES, fmtMeasure } from './statLab.js';
    import { niceTicks, linear, tickText } from './scale.js';

    let { rows = [], ds, measure, people, nameOf, narrow, narrowLabel, narrowScreen = false } = $props();

    const SLOTS = ['var(--vizS1)', 'var(--vizS2)', 'var(--vizS3)', 'var(--vizS4)'];

    let width = $state(0);
    let hoverIdx = $state(null);
    let hoverUid = $state(null);
    let pinned = $state(null);
    let readoutX = $state(0);
    let touch = $state(false);

    const def = $derived(MEASURES[measure]);
    const keyOf = (r) => (ds === 'games' ? r.season * 100 + r.week : r.season);

    const xKeys = $derived([...new Set(rows.map(keyOf))].sort((a, b) => a - b));
    const multiSeason = $derived(ds === 'games' && new Set(rows.map((r) => r.season)).size > 1);

    const series = $derived.by(() => {
        const by = new Map();
        for(const r of rows) {
            if(r[measure] === null || r[measure] === undefined) continue;
            if(!by.has(r.user_id)) by.set(r.user_id, new Map());
            by.get(r.user_id).set(keyOf(r), r);
        }
        const order = Object.keys(people);
        return [...by.entries()]
            .sort((a, b) => order.indexOf(a[0]) - order.indexOf(b[0]))
            .map(([uid, pts]) => ({ uid, pts }));
    });

    const categorical = $derived(series.length <= 4);
    const colorOf = (i) => (categorical ? SLOTS[i] : 'var(--vizDim)');

    const height = $derived(narrowScreen ? 280 : 360);
    const m = $derived({ top: 14, bottom: 34, left: narrowScreen ? 44 : 56, right: categorical ? (narrowScreen ? 70 : 100) : 16 });
    const plotW = $derived(Math.max(10, width - m.left - m.right));
    const plotH = $derived(height - m.top - m.bottom);

    const yScale = $derived.by(() => {
        const vals = rows.map((r) => r[measure]).filter((v) => v !== null && v !== undefined);
        const t = niceTicks(Math.min(...vals), Math.max(...vals), narrowScreen ? 4 : 5);
        return { ...t, y: linear([t.lo, t.hi], [m.top + plotH, m.top]) };
    });

    const xAt = (i) => (xKeys.length < 2 ? m.left + plotW / 2 : m.left + (i * plotW) / (xKeys.length - 1));
    const idxOf = $derived(new Map(xKeys.map((k, i) => [k, i])));

    const xLabel = (k) => (ds === 'games' ? `${Math.floor(k / 100)} week ${k % 100}` : String(k));

    // x ticks: season starts on a multi-season timeline, otherwise as many weeks/seasons as fit
    const xTicks = $derived.by(() => {
        if(multiSeason) {
            const out = [];
            let last = null;
            xKeys.forEach((k, i) => {
                const s = Math.floor(k / 100);
                if(s !== last) out.push({ i, text: String(s) });
                last = s;
            });
            return out;
        }
        const room = Math.max(1, Math.floor(plotW / 44));
        const every = Math.ceil(xKeys.length / room);
        return xKeys.map((k, i) => ({ i, text: ds === 'games' ? `W${k % 100}` : String(k) })).filter((_, i) => i % every === 0);
    });

    const pathOf = (s) => {
        let d = '';
        let pen = false;
        xKeys.forEach((k, i) => {
            const r = s.pts.get(k);
            if(!r) { pen = false; return; }
            d += `${pen ? 'L' : 'M'}${xAt(i).toFixed(1)},${yScale.y(r[measure]).toFixed(1)}`;
            pen = true;
        });
        return d;
    };

    // isolated points (a gap on both sides) would otherwise draw nothing
    const lonePoints = (s) => xKeys
        .map((k, i) => ({ i, r: s.pts.get(k) }))
        .filter(({ i, r }) => r && !s.pts.get(xKeys[i - 1]) && !s.pts.get(xKeys[i + 1]));

    const lastPoint = (s) => {
        for(let i = xKeys.length - 1; i >= 0; i--) {
            const r = s.pts.get(xKeys[i]);
            if(r) return { i, r };
        }
        return null;
    };

    const active = $derived(hoverUid ?? pinned);

    // End labels (categorical only): pushed apart where lines finish close together, with a
    // short leader from the line end to its label.
    const endLabels = $derived.by(() => {
        if(!categorical) return [];
        const items = series.map((s, si) => {
            const lp = lastPoint(s);
            if(!lp) return null;
            const y = yScale.y(lp.r[measure]);
            return { uid: s.uid, si, x: xAt(lp.i), y, ly: y };
        }).filter(Boolean).sort((a, b) => a.y - b.y);
        for(let i = 1; i < items.length; i++) {
            if(items[i].ly - items[i - 1].ly < 16) items[i].ly = items[i - 1].ly + 16;
        }
        return items;
    });

    const readout = $derived.by(() => {
        if(hoverIdx === null) return null;
        const k = xKeys[hoverIdx];
        const list = series
            .map((s, si) => ({ uid: s.uid, si, r: s.pts.get(k) }))
            .filter((e) => e.r)
            .sort((a, b) => b.r[measure] - a.r[measure]);
        return { k, list, activeRow: list.find((e) => e.uid === active)?.r ?? null };
    });

    const locate = (e) => {
        const svg = e.currentTarget.ownerSVGElement || e.currentTarget;
        const rect = svg.getBoundingClientRect();
        const px = e.clientX - rect.left;
        const py = e.clientY - rect.top;
        let i = xKeys.length < 2 ? 0 : Math.round(((px - m.left) / plotW) * (xKeys.length - 1));
        i = Math.max(0, Math.min(xKeys.length - 1, i));
        let best = null, bestD = Infinity;
        for(const s of series) {
            const r = s.pts.get(xKeys[i]);
            if(!r) continue;
            const d = Math.abs(yScale.y(r[measure]) - py);
            if(d < bestD) { bestD = d; best = s.uid; }
        }
        hoverIdx = i;
        hoverUid = best;
        readoutX = xAt(i);
    };

    const onmove = (e) => {
        touch = e.pointerType !== 'mouse';
        locate(e);
    };
    const onleave = (e) => {
        if(e.pointerType === 'mouse') { hoverIdx = null; hoverUid = null; }
    };
    const onclick = (e) => {
        if(touch) return;           // a tap only inspects; the readout below has the button
        if(readout?.activeRow) narrow(readout.activeRow);
    };

    const pin = (uid) => (pinned = pinned === uid ? null : uid);

    const ariaSummary = $derived(
        `Line chart of ${def.label} by ${ds === 'games' ? 'week' : 'season'}, ${series.length} ` +
        `${series.length === 1 ? 'manager' : 'managers'}. Every value is in the table below.`
    );
</script>

<style>
    .wrap { position: relative; }

    svg { display: block; overflow: visible; touch-action: pan-y; }

    .grid { stroke: var(--vizGrid); stroke-width: 1; shape-rendering: crispEdges; }
    .tick { fill: var(--vizInk2); font-size: 12px; font-variant-numeric: tabular-nums; }
    .line { fill: none; stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; transition: opacity 0.12s; }
    .line.emph { stroke-width: 2.5; }
    .faded { opacity: 0.22; }
    .cross { stroke: var(--vizAxis); stroke-width: 1; }
    .endName { fill: var(--vizInk); font-size: 12px; }
    .leader { stroke: var(--vizAxis); stroke-width: 1; }
    .hit { fill: transparent; cursor: crosshair; }

    .legend { display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 0.6em; padding: 0; list-style: none; }

    .key {
        appearance: none;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        min-height: 44px;
        padding: 0 0.7em;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusPill);
        background: var(--fff);
        color: var(--vizInk);
        font: inherit;
        font-size: 0.85rem;
        cursor: pointer;
    }

    .key[aria-pressed='true'] { border-color: var(--navy700); box-shadow: inset 0 0 0 1px var(--navy700); }
    .key:focus-visible { outline: 2px solid var(--blueOne); outline-offset: 2px; }
    .swatch { width: 16px; height: 0; border-top: 3px solid; border-radius: 2px; }

    .tip {
        position: absolute;
        top: 8px;
        z-index: 2;
        min-width: 11em;
        max-width: 16em;
        padding: 0.5em 0.7em;
        background: var(--fff);
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusSm);
        box-shadow: var(--shadowCardHover);
        pointer-events: none;
        font-size: 0.85rem;
    }

    .panel {
        margin-top: 0.6em;
        padding: 0.6em 0.7em;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusSm);
        font-size: 0.875rem;
    }

    .tipHead { margin: 0 0 0.3em; color: var(--vizInk2); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; }
    .tipRow { display: flex; align-items: center; gap: 0.5em; line-height: 1.5; }
    .tipRow strong { font-variant-numeric: tabular-nums; min-width: 4.6em; }
    .tipRow.on { font-weight: 700; }
    .tipRow .swatch { flex-shrink: 0; }
    .tipName { color: var(--vizInk2); }
    .tipRow.on .tipName { color: var(--vizInk); }

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

    .hint { margin: 0.4em 0 0; font-size: 0.8rem; color: var(--vizInk2); }
</style>

{#if series.length > 1}
    <ul class="legend" aria-label="Managers: choose one to highlight">
        {#each series as s, si (s.uid)}
            <li>
                <button type="button" class="key" aria-pressed={pinned === s.uid} onclick={() => pin(s.uid)}>
                    <span class="swatch" style="border-color: {categorical ? colorOf(si) : (active === s.uid ? 'var(--vizS1)' : 'var(--vizDim)')}"></span>
                    {nameOf(s.uid)}
                </button>
            </li>
        {/each}
    </ul>
{/if}

<div class="wrap" bind:clientWidth={width} style="min-height: {height}px">
    {#if width}
        <svg {width} {height} role="img" aria-label={ariaSummary}>
            {#each yScale.ticks as t}
                <line class="grid" x1={m.left} x2={m.left + plotW} y1={yScale.y(t)} y2={yScale.y(t)} />
                <text class="tick" x={m.left - 8} y={yScale.y(t)} dy="0.32em" text-anchor="end">{tickText(t, def.fmt, yScale.step)}</text>
            {/each}
            {#each xTicks as t}
                <text class="tick" x={xAt(t.i)} y={m.top + plotH + 22} text-anchor={multiSeason ? 'start' : 'middle'}>{t.text}</text>
            {/each}

            {#if hoverIdx !== null}
                <line class="cross" x1={xAt(hoverIdx)} x2={xAt(hoverIdx)} y1={m.top} y2={m.top + plotH} />
            {/if}

            {#each series as s, si (s.uid)}
                {#if s.uid !== active}
                    <path class="line" class:faded={active && categorical} d={pathOf(s)} stroke={colorOf(si)} />
                    {#each lonePoints(s) as p}
                        <circle cx={xAt(p.i)} cy={yScale.y(p.r[measure])} r="3" fill={colorOf(si)} class:faded={active && categorical} />
                    {/each}
                {/if}
            {/each}
            {#each series as s, si (s.uid)}
                {#if s.uid === active}
                    {@const lp = lastPoint(s)}
                    <path class="line emph" d={pathOf(s)} stroke={categorical ? colorOf(si) : 'var(--vizS1)'} />
                    {#each lonePoints(s) as p}
                        <circle cx={xAt(p.i)} cy={yScale.y(p.r[measure])} r="4" fill={categorical ? colorOf(si) : 'var(--vizS1)'} />
                    {/each}
                    {#if hoverIdx !== null && s.pts.get(xKeys[hoverIdx])}
                        <circle cx={xAt(hoverIdx)} cy={yScale.y(s.pts.get(xKeys[hoverIdx])[measure])} r="5"
                            fill={categorical ? colorOf(si) : 'var(--vizS1)'} stroke="var(--vizSurface)" stroke-width="2" />
                    {/if}
                    {#if !categorical && lp}
                        <text class="endName" x={Math.min(xAt(lp.i), m.left + plotW - 4)} y={yScale.y(lp.r[measure]) - 10}
                            text-anchor="end" paint-order="stroke" stroke="var(--vizSurface)" stroke-width="4">{nameOf(s.uid)}</text>
                    {/if}
                {/if}
            {/each}

            {#each endLabels as l (l.uid)}
                <circle cx={l.x} cy={l.y} r="4" fill={colorOf(l.si)} stroke="var(--vizSurface)" stroke-width="2"
                    class:faded={active && active !== l.uid} />
                {#if Math.abs(l.ly - l.y) > 2}
                    <line class="leader" x1={l.x + 5} y1={l.y} x2={l.x + 10} y2={l.ly} />
                {/if}
                <text class="endName" x={l.x + 12} y={l.ly} dy="0.32em" class:faded={active && active !== l.uid}>{nameOf(l.uid)}</text>
            {/each}

            <rect class="hit" x={m.left - 10} y={m.top} width={plotW + 20} height={plotH}
                role="presentation"
                onpointermove={onmove} onpointerdown={onmove} onpointerleave={onleave} {onclick} />
        </svg>

        {#if readout && !narrowScreen && !touch}
            <div class="tip" style={readoutX > width / 2 ? `right: ${width - readoutX + 14}px` : `left: ${readoutX + 14}px`}>
                <p class="tipHead">{xLabel(readout.k)}</p>
                {#each readout.list.slice(0, 11) as e (e.uid)}
                    <div class="tipRow" class:on={e.uid === active}>
                        <span class="swatch" style="border-color: {categorical ? colorOf(e.si) : (e.uid === active ? 'var(--vizS1)' : 'var(--vizDim)')}"></span>
                        <strong>{fmtMeasure(e.r[measure], measure)}</strong>
                        <span class="tipName">{nameOf(e.uid)}</span>
                    </div>
                {/each}
            </div>
        {/if}
    {/if}
</div>

{#if readout && (narrowScreen || touch)}
    <div class="panel" aria-live="polite">
        <p class="tipHead">{xLabel(readout.k)}</p>
        {#each readout.list as e (e.uid)}
            <div class="tipRow" class:on={e.uid === active}>
                <span class="swatch" style="border-color: {categorical ? colorOf(e.si) : (e.uid === active ? 'var(--vizS1)' : 'var(--vizDim)')}"></span>
                <strong>{fmtMeasure(e.r[measure], measure)}</strong>
                <span class="tipName">{nameOf(e.uid)}</span>
            </div>
        {/each}
        {#if readout.activeRow}
            <button type="button" class="narrowBtn" onclick={() => narrow(readout.activeRow)}>{narrowLabel(readout.activeRow)}</button>
        {/if}
    </div>
{:else}
    <p class="hint">{narrowScreen ? 'Tap the chart to inspect a point.' : 'Hover to inspect; click to narrow to the highlighted line.'}</p>
{/if}
