<script>
    /*
    A dropdown grid of NFL team logos; click a logo to toggle that team, or use All / None.
    `selected` is an array of team abbreviations, bound by the parent.

    Logos come from Sleeper's CDN, the same source Rosters and Drafts already use. The grid is
    only rendered while open, so the 32 images aren't fetched until someone asks for them.

    The panel opens IN FLOW, as its own row of the parent's flex-wrap controls (the wrapper is
    display: contents, and the panel takes flex-basis 100%), pushing the table down. An absolutely
    positioned popover can't work here: the page's .main and the Footer are both z-index: 1 and
    the footer comes later, so on a short result list the footer painted over the grid and ate
    the clicks. Raising .main above 1 would cover the nav's submenu (z-index 2) instead.

    A11Y: each logo is a toggle button (aria-pressed), and "off" is shown by greyscale AND a
    struck-through label, not by opacity alone. Escape or a click outside closes the panel.
    */
    let { teams = [], selected = $bindable([]) } = $props();

    let open = $state(false);
    let root;
    let trigger;

    const allOn = $derived(selected.length == teams.length);
    const label = $derived(
        allOn ? 'All teams'
        : selected.length == 0 ? 'No teams'
        : selected.length <= 3 ? [...selected].sort().join(', ')
        : `${selected.length} of ${teams.length} teams`
    );

    const toggle = (team) => {
        selected = selected.includes(team) ? selected.filter((t) => t != team) : [...selected, team];
    };

    const onWindowClick = (e) => {
        if(open && root && !root.contains(e.target)) open = false;
    };

    const onKeydown = (e) => {
        if(open && e.key == 'Escape') {
            open = false;
            trigger?.focus();
        }
    };
</script>

<svelte:window onclick={onWindowClick} onkeydown={onKeydown} />

<style>
    .picker {
        display: contents;
    }

    .trigger {
        font: inherit;
        display: inline-flex;
        align-items: center;
        gap: 0.4em;
        padding: 0.45em 0.6em 0.45em 0.9em;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusPill);
        background: var(--fff);
        color: var(--navy700);
        cursor: pointer;
        white-space: nowrap;
    }

    .trigger:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }

    .trigger.filtered {
        border-color: var(--accentFill);
        font-weight: 500;
    }

    .caret {
        font-size: 0.75em;
        transition: transform 0.15s ease;
    }

    .caret.up { transform: rotate(180deg); }

    .panel {
        order: 99;
        flex-basis: 100%;
    }

    .panelInner {
        max-width: 31em;
        margin: 0 auto;
        box-sizing: border-box;
        padding: 0.9em;
        background: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCardHover), var(--shadowCard);
    }

    .bulk {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.7em;
        color: var(--g555);
        font-size: 0.85em;
    }

    .bulk button {
        font: inherit;
        font-family: var(--fontDisplay);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--accentInk);
        background: none;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusPill);
        padding: 0.25em 0.9em;
        margin-left: 0.4em;
        cursor: pointer;
    }

    .bulk button:disabled {
        color: var(--g555);
        opacity: 0.5;
        cursor: default;
    }

    .grid {
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        gap: 0.35em;
    }

    .team {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.15em;
        padding: 0.35em 0.1em 0.25em;
        border: 2px solid transparent;
        border-radius: var(--radiusSm);
        background: var(--navy050);
        cursor: pointer;
        font: inherit;
    }

    .team:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 1px;
    }

    .team[aria-pressed='true'] {
        border-color: var(--accentFill);
        background: var(--fff);
    }

    .team img {
        width: 2.2em;
        height: 2.2em;
        object-fit: contain;
        transition: filter 0.15s ease, opacity 0.15s ease;
    }

    .team[aria-pressed='false'] img {
        filter: grayscale(1);
        opacity: 0.35;
    }

    .abbr {
        font-size: 0.68em;
        font-weight: 600;
        color: var(--navy700);
    }

    .team[aria-pressed='false'] .abbr {
        color: var(--g555);
        text-decoration: line-through;
    }

    @media (hover: hover) {
        .team:hover { border-color: var(--navy400); }
    }

    @media (max-width: 640px) {
        .grid { grid-template-columns: repeat(6, 1fr); }
    }
</style>

<div class="picker" bind:this={root}>
    <button
        class="trigger"
        class:filtered={!allOn}
        type="button"
        aria-expanded={open}
        aria-haspopup="true"
        bind:this={trigger}
        onclick={() => open = !open}
    >
        {label}
        <span class="caret" class:up={open} aria-hidden="true">▼</span>
    </button>

    {#if open}
        <div class="panel" role="group" aria-label="Filter by NFL team"><div class="panelInner">
            <div class="bulk">
                <span>{selected.length} of {teams.length} selected</span>
                <span>
                    <button type="button" disabled={allOn} onclick={() => selected = [...teams]}>All</button>
                    <button type="button" disabled={selected.length == 0} onclick={() => selected = []}>None</button>
                </span>
            </div>
            <div class="grid">
                {#each teams as team (team)}
                    <button
                        class="team"
                        type="button"
                        aria-pressed={selected.includes(team)}
                        title={team}
                        onclick={() => toggle(team)}
                    >
                        <img src="https://sleepercdn.com/images/team_logos/nfl/{team.toLowerCase()}.png" alt="" />
                        <span class="abbr">{team}</span>
                    </button>
                {/each}
            </div>
        </div></div>
    {/if}
</div>
