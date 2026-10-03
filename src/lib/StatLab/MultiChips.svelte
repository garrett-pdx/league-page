<script>
    /*
    A multi-select as a row of toggle chips (seasons, managers). Each chip is a real button with
    aria-pressed; "All" clears the selection, which means no filter. Selecting every chip is the
    same as none, so it collapses back to "All" rather than writing a long list into the URL.
    44px tall everywhere, since the page's targets are checked at desktop sizes too.
    */
    let { label, options = [], selected = [], onchange = () => {} } = $props();

    const toggle = (value) => {
        const next = selected.includes(value) ? selected.filter((v) => v !== value) : [...selected, value];
        // keep the options' order, so the URL doesn't depend on click order
        const ordered = options.map((o) => o.value).filter((v) => next.includes(v));
        onchange(ordered.length === options.length ? [] : ordered);
    };
</script>

<style>
    fieldset { border: none; margin: 0; padding: 0; min-width: 0; }

    legend {
        padding: 0;
        margin-bottom: 6px;
        font-family: var(--fontDisplay);
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--g555);
    }

    .row { display: flex; flex-wrap: wrap; gap: 6px; }

    button {
        appearance: none;
        min-height: 44px;
        min-width: 44px;
        padding: 0 0.85em;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusPill);
        background: var(--fff);
        color: var(--navy700);
        font: inherit;
        font-size: 0.9rem;
        cursor: pointer;
    }

    button[aria-pressed='true'] {
        background: var(--accentFill);
        border-color: var(--accentFill);
        color: #fff;
    }

    @media (hover: hover) {
        button:hover:not([aria-pressed='true']) { background: var(--navy050); }
    }

    button:focus-visible { outline: 2px solid var(--blueOne); outline-offset: 2px; }
</style>

<fieldset>
    <legend>{label}</legend>
    <div class="row">
        <button type="button" aria-pressed={!selected.length} onclick={() => onchange([])}>All</button>
        {#each options as o}
            <button type="button" aria-pressed={selected.includes(o.value)} onclick={() => toggle(o.value)}>{o.label}</button>
        {/each}
    </div>
</fieldset>
