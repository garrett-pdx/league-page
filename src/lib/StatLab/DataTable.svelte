<script>
    /*
    The table under every chart: the same rows, in the same order, and the chart's text
    alternative. Click any heading to sort; the rank is recomputed for the new order (sortRows in
    statLab.js), which is what makes sorting safe here when it wasn't on Records' top-N tables.

    Desktop: every column, the chart's measure tinted. Clicking a row (or its name, for the
    keyboard) narrows the filters, exactly as clicking its bar or dot does.

    Phones: three columns -- rank, name, and the sorted measure -- and a tap expands the row to
    show the rest, with the narrowing button and a link to the manager's page. A "Sort by" menu
    reaches the columns that aren't on screen.

    Points always show two decimals and percentages one, through fmt() in statLab.js.
    */
    import { MEASURES, fmt, fmtMeasure, record } from './statLab.js';

    let {
        rows = [], ds, measure, xMeasure = null, sort, dir, setSort,
        people, nameOf, narrow, narrowLabel, narrowScreen = false,
    } = $props();

    const PAGE = 25;
    let showAll = $state(false);
    let expanded = $state(null);

    const KIND = { regular: '', playoff: 'Playoff', placement: '3rd-place game', consolation: 'Consolation' };

    const m = (key) => ({ key, label: MEASURES[key].label, short: MEASURES[key].short, num: true,
        cell: (r) => fmtMeasure(r[key], key) });

    const columns = $derived.by(() => {
        const name = { key: 'name', label: 'Manager', short: 'Manager', cell: (r) => nameOf(r.user_id) };
        if(ds === 'games') return [
            name,
            { key: 'season', label: 'Week', short: 'Week', cell: (r) => `${r.season} W${r.week}` },
            { key: 'opponent', label: 'Opponent', short: 'Opp.', cell: (r) => nameOf(r.opponent_id) },
            { key: 'record', label: 'Result', short: 'Result', cell: (r) => r.result + (KIND[r.gameKind] ? ` · ${KIND[r.gameKind]}` : '') },
            m('pf'), m('pa'), m('margin'), m('allPlayPct'), m('maxPf'), m('bench'), m('eff'),
        ];
        const common = [
            { key: 'record', label: 'Record', short: 'W-L', cell: (r) => record(r.wins, r.losses, r.ties) },
            { key: 'allPlay', label: 'All-play record', short: 'All-play W-L', cell: (r) => record(r.apW, r.apL, r.apT) },
            m('pf'), m('pa'), m('margin'), m('ppg'), m('winPct'), m('allPlayPct'), m('luck'), m('sd'),
            m('maxPf'), m('bench'), m('eff'),
        ];
        if(ds === 'seasons') return [
            name,
            { key: 'season', label: 'Season', short: 'Season', cell: (r) => String(r.season) },
            { key: 'games', label: 'Games', short: 'G', num: true, cell: (r) => String(r.games) },
            ...common, m('finish'),
        ];
        return [
            name,
            { key: 'games', label: 'Games', short: 'G', num: true, cell: (r) => String(r.games) },
            ...common, m('titles'),
        ];
    });

    const sortable = (c) => c.key !== 'games';

    // phones: the third column is the sorted column when it is a measure, else the chart's measure
    const third = $derived(columns.find((c) => c.key === sort && MEASURES[c.key]) ?? columns.find((c) => c.key === measure));
    const rest = $derived(columns.filter((c) => c.key !== 'name' && c.key !== third.key));

    const visible = $derived(showAll ? rows : rows.slice(0, PAGE));

    const ariaSort = (key) => (sort === key ? (dir === 'asc' ? 'ascending' : 'descending') : 'none');
    const arrow = (key) => (sort === key ? (dir === 'asc' ? '▲' : '▼') : '');

    const context = (r) => {
        if(ds === 'games') return `${r.season} W${r.week} · ${r.result} vs ${nameOf(r.opponent_id)}`;
        if(ds === 'seasons') return `${r.season} · ${record(r.wins, r.losses, r.ties)}`;
        return `${r.seasonCount} ${r.seasonCount === 1 ? 'season' : 'seasons'} · ${record(r.wins, r.losses, r.ties)}`;
    };

    const rowClick = (e, r) => {
        if(e.target.closest('button, a')) return;
        if(narrowScreen) expanded = expanded === r.id ? null : r.id;
        else narrow(r);
    };

    const sortOptions = $derived(columns.filter(sortable));
</script>

<style>
    .tableCard {
        background: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        overflow: hidden;
    }

    .scroll { overflow-x: auto; }

    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.875rem;
        font-variant-numeric: tabular-nums;
    }

    th {
        position: sticky;
        top: 0;
        background: var(--navy050);
        padding: 0;
        text-align: left;
        vertical-align: bottom;
        border-bottom: 1px solid var(--accentBorder);
    }

    th.num, td.num { text-align: right; }

    .sortBtn {
        appearance: none;
        display: inline-flex;
        align-items: flex-end;
        gap: 3px;
        width: 100%;
        min-width: 48px;
        min-height: 44px;
        padding: 6px 8px;
        border: none;
        background: transparent;
        font-family: var(--fontDisplay);
        font-size: 0.75rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--g444);
        text-align: inherit;
        justify-content: inherit;
        cursor: pointer;
        line-height: 1.2;
    }

    th.num .sortBtn { justify-content: flex-end; text-align: right; }
    th[aria-sort='ascending'] .sortBtn, th[aria-sort='descending'] .sortBtn { color: var(--navy700); font-weight: 600; }
    .sortBtn:focus-visible, .nameBtn:focus-visible, .more:focus-visible, .act:focus-visible { outline: 2px solid var(--blueOne); outline-offset: -2px; }
    .arrow { font-size: 0.75rem; }

    .plainTh {
        display: block;
        padding: 6px 8px;
        font-family: var(--fontDisplay);
        font-size: 0.75rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--g444);
    }

    td {
        padding: 0 8px;
        height: 44px;
        border-bottom: 1px solid var(--eee);
        white-space: nowrap;
    }

    td.hot, th.hot { background: rgba(42, 120, 214, 0.08); }
    th.hot { background: #e3edf9; }

    tr.row { cursor: pointer; }
    @media (hover: hover) {
        tr.row:hover td { background: var(--navy050); }
    }

    .rank { color: var(--g555); width: 2.5em; text-align: right; }

    .nameBtn {
        appearance: none;
        display: block;
        width: 100%;
        min-width: 48px;
        min-height: 44px;
        padding: 0;
        border: none;
        background: none;
        font: inherit;
        font-weight: 500;
        color: var(--accentInk);
        text-align: left;
        cursor: pointer;
    }

    .srOnly {
        position: absolute;
        width: 1px;
        height: 1px;
        overflow: hidden;
        clip-path: inset(50%);
        white-space: nowrap;
    }

    .foot { display: flex; justify-content: center; padding: 0.6em; }

    .more, .act {
        appearance: none;
        min-height: 44px;
        padding: 0 1.2em;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusPill);
        background: var(--navy050);
        color: var(--navy700);
        font: inherit;
        font-weight: 500;
        cursor: pointer;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }

    /* phones */
    .phoneSort {
        display: flex;
        gap: 8px;
        align-items: center;
        padding: 8px;
        background: var(--navy050);
        border-bottom: 1px solid var(--accentBorder);
    }

    .phoneSort label { font-size: 0.8rem; color: var(--g555); white-space: nowrap; }

    .phoneSort select {
        flex: 1;
        min-width: 0;
        min-height: 44px;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusSm);
        background: var(--fff);
        font: inherit;
        font-size: 0.9rem;
    }

    .dirBtn {
        appearance: none;
        min-width: 44px;
        min-height: 44px;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusSm);
        background: var(--fff);
        color: var(--navy700);
        font: inherit;
        cursor: pointer;
    }

    .phone td { white-space: normal; padding: 6px 8px; }
    .phone td:nth-child(2) { padding: 0 8px; }
    .phone .who { display: flex; flex-direction: column; justify-content: center; width: 100%; min-height: 52px; padding: 4px 0; }
    .ctx { font-size: 0.8rem; color: var(--g555); }
    .phone td.val { font-weight: 600; text-align: right; white-space: nowrap; }

    .detail td { background: var(--navy050); padding: 8px 12px 12px; }

    dl {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 4px 12px;
        margin: 0 0 10px;
        font-size: 0.875rem;
    }

    dt { color: var(--g555); }
    dd { margin: 0; text-align: right; font-variant-numeric: tabular-nums; }

    .acts { display: flex; flex-wrap: wrap; gap: 8px; }
    .acts .act { flex: 1 1 auto; }
    .act.primary { background: var(--accentFill); border-color: var(--accentFill); color: #fff; }
</style>

<div class="tableCard">
    {#if !narrowScreen}
        <div class="scroll">
            <table>
                <caption class="srOnly">Stat Lab rows, sorted by {columns.find((c) => c.key === sort)?.label ?? 'rank'}</caption>
                <thead>
                    <tr>
                        <th class="num"><span class="plainTh">#</span></th>
                        {#each columns as c (c.key)}
                            <th class:num={c.num} class:hot={c.key === measure || c.key === xMeasure} aria-sort={sortable(c) ? ariaSort(c.key) : undefined}>
                                {#if sortable(c)}
                                    <button type="button" class="sortBtn" onclick={() => setSort(c.key)} title="Sort by {c.label}">
                                        {c.short}<span class="arrow" aria-hidden="true">{arrow(c.key)}</span>
                                    </button>
                                {:else}
                                    <span class="plainTh">{c.short}</span>
                                {/if}
                            </th>
                        {/each}
                    </tr>
                </thead>
                <tbody>
                    {#each visible as r (r.id)}
                        <tr class="row" onclick={(e) => rowClick(e, r)}>
                            <td class="rank">{r.rank ?? '–'}</td>
                            {#each columns as c (c.key)}
                                <td class:num={c.num} class:hot={c.key === measure || c.key === xMeasure}>
                                    {#if c.key === 'name'}
                                        <button type="button" class="nameBtn" onclick={() => narrow(r)} title={narrowLabel(r)}>{c.cell(r)}</button>
                                    {:else}
                                        {c.cell(r)}
                                    {/if}
                                </td>
                            {/each}
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {:else}
        <div class="phoneSort">
            <label for="sl-phone-sort">Sort by</label>
            <select id="sl-phone-sort" value={sort} onchange={(e) => setSort(e.currentTarget.value)}>
                {#each sortOptions as c (c.key)}<option value={c.key}>{c.label}</option>{/each}
            </select>
            <button type="button" class="dirBtn" onclick={() => setSort(sort)}
                aria-label={dir === 'asc' ? 'Sorted lowest first; switch to highest first' : 'Sorted highest first; switch to lowest first'}>
                {dir === 'asc' ? '▲' : '▼'}
            </button>
        </div>
        <table class="phone">
            <thead>
                <tr>
                    <th class="num"><span class="plainTh">#</span></th>
                    <th aria-sort={ariaSort('name')}>
                        <button type="button" class="sortBtn" onclick={() => setSort('name')}>Manager<span class="arrow" aria-hidden="true">{arrow('name')}</span></button>
                    </th>
                    <th class="num hot" aria-sort={ariaSort(third.key)}>
                        <button type="button" class="sortBtn" onclick={() => setSort(third.key)}>{third.short}<span class="arrow" aria-hidden="true">{arrow(third.key)}</span></button>
                    </th>
                </tr>
            </thead>
            <tbody>
                {#each visible as r (r.id)}
                    <tr class="row" onclick={(e) => rowClick(e, r)}>
                        <td class="rank">{r.rank ?? '–'}</td>
                        <td>
                            <button type="button" class="nameBtn who" aria-expanded={expanded === r.id}
                                onclick={() => (expanded = expanded === r.id ? null : r.id)}>
                                <span>{nameOf(r.user_id)}</span>
                                <span class="ctx">{context(r)}</span>
                            </button>
                        </td>
                        <td class="val hot">{third.cell(r)}</td>
                    </tr>
                    {#if expanded === r.id}
                        <tr class="detail">
                            <td colspan="3">
                                <dl>
                                    {#each rest as c (c.key)}<dt>{c.label}</dt><dd>{c.cell(r)}</dd>{/each}
                                </dl>
                                <div class="acts">
                                    <button type="button" class="act primary" onclick={() => narrow(r)}>{narrowLabel(r)}</button>
                                    <a class="act" href={people[r.user_id]?.href ?? '/managers'}>Manager page</a>
                                </div>
                            </td>
                        </tr>
                    {/if}
                {/each}
            </tbody>
        </table>
    {/if}

    {#if rows.length > PAGE}
        <div class="foot">
            <button type="button" class="more" onclick={() => (showAll = !showAll)}>
                {showAll ? `Show the first ${PAGE}` : `Show all ${rows.length} rows`}
            </button>
        </div>
    {/if}
</div>
