<script>
    /*
    The title block at the top of a page: the page name in the display face, then an optional
    one-line intro.

    Mount it in the ROUTE file (src/routes/<page>/+page.svelte), above whatever the page loads,
    so it renders straight away instead of waiting on the data -- and so the upstream components
    underneath only ever lose their old heading, never gain one.

        <PageHeader title="Standings" intro="Ten teams, one table." />

    The intro can also be passed as children when it needs a link or markup. Sections below the
    header use <SectionHeading level={3}>, which renders smaller than this.

    The eyebrow defaults to the league name, as it did on Free Agents and Managers before this
    existed. Pass eyebrow={null} on a page that should not carry it.
    */
    import { leagueName } from '$lib/utils/leagueInfo';
    import SectionHeading from './SectionHeading.svelte';

    let {
        title,
        intro = null,
        eyebrow = leagueName,
        accent = 'navy',        // 'navy' | 'gold'
        children,
    } = $props();
</script>

<style>
    .intro {
        text-align: center;
        color: var(--g555);
        line-height: 1.45em;
        max-width: 36em;
        width: 90%;
        margin: 0 auto 1.6em;
    }
</style>

<SectionHeading {eyebrow} {accent} level={2}>{title}</SectionHeading>

{#if children}
    <p class="intro">{@render children()}</p>
{:else if intro}
    <p class="intro">{intro}</p>
{/if}
