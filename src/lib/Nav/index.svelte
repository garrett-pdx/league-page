<script>
	import NavSmall from './NavSmall.svelte';
	import NavLarge from './NavLarge.svelte';
    import { page } from '$app/state';
	import { leagueName } from '$lib/utils/leagueInfo';
</script>

<svelte:head>
	<title>{!page.url.pathname[1] ? 'Home' : page.url.pathname[1].toUpperCase() + page.url.pathname.slice(2)} | {leagueName}</title>
</svelte:head>

<style>
	a {
		display: table;
    	margin: 0 auto;
	}
	nav {
		background-color: var(--fff);
		position: relative;
		z-index: 2;
		border-bottom: 1px solid var(--blueOne);
		box-shadow: var(--shadowNav);
	}

	#logo {
		width: 80px;
		display: block;
		margin: 0 auto;
		padding: 10px;
	}

    .large {
		display: block;
    }

	.small {
		display: none;
	}

	@media (max-width: 950px) { /* width of the large navBar */
		.large {
			display: none;
		}

		.small {
			display: block;
		}

		/* Phones only: a compact bar that stays put on 5,000-7,000px pages, so the menu is
		   always one tap away. Desktop keeps its non-sticky header on purpose: NavLarge
		   positions its dropdown from getBoundingClientRect, untested under a sticky bar. */
		nav {
			position: sticky;
			top: 0;
		}

		#logo {
			width: 48px;
			padding: 6px;
		}
	}
</style>

<nav>
	<a href="/"><img id="logo" alt="{leagueName}" src="/brand/seal-simple.svg" /></a>

	<div class="large">
		<NavLarge />
	</div>

	<div class="small">
		<NavSmall />
	</div>

</nav>
