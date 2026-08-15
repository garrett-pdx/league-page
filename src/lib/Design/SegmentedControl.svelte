<script>
    /*
    A small in-card filter toggle -- Active / Moratorium on the managers page being the first use,
    mirroring the "Active Owners / Retired Owners" tabs on the reference sites.

    SCOPE: this is for 2-4 option filters INSIDE a page. @smui/tab-bar is already a dependency and
    is what NavLarge uses; keep it for anything page-level rather than reimplementing it here.

    A11Y: it swaps a filter, not a panel, so it is a radiogroup -- not a tablist. That means roving
    tabindex (exactly one button is tabbable) plus arrow-key movement, which is implemented below.
    The selected state is a navy FILL, not just a colour change, so it does not rely on colour
    alone (WCAG 1.4.1).
    */
    let {
        options = [],           // ['A','B'] or [{value, label, disabled?}]
        value = $bindable(),
        size = 'md',            // 'sm' | 'md'
        fullWidth = false,
        ariaLabel = '',
        onchange = () => {},
        class: className = '',
    } = $props();

    const items = $derived(
        options.map((o) => (typeof o === 'string' ? { value: o, label: o } : o))
    );

    let refs = $state([]);

    const select = (i) => {
        const item = items[i];
        if (!item || item.disabled) return;
        value = item.value;
        onchange(item.value);
    };

    const onkeydown = (e) => {
        const count = items.length;
        if (!count) return;
        const current = items.findIndex((o) => o.value === value);
        let next = null;

        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = (current + 1 + count) % count;
        else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = (current - 1 + count) % count;
        else if (e.key === 'Home') next = 0;
        else if (e.key === 'End') next = count - 1;
        if (next === null) return;

        // step over disabled options rather than landing on one
        let guard = 0;
        while (items[next].disabled && guard < count) {
            next = (next + 1) % count;
            guard++;
        }
        if (items[next].disabled) return;

        e.preventDefault();
        select(next);
        refs[next]?.focus();
    };
</script>

<style>
    .segmented {
        display: inline-flex;
        padding: 3px;
        gap: 3px;
        background-color: var(--navy050);
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusPill);
        box-sizing: border-box;
        max-width: 100%;
    }

    .segmented.fullWidth { display: flex; width: 100%; }

    .segment {
        appearance: none;
        border: none;
        background: transparent;
        cursor: pointer;
        font-family: var(--fontDisplay);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: var(--navy700);
        border-radius: var(--radiusPill);
        white-space: nowrap;
        transition: background-color 0.15s ease, color 0.15s ease;
        flex: 1 1 auto;
    }

    .md .segment { font-size: 0.86em; padding: 0.5em 1.15em; }
    .sm .segment { font-size: 0.74em; padding: 0.35em 0.8em; }

    @media (hover: hover) {
        .segment:hover:not(.selected):not(:disabled) { background-color: var(--navy100); }
    }

    .segment.selected {
        background-color: var(--accentFill);
        color: #fff;
    }

    .segment:disabled {
        opacity: 1;              /* keep the text readable; convey state with colour + cursor */
        color: var(--g999);
        cursor: not-allowed;
    }

    .segment:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }
</style>

<div
    class="segmented {size} {className}"
    class:fullWidth={fullWidth}
    role="radiogroup"
    aria-label={ariaLabel}
    onkeydown={onkeydown}
>
    {#each items as item, i}
        <button
            bind:this={refs[i]}
            type="button"
            class="segment"
            class:selected={item.value === value}
            role="radio"
            aria-checked={item.value === value}
            disabled={item.disabled}
            tabindex={item.value === value ? 0 : -1}
            onclick={() => select(i)}
        >
            {item.label}
        </button>
    {/each}
</div>
