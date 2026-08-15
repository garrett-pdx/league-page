/*
Design primitives for The Mudd League. Import as: import { Card, StatTile } from '$lib/Design';

Deliberately a SEPARATE barrel from $lib/components. That file is byte-identical to
nmelhado/league-page and gains entries on most upstream releases, so adding to it would conflict
for the sake of three lines. $lib/components stays "upstream's page-level feature components";
this stays "our design layer".

Tokens these consume live in src/theme/_tokens.scss.
*/
export { default as Card } from './Card.svelte';
export { default as StatTile } from './StatTile.svelte';
export { default as SectionHeading } from './SectionHeading.svelte';
export { default as SegmentedControl } from './SegmentedControl.svelte';
