<script>
	import { Icon } from '@smui/tab';
    export let total, perPage, page, target, scroll = true;

    let pageLabels = [];

    $: totPages = Math.ceil(total / perPage);

    const computePages = (curPage, pages, iW) => {
        let tempPageLabels = []
        let before = false;
        let after = false;
        const limit = iW && iW > 380 ? 3 : 1;
        for(let i = 0; i < pages; i++) {
            if(i == 0 || (i == (pages - 1) && (!iW || iW > 300)) || ((curPage - limit) < i && i < (curPage +  limit))) {
                tempPageLabels.push(i + 1);
            } else if(!before && (curPage - limit) < i && (!iW || iW > 300)) {
                before = true;
                tempPageLabels.push("...");
            } else if(!after && i < (curPage +  limit)) {
                after = true;
                tempPageLabels.push("...");
            }
        }
        pageLabels = tempPageLabels;
    }

    const changePage = (dest) => {
        if(scroll) {
            // below 951px a 61px bar is stuck to the top; land under it, not behind it
            const bar = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--stickyBar')) || 0;
            window.scrollTo({left: 0, top: target - bar, behavior: 'smooth'});
        }
        page = dest;
    }

    let innerWidth;
    $: computePages(page, totPages, innerWidth);
</script>

<svelte:window bind:innerWidth={innerWidth} />

<style>
    :global(.button) {
        color: #aaa;
        cursor: pointer;
        vertical-align: sub;
    }

    /* The arrows are the only way to turn the page: 44px, not the icon's 24px. Scoped to the bar
       because `.button` above is global and Posts uses the same class name for a link. */
    .paginationBar :global(.button) {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 44px;
        height: 44px;
    }

    :global(.button:hover) {
        color: var(--accentInk);
    }

    .paginationBar {
        display: flex;
        justify-content: space-between;
        width: 100%;
        max-width: 550px;
        margin: 10px auto;
        text-align: center;
    }

    .pg {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        box-sizing: border-box;
        min-width: 44px;
        min-height: 44px;
        font-size: 1.2em;
        padding: 0 .4em;
        color: #aaa;
    }
    
    .spacer {
        min-width: 0;
        padding: 0;
        cursor: default;
        user-select: none;
    }

    .dest {
        cursor: pointer;
    }

    .dest:hover {
        color: var(--accentInk);
    }

    .selected {
        color: var(--blueOne);
        cursor: default;
        user-select: none;
    }

    .placeholder {
        width: 44px;
    }

    .totals {
        font-style: italic;
        cursor: default;
        user-select: none;
        color: var(--g999);
        font-size: max(12px, 0.8em);
        text-align: center;
    }
</style>
{#if total > 0 && totPages > 1 }
    <div class="paginationBar">
        {#if page > 0}
            <Icon class="material-icons button" onclick={() => changePage(page - 1)}>chevron_left</Icon>
        {:else}
            <span class="placeholder" />
        {/if}
        <div class="numbers">
            {#each pageLabels as pageLabel}
                {#if pageLabel == page + 1}
                    <span class="selected pg">{pageLabel}</span>
                {:else if pageLabel == "..."}
                    <span class="pg spacer">{pageLabel}</span>
                {:else}
                    <span class="dest pg" onclick={() => changePage(pageLabel - 1)}>{pageLabel}</span>
                {/if}
            {/each}
        </div>
        {#if page < totPages - 1}
            <Icon class="material-icons button" onclick={() => changePage(page + 1)}>chevron_right</Icon>
        {:else}
            <span class="placeholder" />
        {/if}
    </div>
    <div class="totals">{page * perPage + 1} - {page + 1 == totPages ? total : (page + 1) * perPage} of {total}</div>
{/if}
