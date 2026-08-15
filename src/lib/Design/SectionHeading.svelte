<script>
    /*
    A page/section title in the display face.

    TWO TRAPS, both silent:

    1. This renders a real heading through <svelte:element>, so Svelte's CSS scoper cannot see the
       tag name. A scoped `h2 { }` rule would be stripped as unused with no warning. Everything
       below styles the .heading CLASS instead. Do not "simplify" it back to a tag selector.

    2. Because it IS a real h2-h6, it inherits MDC's stock type scale -- headline2 is 3.75rem/60px.
       The .heading rule therefore sets its own font-size unconditionally. This is the same reason
       48 heading overrides already exist across the app.
    */
    let {
        level = 2,              // 2-6; renders the real h{level} so the document outline stays honest
        align = 'center',       // 'left' | 'center'
        eyebrow = null,         // small label above, as on the reference sites
        rule = true,            // the accent underline
        accent = 'navy',        // 'navy' | 'gold'
        class: className = '',
        children,
        actions,
    } = $props();

    const tag = $derived(`h${Math.min(6, Math.max(2, level))}`);
</script>

<style>
    .wrap {
        display: flex;
        align-items: flex-end;
        gap: 1em;
        margin: 2em auto 1em;
        max-width: 1100px;
        width: 94%;
    }

    .wrap.center { flex-direction: column; align-items: center; gap: 0.35em; }
    .wrap.left { justify-content: space-between; }

    .heading {
        font-family: var(--fontDisplay);
        /* MDC would otherwise apply headline2 = 60px here. */
        font-size: 2.1em;
        font-weight: 600;
        line-height: 1.05;
        letter-spacing: 0.01em;
        text-transform: uppercase;
        color: var(--navy700);
        margin: 0;
    }

    .eyebrow {
        font-family: var(--fontDisplay);
        font-size: 0.78em;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: var(--g555);
        line-height: 1;
        margin: 0 0 0.15em;
    }

    .rule {
        display: block;
        height: 3px;
        width: 3.5em;
        border-radius: var(--radiusPill);
        margin-top: 0.45em;
    }

    .rule.navy { background-color: var(--accentFill); }
    .rule.gold { background-color: var(--goldFill); }

    .left .rule { margin-left: 0; }

    .actions { flex-shrink: 0; }

    @media (max-width: 500px) {
        .heading { font-size: 1.6em; }
    }
</style>

<div class="wrap {align} {className}">
    <div>
        {#if eyebrow}
            <p class="eyebrow">{eyebrow}</p>
        {/if}
        <svelte:element this={tag} class="heading">
            {@render children?.()}
        </svelte:element>
        {#if rule}
            <span class="rule {accent}"></span>
        {/if}
    </div>
    {#if actions}
        <div class="actions">{@render actions()}</div>
    {/if}
</div>
