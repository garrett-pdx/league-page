<script>
    import { managers, enableBlog } from '$lib/utils/helper';
	import { tabs } from '$lib/utils/tabs';
	import { onMount } from 'svelte';

	/*
	Links are real anchors now, not divs with click handlers.

	That fixes two things at once. The whole footer nav was previously unreachable by keyboard
	-- a <div onclick> has no focus and no role -- and it needed a navigate() helper to
	special-case off-site destinations, because SvelteKit 2's goto() throws on external URLs.
	An <a href> needs neither: the client router intercepts internal hrefs on its own and leaves
	external ones to the browser. The equivalent helpers in NavLarge/NavSmall still earn their
	keep, since those are driven by SMUI components rather than anchors.
	*/

	let outOfDate = false;

    let el, footerHeight;

    let innerWidth;

    const resize = (e, delay) => {
        const bottom = el?.getBoundingClientRect().bottom;
        const top = el?.getBoundingClientRect().top;
        if(delay) {
            setTimeout(() => {
                resize(e, false);
            }, 100)
        } else {
            footerHeight = bottom - top;
        }
    }

	onMount(async () => {
		const res = await fetch('/api/checkVersion', {compress: true})
		const needUpdate = await res.json();
		outOfDate = needUpdate;
        resize(el?.getBoundingClientRect(), true);
	})

    let managersOutOfDate = false;
    if(managers) {
        for(const manager of managers) {
            if(manager.roster && !manager.managerID) {
                managersOutOfDate = true;
                resize(el?.getBoundingClientRect(), true);
                break;
            }
        }
    }

	const year = new Date().getFullYear();

	/*
	Flatten the nav into one list. Two entries need guarding, both by label, matching how
	NavLarge and NavSmall do it -- see the note in tabs.js:

	  Blog is hidden while enableBlog is false. The footer previously had NO such guard, so it
	  advertised a link to a disabled page that both navs correctly hid.
	  Managers is hidden while the managers array is empty.
	*/
	$: footerLinks = tabs
		.flatMap((tab) => (tab.nest ? tab.children : [tab]))
		.filter((link) => link.dest)
		.filter((link) => link.label != 'Blog' || enableBlog)
		.filter((link) => link.label != 'Managers' || managers.length > 0);

    $: resize(el?.getBoundingClientRect(), false, innerWidth);
</script>

<svelte:window bind:innerWidth={innerWidth} />

<style>
	footer {
		background-color: var(--navy050);
		width: 100%;
        display: block;
        position: absolute;
        bottom: 0;
		z-index: 1;
		border-top: 1px solid var(--accentBorder);
		padding: 2.5em 0 3.5em;
		text-align: center;
		color: var(--g555);
	}

	#navigation {
		margin: 0 auto 2em;
		width: 92%;
		max-width: 900px;
	}

	#navigation ul {
		margin: 0;
		padding: 0;
		/* A wrapping grid rather than a pipe-separated run: seventeen links on one line
		   reflowed into an unreadable block on a phone. */
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(9em, 1fr));
		gap: 0.15em 0.5em;
	}

	#navigation ul li {
		list-style-type: none;
	}

	.navLink {
		display: block;
		padding: 0.5em 0.4em;
		color: var(--navy700);
		text-decoration: none;
		font-family: var(--fontDisplay);
		font-size: 0.82em;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		border-radius: var(--radiusSm);
	}

	@media (hover: hover) {
		.navLink:hover {
			background-color: var(--fff);
			color: var(--accentInk);
		}
	}

	.navLink:focus-visible {
		outline: 2px solid var(--blueOne);
		outline-offset: -2px;
	}

	.credit {
		font-size: 0.82em;
		line-height: 1.7;
	}

	.credit a {
		color: var(--accentInk);
	}

	.updateNotice {
		color: var(--g555);
		font-style: italic;
		font-size: 0.8em;
		margin-top: 0;
	}
</style>

<div class="footerSpacer" style="height: {footerHeight}px;"></div>

<!-- footer with update notice -->
<footer bind:this={el}>
    {#if outOfDate}
	    <p class="updateNotice">There is an update available for your League Page. <a href="https://github.com/nmelhado/league-page/blob/master/TRAINING_WHEELS.md#iv-updates">Follow the Update Instructions</a> to get all of the newest features!</p>
    {/if}
    {#if managersOutOfDate}
	    <p class="updateNotice">Your managers page needs an update, <a href="https://github.com/nmelhado/league-page/blob/master/TRAINING_WHEELS.md#2-add-managers">please follow the instructions</a> to get the most up-to-date experience.</p>
    {/if}
	<nav id="navigation" aria-label="Footer">
		<ul>
			{#each footerLinks as link}
				<li>
					<!-- Off-site destinations (Sleeper, the Keeper Draft Board) open in a new tab
					     so a visitor never loses the league page to leave it. rel is not optional
					     with target=_blank: without noopener the opened page gets a window.opener
					     handle and can navigate ours out from under the reader. -->
					{#if /^https?:\/\//.test(link.dest)}
						<a class="navLink" href={link.dest} target="_blank" rel="noopener noreferrer">{link.label}</a>
					{:else}
						<a class="navLink" href={link.dest}>{link.label}</a>
					{/if}
				</li>
			{/each}
		</ul>
	</nav>
	<div class="credit">
		<!-- PLEASE DO NOT REMOVE THE COPYRIGHT -->
		<span class="copyright">&copy; 2021 - {year} <a href="https://github.com/nmelhado/league-page">League Page</a></span>
		<br />
		<!-- PLEASE DO NOT REMOVE THE BUILT BY -->
		<span class="creator">Built by <a href="http://www.nmelhado.com/">Nicholas Melhado</a><br /></span>
		<!-- You can remove the donation link (although any donations to help
		 maintain and enhance League Page would be greatly appreciated!) -->
		Love League Page? Please consider <a href="https://www.buymeacoffee.com/nmelhado">donating</a> to support enhancements or just to say thank you!
	</div>
</footer>
