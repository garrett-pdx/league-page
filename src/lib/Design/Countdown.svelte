<script>
    import { onMount, onDestroy } from 'svelte';

    /*
    Counts down to a timestamp. Purely presentational -- the caller decides what the event is
    and whether the target is still in the future.

    Deliberately renders NOTHING until mounted. A countdown is the one thing on the page that is
    guaranteed to be wrong by the time SSR HTML reaches the browser, and rendering a server-side
    value would both flash stale digits and produce a hydration mismatch on every load.
    */
    let {
        target,                 // epoch ms
        label = 'Countdown',
        expiredLabel = null,    // shown once the target passes; hides the block when null
        class: className = '',
    } = $props();

    let now = $state(null);
    let timer;

    onMount(() => {
        now = Date.now();
        timer = setInterval(() => { now = Date.now(); }, 1000);
    });

    onDestroy(() => {
        // setInterval survives client-side navigation otherwise -- this component is mounted on
        // the home page, which is the page people leave and come back to most.
        if(timer) clearInterval(timer);
    });

    const remaining = $derived(now === null || !target ? null : target - now);
    const expired = $derived(remaining !== null && remaining <= 0);

    const parts = $derived.by(() => {
        if(remaining === null || remaining <= 0) return null;
        const totalSeconds = Math.floor(remaining / 1000);
        return [
            {value: Math.floor(totalSeconds / 86400), unit: 'days'},
            {value: Math.floor(totalSeconds / 3600) % 24, unit: 'hrs'},
            {value: Math.floor(totalSeconds / 60) % 60, unit: 'min'},
            {value: totalSeconds % 60, unit: 'sec'},
        ];
    });

    const pad = (n) => String(n).padStart(2, '0');
</script>

<style>
    .countdown {
        text-align: center;
    }

    .label {
        display: block;
        font-family: var(--fontDisplay);
        font-size: 0.72em;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: var(--g555);
        margin-bottom: 0.5em;
    }

    .clock {
        display: flex;
        justify-content: center;
        align-items: flex-start;
        gap: 0.15em;
    }

    .part {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 2.6em;
    }

    .num {
        font-family: var(--fontMono);
        font-size: 1.75em;
        font-weight: 700;
        line-height: 1;
        color: var(--navy700);
        font-variant-numeric: tabular-nums;
    }

    .unit {
        font-family: var(--fontDisplay);
        font-size: 0.6em;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--g555);
        margin-top: 0.35em;
    }

    .colon {
        font-family: var(--fontMono);
        font-size: 1.75em;
        font-weight: 700;
        line-height: 1;
        color: var(--ccc);
    }

    .expired {
        font-family: var(--fontDisplay);
        font-size: 1.2em;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--navy700);
    }

    @media (max-width: 400px) {
        .num, .colon { font-size: 1.4em; }
        .part { min-width: 2.2em; }
    }
</style>

{#if parts}
    <div class="countdown {className}">
        <span class="label">{label}</span>
        <div class="clock">
            {#each parts as part, i}
                {#if i > 0}<span class="colon" aria-hidden="true">:</span>{/if}
                <span class="part">
                    <span class="num">{pad(part.value)}</span>
                    <span class="unit">{part.unit}</span>
                </span>
            {/each}
        </div>
    </div>
{:else if expired && expiredLabel}
    <div class="countdown {className}">
        <span class="label">{label}</span>
        <span class="expired">{expiredLabel}</span>
    </div>
{/if}
