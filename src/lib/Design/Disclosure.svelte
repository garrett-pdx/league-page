<script>
    /*
    A collapsed-by-default control that reveals a block of content: "Projected 2027 draft order" on
    Drafts, "Show earlier seasons" on the Trophy Room.

    It is a real <button aria-expanded>, not <details>, for one reason: the content is only
    rendered once it is opened. Both uses wrap a heavy, data-fed component (a 130-cell draft board,
    a dozen award podiums), and mounting those hidden costs layout and images for content nobody
    asked to see.

        <Disclosure label="Show earlier seasons" openLabel="Hide earlier seasons">
            ...
        </Disclosure>

    The button is at least 44px tall (WCAG 2.5.5), and its text is the display face at 14px or more.
    */
    let {
        label,                  // text while closed
        openLabel = null,       // text while open; defaults to the same label
        open = $bindable(false),
        align = 'center',       // 'left' | 'center'
        class: className = '',
        children,
    } = $props();
</script>

<style>
    .disclosure {
        width: 94%;
        max-width: 1100px;
        margin: 1.5em auto;
    }

    .bar {
        display: flex;
    }

    .center .bar { justify-content: center; }

    .toggle {
        appearance: none;
        display: inline-flex;
        align-items: center;
        gap: 0.5em;
        min-height: 44px;
        padding: 0 1.3em;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusPill);
        background-color: var(--navy050);
        color: var(--navy700);
        font-family: var(--fontDisplay);
        font-size: 0.95em;
        font-weight: 500;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        cursor: pointer;
        transition: background-color 0.15s ease;
    }

    @media (hover: hover) {
        .toggle:hover { background-color: var(--navy100); }
    }

    .toggle:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }

    .chevron {
        display: inline-block;
        width: 0.5em;
        height: 0.5em;
        border-right: 2px solid currentColor;
        border-bottom: 2px solid currentColor;
        transform: translateY(-0.12em) rotate(45deg);
        transition: transform 0.15s ease;
    }

    .open .chevron { transform: translateY(0.12em) rotate(-135deg); }

    .content { margin-top: 1em; }
</style>

<div class="disclosure {align} {className}" class:open>
    <div class="bar">
        <button type="button" class="toggle" aria-expanded={open} onclick={() => (open = !open)}>
            {open ? (openLabel ?? label) : label}
            <span class="chevron" aria-hidden="true"></span>
        </button>
    </div>
    {#if open}
        <div class="content">
            {@render children?.()}
        </div>
    {/if}
</div>
