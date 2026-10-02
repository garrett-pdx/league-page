<script>
    import { leagueName, loadPlayers } from '$lib/utils/helper';
    import { onMount } from 'svelte';
    import { players as playersStore } from '$lib/stores';
    import { Card, SectionHeading, SegmentedControl } from '$lib/Design';
    import TeamPicker from './TeamPicker.svelte';

    /*
    Free agents filtered by NFL depth-chart slot ("show me every RB2"). League-specific; the data
    and its traps are documented in routes/api/fetch_free_agents/+server.js.

    Projections are joined client-side from the shared players cache (fetch_players_info, already
    scored with this league's settings) rather than recomputed on the server. That cache lives
    24h in localStorage; when it comes back stale we reload it in the background, as Rosters does.

    Refresh asks the endpoint for ?fresh=<current minute> to step past the CDN's 15-minute cache;
    the server's comment explains why only the current minute is accepted. Filters are plain
    state and survive it.

    Refresh also reloads projections, by calling fetch_players_info directly: loadPlayers() can't be
    forced (it returns the in-memory store first) and players.js is upstream's. The result is
    written back to the same localStorage keys and store loadPlayers uses, so every other page gets
    the fresh copy too. That endpoint is uncached and rebuilds ~2MB from Sleeper on every call, so
    it is skipped while the saved copy is under PROJ_MIN_AGE old -- Sleeper only revises
    projections a few times a day.
    */
    const PROJ_MIN_AGE = 15 * 60;       // seconds
    const PLAYERS_TTL = 24 * 3600;      // must match loadPlayers' expiration in players.js
    let { faData: initialData, playersInfo = {}, nflState = {} } = $props();

    let faData = $state(initialData);
    let players = $state(playersInfo.players ?? {});
    let refreshing = $state(false);
    let refreshError = $state('');
    let now = $state(Date.now());

    onMount(() => {
        if(playersInfo.stale) {
            loadPlayers(null, true).then((res) => { players = res.players; }).catch(() => {});
        }
        const tick = setInterval(() => { now = Date.now(); }, 30000);
        return () => clearInterval(tick);
    });

    const refreshFreeAgents = async () => {
        const res = await fetch(`/api/fetch_free_agents?fresh=${Math.floor(Date.now() / 60000)}`);
        if(!res.ok) throw new Error(res.status);
        faData = await res.json();
    };

    const refreshProjections = async () => {
        const nowSec = Math.round(Date.now() / 1000);
        let expiration = null;
        try { expiration = parseInt(localStorage.getItem('expiration')); } catch {}
        if(expiration && PLAYERS_TTL - (expiration - nowSec) < PROJ_MIN_AGE) return;

        const res = await fetch('/api/fetch_players_info');
        if(!res.ok) throw new Error(res.status);
        const data = await res.json();
        try {
            localStorage.setItem('playersInfo', JSON.stringify(data));
            localStorage.setItem('expiration', nowSec + PLAYERS_TTL);
        } catch {}
        playersStore.set(data);
        players = data;
    };

    const refresh = async () => {
        refreshing = true;
        refreshError = '';
        const [list, proj] = await Promise.allSettled([refreshFreeAgents(), refreshProjections()]);
        if(list.status == 'rejected' && proj.status == 'rejected') refreshError = "Couldn't refresh; try again.";
        else if(list.status == 'rejected') refreshError = "Couldn't refresh the list; try again.";
        else if(proj.status == 'rejected') refreshError = "Couldn't refresh projections; try again.";
        now = Date.now();
        refreshing = false;
    };

    const age = $derived.by(() => {
        const mins = Math.floor((now - new Date(faData.updated).getTime()) / 60000);
        if(mins < 1) return 'just now';
        if(mins < 60) return `${mins} min ago`;
        const hrs = Math.floor(mins / 60);
        return hrs < 24 ? `${hrs} hr ago` : new Date(faData.updated).toLocaleDateString('en-US', {month: 'short', day: 'numeric'});
    });

    const week = nflState.display_week ?? nflState.week ?? 0;
    const positions = ['QB', 'RB', 'WR', 'TE'];

    let pos = $state('RB');
    let depth = $state('2');
    let query = $state('');

    // the team list is fixed at first load so a refresh can't reset the picker
    const teams = [...new Set(initialData.players.map((p) => p.t))].sort();
    let selectedTeams = $state([...teams]);

    const withProj = $derived(faData.players.map((p) => {
        const info = players[p.id]?.wi;
        const wk = info && week ? info[week] : null;
        return {
            ...p,
            proj: wk ? parseFloat(wk.p) : null, // round() in fetch_players_info returns a string
            opp: wk ? wk.o : null,
            bye: Boolean(info && week && !wk),
        };
    }));

    const depthOptions = $derived(
        ['1', '2', '3', 'Any'].map((d) => {
            const count = withProj.filter((p) => p.pos == pos && selectedTeams.includes(p.t) && (d == 'Any' || p.depth == d)).length;
            return {value: d, label: d == 'Any' ? `Any (${count})` : `${pos}${d} (${count})`};
        })
    );

    const shown = $derived(
        withProj
            .filter((p) => p.pos == pos)
            .filter((p) => depth == 'Any' || p.depth == depth)
            .filter((p) => selectedTeams.includes(p.t))
            .filter((p) => !query || p.n.toLowerCase().includes(query.toLowerCase()))
            .sort((a, b) => (b.proj ?? -1) - (a.proj ?? -1) || (a.rank ?? 1e9) - (b.rank ?? 1e9))
    );

    const fmtDate = (iso) => new Date(`${iso}T00:00:00Z`).toLocaleDateString('en-US', {month: 'short', day: 'numeric', timeZone: 'UTC'});
    const fmtCount = (n) => new Intl.NumberFormat('en-US', {notation: 'compact', maximumFractionDigits: 1}).format(n);
    const injuryClass = (is) => ['IR', 'PUP', 'Out', 'Sus', 'DNR', 'NA'].includes(is) ? 'out' : 'q';
</script>

<style>
    .wrap {
        width: 94%;
        max-width: var(--pageMax);
        margin: 0 auto 5em;
    }

    .blurb {
        text-align: center;
        color: var(--g555);
        margin: 0 auto 1.6em;
        max-width: 36em;
        line-height: 1.4em;
    }

    .controls {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        align-items: center;
        gap: 0.8em;
        margin: 0 auto 1.4em;
    }

    .search {
        font: inherit;
        padding: 0.45em 0.8em;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusPill);
        min-width: 12em;
        background: var(--fff);
        color: inherit;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        font-variant-numeric: tabular-nums;
    }

    th {
        font-family: var(--fontDisplay);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-size: 0.8em;
        color: var(--g555);
        text-align: left;
        padding: 0.6em 0.7em;
        border-bottom: 2px solid var(--accentBorder);
    }

    td {
        padding: 0.6em 0.7em;
        border-bottom: 1px solid var(--accentBorder);
        vertical-align: middle;
    }

    tr:last-child td { border-bottom: none; }

    .num { text-align: right; }

    .name {
        font-weight: 500;
        color: var(--navy700);
    }

    .team {
        color: var(--g555);
        font-size: 0.85em;
        margin-left: 0.3em;
    }

    .depth {
        display: inline-block;
        font-family: var(--fontDisplay);
        font-weight: 600;
        color: #fff;
        background: var(--accentFill);
        border-radius: var(--radiusXs);
        padding: 0.1em 0.45em;
        min-width: 2.6em;
        text-align: center;
    }

    .depth.none {
        background: none;
        color: var(--g555);
        font-weight: 400;
    }

    .slot {
        color: var(--g555);
        font-size: 0.8em;
        margin-left: 0.35em;
    }

    .inj {
        display: inline-block;
        font-size: 0.75em;
        font-weight: 600;
        border-radius: var(--radiusXs);
        padding: 0.1em 0.4em;
        margin-left: 0.4em;
        white-space: nowrap;
    }

    .inj.out { background: var(--cardinal); color: #fff; }
    .inj.q { background: var(--goldFill); color: var(--goldOnFill); }

    .opp {
        display: block;
        color: var(--g555);
        font-size: 0.8em;
    }

    .trend { color: var(--accentInk); white-space: nowrap; }

    .muted { color: var(--g555); }

    .empty {
        text-align: center;
        color: var(--g555);
        padding: 2em 1em;
    }

    .status {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 0.7em;
        margin: 0 0 0.5em;
        font-size: 0.85em;
        color: var(--g555);
    }

    .status .error { color: var(--cardinal); }

    .refresh {
        font: inherit;
        font-family: var(--fontDisplay);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        display: inline-flex;
        align-items: center;
        gap: 0.3em;
        color: var(--accentInk);
        background: var(--fff);
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusPill);
        padding: 0.25em 0.9em;
        cursor: pointer;
    }

    .refresh:disabled { cursor: default; opacity: 0.6; }

    .refresh:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }

    .spin { display: inline-block; }
    .refresh:disabled .spin { animation: spin 0.9s linear infinite; }

    @keyframes spin { to { transform: rotate(360deg); } }

    @media (prefers-reduced-motion: reduce) {
        .refresh:disabled .spin { animation: none; }
    }

    .foot {
        text-align: center;
        color: var(--g555);
        font-size: 0.85em;
        margin: 1.2em auto 0;
        max-width: 44em;
        line-height: 1.4em;
    }

    @media (max-width: 640px) {
        .hideSmall { display: none; }
        td, th { padding: 0.55em 0.4em; }
        .team { display: block; margin-left: 0; }
    }
</style>

<div class="wrap">
    <SectionHeading eyebrow={leagueName} level={2}>Free Agents</SectionHeading>

    <p class="blurb">
        Every unrostered player, by where he sits on his NFL team's depth chart. Looking for a
        handcuff? Start with the RB2s.
    </p>

    <div class="controls">
        <SegmentedControl options={positions} bind:value={pos} ariaLabel="Position" />
        <SegmentedControl options={depthOptions} bind:value={depth} size="sm" ariaLabel="Depth chart slot" />
        <TeamPicker {teams} bind:selected={selectedTeams} />
        <input class="search" type="search" placeholder="Player name" aria-label="Filter by player name" bind:value={query} />
    </div>

    <div class="status" aria-live="polite">
        {#if refreshError}<span class="error">{refreshError}</span>{/if}
        <span>Updated {age}</span>
        <button class="refresh" type="button" onclick={refresh} disabled={refreshing}>
            <span class="spin" aria-hidden="true">↻</span>{refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
    </div>

    <Card padding="none">
        <table>
            <thead>
                <tr>
                    <th>Player</th>
                    <th>Depth</th>
                    {#if week}<th class="num">Wk {week} proj</th>{/if}
                    <th class="num" title="Share of the team's offensive snaps this season">Snap %</th>
                    <th class="num hideSmall" title="Sleeper-wide adds in the last 48 hours">Trending</th>
                    <th class="num hideSmall" title="Sleeper's overall player rank">Rank</th>
                </tr>
            </thead>
            <tbody>
                {#each shown as p (p.id)}
                    <tr>
                        <td>
                            <span class="name">{p.n}</span><span class="team">{p.t}</span>
                            {#if p.is}
                                <span class="inj {injuryClass(p.is)}">{p.is}{#if p.ret} · back ~{fmtDate(p.ret)}{/if}</span>
                            {/if}
                        </td>
                        <td>
                            {#if p.depth}
                                <span class="depth">{p.pos}{p.depth}</span>{#if p.slot}<span class="slot">{p.slot}</span>{/if}
                            {:else}
                                <span class="depth none">—</span>
                            {/if}
                        </td>
                        {#if week}
                            <td class="num">
                                {#if p.bye}
                                    <span class="muted">BYE</span>
                                {:else if p.proj != null}
                                    {p.proj.toFixed(1)}
                                    {#if p.opp}<span class="opp">vs {p.opp}</span>{/if}
                                {:else}
                                    <span class="muted">—</span>
                                {/if}
                            </td>
                        {/if}
                        <td class="num">{#if p.snap != null}{p.snap}%{:else}<span class="muted">—</span>{/if}</td>
                        <td class="num hideSmall">{#if p.trend}<span class="trend">▲ {fmtCount(p.trend)}</span>{/if}</td>
                        <td class="num hideSmall">{#if p.rank}{p.rank}{:else}<span class="muted">—</span>{/if}</td>
                    </tr>
                {:else}
                    <tr><td class="empty" colspan="6">{selectedTeams.length ? 'No free agents match.' : 'No teams selected.'}</td></tr>
                {/each}
            </tbody>
        </table>
    </Card>

    <p class="foot">
        Depth charts from Sleeper; injury return dates from ESPN. Players out for the season are
        hidden, and the player behind them moves up. A recently dropped player may still be on
        waivers rather than free.
    </p>
</div>
