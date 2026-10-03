/*
The two pieces of d3-scale Stat Lab actually needs -- a linear map and "nice" round ticks -- in
twenty lines, rather than a dependency. Pure; Node can import it.
*/

/** Round tick values covering [min, max], about `count` of them, on a 1/2/5 x 10^n step. */
export const niceTicks = (min, max, count = 5) => {
    if(!Number.isFinite(min) || !Number.isFinite(max)) return { ticks: [0, 1], lo: 0, hi: 1 };
    if(min === max) {
        const pad = Math.abs(min) * 0.1 || 1;
        min -= pad;
        max += pad;
    }
    const raw = (max - min) / count;
    let step = 10 ** Math.floor(Math.log10(raw));
    const err = raw / step;
    if(err >= 7.5) step *= 10;
    else if(err >= 3.5) step *= 5;
    else if(err >= 1.5) step *= 2;
    const lo = Math.floor(min / step) * step;
    const hi = Math.ceil(max / step) * step;
    const ticks = [];
    // the epsilon keeps floating-point drift from dropping the last tick
    for(let v = lo; v <= hi + step * 1e-9; v += step) ticks.push(Math.round(v / step) * step);
    return { ticks, lo, hi, step };
};

/** A linear map from [d0, d1] to [r0, r1]. */
export const linear = ([d0, d1], [r0, r1]) => {
    const k = d1 === d0 ? 0 : (r1 - r0) / (d1 - d0);
    return (v) => r0 + (v - d0) * k;
};

/** Tick text: percentages as whole or one-decimal %, points without needless decimals. */
export const tickText = (v, fmt, step) => {
    if(fmt === 'pct') return `${(v * 100).toFixed(step * 100 < 1 ? 1 : 0)}%`;
    const decimals = step < 1 ? (step < 0.1 ? 2 : 1) : 0;
    const s = Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
    if(v < 0) return `−${s}`;
    if(fmt === 'signed' && v > 0) return `+${s}`;
    return s;
};

/**
 * A beeswarm: given each dot's x, return each dot's vertical offset so no two dots overlap, as far
 * as `maxOff` allows. Dots are placed left to right, each at the offset nearest the centre line
 * (0, +1, -1, +2 ...) that clears every dot already placed. Deterministic, so a chart never
 * reshuffles on re-render the way random jitter does. If a crowd is deeper than `maxOff` allows,
 * a dot takes the offset where it overlaps least rather than leaving the row.
 */
export const swarm = (xs, r, maxOff) => {
    const gap = 2 * r + 0.5;
    const order = xs.map((_, i) => i).sort((a, b) => xs[a] - xs[b] || a - b);
    const placed = [];
    const out = new Array(xs.length).fill(0);
    for(const i of order) {
        const x = xs[i];
        let best = 0, bestClear = -1;
        search:
        for(let k = 0; k <= maxOff; k++) {
            for(const y of k === 0 ? [0] : [k, -k]) {
                let clear = Infinity;
                // placed[] is in ascending x, so once a neighbour is further left than one gap, all earlier ones are
                for(let j = placed.length - 1; j >= 0; j--) {
                    const dx = x - placed[j].x;
                    if(dx > gap) break;
                    const d = Math.hypot(dx, y - placed[j].y);
                    if(d < clear) clear = d;
                }
                if(clear >= gap) { best = y; bestClear = Infinity; break search; }
                if(clear > bestClear) { bestClear = clear; best = y; }
            }
        }
        out[i] = best;
        placed.push({ x, y: best });
    }
    return out;
};
