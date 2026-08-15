<script>
    /*
    The shared surface. Before this existed the "card" was an MDC elevation-3 box-shadow string
    copy-pasted verbatim into seven components, alongside twenty ad-hoc border-radius values.

    Styling is class-based on purpose: this renders through <svelte:element>, and Svelte's CSS
    scoper cannot see a dynamic tag name -- a scoped `div { }` rule here would be silently
    stripped as unused, with no error.
    */
    let {
        elevation = 'raised',   // 'flat' | 'raised' | 'interactive'
        padding = 'md',         // 'none' | 'sm' | 'md' | 'lg'
        radius = 'md',          // 'sm' | 'md' | 'lg'
        accent = false,         // false | 'navy' | 'gold' -- draws a 3px top rule
        href = null,            // renders an <a> and enables the hover lift
        class: className = '',
        children,
        ...rest
    } = $props();
</script>

<style>
    .card {
        display: block;
        position: relative;
        background-color: var(--fff);
        color: inherit;
        text-decoration: none;
        box-sizing: border-box;
    }

    /* elevation */
    .flat { border: 1px solid var(--accentBorder); }
    .raised { box-shadow: var(--shadowCard); }
    .interactive {
        box-shadow: var(--shadowCard);
        transition: box-shadow 0.18s ease, transform 0.18s ease;
    }

    /* Gate the lift behind a real pointer -- on touch it sticks after tap. */
    @media (hover: hover) {
        .interactive:hover {
            box-shadow: var(--shadowCardHover);
            transform: translateY(-2px);
        }
    }

    .interactive:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }

    /* padding */
    .pad-none { padding: 0; }
    .pad-sm { padding: 0.75em; }
    .pad-md { padding: 1.25em; }
    .pad-lg { padding: 2em; }

    /* radius */
    .rad-sm { border-radius: var(--radiusSm); }
    .rad-md { border-radius: var(--radiusMd); }
    .rad-lg { border-radius: var(--radiusLg); }

    /* accent rule -- an overlay so it follows the corner radius without clipping content */
    .accent-navy::before,
    .accent-gold::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        border-radius: inherit;
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
    }

    .accent-navy::before { background-color: var(--accentFill); }
    .accent-gold::before { background-color: var(--goldFill); }
</style>

<svelte:element
    this={href ? 'a' : 'div'}
    href={href || undefined}
    class="card {elevation} pad-{padding} rad-{radius} {accent ? `accent-${accent}` : ''} {className}"
    {...rest}
>
    {@render children?.()}
</svelte:element>
