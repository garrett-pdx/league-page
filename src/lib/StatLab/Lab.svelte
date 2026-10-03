<script>
    /*
    The whole of Stat Lab once the data is in: presets, controls, chart, table.

    THE ADDRESS IS THE STATE. `view` is derived from page.url on every render and nothing else
    holds a copy, so a link, a reload and the Back button all land on exactly the same view.
    Controls never set local state -- they call update(), which writes the query string:
      * an ordinary control change REPLACES the history entry (no entry per click or keystroke);
      * a preset, or clicking a bar / point / row to narrow the filters, PUSHES one, so Back
        undoes it.
    Both keep focus and scroll position. See statLab.js for the parameter list.
    */
    import { page } from '$app/state';
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';
    import { managers } from '$lib/utils/leagueInfo';
    import { managerHref } from '$lib/utils/managerLink';
    import { SegmentedControl } from '$lib/Design';
    import {
        DATASETS, GAME_TYPES, MEASURES, DEFAULT_MEASURE,
        measuresFor, chartsFor, annotateGames, buildRows, sortRows,
        parseState, serializeState, presets as makePresets, defaultDir,
    } from './statLab.js';
    import MultiChips from './MultiChips.svelte';
    import BarChart from './BarChart.svelte';
    import LineChart from './LineChart.svelte';
    import ScatterChart from './ScatterChart.svelte';
    import DataTable from './DataTable.svelte';

    let { games, history } = $props();

    /* ---- who's who ------------------------------------------------------------------------ */

    const seasons = [...new Set(games.games.map((g) => g.season))].sort();
    const currentSeason = games.through?.season ?? seasons[seasons.length - 1];
    const playingNow = new Set(games.games.filter((g) => g.season === currentSeason).map((g) => g.user_id));

    // leagueInfo order first (it is the order the Managers page uses), anyone else after.
    // Football_Team never held a roster and so is never in games.json; the filter is a guard.
    const order = (uid) => {
        const i = managers.findIndex((m) => m.managerID == uid);
        return i < 0 ? 999 : i;
    };
    const uids = games.managers
        .filter((uid) => history.managers?.[uid]?.handle !== 'Football_Team')
        .sort((a, b) => order(a) - order(b));

    const people = {};
    for(const uid of uids) {
        const handle = history.managers?.[uid]?.handle ?? uid;
        const entry = managers.find((m) => m.managerID == uid);
        const name = entry?.name ?? handle;
        people[uid] = {
            uid,
            handle: handle.toLowerCase(),
            name,
            first: name.split(' ')[0],
            photo: entry?.photo ?? null,
            href: managerHref({ leagueTeamManagers: {}, managerID: uid }),
            former: !playingNow.has(uid),
        };
    }
    // first names, unless two managers share one
    const firstCount = {};
    for(const p of Object.values(people)) firstCount[p.first] = (firstCount[p.first] || 0) + 1;
    for(const p of Object.values(people)) p.short = firstCount[p.first] > 1 ? p.name : p.first;

    const handles = {};
    for(const p of Object.values(people)) handles[p.handle] = p.uid;

    const ctx = { seasons, handles };
    const nameOf = (uid) => people[uid]?.short ?? uid;

    const lastFinished = Object.keys(history.final_standings || {}).sort().pop();
    const champUid = history.final_standings?.[lastFinished]?.find((p) => p.place === 1)?.user_id;
    const finished = seasons.filter((s) => history.final_standings?.[String(s)]?.length);
    const presetList = makePresets({ currentSeason, finished, champion: people[champUid]?.handle });

    const annotated = annotateGames(games.games);

    /* ---- the view ------------------------------------------------------------------------- */

    const view = $derived(parseState(page.url.searchParams, ctx));
    const rows = $derived(buildRows(annotated, history, view));
    const sorted = $derived(sortRows(rows, view.sort, view.dir, nameOf));
    const measureList = $derived(measuresFor(view.ds));

    const canon = (query) => serializeState(parseState(new URLSearchParams(query), ctx));
    const activePreset = $derived.by(() => {
        const here = serializeState(view);
        return presetList.find((p) => canon(p.query) === here)?.id ?? null;
    });

    const commit = (next, push = false) => {
        const qs = serializeState(next);
        goto(qs ? `?${qs}` : page.url.pathname, { replaceState: !push, keepFocus: true, noScroll: true });
    };
    const update = (patch, push = false) => commit({ ...view, ...patch }, push);

    const otherThan = (m) => (m === 'pf' ? 'pa' : 'pf');

    const setDataset = (ds) => {
        const ok = (k) => MEASURES[k].ds.includes(ds);
        const m = ok(view.m) ? view.m : DEFAULT_MEASURE[ds];
        let x = ok(view.x) ? view.x : otherThan(m);
        if(x === m) x = otherThan(m);
        const chart = view.chart === 'line' && ds === 'managers' ? 'bar' : view.chart;
        update({ ds, m, x, chart, sort: m, dir: defaultDir(m) });
    };
    const setMeasure = (m) => update({ m, x: view.x === m ? otherThan(m) : view.x, sort: m, dir: defaultDir(m) });
    const setX = (x) => update({ x, m: view.m === x ? otherThan(x) : view.m });

    const setWeek = (end, value) => {
        const wk = [...view.wk];
        wk[end] = value === '' ? null : Number(value);
        if(wk[0] !== null && wk[1] !== null && wk[0] > wk[1]) wk[end === 0 ? 1 : 0] = wk[end];
        update({ wk });
    };

    const setSort = (key) => {
        const dir = view.sort === key ? (view.dir === 'asc' ? 'desc' : 'asc') : defaultDir(key);
        update({ sort: key, dir });
    };

    const applyPreset = (p) => goto(`?${p.query}`, { keepFocus: true, noScroll: true });

    /** Clicking a bar, point or row: a game narrows to its week, anything else to its manager. */
    const narrow = (row) => {
        if(view.ds === 'games') update({ season: [row.season], wk: [row.week, row.week] }, true);
        else update({ mgr: [people[row.user_id].handle] }, true);
    };
    const narrowLabel = (row) =>
        view.ds === 'games' ? `Show ${row.season} week ${row.week}` : `Show only ${nameOf(row.user_id)}`;

    /** How a row is named on a chart: "Michael · 2023 W5", "Michael · 2023", "Michael". */
    const labelOf = (row) => {
        // a single selected season is already in the caption, so it isn't repeated on every mark
        const who = nameOf(row.user_id);
        const one = view.season.length === 1;
        if(view.ds === 'games') return `${who} · ${one ? '' : `${row.season} `}W${row.week}`;
        if(view.ds === 'seasons' && !one) return `${who} · ${row.season}`;
        return who;
    };

    /* ---- summary ------------------------------------------------------------------------- */

    const listOf = (items, all, many) =>
        !items.length ? all : items.length <= 3 ? items.join(', ') : `${items.length} ${many}`;

    const summary = $derived.by(() => {
        const out = [
            DATASETS.find((d) => d.value === view.ds).label,
            view.chart === 'scatter' ? `${MEASURES[view.x].short} vs ${MEASURES[view.m].short}` : MEASURES[view.m].label,
            listOf(view.season.map(String), 'All seasons', 'seasons'),
            listOf(view.mgrIds.map(nameOf), 'All managers', 'managers'),
            { regular: 'Regular season', playoffs: 'Playoffs', all: 'All games' }[view.type],
        ];
        const [a, b] = view.wk;
        if(a !== null || b !== null) out.push(a === b ? `Week ${a}` : `Weeks ${a ?? 1}–${b ?? 17}`);
        if(view.oppIds.length) out.push(`vs ${listOf(view.oppIds.map(nameOf), '', 'opponents')}`);
        return out;
    });

    /* ---- layout -------------------------------------------------------------------------- */

    let narrowScreen = $state(false);
    let sheetOpen = $state(false);
    onMount(() => {
        const mq = window.matchMedia('(max-width: 700px)');
        const set = () => (narrowScreen = mq.matches);
        set();
        mq.addEventListener('change', set);
        return () => mq.removeEventListener('change', set);
    });

    const weeks = Array.from({ length: 17 }, (_, i) => i + 1);
    const seasonOptions = seasons.map((s) => ({ value: String(s), label: String(s) }));
    const managerOptions = uids.map((uid) => ({ value: people[uid].handle, label: people[uid].short }));

    const topN = $derived(view.top === 'all' ? Infinity : Number(view.top));
    const barRows = $derived(sorted.slice(0, topN));
    const allowAll = $derived(sorted.length <= 100);

    const stamp = `Data through ${games.through.season} week ${games.through.week}`;
    const showLuckNote = $derived(['luck', 'allPlayPct'].includes(view.m) || (view.chart === 'scatter' && ['luck', 'allPlayPct'].includes(view.x)));
</script>

<style>
    .lab {
        width: 94%;
        max-width: var(--pageMax);
        margin: 0 auto 4em;
        /* chart palette: the dataviz reference palette's first four categorical slots, validated
           on white (adjacent CVD dE >= 9.1). Slots 3 and 4 sit under 3:1 on white, so lines
           using them always carry an end label and a legend, and the table is under every chart. */
        --vizSurface: #fff;
        --vizS1: #2a78d6;
        --vizS2: #eb6834;
        --vizS3: #1baf7a;
        --vizS4: #eda100;
        --vizNeg: #e34948;          /* the diverging pair's warm pole, for negative values */
        --vizDim: #c3c2b7;          /* de-emphasised series */
        --vizGrid: #e1e0d9;
        --vizAxis: #c3c2b7;
        --vizInk: var(--g333);
        --vizInk2: var(--g555);     /* 7.4:1 on white: safe for 12px tick labels */
    }

    /* SegmentedControl keeps a compact 34px for a mouse on desktop; every Stat Lab control is 44px
       at every width, so the segments are raised here rather than in the shared primitive. */
    .lab :global(.segmented .segment) { min-height: 44px; }

    /* presets */
    .presets {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 8px;
        margin: 0 0 1.2em;
    }

    .presetsLabel {
        width: 100%;
        text-align: center;
        font-family: var(--fontDisplay);
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--g555);
    }

    .chip {
        appearance: none;
        min-height: 44px;
        padding: 0 1em;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusPill);
        background: var(--fff);
        color: var(--accentInk);
        font: inherit;
        font-size: 0.9rem;
        font-weight: 500;
        cursor: pointer;
    }

    .chip[aria-pressed='true'] {
        background: var(--accentFill);
        border-color: var(--accentFill);
        color: #fff;
    }

    @media (hover: hover) {
        .chip:hover:not([aria-pressed='true']) { background: var(--navy050); }
    }

    .chip:focus-visible, .sheetToggle:focus-visible, select:focus-visible, .reset:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }

    /* the phone summary + filter sheet toggle */
    .sheetToggle { display: none; }

    .controls {
        background: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        padding: 1em 1.2em;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
        gap: 1em 1.4em;
        align-items: start;
        margin-bottom: 1.2em;
    }

    .field { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
    .field.wide { grid-column: 1 / -1; }

    .label {
        font-family: var(--fontDisplay);
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--g555);
    }

    select {
        min-height: 44px;
        padding: 0 0.6em;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusSm);
        background: var(--fff);
        color: var(--g111);
        font: inherit;
        font-size: 1rem;
        max-width: 100%;
    }

    .weeks { display: flex; align-items: center; gap: 0.5em; }
    .weeks select { flex: 1; }

    .measureNote {
        margin: 0;
        font-size: 0.85rem;
        color: var(--g555);
        line-height: 1.4;
    }

    .actions { display: flex; justify-content: flex-end; align-items: end; }

    .reset {
        display: inline-flex;
        align-items: center;
        min-height: 44px;
        padding: 0 1em;
        color: var(--accentInk);
        font-weight: 500;
        text-decoration: underline;
        text-underline-offset: 3px;
    }

    /* chart card */
    .chartCard {
        margin: 0 0 1.4em;
        background: var(--vizSurface);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        padding: 1em 1.2em 0.8em;
    }

    .chartHead {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.6em 1em;
        margin-bottom: 0.8em;
    }

    .caption h3 {
        margin: 0;
        font-size: 1.3rem;
        color: var(--navy700);
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    .caption p {
        margin: 0.2em 0 0;
        font-size: 0.9rem;
        color: var(--g555);
    }

    .stamp {
        margin: 0.8em 0 0;
        font-size: 0.8rem;
        color: var(--g555);
    }

    .empty {
        padding: 3em 1em;
        text-align: center;
        color: var(--g555);
    }

    @media (max-width: 700px) {
        .lab { width: auto; margin: 0 16px 3em; }

        .presets { justify-content: flex-start; }
        .presetsLabel { text-align: left; }

        .sheetToggle {
            appearance: none;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 6px;
            width: 100%;
            min-height: 44px;
            padding: 8px 10px;
            margin-bottom: 0.8em;
            border: 1px solid var(--accentBorder);
            border-radius: var(--radiusMd);
            background: var(--fff);
            box-shadow: var(--shadowCard);
            text-align: left;
            font: inherit;
            cursor: pointer;
        }

        .sumChip {
            padding: 3px 9px;
            border-radius: var(--radiusPill);
            background: var(--navy050);
            border: 1px solid var(--accentBorder);
            color: var(--navy700);
            font-size: 0.8rem;
        }

        .sheetLabel {
            margin-left: auto;
            font-family: var(--fontDisplay);
            font-size: 0.85rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--accentInk);
            padding-left: 6px;
        }

        .controls { display: none; grid-template-columns: 1fr; padding: 1em; }
        .controls.open { display: grid; }

        .chartCard { padding: 0.9em 0.7em 0.7em; }
    }
</style>

<div class="lab">
    <div class="presets" role="group" aria-label="Presets">
        <span class="presetsLabel">Start from</span>
        {#each presetList as p}
            <button type="button" class="chip" aria-pressed={activePreset === p.id} onclick={() => applyPreset(p)}>
                {p.label}
            </button>
        {/each}
    </div>

    <button
        type="button"
        class="sheetToggle"
        aria-expanded={sheetOpen}
        aria-controls="statlab-controls"
        onclick={() => (sheetOpen = !sheetOpen)}
    >
        {#each summary as s}<span class="sumChip">{s}</span>{/each}
        <span class="sheetLabel">{sheetOpen ? 'Done' : 'Filters'}</span>
    </button>

    <section id="statlab-controls" class="controls" class:open={sheetOpen} aria-label="Stat Lab controls">
        <div class="field">
            <span class="label" id="sl-ds">Dataset</span>
            <SegmentedControl options={DATASETS} value={view.ds} onchange={setDataset} ariaLabel="Dataset" fullWidth />
        </div>

        <div class="field">
            <span class="label">Chart</span>
            <SegmentedControl options={chartsFor(view.ds)} value={view.chart} onchange={(chart) => update({ chart })} ariaLabel="Chart type" fullWidth />
        </div>

        <div class="field">
            <label class="label" for="sl-measure">{view.chart === 'scatter' ? 'Measure (up)' : 'Measure'}</label>
            <select id="sl-measure" value={view.m} onchange={(e) => setMeasure(e.currentTarget.value)}>
                {#each measureList as m}<option value={m.key}>{m.label}</option>{/each}
            </select>
        </div>

        {#if view.chart === 'scatter'}
            <div class="field">
                <label class="label" for="sl-x">Measure (across)</label>
                <select id="sl-x" value={view.x} onchange={(e) => setX(e.currentTarget.value)}>
                    {#each measureList as m}<option value={m.key}>{m.label}</option>{/each}
                </select>
            </div>
        {/if}

        <div class="field">
            <span class="label">Game type</span>
            <SegmentedControl options={GAME_TYPES} value={view.type} onchange={(type) => update({ type })} ariaLabel="Game type" fullWidth />
        </div>

        <div class="field">
            <span class="label" id="sl-weeks">Weeks</span>
            <div class="weeks" role="group" aria-labelledby="sl-weeks">
                <select aria-label="From week" value={view.wk[0] ?? ''} onchange={(e) => setWeek(0, e.currentTarget.value)}>
                    <option value="">Week 1</option>
                    {#each weeks.slice(1) as w}<option value={w}>Week {w}</option>{/each}
                </select>
                <span aria-hidden="true">–</span>
                <select aria-label="To week" value={view.wk[1] ?? ''} onchange={(e) => setWeek(1, e.currentTarget.value)}>
                    {#each weeks.slice(0, -1) as w}<option value={w}>Week {w}</option>{/each}
                    <option value="">Week 17</option>
                </select>
            </div>
        </div>

        <div class="field">
            <label class="label" for="sl-opp">Opponent</label>
            <select id="sl-opp" value={view.opp[0] ?? ''} onchange={(e) => update({ opp: e.currentTarget.value ? [e.currentTarget.value] : [] })}>
                <option value="">Anyone</option>
                {#each uids as uid}<option value={people[uid].handle}>{people[uid].name}</option>{/each}
            </select>
        </div>

        <div class="field wide">
            <MultiChips label="Seasons" options={seasonOptions} selected={view.season.map(String)}
                onchange={(list) => update({ season: list.map(Number) })} />
        </div>

        <div class="field wide">
            <MultiChips label="Managers" options={managerOptions} selected={view.mgr}
                onchange={(list) => update({ mgr: list })} />
        </div>

        <div class="field wide">
            <p class="measureNote"><strong>{MEASURES[view.m].label}:</strong> {MEASURES[view.m].desc}
                {#if view.chart === 'scatter'}<br /><strong>{MEASURES[view.x].label}:</strong> {MEASURES[view.x].desc}{/if}
                {#if showLuckNote}<br />All-play scores each team against every team that played that week, whatever the other filters.{/if}
            </p>
        </div>

        <div class="field wide actions">
            <a class="reset" href="/stat-lab" data-sveltekit-noscroll data-sveltekit-keepfocus>Reset everything</a>
        </div>
    </section>

    <section class="chartCard" aria-labelledby="sl-chart-title">
        <div class="chartHead">
            <div class="caption">
                <h3 id="sl-chart-title">{view.chart === 'scatter' ? `${MEASURES[view.x].label} vs. ${MEASURES[view.m].label}` : MEASURES[view.m].label}</h3>
                <p>{summary.filter((_, i) => i !== 1).join(' · ')}</p>
            </div>
            {#if view.chart === 'bar' && sorted.length > 10}
                <SegmentedControl
                    size="sm"
                    ariaLabel="Bars shown"
                    value={view.top}
                    onchange={(top) => update({ top })}
                    options={[
                        { value: '10', label: 'Top 10' },
                        { value: '25', label: 'Top 25' },
                        { value: 'all', label: `All ${sorted.length}`, disabled: !allowAll },
                    ]}
                />
            {/if}
        </div>

        {#if !sorted.length}
            <p class="empty">No games match these filters. <a class="reset" href="/stat-lab">Reset everything</a></p>
        {:else if view.chart === 'bar'}
            <BarChart rows={barRows} measure={view.m} {labelOf} {narrow} {narrowLabel} total={sorted.length} />
        {:else if view.chart === 'line'}
            <LineChart rows={sorted} ds={view.ds} measure={view.m} {people} {nameOf} {narrow} {narrowLabel} {narrowScreen} />
        {:else}
            <ScatterChart rows={sorted} x={view.x} y={view.m} {labelOf} {narrow} {narrowLabel} {narrowScreen} />
        {/if}

        <p class="stamp">{stamp}. {sorted.length} {sorted.length === 1 ? 'row' : 'rows'}; every one is in the table below.</p>
    </section>

    {#if sorted.length}
        <DataTable rows={sorted} ds={view.ds} measure={view.m} xMeasure={view.chart === 'scatter' ? view.x : null}
            sort={view.sort} dir={view.dir} {setSort} {people} {nameOf} {narrow} {narrowLabel} {narrowScreen} />
    {/if}
</div>
