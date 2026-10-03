<script>
    import { managerHref } from '$lib/utils/managerLink';
  	import { Row, Cell } from '@smui/data-table';

    export let columnOrder, team, standing, leagueTeamManagers;
</script>

<style>
    .clickable {
        cursor: pointer;
    }
	
	.teamAvatar {
		vertical-align: middle;
		border-radius: 50%;
		height: 40px;
		margin-right: 15px;
		border: 0.25px solid #777;
	}

    :global(.contrastRow) {
        background-color: var(--f8f8f8);
    }

    .team {
        display: block;
        text-align: center;
        color: inherit;
        text-decoration: none;
    }

    a.team:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }
</style>

<Row class="contrastRow">
    <Cell class="">
        <a class="clickable team" href={managerHref({leagueTeamManagers, rosterID: standing.rosterID})}>
            <img alt="team avatar" class="teamAvatar clickable" src="{team.avatar}" />
            <div>
                {team.name}
            </div>
        </a>
    </Cell>
    {#each columnOrder as column}
        <Cell class="center">{standing[column.field]}</Cell>
    {/each}
</Row>