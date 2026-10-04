<script>
    /*
    The constitution is league/constitution.md, parsed by parseConstitution() in
    src/lib/utils/markdown.js: each `##` heading is a numbered section and each `###` a
    numbered rule, so this page builds the table of contents and the collapsible sections from
    the document itself. Nothing here is league-specific.
    */
    import { leagueName, constitution } from '$lib/utils/helper';

    const sections = constitution?.sections || [];
    let container;

    const goToSection = (id) => {
        const target = document.getElementById(id);
        if(!target) return;

        /*
        A collapsed <details> lays out none of its children, so a subsection inside one
        measures at the wrong position (or zero). Open the target and every <details> it lives
        inside before measuring, then wait a frame so the expanded height is real.
        */
        let node = target;
        while(node && node !== document.body) {
            if(node.tagName === 'DETAILS') node.open = true;
            node = node.parentElement;
        }

        requestAnimationFrame(() => {
            // On phones the nav bar is sticky (Nav/index.svelte); land below it, not under it.
            const nav = document.querySelector('main > nav');
            const navOffset = nav && getComputedStyle(nav).position === 'sticky' ? nav.offsetHeight + 8 : 0;
            const top = target.getBoundingClientRect().top + window.pageYOffset - navOffset;
            window.scrollTo({left: 0, top, behavior: 'smooth'});
        });
    }

    /*
    Expand/collapse all is not decoration. Find-in-page does not reliably match text inside a
    closed <details> across browsers, and this is a document people search for one specific rule.
    "Expand all" restores Ctrl+F over the whole constitution.

    Sections are left uncontrolled (no `open={...}` binding) so a reader's own toggling is never
    fought by a reactive value; this sets .open imperatively instead.
    */
    const setAll = (open) => container?.querySelectorAll('details.section').forEach((s) => { s.open = open; });
</script>

<style>
    .constitution {
        position: relative;
        z-index: 1;
        width: 92%;
        max-width: var(--pageMaxText);
        margin: 2em auto 10em;
    }

    h1 {
        font-size: 2em;
        line-height: 1.2em;
        text-align: center;
        margin: 0 0 1.5em;
    }

    h2 {
        font-size: 1.5em;
        line-height: 1.2em;
    }

    .sectionHeading {
        margin: 4em 0 1.5em;
    }

    /* Rule headings and body markup arrive through {@html}, which Svelte's scoper never sees,
       so they are styled as :global inside .sectionBody. */
    .sectionBody :global(.subSectionHeading) {
        text-decoration: underline;
        font-size: 1.3em;
        line-height: 1.2em;
        margin: 1.5em 0 1.5em;
    }

    .sectionBody :global(p) {
        color: var(--g555);
    }

    .noUnderscore {
        text-decoration: none;
    }

    /* The table of contents is a real <nav> of <button>s rather than a stack of
       clickable <h3>/<h4>. Two reasons: headings here duplicated every section
       title in the document outline, and click-only headings were completely
       unreachable by keyboard. Styled to match what they replaced.
       It is kept alongside the accordion because <summary> only indexes the nine
       sections; the TOC is the only way to jump straight to a numbered subsection. */
    .tocList,
    .tocSubList {
        list-style: none;
        margin: 0;
        padding: 0;
    }

    .tocSubList {
        margin-left: 2em;
    }

    .tocLink {
        background: none;
        border: none;
        padding: 0.15em 0;
        font-family: inherit;
        color: inherit;
        cursor: pointer;
        text-align: left;
        display: block;
        line-height: 1.2em;
    }

    .tocSection {
        font-size: 1.3em;
        font-weight: 700;
        margin-top: 0.9em;
    }

    .tocSub {
        font-size: 1.2em;
    }

    .tocLink:hover {
        color: var(--blueOne);
    }

    /* On a phone every contents entry is its own tap target, so each gets 44px. Desktop keeps the
       tight list. */
    @media (max-width: 700px), (pointer: coarse) {
        .tocLink {
            display: flex;
            align-items: center;
            min-height: 44px;
        }

        .allToggle button {
            min-height: 44px;
        }
    }

    .tocLink:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
        border-radius: 2px;
    }

    .preamble :global(p) {
        /* was a hardcoded #777, which lands at ~3.6-4.2:1 on this page's
           gradient in both themes and fails AA for body text. --g555 is the
           theme-aware token the rest of the site uses. */
        color: var(--g555);
    }

    /* ---- accordion ---- */

    .allToggle {
        display: flex;
        justify-content: flex-end;
        gap: 0.5em;
        margin: 2em 0 0.5em;
    }

    .allToggle button {
        background: none;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusPill);
        padding: 0.35em 0.9em;
        font-family: var(--fontDisplay);
        font-size: 0.78em;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--navy700);
        cursor: pointer;
    }

    .allToggle button:hover {
        background-color: var(--navy050);
    }

    .allToggle button:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }

    .section {
        border-bottom: 1px solid var(--ddd);
    }

    .sectionSummary {
        display: flex;
        align-items: center;
        gap: 0.75em;
        cursor: pointer;
        /* remove the native disclosure triangle in both engines */
        list-style: none;
    }

    .sectionSummary::-webkit-details-marker {
        display: none;
    }

    .sectionSummary:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
        border-radius: var(--radiusSm);
    }

    /* the 4em top margin belongs to the standalone heading it used to be */
    .sectionSummary .sectionHeading {
        margin: 0.9em 0;
        flex-grow: 1;
    }

    .chevron {
        width: 0.5em;
        height: 0.5em;
        border-right: 2px solid var(--navy500);
        border-bottom: 2px solid var(--navy500);
        transform: rotate(45deg);
        transition: transform 0.2s ease;
        flex-shrink: 0;
        margin-right: 0.5em;
    }

    .section[open] .chevron {
        transform: rotate(-135deg);
    }

    .sectionBody {
        padding-bottom: 1.5em;
    }

    /* the first subsection heading sits right under the summary, so drop its top margin */
    .sectionBody > :global(.subSectionHeading:first-child) {
        margin-top: 0;
    }
</style>

<div class="constitution" bind:this={container}>
    <h1 class="noUnderscore">{leagueName.toUpperCase()} CONSTITUTION</h1>

    {#if constitution?.preamble}
        <div class="preamble">{@html constitution.preamble}</div>
    {/if}

    <nav class="toc" aria-label="Table of contents">
        <h2 class="noUnderscore">TABLE OF CONTENTS</h2>
        <ul class="tocList">
            {#each sections as section (section.id)}
                <li>
                    <button type="button" class="tocLink tocSection" onclick={() => goToSection(section.id)}>Section {section.n}: {@html section.title}</button>
                    {#if section.rules.length}
                        <ul class="tocSubList">
                            {#each section.rules as rule (rule.id)}
                                <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(rule.id)}>{rule.n} {@html rule.title}</button></li>
                            {/each}
                        </ul>
                    {/if}
                </li>
            {/each}
        </ul>
    </nav>

    <hr />

    <div class="allToggle">
        <button type="button" onclick={() => setAll(true)}>Expand all</button>
        <button type="button" onclick={() => setAll(false)}>Collapse all</button>
    </div>

    {#each sections as section (section.id)}
        <details class="section" id={section.id}>
            <summary class="sectionSummary">
                <span class="chevron" aria-hidden="true"></span>
                <h2 class="sectionHeading">Section {section.n} {@html section.title}</h2>
            </summary>
            <div class="sectionBody">{@html section.html}</div>
        </details>
    {/each}
</div>
