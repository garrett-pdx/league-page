<script>
    /*
    The ranking chart: horizontal bars, in the table's order, top N.

    Built from HTML rather than SVG because every bar is also a control. Each row is one real
    <button> -- rank, name, bar, value -- so it is keyboard reachable, 44px tall, announces itself
    properly, and clicking it narrows the filters (see Lab's narrow()). Every bar carries its value
    at the tip, so there is no value axis to read and nothing hides behind a tooltip.

    Bars start at zero, always: a bar's length is its value. Signed measures (luck, margin) run
    either side of a centre line, positive in the series blue and negative in the warm pole of the
    diverging pair -- and the value text keeps its + or minus, so colour is never the only cue.
    */
    import { MEASURES, fmtMeasure } from './statLab.js';

    let { rows = [], measure, labelOf, narrow, narrowLabel, total = 0 } = $props();

    const def = $derived(MEASURES[measure]);
    const values = $derived(rows.map((r) => r[measure]).filter((v) => v !== null && v !== undefined));
    const lo = $derived(Math.min(0, ...values));
    const hi = $derived(Math.max(0, ...values, lo === 0 ? 1e-9 : 0));
    const signed = $derived(lo < 0);
    const pos = (v) => ((v - lo) / (hi - lo || 1)) * 100;
    const zero = $derived(pos(0));
</script>

<style>
    .bars { list-style: none; margin: 0; padding: 0; }

    .row {
        appearance: none;
        display: grid;
        grid-template-columns: 2.4em minmax(0, 13em) minmax(0, 1fr);
        align-items: center;
        gap: 0.6em;
        width: 100%;
        min-height: 44px;
        padding: 2px 0.4em;
        border: none;
        border-radius: var(--radiusSm);
        background: transparent;
        font: inherit;
        color: var(--vizInk);
        text-align: left;
        cursor: pointer;
    }

    @media (hover: hover) {
        .row:hover { background: var(--navy050); }
        .row:hover .bar { filter: brightness(0.88); }
    }

    .row:focus-visible { outline: 2px solid var(--blueOne); outline-offset: -2px; }

    .rank {
        font-variant-numeric: tabular-nums;
        color: var(--vizInk2);
        font-size: 0.9rem;
        text-align: right;
    }

    .name {
        font-size: 0.95rem;
        line-height: 1.2;
        overflow-wrap: anywhere;
    }

    /* the plot area leaves room at the ends for the value labels, so a label never overflows */
    .track { position: relative; height: 24px; margin: 0 4.6em 0 0; }
    .track.signed { margin-left: 4.6em; }

    .bar {
        position: absolute;
        top: 2px;
        height: 20px;
        background: var(--vizS1);
        border-radius: 0 4px 4px 0;
    }

    .bar.neg { background: var(--vizNeg); border-radius: 4px 0 0 4px; }

    .zero {
        position: absolute;
        top: -11px;
        bottom: -11px;
        width: 1px;
        background: var(--vizAxis);
    }

    .value {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        font-size: 0.9rem;
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
        color: var(--vizInk);
    }

    .value.right { padding-left: 6px; }
    .value.left { padding-right: 6px; transform: translate(-100%, -50%); }

    .more {
        margin: 0.4em 0 0;
        font-size: 0.85rem;
        color: var(--vizInk2);
    }

    @media (max-width: 700px) {
        .row { grid-template-columns: 1.8em minmax(0, 7.5em) minmax(0, 1fr); gap: 0.4em; padding: 2px 0.2em; }
        .name { font-size: 0.875rem; }
        .track { margin-right: 4.2em; }
        .track.signed { margin-left: 4.2em; }
        .value { font-size: 0.8rem; }
    }
</style>

<ul class="bars" aria-label="{def.label}, ranked">
    {#each rows as r (r.id)}
        {@const v = r[measure]}
        {@const has = v !== null && v !== undefined}
        {@const neg = has && v < 0}
        <li>
            <button
                type="button"
                class="row"
                onclick={() => narrow(r)}
                title={narrowLabel(r)}
                aria-label="{r.rank ?? '–'}. {labelOf(r)}: {fmtMeasure(v, measure)}. {narrowLabel(r)}"
            >
                <span class="rank" aria-hidden="true">{r.rank ?? '–'}</span>
                <span class="name" aria-hidden="true">{labelOf(r)}</span>
                <span class="track" class:signed aria-hidden="true">
                    {#if signed}<span class="zero" style="left: {zero}%"></span>{/if}
                    {#if has}
                        <span class="bar" class:neg
                            style="left: {Math.min(zero, pos(v))}%; width: {Math.max(Math.abs(pos(v) - zero), 0.6)}%"></span>
                        <span class="value {neg ? 'left' : 'right'}" style="left: {pos(v)}%">{fmtMeasure(v, measure)}</span>
                    {:else}
                        <span class="value right" style="left: {zero}%">—</span>
                    {/if}
                </span>
            </button>
        </li>
    {/each}
</ul>
{#if total > rows.length}
    <p class="more">Showing {rows.length} of {total}, in rank order.</p>
{/if}
