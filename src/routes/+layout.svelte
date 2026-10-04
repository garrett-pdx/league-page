<!-- __layout.svelte -->
<script>
	import { Nav, Footer } from "$lib/components"
    import { league, leagueName, leagueShortName, leagueDescription } from '$lib/utils/leagueInfo';
    const brandColor = league.theme?.tokens?.brand700 || league.theme?.primary || '#00316b';
    import { dev } from '$app/environment';
    import { injectAnalytics } from '@vercel/analytics/sveltekit';
 
    injectAnalytics({ mode: dev ? 'development' : 'production' });
</script>

<svelte:head>
    <meta name="apple-mobile-web-app-title" content={leagueShortName}>
    <meta name="application-name" content={leagueName}>
    <link rel="mask-icon" href="/favicons/safari-pinned-tab.svg" color={brandColor}>
    {#if leagueDescription}<meta name="description" content={leagueDescription}>{/if}
</svelte:head>

<main>
    <Nav /> <!-- adds the nav (small and large) -->
  
    <slot />

    <Footer /> <!-- adds the footer -->
</main>