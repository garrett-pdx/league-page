<script>
	import { tabs, currentDest } from '$lib/utils/tabs';
	import Drawer, {
	  Content,
	  Header,
	  Title,
	} from '@smui/drawer';
	import { Icon } from '@smui/tab';
  	import List, { Item, Text, Graphic, Meta, Separator, Subheader } from '@smui/list';
	import { goto, preloadData } from '$app/navigation';
    import { page } from '$app/state';
	import { leagueName } from '$lib/utils/helper';
	import { enableBlog, managers } from '$lib/utils/leagueInfo';

	// Derived, not captured once: client-side navigation never remounts the nav, so a value
	// read at mount kept highlighting the page you landed on. currentDest (tabs.js) also
	// lights Managers on /manager and Blog on a post.
	let active = $derived(currentDest(page.url.pathname));

	const isExternal = (dest) => /^https?:\/\//.test(dest);

	let open = $state(false);

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

	// Same reasoning as navigate(): preloadData() only understands this app's own routes.
	// Upstream guarded it by label (`label != 'Go to Sleeper'`), which stopped covering
	// everything as soon as a second external tab existed. Test the destination.
	const preload = (dest) => {
		if(/^https?:\/\//.test(dest)) return;
		preloadData(dest);
	}

	const selectTab = (tab) => {
		open = false;
		navigate(tab.dest);
	}
</script>

<style>
	:global(.menuIcon) {
		position: absolute;
		top: 15px;
		left: 15px;
		font-size: 2em;
		color: #888;
		padding: 6px;
		cursor: pointer;
	}

	:global(.menuIcon:hover) {
		color: var(--blueOne);
	}

	:global(.nav-drawer) {
		z-index: 9;
		top: 0;
		left: 0;
	}

	:global(.nav-item) {
		color: #858585 !important;
	}

	:global(.nav-drawer .externalIcon) {
		font-size: 18px;
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

	.nav-back {
		position: fixed;
		z-index: 8;
		width: 100%;
		width: 100vw;
		height: 100%;
		height: 100vh;
		top: 0;
		left: 0;
		background-color: rgba(0, 0, 0, 0.32);
		transition: all 0.7s;
	}
</style>

<Icon class="material-icons menuIcon" onclick={() => open = true} ripple={false} touch={true}>menu</Icon>

<div class="nav-back" style="pointer-events: {open ? "visible" : "none"}; opacity: {open ? 1 : 0};" onclick={() => open = false}></div>

<Drawer variant="modal" class="nav-drawer" fixed={true} bind:open>
	<Header>
		<Title>{leagueName}</Title>
	</Header>
	<Content>
		<List>
			{#each tabs as tab}
				{#if !tab.nest && (tab.label != 'Blog' || enableBlog) && (tab.label != 'Managers' || managers.length)}
					<Item href="javascript:void(0)" onSMUIAction={() => selectTab(tab)} ontouchstart={() => preload(tab.dest)} onmouseover={() => preload(tab.dest)} activated={active == tab.dest} >
						<Graphic class="material-icons{active == tab.dest ? "" : " nav-item"}" aria-hidden="true">{tab.icon}</Graphic>
						<Text class="{active == tab.dest ? "" : "nav-item"}">{tab.label}</Text>
					</Item>
				{/if}
			{/each}
			{#each tabs as tab}
				{#if tab.nest}
					<Separator />
					{#if !tab.children[0]?.group}
						<Subheader>{tab.label}</Subheader>
					{/if}
					{#each tab.children as subTab}
						{#if subTab.group}
							<!-- a group heading from tabs.js, not a destination -->
							<Subheader>{subTab.group}</Subheader>
						{:else if subTab.label == 'Managers'}
							{#if managers.length}
								<Item href="javascript:void(0)" onSMUIAction={() => selectTab(subTab)} activated={active == subTab.dest}  ontouchstart={() => preload(subTab.dest)} onmouseover={() => preload(subTab.dest)}>
									<Graphic class="material-icons{active == subTab.dest ? "" : " nav-item"}" aria-hidden="true">{subTab.icon}</Graphic>
									<Text class="{active == subTab.dest ? "" : "nav-item"}">{subTab.label}</Text>
								</Item>
							{/if}
						{:else}
							<Item href="javascript:void(0)" onSMUIAction={() => selectTab(subTab)} activated={active == subTab.dest}  ontouchstart={() => preload(subTab.dest)} onmouseover={() => preload(subTab.dest)}>
								<Graphic class="material-icons{active == subTab.dest ? "" : " nav-item"}" aria-hidden="true">{subTab.icon}</Graphic>
								<Text class="{active == subTab.dest ? "" : "nav-item"}">{subTab.label}{#if isExternal(subTab.dest)}<span class="srOnly"> (opens in a new tab)</span>{/if}</Text>
								{#if isExternal(subTab.dest)}
									<Meta class="material-icons externalIcon" aria-hidden="true">open_in_new</Meta>
								{/if}
							</Item>
						{/if}
					{/each}
				{/if}
			{/each}
		</List>
	</Content>
  </Drawer>
	
