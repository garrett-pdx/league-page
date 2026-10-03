<script>
    /*
    Two measures against each other, one dot per row. Hairlines at the average of each measure cut
    the plot into quadrants, captioned in the corners ("In control", "Shootouts" ... for points for
    vs. against; generic "High PF, low PA" captions for any other pair).

    One series, so one colour and no legend. Labels are selective: the most extreme dot in each
    quadrant is named, and so is whichever dot is being inspected. Everything else is in the table.

    The pointer finds the NEAREST dot within 28px rather than needing to land on an 10px circle.
    With a mouse, hovering inspects and clicking narrows the filters to that row; on a phone a tap
    inspects, and the readout under the chart carries the button that narrows.
    */
    import { MEASURES, fmtMeasure, quadrantLabels } from './statLab.js';
    import { niceTicks, linear, tickText } from './scale.js';

    let { rows = [], x, y, labelOf, narrow, narrowLabel, narrowScreen = false } = $props();

    let width = $state(0);
    let activeId = $state(null);
    let touch = $state(false);

    const has = (v) => v !== null && v !== undefined;
    const pts = $derived(rows.filter((r) => has(r[x]) && has(r[y])));
    const dx = $derived(MEASURES[x]);
    const dy = $derived(MEASURES[y]);

    const height = $derived(narrowScreen ? 320 : 420);
    const m = $derived({ top: 30, right: 16, bottom: 46, left: narrowScreen ? 48 : 62 });
    const plotW = $derived(Math.max(10, width - m.left - m.right));
    const plotH = $derived(height - m.top - m.bottom);

    const axis = (key, count, r0, r1) => {
        const vals = pts.map((r) => r[key]);
        const t = niceTicks(Math.min(...vals), Math.max(...vals), count);
        return { ...t, s: linear([t.lo, t.hi], [r0, r1]) };
    };
    const X = $derived(axis(x, narrowScreen ? 4 : 6, m.left, m.left + plotW));
    // lower-is-better on the vertical axis (final place) puts 1st at the top
    const Y = $derived(dy.low ? axis(y, 5, m.top, m.top + plotH) : axis(y, 5, m.top + plotH, m.top));

    const mean = (key) => pts.reduce((s, r) => s + r[key], 0) / (pts.length || 1);
    const mx = $derived(mean(x));
    const my = $derived(mean(y));
    const quads = $derived(quadrantLabels(x, y));

    // the most extreme dot in each quadrant, by distance from the averages in axis-scaled units
    const extremes = $derived.by(() => {
        if(pts.length < 3) return new Set(pts.map((r) => r.id));
        const best = {};
        for(const r of pts) {
            const ddx = (r[x] - mx) / (X.hi - X.lo || 1);
            const ddy = (r[y] - my) / (Y.hi - Y.lo || 1);
            const q = `${ddx >= 0}${ddy >= 0}`;
            const d = ddx * ddx + ddy * ddy;
            if(!best[q] || d > best[q].d) best[q] = { d, id: r.id };
        }
        return new Set(Object.values(best).map((b) => b.id));
    });

    const active = $derived(pts.find((r) => r.id === activeId) ?? null);

    /*
    Point labels, placed so they never sit on a quadrant caption or run off the plot: try the
    right of the dot, then the left, then above, then below; a label with nowhere free is
    dropped (the table still has it). Text width is estimated at 6.6px a character at 12px,
    which is generous for Roboto, so the estimate errs towards keeping clear.
    */
    const textW = (t) => t.length * 6.6;
    const overlaps = (a, b) => a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1;
    const labels = $derived.by(() => {
        const taken = [
            { x0: m.left, x1: m.left + textW(quads[0]) + 8, y0: m.top, y1: m.top + 20 },
            { x0: m.left + plotW - textW(quads[1]) - 8, x1: m.left + plotW, y0: m.top, y1: m.top + 20 },
            { x0: m.left, x1: m.left + textW(quads[2]) + 8, y0: m.top + plotH - 22, y1: m.top + plotH },
            { x0: m.left + plotW - textW(quads[3]) - 8, x1: m.left + plotW, y0: m.top + plotH - 22, y1: m.top + plotH },
        ];
        const out = [];
        for(const r of pts.filter((p) => extremes.has(p.id) || p.id === activeId)) {
            const cx = X.s(r[x]), cy = Y.s(r[y]), text = labelOf(r), w = textW(text);
            const tries = [
                { x: cx + 9, y: cy, anchor: 'start', box: { x0: cx + 9, x1: cx + 9 + w } },
                { x: cx - 9, y: cy, anchor: 'end', box: { x0: cx - 9 - w, x1: cx - 9 } },
                { x: cx, y: cy - 14, anchor: 'middle', box: { x0: cx - w / 2, x1: cx + w / 2 } },
                { x: cx, y: cy + 14, anchor: 'middle', box: { x0: cx - w / 2, x1: cx + w / 2 } },
            ];
            for(const t of tries) {
                const box = { ...t.box, y0: t.y - 8, y1: t.y + 8 };
                if(box.x0 < m.left - 4 || box.x1 > m.left + plotW + 4) continue;
                if(taken.some((b) => overlaps(b, box))) continue;
                taken.push(box);
                out.push({ id: r.id, text, x: t.x, y: t.y, anchor: t.anchor });
                break;
            }
        }
        return out;
    });

    const locate = (e) => {
        const rect = e.currentTarget.ownerSVGElement.getBoundingClientRect();
        const px = e.clientX - rect.left;
        const py = e.clientY - rect.top;
        let best = null, bestD = 28 * 28;
        for(const r of pts) {
            const d = (X.s(r[x]) - px) ** 2 + (Y.s(r[y]) - py) ** 2;
            if(d < bestD) { bestD = d; best = r.id; }
        }
        return best;
    };

    const onmove = (e) => {
        touch = e.pointerType !== 'mouse';
        if(touch && e.type === 'pointermove') return;   // a drag on a phone is a scroll
        activeId = locate(e);
    };
    const onleave = (e) => { if(e.pointerType === 'mouse') activeId = null; };
    const onclick = () => { if(!touch && active) narrow(active); };

    const ariaSummary = $derived(
        `Scatter plot of ${dy.label} against ${dx.label}, ${pts.length} points, with lines at the average of each. ` +
        `Every value is in the table below.`
    );
</script>

<style>
    .wrap { position: relative; }
    svg { display: block; overflow: visible; touch-action: pan-y; }
    .grid { stroke: var(--vizGrid); stroke-width: 1; shape-rendering: crispEdges; }
    .avg { stroke: var(--vizAxis); stroke-width: 1; shape-rendering: crispEdges; }
    .tick { fill: var(--vizInk2); font-size: 12px; font-variant-numeric: tabular-nums; }
    .title { fill: var(--vizInk); font-size: 12px; font-weight: 500; }
    .quad { fill: var(--vizInk2); font-size: 12px; font-style: italic; }
    .dot { fill: var(--vizS1); fill-opacity: 0.82; stroke: var(--vizSurface); stroke-width: 2; }
    .dot.on { fill-opacity: 1; fill: var(--navy700); }
    .name { fill: var(--vizInk); font-size: 12px; }
    .hit { fill: transparent; cursor: pointer; }

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
        transform: translate(-50%, calc(-100% - 12px));
    }

    .panel {
        margin-top: 0.6em;
        padding: 0.6em 0.7em;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusSm);
        font-size: 0.875rem;
    }

    .tipHead { margin: 0 0 0.2em; font-weight: 700; }
    .tipRow { display: flex; gap: 0.5em; line-height: 1.5; }
    .tipRow strong { font-variant-numeric: tabular-nums; }
    .tipRow span { color: var(--vizInk2); }

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

<div class="wrap" bind:clientWidth={width} style="min-height: {height}px">
    {#if width && pts.length}
        <svg {width} {height} role="img" aria-label={ariaSummary}>
            {#each Y.ticks as t}
                <line class="grid" x1={m.left} x2={m.left + plotW} y1={Y.s(t)} y2={Y.s(t)} />
                <text class="tick" x={m.left - 8} y={Y.s(t)} dy="0.32em" text-anchor="end">{tickText(t, dy.fmt, Y.step)}</text>
            {/each}
            {#each X.ticks as t}
                <text class="tick" x={X.s(t)} y={m.top + plotH + 18} text-anchor="middle">{tickText(t, dx.fmt, X.step)}</text>
            {/each}
            <text class="title" x={m.left + plotW / 2} y={height - 6} text-anchor="middle">{dx.label} →</text>
            <text class="title" x={m.left - (narrowScreen ? 40 : 54)} y={14}>↑ {dy.label}</text>

            <line class="avg" x1={X.s(mx)} x2={X.s(mx)} y1={m.top} y2={m.top + plotH} />
            <line class="avg" x1={m.left} x2={m.left + plotW} y1={Y.s(my)} y2={Y.s(my)} />

            <text class="quad" x={m.left + 6} y={m.top + 14}>{quads[0]}</text>
            <text class="quad" x={m.left + plotW - 6} y={m.top + 14} text-anchor="end">{quads[1]}</text>
            <text class="quad" x={m.left + 6} y={m.top + plotH - 8}>{quads[2]}</text>
            <text class="quad" x={m.left + plotW - 6} y={m.top + plotH - 8} text-anchor="end">{quads[3]}</text>

            {#each pts as r (r.id)}
                {#if r.id !== activeId}
                    <circle class="dot" cx={X.s(r[x])} cy={Y.s(r[y])} r={pts.length > 150 ? 4 : 5} />
                {/if}
            {/each}
            {#if active}
                <circle class="dot on" cx={X.s(active[x])} cy={Y.s(active[y])} r="7" />
            {/if}

            {#each labels as l (l.id)}
                <text class="name" x={l.x} y={l.y} dy="0.32em" text-anchor={l.anchor}
                    paint-order="stroke" stroke="var(--vizSurface)" stroke-width="4" stroke-linejoin="round">{l.text}</text>
            {/each}

            <rect class="hit" x={m.left - 14} y={m.top - 14} width={plotW + 28} height={plotH + 28}
                role="presentation"
                onpointermove={onmove} onpointerdown={onmove} onpointerleave={onleave} {onclick} />
        </svg>

        {#if active && !touch && !narrowScreen}
            <div class="tip" style="left: {Math.min(Math.max(X.s(active[x]), 90), width - 90)}px; top: {Y.s(active[y])}px">
                <p class="tipHead">{labelOf(active)}</p>
                <div class="tipRow"><strong>{fmtMeasure(active[y], y)}</strong><span>{dy.label}</span></div>
                <div class="tipRow"><strong>{fmtMeasure(active[x], x)}</strong><span>{dx.label}</span></div>
            </div>
        {/if}
    {/if}
</div>

{#if active && (touch || narrowScreen)}
    <div class="panel" aria-live="polite">
        <p class="tipHead">{labelOf(active)}</p>
        <div class="tipRow"><strong>{fmtMeasure(active[y], y)}</strong><span>{dy.label}</span></div>
        <div class="tipRow"><strong>{fmtMeasure(active[x], x)}</strong><span>{dx.label}</span></div>
        <button type="button" class="narrowBtn" onclick={() => narrow(active)}>{narrowLabel(active)}</button>
    </div>
{:else}
    <p class="hint">{narrowScreen ? 'Tap a dot to inspect it.' : 'Hover a dot to inspect it; click to narrow to it.'} Lines mark the averages.</p>
{/if}
