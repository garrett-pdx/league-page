<script>
	import { tabs, findTab, currentDest } from '$lib/utils/tabs';
	import Tab, { Icon, Label } from '@smui/tab';
	import List, { Item, Graphic, Text, Meta, Separator } from '@smui/list';
	import TabBar from '@smui/tab-bar';
    import { page } from '$app/state';
	import { goto, preloadData } from '$app/navigation';
	import { enableBlog, managers } from '$lib/utils/leagueInfo';

	// The highlight has to follow client-side navigation: the nav never remounts, so a value
	// captured once kept underlining the page you landed on. It can't be a plain $derived
	// because SMUI's TabBar writes to it through bind:active (clicking League lights League),
	// so it stays $state and is re-synced whenever the path changes, and again when the
	// dropdown closes without a navigation. findTab matches a tab or any of its children, and
	// treats /manager as Managers.
	//
	// SMUI's TabBar can move the highlight but never clear it (activateTab(-1) is a no-op), so
	// a page outside the nav -- the home page, now there's no Home tab -- would keep the last
	// page's tab lit. `noTab` is a hidden placeholder for those pages to activate instead.
	const noTab = { key: 'none', label: '', hidden: true };
	const barTabs = [...tabs, noTab];
	const tabFor = (pathname) => findTab(pathname)[0] || noTab;

	let active = $state(tabFor(page.url.pathname));
	const syncActive = () => {
		active = tabFor(page.url.pathname);
	}
	$effect(syncActive);

	// The current dropdown entry, for its `activated` state.
	let activeDest = $derived(currentDest(page.url.pathname));

	const isExternal = (dest) => /^https?:\/\//.test(dest);

	let display = $state(false);
	let el = $state();
	let listEl = $state();
	let menuHeight = $state(0);
	let width = $state();
	let height= $state();
	let left = $state();
	let top = $state();

	// The dropdown is at least this wide, so "Keeper Draft Board" and its off-site icon fit
	// under a tab as short as "League", and it is right-aligned to that tab: League is the
	// last tab, and a left-aligned menu wider than it would run off the right of the screen.
	const MIN_MENU_WIDTH = 240;

	// Re-measured on every open, not just at mount: the Oswald swap-in and any resize both
	// move the tab after the first measurement.
	const measure = () => {
		const rect = el?.getBoundingClientRect();
		top = rect ? rect.top : 0;
		height = rect ? rect.bottom - rect.top + 1 : 1;
		width = rect ? Math.max(rect.right - rect.left, MIN_MENU_WIDTH) : MIN_MENU_WIDTH;
		left = rect ? rect.right - width : 0;
	}

	$effect(measure);

	let innerWidth = $state();

	const open = () => {
		display = !display;
		if(display) {
			measure();
			// Group captions make the old `49 * children` estimate wrong, so use the list's
			// real height.
			menuHeight = listEl?.scrollHeight ?? 0;
		} else {
			// Clicking League lights League. Closing the menu without going anywhere -- click
			// away, click League again, or pick an off-site link -- must hand the highlight
			// back to the page we're on. Deferred so it lands after the TabBar's own click
			// handling; after an internal navigation it's a no-op the path effect repeats.
			setTimeout(syncActive);
		}
	}

	// SvelteKit 2's goto() throws on external URLs ("Cannot use `goto` with an
	// external URL"), which silently breaks any tab pointing off-site -- Go to
	// Sleeper, and the Keeper Draft Board. Open those in a NEW tab: a nav click should
	// never cost you the page you were on, and noopener stops the opened page getting a
	// window.opener handle it could navigate ours with.
	const navigate = (dest) => {
		if(/^https?:\/\//.test(dest)) {
			window.open(dest, '_blank', 'noopener,noreferrer');
			return;
		}
		goto(dest);
	}

	// preloadData() only understands this app's own routes, so handing it an off-site
	// URL is the same mistake as goto(). Upstream guarded it by label
	// (`label != 'Go to Sleeper'`), which silently stopped covering anything once a
	// second external tab existed -- ours is the Keeper Draft Board. Test the
	// destination instead, exactly like navigate() above.
	const preload = (dest) => {
		if(/^https?:\/\//.test(dest)) return;
		preloadData(dest);
	}

	const subGoto = (dest) => {
		open(false);
		navigate(dest);
	}

	let tabChildren = $state([]);

	for(const tab of tabs) {
		if(tab.nest) {
			tabChildren = tab.children;
		}
	}

</script>

<svelte:window bind:innerWidth={innerWidth} />

<style>
    :global(.navBar) {
		display: inline-flex;
		position: relative;
    	justify-content: center;
    }

	:global(.navBar .material-icons) {
		font-size: 1.8em;
		height: 25px;
		width: 22px;
	}

	.parent {
		position: relative;
	}

	.subMenu {
		overflow-y: hidden;
		display: block;
		position: absolute;
		z-index: 5;
		background-color: var(--fff);
		transition: all 0.4s;
	}

	.overlay {
		display: block;
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		height: 100vh;
		z-index: 4;
	}

	:global(.mdc-deprecated-list) {
		padding: 0;
	}

	:global(.subText) {
		font-size: 0.8em;
	}

	/* Seven tabs at MDC's stock 24px side padding come to ~1,050px, wider than the 951px
	   where this bar takes over from NavSmall. At 12px they measure 885px, which fits; with
	   room to spare (1100px+), 20px (~997px) spaces them out again. */
	:global(.navBar .mdc-tab) {
		padding-left: 12px;
		padding-right: 12px;
	}

	@media (min-width: 1100px) {
		:global(.navBar .mdc-tab) {
			padding-left: 20px;
			padding-right: 20px;
		}
	}

	.caret {
		font-size: 18px;
		vertical-align: middle;
		margin-left: 2px;
	}

	/* A group heading from tabs.js ({ group: 'History' }): a caption, not a destination. */
	.groupCaption {
		list-style: none;
		padding: 10px 16px 4px;
		font-family: var(--fontDisplay);
		font-size: 12px;
		font-weight: 500;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--g555);
	}

	.groupCaption:not(:first-child) {
		border-top: 1px solid var(--accentBorder);
	}

	:global(.subMenu .externalIcon) {
		font-size: 16px;
		color: var(--g555);
	}

	.srOnly {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip: rect(0 0 0 0);
		white-space: nowrap;
	}

	:global(.dontDisplay) {
		display: none;
	}
</style>

<div tabindex="0" role="button" class="overlay" style="display: {display ? "block" : "none"};" onclick={() => open(true)}></div>

<div class="parent">
	<TabBar class="navBar" tabs={barTabs} key={(tab) => tab.key} bind:active>
		{#snippet tab(tab)}
			{#if tab.hidden}
				<Tab class="dontDisplay" {tab} tabindex="-1" aria-hidden="true"><Label></Label></Tab>
			{:else if tab.nest}
				<div bind:this={el}>
					<Tab
						{tab}
						minWidth
						onclick={() => open()}
					>
						<Icon class="material-icons">{tab.icon}</Icon>
						<Label>{tab.label}<span class="material-icons caret" aria-hidden="true">expand_more</span></Label>
					</Tab>
				</div>
			{:else}
				<Tab
					class="{(tab.label == 'Blog' && !enableBlog) || (tab.label == 'Managers' && !managers.length) ? 'dontDisplay' : ''}"
					{tab}
					onTouchstart={() => preload(tab.dest)}
					onMouseover={() => preload(tab.dest)}
					href={tab.dest}
					minWidth
				>
					<Icon class="material-icons">{tab.icon}</Icon>
					<Label>{tab.label}</Label>
				</Tab>
			{/if}
		{/snippet}
	</TabBar>
	<div class="subMenu" style="max-height: {display ? menuHeight + 1 : 0}px; width: {width}px; top: {height}px; left: {left}px; box-shadow: 0 0 {display ? "3px" : "0"} 0 var(--blueOne); border: {display ? "1px" : "0"} solid var(--blueOne); border-top: none;">
		<div bind:this={listEl}>
		<List>
			{#each tabChildren as subTab, ix}
				{#if subTab.group}
					<li class="groupCaption">{subTab.group}</li>
				{:else if subTab.label == 'Managers'}
					<Item class="{managers.length ? '' : 'dontDisplay'}" onSMUIAction={() => subGoto(subTab.dest)} ontouchstart={() => preload(subTab.dest)} onmouseover={() => preload(subTab.dest)}>
						<Graphic class="material-icons">{subTab.icon}</Graphic>
						<Text class="subText">{subTab.label}</Text>
					</Item>
					{#if ix != tabChildren.length - 1}
						<Separator />
					{/if}
				{:else}
					<Item onSMUIAction={() => subGoto(subTab.dest)} ontouchstart={() => preload(subTab.dest)} onmouseover={() => preload(subTab.dest)} activated={activeDest == subTab.dest}>
						<Graphic class="material-icons">{subTab.icon}</Graphic>
						<Text class="subText">{subTab.label}{#if isExternal(subTab.dest)}<span class="srOnly"> (opens in a new tab)</span>{/if}</Text>
						{#if isExternal(subTab.dest)}
							<Meta class="material-icons externalIcon" aria-hidden="true">open_in_new</Meta>
						{/if}
					</Item>
					{#if ix != tabChildren.length - 1 && !tabChildren[ix + 1].group}
						<Separator />
					{/if}
				{/if}
			{/each}
		</List>
		</div>
	</div>
</div>
