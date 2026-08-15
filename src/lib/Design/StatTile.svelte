<script>
    /*
    One big number with a label -- the "CAREER STATS" band that both reference league sites lead
    their manager profiles with.

    This is where real Roboto Mono lives. It is deliberately NOT applied to data-table cells:
    its glyphs are wider than Roboto's and would overflow the hardcoded name-cell widths in
    Rosters/Roster.svelte and Records/RecordsAndRankings.svelte. Tables get Roboto's own
    tabular figures instead (see the .mdc-data-table__cell rule in src/theme/_tokens.scss).
    */
    let {
        label,
        value = null,
        sub = null,             // optional line under the value, e.g. a year range
        tone = 'default',       // 'default' | 'positive' | 'negative' | 'champion'
        size = 'md',            // 'sm' | 'md' | 'lg'
        mono = true,
        class: className = '',
        children,               // overrides `value` for rich content (avatar + name, etc.)
        icon,
    } = $props();
</script>

<style>
    .tile {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        gap: 0.15em;
        padding: 0.9em 0.6em;
        background-color: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        box-sizing: border-box;
        min-width: 0;
    }

    .label {
        font-family: var(--fontDisplay);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 500;
        color: var(--g555);
        line-height: 1.1;
        order: -1;
    }

    .value {
        font-weight: 700;
        line-height: 1;
        color: var(--navy700);
        /* tabular figures so a column of tiles keeps its digits aligned */
        font-variant-numeric: tabular-nums;
    }

    .value.mono { font-family: var(--fontMono); }
    .value.display { font-family: var(--fontDisplay); }

    .sub {
        font-size: 0.72em;
        color: var(--g555);
        line-height: 1.2;
    }

    .icon {
        display: block;
        margin-bottom: 0.15em;
        order: -2;
    }

    /* sizes */
    .sm .label { font-size: 0.66em; }
    .sm .value { font-size: 1.35em; }
    .md .label { font-size: 0.75em; }
    .md .value { font-size: 2em; }
    .lg .label { font-size: 0.85em; }
    .lg .value { font-size: 2.9em; }

    /* tones */
    .positive .value { color: #1b6b47; }   /* 5.42:1 on #fff */
    .negative .value { color: #a32020; }   /* 6.24:1 on #fff */

    .champion {
        background-color: var(--goldFill);
        box-shadow: var(--shadowCard);
    }
    /* Gold is only ever a fill, never ink -- see the palette note in src/theme/_tokens.scss. */
    .champion .value { color: var(--goldOnFill); }
    .champion .label { color: var(--goldOnFill); }
    .champion .sub { color: var(--goldOnFill); }

    @media (max-width: 500px) {
        .tile { padding: 0.7em 0.4em; }
        .md .value { font-size: 1.6em; }
        .lg .value { font-size: 2.1em; }
    }
</style>

<div class="tile {size} {tone} {className}">
    {#if icon}
        <span class="icon">{@render icon()}</span>
    {/if}
    <span class="label">{label}</span>
    <span class="value" class:mono={mono} class:display={!mono}>
        {#if children}{@render children()}{:else}{value}{/if}
    </span>
    {#if sub}
        <span class="sub">{sub}</span>
    {/if}
</div>
