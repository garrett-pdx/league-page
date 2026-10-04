<!-- __layout.svelte -->
<script>
	import { Nav, Footer } from "$lib/components"
    import { leagueName, leagueShortName, leagueDescription } from '$lib/utils/leagueInfo';
    import { dev } from '$app/environment';
    import { injectAnalytics } from '@vercel/analytics/sveltekit';
 
    injectAnalytics({ mode: dev ? 'development' : 'production' });
</script>

<svelte:head>
    <meta name="apple-mobile-web-app-title" content={leagueShortName}>
    <meta name="application-name" content={leagueName}>
    {#if leagueDescription}<meta name="description" content={leagueDescription}>{/if}
</svelte:head>

<main>
    <Nav /> <!-- adds the nav (small and large) -->
  
    <slot />

    <Footer /> <!-- adds the footer -->
</main>